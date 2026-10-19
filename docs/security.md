# Security and privacy

## Implemented controls

- Allowlisted `https://github.com` URL parsing, host verification after download redirects, repository metadata fetch by official API host, and a bounded source archive download.
- ZIP byte cap, uncompressed aggregate cap, file count/size cap, extension allowlist, normalized paths, unsafe/generated directory skips and compression-ratio check.
- No dependency installation, shell execution, test execution, or application boot in normal analysis.
- Credential-like values are replaced with redacted evidence before findings are shown or passed to the optional explainer. The analyzer never stores the matched secret value as a finding field.
- LLM prompt states repository data is untrusted, limits input findings, demands structured JSON, prohibits made-up measurements and falls back to deterministic text after an error.
- AWS template provisions private S3 with block-public-access, BucketOwnerEnforced and SSE-S3; lifecycle expiry; Cognito tokens validated at API Gateway; a user partition index for history; service-scoped IAM actions; standard CloudWatch log retention.
- No browser-exposed secrets, no repository write permissions, and no automated patches/PRs.

## Limits that must be understood

- Static patterns and the lightweight JS/TS parser can miss issues or report false positives. No static scan proves a repository is safe.
- Secret redaction is pattern-based and cannot guarantee every proprietary value or token is recognized.
- Public GitHub repositories only; private repository OAuth/GitHub App permissions are not implemented in this local build.
- This scanner does not verify live CVE/advisory databases, execute tests, establish reachability/exploitability or guarantee exact source-line semantics across languages.
- Model prompts may include sanitized source excerpts and analysis metadata. Enable AI only after reviewing provider privacy, retention, model access and cost. AI provider calls are off by default.
- CodeBuild is not used to automatically execute user-uploaded code. Before adding that function, require explicit user consent, a per-job sandbox, a role with no secrets or broad API access, output-size/time limits, restricted egress and a documented abuse model.

## Operations

- Never deploy with the AWS root identity for daily work. Prepare a least-privilege deployment role and MFA-protected administrator access.
- Keep `OPENAI_API_KEY`, GitHub App secrets and other credentials out of the frontend, reports, source archives, logs and Git. Prefer secret manager/environment-injection patterns after cost review.
- Make all API calls user-scoped. A missing/invalid owner claim must fail closed. If the app becomes public-facing, add request throttling, authentication/rate limits, WAF/abuse controls if affordable, deletion endpoints, audit events and alerting.
- Reports and source uploads are sensitive. Review retention periods and data residency before deploying.
