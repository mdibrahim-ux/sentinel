from __future__ import annotations

import asyncio
import json
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import HTTPException

from app.config import REPORT_DIR, UPLOAD_DIR
from app.services.ai_explainer import explain_analysis
from app.services.analyzer import analyze_files, parse_manifest_dependencies
from app.services.cloud_state import (delete_object, download_bytes, enabled as cloud_enabled,
                                      get_job as cloud_get_job, save_job as cloud_save_job,
                                      upload_bytes)
from app.services.report import generate_pdf
from app.services.repository import archive_to_files, fetch_github_archive
from app.services.store import now_iso, store


def _demo_files() -> tuple[dict[str, bytes], dict[str, Any]]:
    root = Path(__file__).resolve().parents[2] / "demo_project"
    files: dict[str, bytes] = {}
    for path in root.rglob("*"):
        if path.is_file():
            rel = path.relative_to(root).as_posix()
            if any(x in rel.split("/") for x in {"__pycache__", ".venv", "node_modules"}):
                continue
            files[rel] = path.read_bytes()
    return files, {"type": "demo", "repo_name": "sentinal-demo-vulnerable-service", "repository_url": "", "branch": "demo", "commit_sha": "local-demo-fixture", "snapshot_at": now_iso()}


def _read_local_source(job: dict[str, Any]) -> tuple[dict[str, bytes], dict[str, Any]]:
    source = job.get("source", {})
    if source.get("type") == "demo":
        return _demo_files()
    if source.get("type") == "upload":
        upload_path = Path(source.get("upload_path", ""))
        if not upload_path.exists():
            raise HTTPException(status_code=404, detail="Uploaded archive is no longer available.")
        raw = upload_path.read_bytes()
        try: upload_path.unlink()
        except OSError: pass
        return archive_to_files(raw), {**source, "snapshot_at": now_iso()}
    if source.get("type") == "github":
        files, meta = asyncio.run(fetch_github_archive(source["repository_url"], source.get("branch", "main")))
        return files, meta
    raise HTTPException(status_code=422, detail="Unknown source type.")


def process_local_job(job_id: str) -> None:
    job = store.get(job_id)
    if not job:
        return
    try:
        job["status"] = "analyzing"; job["progress"] = 18; store.save(job)
        files, source_meta = _read_local_source(job)
        opts = job.get("options", {})
        analysis = analyze_files(files, opts, {**source_meta, "project_label": job.get("project_label")})
        analysis["dependencies"] = parse_manifest_dependencies(files)
        analysis["project"] = job.get("project_label") or source_meta.get("repo_name") or "Uploaded codebase"
        job["analysis"] = analysis; job["source"] = {k: v for k,v in source_meta.items() if k != "upload_path"}
        job["status"] = "explaining"; job["progress"] = 60; store.save(job)
        ai_summary = explain_analysis(analysis, job.get("audience", "developer"))
        job["ai_summary"] = ai_summary; job["analysis_completed_at"] = now_iso()
        job["status"] = "reporting"; job["progress"] = 82; store.save(job)
        report_path = REPORT_DIR / f"{job_id}.pdf"
        generate_pdf(
            analysis,
            ai_summary,
            report_path,
            metadata={"analysis_id": job_id, "submitted_at": job.get("created_at"), "analysis_completed_at": job.get("analysis_completed_at")},
        )
        job["report_path"] = str(report_path); job["report_url"] = f"/api/analysis/{job_id}/report.pdf"
        job["status"] = "completed"; job["progress"] = 100; job["completed_at"] = now_iso(); store.save(job)
    except HTTPException as exc:
        job["status"] = "failed"; job["progress"] = 100; job["error"] = exc.detail; store.save(job)
    except Exception as exc:
        job["status"] = "failed"; job["progress"] = 100
        job["error"] = f"Analysis failed safely ({type(exc).__name__}). Check backend logs for a request ID; source content is not logged."
        store.save(job)
        raise


def process_cloud_stage(job_id: str, action: str) -> dict[str, Any]:
    job = cloud_get_job(job_id)
    if not job:
        raise ValueError(f"Unknown job_id: {job_id}")
    source = job.get("source", {})
    try:
        if action == "analyze":
            job["status"] = "analyzing"; job["progress"] = 15; cloud_save_job(job)
            if source.get("type") == "upload":
                raw = download_bytes(source["s3_key"])
                files = archive_to_files(raw)
                source_meta = {k:v for k,v in source.items() if k != "s3_key"}
            elif source.get("type") == "demo":
                files, source_meta = _demo_files()
            elif source.get("type") == "github":
                files, source_meta = asyncio.run(fetch_github_archive(source["repository_url"], source.get("branch", "main")))
            else:
                raise ValueError("Unknown source type")
            analysis = analyze_files(files, job.get("options", {}), {**source_meta, "project_label": job.get("project_label")})
            analysis["dependencies"] = parse_manifest_dependencies(files)
            analysis["project"] = job.get("project_label") or source_meta.get("repo_name") or "Uploaded codebase"
            if source.get("type") == "upload" and source.get("s3_key"):
                try:
                    delete_object(source["s3_key"])
                except Exception:
                    # The configured S3 lifecycle remains the secondary cleanup control.
                    pass
            job["analysis"] = analysis; job["source"] = {k:v for k,v in source_meta.items() if k not in {"upload_path", "s3_key"}}
            job["status"] = "explaining"; job["progress"] = 58; cloud_save_job(job)
        elif action == "explain":
            if not job.get("analysis"):
                raise ValueError("Analysis artifact is missing")
            job["ai_summary"] = explain_analysis(job["analysis"], job.get("audience", "developer"))
            job["analysis_completed_at"] = now_iso()
            job["status"] = "reporting"; job["progress"] = 80; cloud_save_job(job)
        elif action == "report":
            if not job.get("analysis"):
                raise ValueError("Analysis artifact is missing")
            report_path = Path("/tmp") / f"{job_id}.pdf"
            generate_pdf(
                job["analysis"],
                job.get("ai_summary", {}),
                report_path,
                metadata={"analysis_id": job_id, "submitted_at": job.get("created_at"), "analysis_completed_at": job.get("analysis_completed_at")},
            )
            key = f"reports/{job_id}.pdf"
            upload_bytes(key, report_path.read_bytes(), "application/pdf")
            job["report_key"] = key; job["status"] = "completed"; job["progress"] = 100; job["completed_at"] = now_iso()
            cloud_save_job(job)
            if source.get("type") == "upload" and source.get("s3_key"):
                try: delete_object(source["s3_key"])
                except Exception: pass
            try: report_path.unlink()
            except OSError: pass
        else:
            raise ValueError(f"Unsupported workflow action: {action}")
        return {"job_id": job_id, "action": action, "status": job["status"], "progress": job.get("progress", 0)}
    except Exception as exc:
        job["status"] = "failed"; job["progress"] = 100
        job["error"] = f"Cloud analysis failed safely ({type(exc).__name__})."
        try: cloud_save_job(job)
        except Exception: pass
        raise


def create_job(source: dict[str, Any], project_label: str, options: dict[str, bool], audience: str) -> dict[str, Any]:
    job_id = uuid.uuid4().hex[:16]
    project = project_label.strip() or source.get("repo_name") or (Path(source.get("filename", "")).stem if source.get("filename") else "Codebase analysis")
    job = {"id": job_id, "project": project, "project_label": project_label.strip(), "source": source,
           "options": options, "audience": audience, "status": "queued", "progress": 0,
           "created_at": now_iso(), "updated_at": now_iso(), "analysis": None, "ai_summary": None}
    return job
