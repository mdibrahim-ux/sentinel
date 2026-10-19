# Sentinal product experience audit

Audit completed on 2026-10-19 against the routes and workflows present in this workspace. The current implementation already supports eight workspace destinations, local/public-repository or ZIP intake, analysis progress, findings and triage, a static repository map, Ask Sentinal, history, settings, profile, and report export. The backend remains the authority for analysis state and measurements.

## User journeys reviewed

1. **First visit:** local-workspace access when Cognito is not configured, Home overview, product tour, and the route to New analysis.
2. **Submit a project:** public GitHub URL or ZIP, branch/project label, enabled scan checks, and report audience.
3. **Understand results:** Home metrics and charts, Findings empty/list/detail states, and the statically inferred Architecture map.
4. **Continue work:** Ask Sentinal's completed-analysis requirement, History list/refresh/open, and profile/settings controls.
5. **Export:** on-screen summary preview, download action, backend report generation, and the actual PDF artifact.

## Audit findings and changes

| Priority | Finding | Change |
|---|---|---|
| P1 | The compact dock exposed eight routes plus download, making some destinations easy to miss on narrow screens. | At widths up to 980 px, show Home, New analysis, Findings, and History plus a More menu for Architecture, Ask Sentinal, Settings, Profile, and the PDF action. Keep the full dock on desktop. |
| P1 | Tilted capability cards used a horizontal flex row; the third card could extend past the viewport at tablet widths. | Keep the tilt effect but stack card content vertically. The viewport sweep now reports no horizontal overflow from 360 px through 1920 px. |
| P1 | The empty Home state repeated the same start-analysis action in the header, workflow panel, hero, and empty-history panel. | Keep the hero as the main first-run action, remove the empty-state header duplicate, hide the process panel until a job exists, and make the no-history state informational. |
| P1 | Report preview pagination could be mistaken for the final PDF's page count. | Label its three cards as preview sections and state that the downloaded document is four full pages. |
| P1 | The product tour was attached under an animated page container and lacked focus containment. | Portal the dialog to the document body, lock background scrolling, trap Tab focus, restore focus on close, and retain Escape/arrow-key controls. |
| P1 | The prior PDF layout grouped content differently from the required page contract. | Compose four explicit A4 pages and verify page-specific content visually. |

## Preserved behavior and constraints

- Public GitHub repositories and ZIP uploads remain the supported intake paths. Private repository OAuth is not enabled.
- Analysis progress comes from the backend job state. No synthetic progress was added.
- Finding, health, chart, and report values continue to use the analysis snapshot. The PDF demo fixture is clearly identified as a demo.
- The Architecture map remains a static import graph; runtime-only relationships are not implied.
- Light, Dark, and System preferences remain available. The responsive dock change does not alter desktop destinations.
- The local model path, Cognito configuration, GitHub API, and AWS deployment require their respective services/configuration; these integrations were not live-tested in this workspace.

## Verification status

The workspace has a passing Vite production build and 14 passing backend tests. Route smoke checks reached all eight destinations. Responsive CSS viewport checks at 360, 390, 768, 1024, 1280, 1366, 1440, 1600, and 1920 px showed no horizontal overflow; the More menu exposes the hidden routes at compact widths. The tour fits a 375 by 812 CSS viewport, and keyboard focus cycles within the dialog and returns on dismissal. A bundled five-file ZIP completed through the browser intake flow, produced eight findings, and fetched its PDF with HTTP 200. The final demo report was counted as four pages, rendered, and inspected page by page. Cognito sign-in, live GitHub repository intake, and AWS deployment remain outside this local verification.
