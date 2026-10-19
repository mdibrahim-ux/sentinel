from __future__ import annotations

import io
import re
import zipfile
from datetime import datetime, timezone
from urllib.parse import quote, urlparse, urljoin
from typing import Any

import httpx
from fastapi import HTTPException, UploadFile

from app.config import MAX_FILES, MAX_UPLOAD_BYTES, MAX_FILE_BYTES
from app.services.analyzer import SKIP_PARTS, SOURCE_EXTENSIONS, TEXT_EXTENSIONS, _normalize_path

GITHUB_REPO_RE = re.compile(r"^[A-Za-z0-9_.-]{1,100}$")


def validate_github_repo_url(url: str) -> tuple[str, str, str | None]:
    """Accept only standard github.com repo URLs; reject arbitrary hosts and URL tricks."""
    try:
        parsed = urlparse(url.strip())
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="Enter a valid GitHub repository URL.") from exc
    if parsed.scheme != "https" or parsed.hostname not in {"github.com", "www.github.com"}:
        raise HTTPException(status_code=422, detail="Only https://github.com/OWNER/REPO URLs are supported.")
    if parsed.username or parsed.password or parsed.port or parsed.query or parsed.fragment:
        raise HTTPException(status_code=422, detail="The repository URL must not contain credentials, a port, query, or fragment.")
    parts = [p for p in parsed.path.split("/") if p]
    if len(parts) not in {2, 4} or (len(parts) == 4 and parts[2] != "tree"):
        raise HTTPException(status_code=422, detail="Use a repository URL or a branch URL ending in /tree/BRANCH.")
    owner, repo = parts[0], parts[1].removesuffix(".git")
    branch = parts[3] if len(parts) == 4 else None
    if not GITHUB_REPO_RE.fullmatch(owner) or not GITHUB_REPO_RE.fullmatch(repo):
        raise HTTPException(status_code=422, detail="Owner or repository name contains unsupported characters.")
    if branch and (len(branch) > 120 or branch.startswith("-") or ".." in branch or "\\" in branch or "\x00" in branch):
        raise HTTPException(status_code=422, detail="Branch name contains unsupported characters.")
    return owner, repo, branch


async def _fetch_limited(client: httpx.AsyncClient, url: str, max_bytes: int) -> bytes:
    """Fetch a bounded response without trusting redirects or Content-Length headers."""
    current_url = url
    allowed_hosts = {"codeload.github.com", "github.com", "api.github.com"}
    for _ in range(4):
        try:
            parsed = urlparse(current_url)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail="GitHub returned an invalid download URL.") from exc
        if parsed.scheme != "https" or parsed.hostname not in allowed_hosts or parsed.username or parsed.password or parsed.port:
            raise HTTPException(status_code=422, detail="GitHub redirected to a URL outside the trusted download hosts.")
        async with client.stream("GET", current_url, follow_redirects=False, timeout=20.0) as response:
            if response.status_code in {301, 302, 303, 307, 308}:
                location = response.headers.get("location")
                if not location:
                    raise HTTPException(status_code=502, detail="GitHub returned an incomplete redirect.")
                current_url = urljoin(current_url, location)
                continue
            if response.status_code == 404:
                raise HTTPException(status_code=404, detail="Repository or branch was not found, or the repository is private.")
            if response.status_code in {401, 403}:
                raise HTTPException(status_code=403, detail="GitHub denied access. Only public repositories are supported without an authorization integration.")
            response.raise_for_status()
            size = response.headers.get("content-length")
            if size and size.isdigit() and int(size) > max_bytes:
                raise HTTPException(status_code=413, detail=f"Repository archive exceeds the {max_bytes // (1024 * 1024)} MB input limit.")
            chunks: list[bytes] = []
            received = 0
            async for chunk in response.aiter_bytes(64 * 1024):
                received += len(chunk)
                if received > max_bytes:
                    raise HTTPException(status_code=413, detail=f"Repository archive exceeds the {max_bytes // (1024 * 1024)} MB input limit.")
                chunks.append(chunk)
            return b"".join(chunks)
    raise HTTPException(status_code=502, detail="GitHub returned too many redirects.")


async def fetch_github_archive(repository_url: str, requested_branch: str = "main") -> tuple[dict[str, bytes], dict[str, Any]]:
    owner, repo, url_branch = validate_github_repo_url(repository_url)
    branch = url_branch or requested_branch
    if len(branch) > 120 or branch.startswith("-") or ".." in branch or "\\" in branch:
        raise HTTPException(status_code=422, detail="Branch name contains unsupported characters.")
    api_url = f"https://api.github.com/repos/{quote(owner)}/{quote(repo)}"
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "Sentinal-Codebase-Analyzer/0.1"}
    async with httpx.AsyncClient(headers=headers) as client:
        try:
            info_response = await client.get(api_url, follow_redirects=False, timeout=10.0)
            if info_response.status_code == 404:
                raise HTTPException(status_code=404, detail="Repository was not found or is private.")
            if info_response.status_code in {401, 403}:
                raise HTTPException(status_code=403, detail="Repository requires authorization; private GitHub access is not enabled in this build.")
            info_response.raise_for_status()
            info = info_response.json()
            if not url_branch and requested_branch == "main":
                branch = info.get("default_branch") or "main"
            archive_url = f"https://codeload.github.com/{quote(owner)}/{quote(repo)}/zip/refs/heads/{quote(branch, safe='/') }"
            raw = await _fetch_limited(client, archive_url, MAX_UPLOAD_BYTES)
        except HTTPException:
            raise
        except httpx.HTTPError as exc:
            raise HTTPException(status_code=502, detail="Could not safely fetch the public repository from GitHub.") from exc
    files = archive_to_files(raw)
    if not files:
        raise HTTPException(status_code=422, detail="The archive contained no supported text/source files.")
    return files, {"type": "github", "repo_name": info.get("full_name", f"{owner}/{repo}"),
                   "repository_url": f"https://github.com/{owner}/{repo}", "branch": branch,
                   "commit_sha": "unknown; archive endpoint does not guarantee a commit identifier",
                   "snapshot_at": datetime.now(timezone.utc).isoformat()}


def archive_to_files(raw: bytes) -> dict[str, bytes]:
    if len(raw) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail=f"ZIP file exceeds the {MAX_UPLOAD_BYTES // (1024 * 1024)} MB limit.")
    files: dict[str, bytes] = {}
    total_uncompressed = 0
    try:
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            infos = archive.infolist()
            if len(infos) > MAX_FILES * 4:
                raise HTTPException(status_code=413, detail=f"Archive contains too many entries; maximum is {MAX_FILES * 4}.")
            for info in infos:
                if info.is_dir():
                    continue
                path = _normalize_path(info.filename)
                if not path:
                    continue
                parts = path.split("/")
                if any(p in SKIP_PARTS for p in parts):
                    continue
                # GitHub archives have a common root directory; remove it for stable paths.
                if len(parts) > 1 and (parts[0].endswith("-main") or parts[0].endswith("-master") or re.match(r".+-[0-9a-f]{7,40}$", parts[0])):
                    path = "/".join(parts[1:])
                if not path or path in files:
                    continue
                basename = path.rsplit("/", 1)[-1].lower()
                is_text = any(path.lower().endswith(ext) for ext in TEXT_EXTENSIONS)
                if basename.startswith("dockerfile") or basename == "makefile":
                    is_text = True
                if not is_text:
                    continue
                if info.file_size > MAX_FILE_BYTES or info.file_size < 0:
                    continue
                total_uncompressed += info.file_size
                if total_uncompressed > MAX_UPLOAD_BYTES * 4:
                    raise HTTPException(status_code=413, detail="Expanded archive exceeds the safe uncompressed size limit.")
                if len(files) >= MAX_FILES:
                    raise HTTPException(status_code=413, detail=f"Archive contains more than {MAX_FILES} supported files.")
                if info.compress_size and info.file_size / info.compress_size > 250:
                    raise HTTPException(status_code=413, detail="Archive contains an unusually compressed entry and was rejected.")
                with archive.open(info) as f:
                    content = f.read(MAX_FILE_BYTES + 1)
                if len(content) <= MAX_FILE_BYTES and b"\x00" not in content[:4096]:
                    files[path] = content
    except zipfile.BadZipFile as exc:
        raise HTTPException(status_code=422, detail="The uploaded file is not a valid ZIP archive.") from exc
    return files


async def read_upload(upload: UploadFile) -> dict[str, bytes]:
    if not upload.filename or not upload.filename.lower().endswith(".zip"):
        raise HTTPException(status_code=415, detail="Upload a .zip archive containing source files.")
    raw = await upload.read(MAX_UPLOAD_BYTES + 1)
    if len(raw) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail=f"Upload exceeds the {MAX_UPLOAD_BYTES // (1024 * 1024)} MB limit.")
    return archive_to_files(raw)
