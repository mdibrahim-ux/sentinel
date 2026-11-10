# API reference

Default local base URL: `http://localhost:8000`. JSON API routes are under `/api`. In AWS mode, API Gateway JWT authorization requires a Cognito ID/access token in `Authorization: Bearer <token>`.

| Method | Path | Request / response |
|---|---|---|
| GET | `/api/health` | application version, local/AWS mode, AI provider setting |
| GET | `/api/analysis/history?limit=20` | most recent job summaries (limit is bounded server-side) |
| POST | `/api/analysis` | JSON: `repository_url`, `branch`, `project_label`, `include_security`, `include_quality`, `include_architecture`, `audience` (`developer`/`mentor`) |
| POST | `/api/analysis/upload` | multipart `file` (.zip), `project_label`, analysis flags, `audience` |
| POST | `/api/analysis/demo` | starts the included deterministic demo fixture |
| GET | `/api/analysis/{job_id}` | job status/progress; full normalized analysis when available |
| GET | `/api/analysis/{job_id}/report.pdf` | Four-page PDF download; AWS mode redirects to a short-lived presigned S3 object URL |
| POST | `/api/analysis/{job_id}/ask` | AI Q&A: JSON `question`, optional `selected_path`, and up to 8 prior `history` turns. Requires a completed local analysis and either `AI_PROVIDER=ollama` or `AI_PROVIDER=openrouter` (with `OPENROUTER_API_KEY`); unavailable in AWS runtime. |
| PATCH | `/api/analysis/{job_id}/findings/{finding_id}` | JSON `status` (`open`, `investigate`, `accepted`, `fixed`, `ignored`) and optional `note` |

## Job states

`queued → analyzing → explaining → reporting → completed`; `failed` is terminal and includes a safe user-facing error. Progress percentages are stage indicators, not estimates of total compute time. Clients should poll the status endpoint while a job is active.

## Input constraints

- `https` GitHub URLs on the official public host only. Supported forms: `https://github.com/owner/repo`, `.git` suffix, or `/tree/branch` form.
- ZIP upload cap: 5 MB by default; up to 500 supported files and 1 MB per file. Binary, unsupported, and generated content may be skipped. Values are configurable in backend environment variables.
- The application does not install requirements, build packages, execute user code, or fetch private source without authorization.

## Error behavior

- `401`: missing/invalid authentication for cloud calls.
- `404`: job/resource not found (cross-user jobs appear not found in cloud mode).
- `409`: report/finding is not available until analysis reaches the relevant state.
- `413`: upload/archive size or file-count constraint exceeded.
- `415`: upload is not a `.zip` archive.
- `422`: malformed/unsupported input.
- `502`/`503`: safely reported GitHub or orchestration failures.

See FastAPI `/docs` locally for the OpenAPI schema and concrete request models.


## Ask Sentinal (local Ollama or OpenRouter cloud)

`POST /api/analysis/{job_id}/ask` requires a completed local analysis and either `AI_PROVIDER=ollama` or `AI_PROVIDER=openrouter` with `OPENROUTER_API_KEY`. OpenRouter sends the bounded analysis context to its cloud service; review its model/provider data policies before use. Example request:

```json
{
  "question": "What should I fix first?",
  "selected_path": "backend/app.py",
  "history": [
    {"role": "user", "content": "Summarize this review."}
  ]
}
```

`selected_path` and `history` are optional. The endpoint returns `{ "answer": "...", "provider": "ollama" | "openrouter", "model": "..." }`. Questions and prior turn content are bounded by the request schema. The route is currently disabled in the AWS runtime. An unavailable provider responds with `503`, an Ollama timeout with `504`, and other upstream failures with `502`.
