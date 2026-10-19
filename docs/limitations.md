# Limitations and honest status

- The supplied `AWS` page specifies an AI PR-review agent; this application currently focuses on URL/ZIP codebase intake and PDF reporting. GitHub `pull_request` webhooks and posting inline PR comments are not implemented end-to-end.
- Python has AST-based parsing; JS/TS support uses selected pattern checks and import-string extraction rather than a full tree-sitter AST.
- Repository-aware explanation uses a bounded evidence prompt, not a vector-search or embedding-based RAG index.
- No untrusted project code, package manager, test suite, Dockerfile, or build script is executed during standard analysis. The CodeBuild project is intended for the platform's reviewed CI archive only.
- No automatic pull request, code change, or remediation patch is generated or applied.
- Private GitHub repository access needs an authorized GitHub App/OAuth integration; this version only supports public repositories and ZIP upload.
- Duplicate code detection, dependency advisory database lookup, runtime behavior analysis, and full data-flow/taint analysis are not implemented.
- Scan-to-scan comparison UI and Prompt templates in S3/Parameter Store are deferred. History records are saved; comparison isn't yet computed.
- AI narrative is disabled by default. Configuring Bedrock or OpenAI can send evidence excerpts to a provider and may create usage costs.
- UI is rebuilt based on screenshots/representative animation frames; the reference files do not expose source code, exact layout tokens, or pixel dimensions for every control. Therefore it is a close style reconstruction, not a claim of pixel-perfect equivalence.
- AWS SAM is infrastructure code only. This session made read-only AWS checks and did not create, update, or delete resources. Account-specific free-tier eligibility is unverified.
- The GitHub connector can inspect and write repository content but does not expose a repository-creation operation. Existing private repo `mdibrahim-ux/codebase-intelligence-agent` is a relevant starting project, but its name differs; it was not overwritten or repurposed. This delivery therefore includes a local project folder and a ZIP archive; the exact `sentinal` repository creation remains a manual/permission-dependent step.
