from __future__ import annotations

import json
import os
from typing import Any

import boto3
from boto3.dynamodb.conditions import Key

from app.config import AWS_REGION, SENTINAL_BUCKET, SENTINAL_FINDINGS_TABLE, SENTINAL_JOBS_TABLE, SENTINAL_PROFILES_TABLE


def enabled() -> bool:
    return os.getenv("AWS_RUNTIME_ENABLED", "false").lower() == "true" and bool(SENTINAL_BUCKET and SENTINAL_JOBS_TABLE and SENTINAL_FINDINGS_TABLE)


def _dynamodb():
    return boto3.resource("dynamodb", region_name=AWS_REGION)


def _s3():
    return boto3.client("s3", region_name=AWS_REGION)


def _jobs_table():
    return _dynamodb().Table(SENTINAL_JOBS_TABLE)


def save_job(job: dict[str, Any]) -> None:
    safe = {k: v for k, v in job.items() if k not in {"analysis", "ai_summary"}}
    item = {"job_id": job["id"], "owner_id": str(job.get("owner_id", "")),
            "status": job.get("status", "queued"), "created_at": job.get("created_at", ""),
            "updated_at": job.get("updated_at", ""), "payload_json": json.dumps(safe, ensure_ascii=False)}
    if job.get("analysis"):
        analysis_payload = {"analysis": job["analysis"], "ai_summary": job.get("ai_summary", {})}
        key = f"analysis/{job['id']}/result.json"
        _s3().put_object(Bucket=SENTINAL_BUCKET, Key=key, Body=json.dumps(analysis_payload, ensure_ascii=False).encode(), ContentType="application/json", ServerSideEncryption="AES256")
        item["analysis_key"] = key
        item["summary_json"] = json.dumps(job["analysis"].get("summary", {}))
    if job.get("report_key"):
        item["report_key"] = job["report_key"]
    _jobs_table().put_item(Item=item)
    if job.get("analysis"):
        table = _dynamodb().Table(SENTINAL_FINDINGS_TABLE)
        for finding in job["analysis"].get("findings", []):
            table.put_item(Item={"job_id": job["id"], "finding_id": finding["id"], "severity": finding.get("severity", "INFO"),
                                 "category": finding.get("category", "quality"), "path": finding.get("path", ""),
                                 "line_start": int(finding.get("line_start") or 0), "status": finding.get("status", "open"),
                                 "payload_json": json.dumps(finding, ensure_ascii=False)})


def get_job(job_id: str) -> dict[str, Any] | None:
    response = _jobs_table().get_item(Key={"job_id": job_id}, ConsistentRead=True)
    item = response.get("Item")
    if not item:
        return None
    job = json.loads(item.get("payload_json", "{}"))
    job["id"] = item["job_id"]
    job["status"] = item.get("status", job.get("status", "queued"))
    job["updated_at"] = item.get("updated_at", job.get("updated_at", ""))
    if item.get("analysis_key"):
        obj = _s3().get_object(Bucket=SENTINAL_BUCKET, Key=item["analysis_key"])
        result = json.loads(obj["Body"].read())
        job["analysis"] = result.get("analysis")
        job["ai_summary"] = result.get("ai_summary", {})
    if item.get("report_key"):
        job["report_key"] = item["report_key"]
    return job


def upload_bytes(key: str, content: bytes, content_type: str) -> None:
    _s3().put_object(Bucket=SENTINAL_BUCKET, Key=key, Body=content, ContentType=content_type, ServerSideEncryption="AES256")


def download_bytes(key: str) -> bytes:
    response = _s3().get_object(Bucket=SENTINAL_BUCKET, Key=key)
    return response["Body"].read()


def presigned_get(key: str, expires: int = 90) -> str:
    return _s3().generate_presigned_url("get_object", Params={"Bucket": SENTINAL_BUCKET, "Key": key}, ExpiresIn=expires)


def delete_object(key: str) -> None:
    _s3().delete_object(Bucket=SENTINAL_BUCKET, Key=key)


def list_history(owner_id: str, limit: int = 20) -> list[dict[str, Any]]:
    """Return only records from the authenticated user's owner partition."""
    if not owner_id:
        return []
    response = _jobs_table().query(
        IndexName="OwnerCreatedIndex",
        KeyConditionExpression=Key("owner_id").eq(owner_id),
        ScanIndexForward=False,
        Limit=max(1, min(int(limit), 50)),
    )
    records: list[dict[str, Any]] = []
    for item in response.get("Items", []):
        record = json.loads(item.get("payload_json", "{}"))
        record.update({"id": item.get("job_id"), "status": item.get("status"),
                       "created_at": item.get("created_at"), "updated_at": item.get("updated_at")})
        if item.get("summary_json"):
            try:
                record["summary"] = json.loads(item["summary_json"])
            except (TypeError, json.JSONDecodeError):
                record["summary"] = {}
        records.append({k: record.get(k) for k in ("id", "project", "source", "status", "created_at", "updated_at", "error", "summary") if k in record})
    return records


def get_profile(owner_id: str) -> dict[str, Any] | None:
    if not owner_id:
        raise RuntimeError("Authenticated user identity is not available.")
    if not SENTINAL_PROFILES_TABLE:
        raise RuntimeError("The profile table is not configured for this deployment. Redeploy the updated infrastructure template.")
    response = _dynamodb().Table(SENTINAL_PROFILES_TABLE).get_item(Key={"owner_id": owner_id}, ConsistentRead=True)
    item = response.get("Item")
    if not item:
        return None
    try:
        return json.loads(item.get("payload_json", "{}"))
    except (TypeError, json.JSONDecodeError):
        return None


def save_profile(owner_id: str, profile: dict[str, Any]) -> dict[str, Any]:
    if not owner_id or not SENTINAL_PROFILES_TABLE:
        raise RuntimeError("The profile table is not configured for this deployment.")
    table = _dynamodb().Table(SENTINAL_PROFILES_TABLE)
    existing = table.get_item(Key={"owner_id": owner_id}, ConsistentRead=True).get("Item", {})
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).isoformat()
    profile["created_at"] = existing.get("created_at") or profile.get("created_at") or now
    profile["updated_at"] = now
    table.put_item(Item={"owner_id": owner_id, "created_at": profile["created_at"], "updated_at": now,
                         "payload_json": json.dumps(profile, ensure_ascii=False)})
    return profile
