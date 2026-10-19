#!/usr/bin/env python3
"""Create a deterministic source archive for Sentinal's own CodeBuild CI job.

The archive contains project source and documentation, never credentials, local scan
history, demo reports, dependency folders, caches, or visual reference assets.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED_DIRS = {
    ".git", ".venv", "venv", "node_modules", "dist", "build", "__pycache__",
    ".pytest_cache", ".mypy_cache", ".ruff_cache", "data", "reference-inspection",
    "_sample_render", "coverage", ".idea", ".vscode",
}
EXCLUDED_NAMES = {".env", ".env.local", ".env.production", "sentinal.sqlite3", "sample-report.pdf"}
EXCLUDED_SUFFIXES = {".pyc", ".pyo", ".log"}


def excluded(path: Path) -> bool:
    rel = path.relative_to(ROOT)
    if any(part in EXCLUDED_DIRS for part in rel.parts):
        return True
    if path.name in EXCLUDED_NAMES or path.suffix.lower() in EXCLUDED_SUFFIXES:
        return True
    if path.name.startswith(".env.") and path.name != ".env.example":
        return True
    # Exclude outputs with potentially repository-derived content except the curated example report.
    if rel.as_posix().startswith("backend/data/"):
        return True
    return False


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default=str(ROOT.parent / "sentinal-ci-source.zip"))
    args = parser.parse_args()
    output = Path(args.output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        output.unlink()

    included: list[Path] = []
    for current, dirs, files in os.walk(ROOT):
        current_path = Path(current)
        dirs[:] = sorted(d for d in dirs if d not in EXCLUDED_DIRS and not (current_path / d).is_symlink())
        for name in sorted(files):
            path = current_path / name
            if path.is_symlink() or excluded(path) or path.resolve() == output:
                continue
            included.append(path)

    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=8) as archive:
        for path in sorted(included):
            archive.write(path, path.relative_to(ROOT))

    with zipfile.ZipFile(output) as archive:
        names = archive.namelist()
        forbidden = (".git/", "node_modules/", ".venv/", "reference-inspection/", "_sample_render/", "backend/data/", "data/")
        bad = [n for n in names if any(piece in n for piece in forbidden) or any(part == ".env" or (part.startswith(".env.") and part != ".env.example") for part in Path(n).parts)]
        if bad:
            raise SystemExit(f"Archive contains excluded content: {bad[:5]}")
    print(f"Created {output} ({output.stat().st_size:,} bytes; {len(included)} files)")


if __name__ == "__main__":
    main()
