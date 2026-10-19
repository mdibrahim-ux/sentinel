# Sentinal

**A local-first codebase intelligence workspace for security triage, architecture discovery, and evidence-led PDF reporting.**

Sentinal accepts a public GitHub repository URL or a small source ZIP, inventories supported Python/JavaScript/TypeScript and text files, runs bounded deterministic checks, correlates results into a normalized evidence model, and creates a four-page, presentation-oriented PDF with a repository hierarchy, charts, scan metrics and a prioritized review queue. It does **not** run submitted application code during the normal scan. Model-based narrative is optional and disabled by default.

> Static rules identify review signals, not guaranteed vulnerabilities. A clean result is not a security certification. Local development access is unauthenticated unless Cognito is configured; production builds do not expose the local-access bypass.

## What works in this build

- Public GitHub repository and `.zip` intake with file-count, size, file-type and archive checks.
- Python AST inspection; selected JavaScript/TypeScript unsafe-pattern checks; credential-like-value redaction; dependency-manifest, documentation, test, language and line-count inventory.
- Evidence-linked findings with rule IDs, severity, confidence, file/line references, sanitized evidence, remediation and verification labels.
- Import/dependency relationship map, largest-file graph, severity distribution, and heuristic health triage score with a documented method.
- Four-page PDF report: project metadata and representative repository tree; findings severity pie and bar charts; prioritized solutions; directory-level risk concentration, evidence confidence, and coverage limits.
- Local SQLite history, finding-state updates (`open`, `investigate`, `accepted`, `fixed`, `ignored`), report download, mentor/developer audience.
- Optional Ollama, OpenAI, or Amazon Bedrock narrative layer. Provider choice is explicit; Ollama uses local machine resources, and external providers can incur charges. The Ask Sentinal panel uses local Ollama only and never silently switches to Bedrock.
- AWS SAM/CloudFormation template for API Gateway, Lambda, Step Functions, S3, DynamoDB, Cognito, CodeBuild and CloudWatch logs; optional alarm and model permissions are gated.
- Responsive comic-engineering product UI with a persistent light/dark/system theme, dock navigation, interactive Repo Atlas, Ask Sentinal, and a three-step keyboard-operable product tour.

## Delivery verification status

- **Backend: tested** — `python -m pytest -q -p no:cacheprovider` passed all 14 tests. The cache provider was disabled because the pre-existing `.pytest_cache` directory is not writable in this workspace.
- **Report PDF: generated and inspected** — the completed demo analysis produced exactly four A4 pages. The repository summary, severity pie and bar charts, remediation playbook, and engineering-intelligence page were rendered and visually checked.
- **Frontend: built** — `npm run build` passed with TypeScript and Vite.
- **Browser workflow: exercised** — all eight routes, the compact More menu, the product tour, a bundled ZIP analysis, finding search/detail, theme switching, and PDF retrieval (HTTP 200). No horizontal overflow appeared at 360, 390, 768, 1024, 1280, 1366, 1440, 1600, or 1920 CSS px.
- **Infrastructure: template-only** — YAML parses, but AWS SAM validation and deployment were not run. No account resources were changed.

## Run locally

Requirements: Python 3.12+ (3.13 should also work), Node.js 20+, npm.

### Backend

```bash
cd backend
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
python -m pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend (second terminal)

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. With Cognito unset, Vite development mode provides a clearly labelled **Continue to local workspace** option; it is not a real account and should only be used locally. In the workspace, use New analysis to submit a public GitHub repository or a source ZIP (5 MB maximum). API docs are available at `http://localhost:8000/docs` while the backend is running.

To use a non-default API URL, copy `frontend/.env.example` to `frontend/.env.local` and set `VITE_API_BASE_URL`. For real accounts, configure an Amazon Cognito User Pool and app client, then set `VITE_COGNITO_USER_POOL_ID` and `VITE_COGNITO_CLIENT_ID` in `frontend/.env.local`. The login page supports sign-in, sign-up with email verification, and password reset when those values point at a configured pool. Setting these IDs does not create or deploy Cognito by itself. To change backend limits or AI mode, copy the root `.env.example` to `backend/.env` or export those values in the backend process environment. Environment variables must not be committed.

## Run tests and build

```bash
cd backend
python -m pytest -q
```

```bash
cd frontend
npm install
npm run build
```

The tests assert selected analyzer outcomes, path/ZIP safety and API validation. Record the **actual** commands and results when presenting the project; a successful unit test suite does not prove cloud deployment or broad security coverage.

## Optional AI explanation and Ask Sentinal

The default `AI_PROVIDER=disabled` makes deterministic analysis and report generation work without model inference. For optional AI explanations and Ask Sentinal, `ollama` is the local path (it uses your own machine resources); external Bedrock/OpenAI providers can incur costs. Review data handling and privacy before enabling any provider:

- `AI_PROVIDER=ollama`, `OLLAMA_BASE_URL=http://127.0.0.1:11434`, and `OLLAMA_MODEL=qwen2.5-coder:3b` use a local Ollama API (change the model setting if you have configured a different model). Install Ollama and pull the model separately; generation uses local CPU/GPU/memory and no model API key.
- `AI_PROVIDER=bedrock` and `BEDROCK_MODEL_ID=<approved model or inference-profile ID>` use the AWS SDK. The deployed IAM role must be scoped to the corresponding approved `BedrockModelArn`; both values are required in `infra/template.yaml`.
- `AI_PROVIDER=openai`, `OPENAI_API_KEY`, and optionally `OPENAI_MODEL` use the OpenAI API. Keep keys in an environment secret manager; never place them in Vite variables or frontend source.

Source excerpts sent to a model may include proprietary code. The prompt labels repository content as untrusted and sends a bounded, redacted evidence subset, but this cannot guarantee complete secret removal. AI calls can cost money. No model API is called with the default settings.

## AWS deployment — not performed from this session

The template is at `infra/template.yaml`. It defines a private S3 bucket with block-public-access, SSE-S3 encryption and short lifecycle rules; DynamoDB tables including a user-scoped history index; Cognito browser authentication; a JWT-protected HTTP API; API and worker Lambda functions; a three-stage Step Functions workflow; a CodeBuild project for **Sentinal's own reviewed CI source**; and seven-day function-log retention. An error alarm and Bedrock invocation IAM policy are optional.

This template is infrastructure code, **not evidence of deployment**. The connected account's current caller identity was the AWS root principal. No stack was deployed and no existing AWS resources were modified. Review the template, current regional pricing, account-specific free-plan/credit eligibility, IAM boundaries and service quotas before running `sam deploy`. Do not use the root user for routine deployment; use a least-privilege deployment role instead.

Typical review steps after creating an approved deployment role:

```bash
sam validate --template-file infra/template.yaml
sam build --template-file infra/template.yaml
sam deploy --template-file infra/template.yaml --guided
```

Choose `AiProvider=disabled` and `CreateErrorAlarm=false` initially. `FrontendOrigin` must be the precise UI origin. Configure the frontend `.env.local` with outputs `ApiBaseUrl`, `CognitoUserPoolId`, `CognitoUserPoolClientId`, and the deployment region. Upload a reviewed Sentinal source archive to the output artifact bucket at `ci/sentinal-source.zip` before starting its CodeBuild project. See [deployment](docs/deployment.md) and [cost controls](docs/cost-estimate.md).

**Cost reality:** Free usage is account-, date-, region-, and service-specific. A service being free-tier-eligible does not guarantee a zero bill. The standard workflow uses paid-metered units beyond any eligible allowances; Bedrock inference is not assumed free. Do not deploy solely on the basis of this README.

## Documentation

- [Redesign notes and four-page report structure](docs/redesign-notes.md)
- [Requirement traceability](docs/requirements-traceability.md)
- [Reconstructed design system](docs/design-system.md)
- [Product experience audit](docs/design-audit.md)
- [Visual and interaction research](docs/design-research.md)
- [UI reference mapping](docs/ui-reference-map.md)
- [Architecture and data flow](docs/architecture.md)
- [Data flow](docs/data-flow.md)
- [Security and privacy](docs/security.md)
- [Cost estimate and controls](docs/cost-estimate.md)
- [API reference](docs/api-reference.md)
- [Deployment guide](docs/deployment.md)
- [Testing strategy](docs/testing.md)
- [Limitations and status](docs/limitations.md)

## Design source notes

The current redesign draws on the supplied dashboard and interaction references described in [the UI reference map](docs/ui-reference-map.md), plus the current navigation and accessibility research in [the design research note](docs/design-research.md). The authenticated workspace uses a dock on desktop and a four-destination dock with a More menu on compact screens. Exact source component dimensions and an editable original design system are not supplied, so this is a careful responsive reconstruction rather than a claim of pixel-perfect equivalence with the reference application's underlying code.

## Prepare the CodeBuild source archive

The template configures CodeBuild for Sentinal’s own CI (not for executing uploaded projects):

```bash
python scripts/package-ci-source.py --output sentinal-ci-source.zip
```

The script excludes `.git`, dependency folders, environment secrets, local scan history, generated output and the reference preview images. Upload the result to the deployed artifacts bucket as `ci/sentinal-source.zip` as described in `docs/deployment.md`.


## Developer profile and appearance

The dock-only workspace navigation includes a Profile page. Profile edits and an optional avatar are saved through `GET /api/profile` and `PUT /api/profile`. Local development stores the profile in the same SQLite database under the local workspace owner. In AWS mode, the API scopes records to the authenticated Cognito subject and uses the `SentinalProfilesTable` provisioned by `infra/template.yaml`. The profile-table resource is only live after the updated infrastructure template is deployed.

The Profile page can retrieve public GitHub account and recent public repository details by username through GitHub's public API; this is subject to GitHub rate limits and does not require a personal access token. Saved email/profile visibility settings are preferences only: this project does not expose a public profile publishing endpoint.

Appearance supports Light, Dark, and System modes. System mode follows the browser operating-system preference. The authenticated workspace uses the floating dock as its only primary navigation. Compact layouts expose four frequent routes directly and put secondary routes and PDF download in More; the top navigation and side rail are not part of the workspace shell.
