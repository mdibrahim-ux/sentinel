from __future__ import annotations

import json
import logging
import traceback
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import boto3
from fastapi import BackgroundTasks, FastAPI, File, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse
try:
    from mangum import Mangum
except ImportError:  # Local test environments may omit the Lambda-only adapter.
    Mangum = None  # type: ignore[assignment,misc]

from app.config import AI_PROVIDER, AWS_REGION, MAX_UPLOAD_BYTES, OPENROUTER_API_KEY, REPORT_DIR, UPLOAD_DIR, SENTINAL_STATE_MACHINE_ARN
from app.schemas import AnalysisRequest, AskSentinalRequest, FindingStatusUpdate, ProfilePayload
from app.services.cloud_state import (delete_object, enabled as cloud_enabled, get_job as cloud_get_job,
                                      list_history as cloud_history, presigned_get, save_job as cloud_save_job,
                                      upload_bytes, get_profile as cloud_get_profile, save_profile as cloud_save_profile)
from app.services.pipeline import create_job, process_local_job
from app.services.ai_explainer import answer_question
from app.services.repository import read_upload, validate_github_repo_url
from app.services.store import now_iso, store

app = FastAPI(title="Sentinal API", version="0.1.0", description="Evidence-based codebase analysis and PDF reporting.")
app.add_middleware(CORSMiddleware, allow_origins=[x.strip() for x in __import__("os").getenv("SENTINAL_CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",") if x.strip()], allow_credentials=False, allow_methods=["GET", "POST", "PUT", "PATCH", "OPTIONS"], allow_headers=["Authorization", "Content-Type"])


def _owner(request: Request) -> str:
    if not cloud_enabled():
        return "local-user"
    event = request.scope.get("aws.event", {})
    claims = event.get("requestContext", {}).get("authorizer", {}).get("jwt", {}).get("claims", {})
    return str(claims.get("sub", ""))


def _load_job(job_id: str, owner_id: str) -> dict[str, Any]:
    job = cloud_get_job(job_id) if cloud_enabled() else store.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Analysis job not found.")
    if cloud_enabled() and (not owner_id or job.get("owner_id") != owner_id):
        raise HTTPException(status_code=404, detail="Analysis job not found.")
    return job


def _submit_job(job: dict[str, Any], background_tasks: BackgroundTasks) -> dict[str, Any]:
    job["updated_at"] = now_iso()
    if cloud_enabled():
        if not SENTINAL_STATE_MACHINE_ARN:
            raise HTTPException(status_code=503, detail="AWS workflow is not configured. Check deployment outputs and environment variables.")
        cloud_save_job(job)
        try:
            boto3.client("stepfunctions", region_name=AWS_REGION).start_execution(
                stateMachineArn=SENTINAL_STATE_MACHINE_ARN,
                name=f"sentinal-{job['id']}-{uuid.uuid4().hex[:6]}",
                input=json.dumps({"job_id": job["id"], "action": "analyze"}))
        except Exception as exc:
            job["status"] = "failed"; job["error"] = f"Could not start AWS workflow ({type(exc).__name__})."; cloud_save_job(job)
            raise HTTPException(status_code=503, detail="Could not start the analysis workflow. No source content was logged.") from exc
    else:
        store.save(job)
        background_tasks.add_task(process_local_job, job["id"])
    return {"id": job["id"], "project": job["project"], "status": job["status"], "progress": job.get("progress", 0), "created_at": job["created_at"], "status_url": f"/api/analysis/{job['id']}"}


@app.get("/api/profile/github/{username}")
def github_profile(username: str, request: Request) -> dict[str, Any]:
    owner = _owner(request)
    if cloud_enabled() and not owner:
        raise HTTPException(status_code=401, detail="Authentication required.")
    if not username or len(username) > 39 or not __import__("re").fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?", username):
        raise HTTPException(status_code=422, detail="Enter a valid GitHub username.")
    try:
        import httpx
        headers = {"Accept": "application/vnd.github+json", "User-Agent": "Sentinal-Codebase-Intelligence"}
        with httpx.Client(timeout=5.0, follow_redirects=False, headers=headers) as client:
            response = client.get(f"https://api.github.com/users/{username}")
            if response.status_code == 404:
                raise HTTPException(status_code=404, detail="This GitHub username was not found.")
            response.raise_for_status()
            user_data = response.json()
            repo_response = client.get(f"https://api.github.com/users/{username}/repos", params={"sort": "updated", "per_page": 5, "type": "owner"})
            repo_response.raise_for_status()
            repos = repo_response.json()
        return {"login": user_data.get("login", username), "name": user_data.get("name"),
                "avatar_url": user_data.get("avatar_url", ""), "html_url": user_data.get("html_url", f"https://github.com/{username}"),
                "public_repos": int(user_data.get("public_repos", 0)), "followers": int(user_data.get("followers", 0)),
                "following": int(user_data.get("following", 0)), "bio": user_data.get("bio"),
                "repositories": [{"name": row.get("name", ""), "html_url": row.get("html_url", ""),
                                  "description": row.get("description"), "language": row.get("language"),
                                  "stargazers_count": int(row.get("stargazers_count", 0)), "updated_at": row.get("updated_at", "")} for row in repos if isinstance(row, dict)]}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail="GitHub's public API is unavailable or rate-limited. Try again later.") from exc


@app.get("/api/profile")
def get_profile(request: Request) -> dict[str, Any]:
    owner = _owner(request)
    if cloud_enabled() and not owner:
        raise HTTPException(status_code=401, detail="Authentication required.")
    try:
        profile = cloud_get_profile(owner) if cloud_enabled() else store.get_profile(owner)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    if profile is None:
        claims = request.scope.get("aws.event", {}).get("requestContext", {}).get("authorizer", {}).get("jwt", {}).get("claims", {})
        email = str(claims.get("email", ""))
        username = email.split("@", 1)[0] if email else ""
        profile = {"full_name": "", "username": username, "headline": "", "bio": "", "location": "",
                   "website": "", "email": email, "email_public": False, "github_username": "", "github_url": "",
                   "preferred_languages": [], "technical_skills": [], "interests": [], "role": "", "avatar_data_url": "",
                   "default_dashboard": "Home", "notifications_enabled": True, "privacy_profile_public": False,
                   "created_at": "", "updated_at": ""}
    return profile


@app.put("/api/profile")
def put_profile(payload: ProfilePayload, request: Request) -> dict[str, Any]:
    owner = _owner(request)
    if cloud_enabled() and not owner:
        raise HTTPException(status_code=401, detail="Authentication required.")
    profile = payload.model_dump()
    if len(profile.get("avatar_data_url", "")) > 350000:
        raise HTTPException(status_code=413, detail="Profile images must be 256 KB or smaller.")
    try:
        return cloud_save_profile(owner, profile) if cloud_enabled() else store.save_profile(owner, profile)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Could not save profile ({type(exc).__name__}).") from exc


@app.get("/api/health")
def health() -> dict[str, Any]:
    return {"name": "Sentinal", "status": "ok", "version": "0.1.0", "execution_mode": "aws" if cloud_enabled() else "local", "ai_provider": __import__("app.config", fromlist=["AI_PROVIDER"]).AI_PROVIDER}


@app.get("/api/analysis/history")
def history(request: Request, limit: int = 20) -> dict[str, Any]:
    if cloud_enabled():
        owner = _owner(request)
        if not owner:
            raise HTTPException(status_code=401, detail="Authentication required.")
        return {"items": cloud_history(owner, limit)}
    return {"items": store.history(limit)}


@app.post("/api/analysis")
def submit_analysis(payload: AnalysisRequest, request: Request, background_tasks: BackgroundTasks) -> dict[str, Any]:
    owner = _owner(request)
    if cloud_enabled() and not owner:
        raise HTTPException(status_code=401, detail="Authentication required.")
    # Validate host and URL shape before queueing network access.
    validate_github_repo_url(payload.repository_url)
    job = create_job({"type": "github", "repository_url": payload.repository_url, "branch": payload.branch},
                     payload.project_label, {"include_security": payload.include_security, "include_quality": payload.include_quality, "include_architecture": payload.include_architecture}, payload.audience)
    job["owner_id"] = owner
    # If URL contains a /tree/branch path, the repository intake uses that explicit branch.
    return _submit_job(job, background_tasks)


@app.post("/api/analysis/upload")
async def upload_analysis(request: Request, background_tasks: BackgroundTasks, file: UploadFile = File(...), project_label: str = "", include_security: bool = True, include_quality: bool = True, include_architecture: bool = True, audience: str = "developer") -> dict[str, Any]:
    owner = _owner(request)
    if cloud_enabled() and not owner:
        raise HTTPException(status_code=401, detail="Authentication required.")
    if audience not in {"mentor", "developer"}:
        raise HTTPException(status_code=422, detail="Audience must be 'mentor' or 'developer'.")
    files = await read_upload(file)
    if not files:
        raise HTTPException(status_code=422, detail="The ZIP does not contain any supported source or text files.")
    job = create_job({"type": "upload", "filename": file.filename or "source.zip", "source_files": len(files)}, project_label,
                     {"include_security": include_security, "include_quality": include_quality, "include_architecture": include_architecture}, audience)
    job["owner_id"] = owner
    if cloud_enabled():
        key = f"inputs/{job['id']}/source.zip"
        # The archive is rebuilt from accepted members to avoid retaining skipped/untrusted archive entries.
        import zipfile, io
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as out:
            for path, content in files.items(): out.writestr(path, content)
        upload_bytes(key, buf.getvalue(), "application/zip")
        job["source"] = {"type": "upload", "filename": file.filename or "source.zip", "source_files": len(files), "s3_key": key}
    else:
        # Save a filtered ZIP, not the original archive, to avoid keeping skipped files or unsafe entries.
        import zipfile, io
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as out:
            for path, content in files.items(): out.writestr(path, content)
        path = UPLOAD_DIR / f"{job['id']}.zip"
        path.write_bytes(buf.getvalue())
        job["source"]["upload_path"] = str(path)
    return _submit_job(job, background_tasks)


@app.post("/api/analysis/demo")
def run_demo(request: Request, background_tasks: BackgroundTasks) -> dict[str, Any]:
    owner = _owner(request)
    job = create_job({"type": "demo", "repo_name": "sentinal-demo-vulnerable-service", "branch": "demo"},
                     "Sentinal demonstration service", {"include_security": True, "include_quality": True, "include_architecture": True}, "mentor")
    job["owner_id"] = owner
    return _submit_job(job, background_tasks)


@app.get("/api/analysis/{job_id}")
def get_analysis(job_id: str, request: Request) -> dict[str, Any]:
    job = _load_job(job_id, _owner(request))
    response = {k: v for k, v in job.items() if k not in {"source_files", "upload_path", "owner_id"}}
    if job.get("analysis"):
        response["report_url"] = f"/api/analysis/{job_id}/report.pdf" if job.get("status") == "completed" else None
    return response


@app.get("/api/analysis/{job_id}/report.pdf")
def download_report(job_id: str, request: Request):
    job = _load_job(job_id, _owner(request))
    if job.get("status") != "completed":
        raise HTTPException(status_code=409, detail="The PDF report is not ready yet.")
    if cloud_enabled():
        key = job.get("report_key")
        if not key: raise HTTPException(status_code=404, detail="Report artifact not found.")
        return RedirectResponse(presigned_get(key, 90), status_code=307)
    path = Path(job.get("report_path", ""))
    if not path.exists(): raise HTTPException(status_code=404, detail="Report artifact not found.")
    return FileResponse(path, media_type="application/pdf", filename=f"sentinal-{job_id}.pdf")


@app.post("/api/analysis/{job_id}/ask")
def ask_sentinal(job_id: str, payload: AskSentinalRequest, request: Request) -> dict[str, Any]:
    """Ask a bounded question about one completed local analysis using the configured AI provider."""
    if cloud_enabled():
        raise HTTPException(status_code=503, detail="Ask Sentinal currently requires the local workspace; the deployed AWS runtime cannot reach your local Ollama service.")
    if AI_PROVIDER not in {"ollama", "openrouter"}:
        raise HTTPException(status_code=503, detail="Ask Sentinal requires AI_PROVIDER=ollama or AI_PROVIDER=openrouter. Configure a provider in your local .env and restart the backend.")
    if AI_PROVIDER == "openrouter" and not OPENROUTER_API_KEY:
        raise HTTPException(status_code=503, detail="OpenRouter is selected but OPENROUTER_API_KEY is missing. Add it to your backend environment and restart the backend.")
    job = _load_job(job_id, _owner(request))
    if job.get("status") != "completed" or not job.get("analysis"):
        raise HTTPException(status_code=409, detail="Wait until the analysis is completed before asking questions.")
    selected_path = payload.selected_path
    if selected_path and not any(str(row.get("path")) == selected_path for row in job["analysis"].get("files", [])):
        raise HTTPException(status_code=422, detail="The selected file is not part of this analysis.")
    try:
        return answer_question(
            job["analysis"], payload.question, selected_path,
            [turn.model_dump() for turn in payload.history],
        )
    except TimeoutError as exc:
        raise HTTPException(status_code=504, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:
        # Log only the application traceback and exception class. Do not log request bodies,
        # repository paths, prompts, model responses, or credentials.
        request_id = uuid.uuid4().hex[:10]
        frames = "".join(traceback.format_tb(exc.__traceback__))
        logging.getLogger("uvicorn.error").error(
            "Ask Sentinal internal failure: request_id=%s exception_type=%s\n%s",
            request_id, type(exc).__name__, frames,
        )
        raise HTTPException(
            status_code=502,
            detail=f"Ask Sentinal failed safely ({type(exc).__name__}; reference {request_id}). Check the backend terminal; source content is not logged.",
        ) from exc


@app.patch("/api/analysis/{job_id}/findings/{finding_id}")
def update_finding(job_id: str, finding_id: str, payload: FindingStatusUpdate, request: Request) -> dict[str, Any]:
    job = _load_job(job_id, _owner(request))
    if not job.get("analysis"):
        raise HTTPException(status_code=409, detail="Findings are not available yet.")
    for finding in job["analysis"].get("findings", []):
        if finding.get("id") == finding_id:
            finding["status"] = payload.status; finding["note"] = payload.note
            if cloud_enabled(): cloud_save_job(job)
            else: store.save(job)
            return {"id": finding_id, "status": payload.status, "note": payload.note}
    raise HTTPException(status_code=404, detail="Finding not found.")


# Lambda adapter used by AWS SAM. Local development uses uvicorn app.main:app.
handler = Mangum(app, lifespan="off") if Mangum else app
