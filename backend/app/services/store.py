from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.config import DB_PATH


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class LocalStore:
    """Simple durable local store. The AWS deployment uses DynamoDB/S3 from lambda_worker."""
    def __init__(self, path: Path = DB_PATH):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as con:
            con.execute("CREATE TABLE IF NOT EXISTS analyses (id TEXT PRIMARY KEY, status TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL, payload TEXT NOT NULL)")
            con.execute("CREATE TABLE IF NOT EXISTS profiles (owner_id TEXT PRIMARY KEY, created_at TEXT NOT NULL, updated_at TEXT NOT NULL, payload TEXT NOT NULL)")

    def _connect(self) -> sqlite3.Connection:
        con = sqlite3.connect(self.path, timeout=8)
        con.row_factory = sqlite3.Row
        return con

    def save(self, job: dict[str, Any]) -> dict[str, Any]:
        job["updated_at"] = now_iso()
        payload = json.dumps(job, ensure_ascii=False)
        with self._connect() as con:
            con.execute("INSERT INTO analyses(id,status,created_at,updated_at,payload) VALUES(?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET status=excluded.status,updated_at=excluded.updated_at,payload=excluded.payload",
                        (job["id"], job.get("status", "queued"), job.get("created_at", now_iso()), job["updated_at"], payload))
        return job

    def get(self, job_id: str) -> dict[str, Any] | None:
        with self._connect() as con:
            row = con.execute("SELECT payload FROM analyses WHERE id=?", (job_id,)).fetchone()
        return json.loads(row["payload"]) if row else None

    def get_profile(self, owner_id: str) -> dict[str, Any] | None:
        with self._connect() as con:
            row = con.execute("SELECT payload FROM profiles WHERE owner_id=?", (owner_id,)).fetchone()
        return json.loads(row["payload"]) if row else None

    def save_profile(self, owner_id: str, profile: dict[str, Any]) -> dict[str, Any]:
        now = now_iso()
        existing = self.get_profile(owner_id)
        profile["created_at"] = (existing or {}).get("created_at") or now
        profile["updated_at"] = now
        with self._connect() as con:
            con.execute("INSERT INTO profiles(owner_id,created_at,updated_at,payload) VALUES(?,?,?,?) ON CONFLICT(owner_id) DO UPDATE SET updated_at=excluded.updated_at,payload=excluded.payload",
                        (owner_id, profile["created_at"], now, json.dumps(profile, ensure_ascii=False)))
        return profile

    def history(self, limit: int = 20) -> list[dict[str, Any]]:
        with self._connect() as con:
            rows = con.execute("SELECT payload FROM analyses ORDER BY created_at DESC LIMIT ?", (max(1, min(limit, 100)),)).fetchall()
        result = []
        for row in rows:
            j = json.loads(row["payload"])
            result.append({k: j.get(k) for k in ("id", "project", "source", "status", "created_at", "updated_at", "error")})
            if j.get("analysis"):
                result[-1]["summary"] = j["analysis"].get("summary", {})
        return result


store = LocalStore()
