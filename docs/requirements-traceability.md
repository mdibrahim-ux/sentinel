# Requirements traceability

Status labels: **Implemented** means code exists in the local source tree; **Tested** means the named test/command has actually passed; **Template-only** means infrastructure is defined but not deployed; **Deferred** means intentionally not enabled in this iteration.

## Course requirements from `AWS` reference image

| Requirement | Implementation location | Service / technique | Verification evidence | Status |
|---|---|---|---|---|
| GitHub PR/repository intake | `backend/app/services/repository.py`, `backend/app/main.py` | API Gateway, Lambda; GitHub REST metadata + codeload archive | URL allowlist checks; API test | Implemented locally; cloud not deployed |
| AST-aware understanding | `backend/app/services/analyzer.py` | Python `ast`, import inventory | analyzer tests | Implemented; Python AST, JS/TS pattern support is partial |
| Repo-context-aware explanation | `backend/app/services/ai_explainer.py` | bounded structured evidence prompt | deterministic fallback test/manual behavior | Implemented; no embeddings/vector RAG index |
| Structured JSON response | `backend/app/services/ai_explainer.py` | schema-key validation | local fallback / AI error-path review | Implemented for narrative keys; no external schema-constrained mode guarantee |
| Combine linters/static checks + AI | `analyzer.py`, `ai_explainer.py`, `pipeline.py` | deterministic rules then optional explanation | end-to-end demo once tests pass | Implemented; no external linter subprocesses run by default |
| Feedback loop | `main.py` finding PATCH route, local store, DynamoDB table | DynamoDB / SQLite | API finding-state test | Implemented for triage statuses; accepted/rejected model training is not automatic |
| Lambda webhook/worker | `backend/app/main.py`, `backend/app/lambda_worker.py`, `infra/template.yaml` | Lambda | template validation; not deployed | Template-only. Browser REST API is the live intake path; GitHub webhook PR event endpoint is deferred |
| API Gateway webhook endpoint | `infra/template.yaml` HTTP API | API Gateway HTTP API | template only | Template-only; current template API serves user API, not GitHub webhook-specific processing |
| Bedrock code explanation | `ai_explainer.py`; `AiProvider` parameter | Amazon Bedrock | disabled unless configured | Implemented but disabled by default; calls may cost money |
| Store source snapshot/diff | S3 adapter and input flow | S3 | code path inspection | Implemented in AWS adapter; no source is persisted to AWS in local mode |
| Orchestration | state machine definition in `infra/template.yaml` | Step Functions: analyze → explain → report | template only | Template-only; not deployed |
| Review history & feedback | `cloud_state.py`, `store.py` | DynamoDB / SQLite | owner-scoped `OwnerCreatedIndex` definition; tests | Implemented locally; cloud requires deployment |
| Restricted CodeBuild | `SentinalCiProject` in `infra/template.yaml` | CodeBuild | template only | Template-only. Runs reviewed Sentinal CI source; untrusted user project tests are not run automatically |
| Operational monitoring | Lambda/CodeBuild logs, 7-day log groups, optional error alarm | CloudWatch | template only | Template-only, not deployed |
| Regression suite | `backend/tests`, `.github/workflows/ci.yml` | pytest and Vite build | 14 backend tests passed; production frontend build passed | Verified locally on 2026-10-19 |
| Prompt templates can be revised | prompt builder in `ai_explainer.py` | version-controlled prompt in code | code review | Implemented as version-controlled source; S3/Parameter Store prompt-version rollout is deferred |

## Product/UX and report requirements

| Requirement | Location | Evidence | Status |
|---|---|---|---|
| Public GitHub URL and ZIP input | New analysis screen + `/api/analysis` and `/api/analysis/upload` | UI/API tests | Implemented |
| Python / JavaScript / TypeScript inventory | `backend/app/services/analyzer.py` | analyzer tests | Implemented with scoped JS/TS patterns, not full parsers |
| Findings with ID, rule, severity, confidence, path/line, evidence, remediation | Analyzer and `schemas.py` | analyzer tests | Implemented for supported rules |
| Architecture/module relationship view | `ArchitectureMap`, analyzer import graph | inspect real analysis response | Implemented as statically inferred imports |
| Comparison of historical scans | history stores multiple scans | saved scan records | Implemented history; scan-to-scan diff is deferred |
| Student/mentor wording | audience-specific explanation prompt | local deterministic or optional AI summary | Implemented; AI provider disabled by default |
| Exactly four-page engineering PDF | `backend/app/services/report.py` and `backend/app/services/pipeline.py` | generated demo report, page-count assertion, all-page render inspection | Implemented with explicit A4 pages: repository summary, severity pie + bars, remediation, engineering intelligence |
| Finding distribution and severity charts | PDF vector chart functions | generated demo report and rendered page 2 | Implemented from the completed findings list; zero findings have a labeled empty state |
| Cloud user authentication | Cognito + API Gateway JWT in SAM | template only | Template-only; local mode uses no account |
| Responsive navigation and visual system | `frontend/src/styles.css` and `frontend/src/App.tsx` | route smoke test; 360-1920 CSS viewport sweep | Implemented; four frequent compact destinations plus More; no horizontal overflow in checked widths |

## Security and constraints

- Submitted code is treated as untrusted text and is **not executed** during standard analysis.
- ZIP entries are path-normalized, size bounded, extension filtered and screened for unusual compression ratios.
- Public repository downloads only; private repository OAuth/GitHub App integration is deferred.
- No AWS deployment, no resource modification, and no Bedrock/OpenAI inference was run by this session.
- Free-tier status and cost cannot be guaranteed until account-level plan/credits and current regional pricing are checked.
