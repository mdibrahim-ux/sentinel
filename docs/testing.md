# Testing strategy

## Backend

From `backend/`:

```bash
python -m py_compile app/*.py app/services/*.py
python -m pytest -q
```

Coverage should include URL validation, archive path traversal and ZIP size/compression checks, credential redaction, Python AST patterns, metrics and import graphs, API health/validation, complete demo job generation, report artifact readability, and finding-state updates.

## Frontend

From `frontend/`:

```bash
npm install
npm run build
```

The production build runs `tsc -b` and Vite. Browser smoke checks should cover local access, source intake, findings, repository map, Ask Sentinal, history, settings, profile, and responsive navigation. Authentication against a configured Cognito pool and live GitHub rate limits require their corresponding external services.

## Report acceptance check

The output PDF must be opened, page-rendered, and inspected for clipping after a completed demo analysis. Verify the Page 1 repository tree and metrics, Page 2 finding-severity pie and bar charts, Page 3 prioritized solutions, and Page 4 directory risk map and evidence notes. All values must correspond to the structured analysis object; report metadata should distinguish scan time from report time and state the coverage limits. Render and inspect all four pages, not only the first page or extracted text.

## Verified results for this workspace (2026-10-19)

- Python compilation passed for the changed report renderer and analysis pipeline.
- `SENTINAL_DATA_DIR=<temporary workspace path> python -m pytest -q -p no:cacheprovider`: **14 passed**. The cache provider was disabled because the existing backend `.pytest_cache` folder is not writable in this workspace.
- `npm run build`: passed with TypeScript and Vite.
- The local demo analysis completed with deterministic explanations disabled for the report-generation check. The API returned a 60,317-byte PDF with exactly four page objects.
- Browser E2E: uploaded the bundled ZIP through New analysis, waited for the analysis to complete, confirmed the 5-file/8-finding dashboard, filtered and searched findings, opened evidence/remediation, and fetched the report endpoint with HTTP 200 through the PDF download action.
- All four pages were rendered in the browser PDF viewer and visually inspected: project/tree summary, severity pie and bar charts, remediation playbook, and engineering-intelligence brief.
- Browser navigation smoke checks passed for Findings, Architecture, Ask Sentinal, History, Settings, Profile, Home, and New analysis. On compact layouts the More menu exposed all secondary routes and the PDF action; selecting Architecture closed the menu and opened its destination.
- CSS viewport checks at 360, 390, 768, 1024, 1280, 1366, 1440, 1600, and 1920 px reported no horizontal overflow. The product tour fit at 375 by 812 CSS px; its focus order cycled through the dialog, Escape closed it, and focus returned to the opener.
- Cognito sign-in, live GitHub repository fetching, AWS deployment, and AWS integration were not exercised.

## AWS test plan (not run)

After deployment, validate the infrastructure template, JWT auth, cross-user isolation, S3 private policy/lifecycle, job history query via `OwnerCreatedIndex`, Step Functions retry/failure paths, Lambda log retention, CodeBuild builds, and optional alarm only after a cost review. No AWS integration or deployment tests are claimed in this delivery unless separately recorded.
