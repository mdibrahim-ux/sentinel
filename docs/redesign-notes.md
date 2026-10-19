# Sentinal presentation redesign

## Experience goals

- Use neutral light and dark surfaces with blue as the primary interaction accent. Severity colors are reserved for meaningful finding semantics, not decorative backgrounds.
- Use pill-shaped primary actions, clearer typography, responsive grids, and larger readable chart labels.
- Make the empty Home page useful as a start page, including first actions, core capabilities, and recent completed snapshots.
- Keep the existing deterministic analyzer and Ollama provider selection; no automatic Bedrock fallback was added.

## Home and Repo Atlas

The Home page has a meaningful onboarding state plus an analysis-focused state with metrics, severity distribution, language composition, file-size comparisons, and prioritized signals. Repo Atlas draws only static relationships returned by the analyzer. Selecting a node reveals the selected file's language, line counts, size, and attached findings. A file without a finding is not presented as certified safe.

## Four-page PDF structure

1. **Project identity and repository shape:** actual source metadata, timestamps, analysis ID, representative file tree, and the files/source lines/findings/health/triage summary.
2. **Signal distribution:** a real findings severity pie chart and a severity count bar graph from the same completed analysis.
3. **Remediation playbook:** prioritized findings with real path/line, impact description, remediation, verification guidance, triage status, and an explicit omitted-item count.
4. **Engineering intelligence brief:** directory-level signal concentration, a fix-first sequence, measured facts, match-confidence caveats, coverage gaps, and a scoped conclusion.

The hierarchy graphic shows representative paths for readability, not every path when the repository is large. The playbook shows up to five prioritized fixes and reports the number omitted; the full Findings screen remains the place to inspect the entire queue. The PDF renderer has explicit page boundaries and the exported artifact is checked for exactly four pages.

## Ask Sentinal (local Ollama)

`POST /api/analysis/{job_id}/ask` answers bounded questions about a completed local snapshot. It accepts `question`, optional `selected_path`, and up to eight prior `history` turns. The handler requires `AI_PROVIDER=ollama` and returns a clear service error when Ollama isn't configured or responds too slowly. The prompt is limited to summary metrics, file inventory, and relevant finding records; it doesn't send the entire source archive as chat context. It does not execute code or query a live advisory database. The cloud/AWS runtime deliberately does not claim it can reach a developer's local Ollama server.

## Validation performed

- Backend tests pass, including the local Q&A route's disabled-provider response and a mocked successful Q&A request.
- The report generator has been exercised against the sample analysis and creates exactly four pages.
- Frontend TypeScript/JSX syntax transpilation passed. A full `npm run build` could not be completed in this build environment because the npm registry was unreachable; run `npm ci` and `npm run build` locally before presenting.
