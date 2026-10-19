from __future__ import annotations

from app.services.pipeline import process_cloud_stage


def handler(event, context):
    job_id = event.get("job_id")
    action = event.get("action")
    if not job_id or action not in {"analyze", "explain", "report"}:
        raise ValueError("Expected job_id and action in {analyze, explain, report}.")
    return process_cloud_stage(job_id, action)
