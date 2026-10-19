from __future__ import annotations

import os
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
DEFAULT_DATA_DIR = Path("/tmp/sentinal") if os.getenv("AWS_LAMBDA_FUNCTION_NAME") else ROOT_DIR / "data"
DATA_DIR = Path(os.getenv("SENTINAL_DATA_DIR", DEFAULT_DATA_DIR)).resolve()
UPLOAD_DIR = DATA_DIR / "uploads"
REPORT_DIR = DATA_DIR / "reports"
DB_PATH = DATA_DIR / "sentinal.sqlite3"
MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "5"))
MAX_UPLOAD_BYTES = MAX_UPLOAD_MB * 1024 * 1024
MAX_FILES = int(os.getenv("MAX_FILES", "500"))
MAX_FILE_BYTES = int(os.getenv("MAX_FILE_BYTES", str(1024 * 1024)))
AWS_REGION = os.getenv("AWS_REGION", "ap-south-1")
AI_PROVIDER = os.getenv("AI_PROVIDER", "disabled").lower()
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5-coder:3b")
BEDROCK_MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "")
AWS_RUNTIME_ENABLED = os.getenv("AWS_RUNTIME_ENABLED", "false").lower() == "true"
SENTINAL_BUCKET = os.getenv("SENTINAL_BUCKET", "")
SENTINAL_JOBS_TABLE = os.getenv("SENTINAL_JOBS_TABLE", "")
SENTINAL_FINDINGS_TABLE = os.getenv("SENTINAL_FINDINGS_TABLE", "")
SENTINAL_PROFILES_TABLE = os.getenv("SENTINAL_PROFILES_TABLE", "")
SENTINAL_STATE_MACHINE_ARN = os.getenv("SENTINAL_STATE_MACHINE_ARN", "")

for path in (DATA_DIR, UPLOAD_DIR, REPORT_DIR):
    path.mkdir(parents=True, exist_ok=True)
