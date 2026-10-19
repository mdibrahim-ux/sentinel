# Sentinal UI Reference Mapping

This note maps the supplied UI clips to the application. Each clip is a focused component demo, so the implementation combines their shared design language within Sentinal's existing code-analysis workflow and preserves the real API-driven states.

## Reference-by-reference implementation

| Supplied video | Reference behavior | Sentinal implementation |
|---|---|---|
| `Dashboard-UI-Style(1).mp4` | Pale dashboard with compact spacing, rounded KPI cards, clear charts, and an animated transition between Light and Dark views | Sentinal Home, API-backed metric cards, severity/language/file charts, and the repository intelligence workflow. The reference contains its own sidebar and top tabs, which are intentionally not reproduced because the product requirement calls for dock-only navigation. |
| `Button-UI.mp4` | Animated download progress, complete state, compact share menu | PDF export controls and `ShareSummaryControl`, tied to the real report request |
| `Dock-Animation.mp4` | Floating dark capsule, expanding labels, active icons | Bottom-center `FloatingDock` for quick actions |
| `File-Upload-Style.mp4` | Dashed drop target, layered file glyphs, selected-file state | New Analysis → Upload ZIP, selected file card and size/type feedback |
| `File-Upload-Ui.mp4` | Warm upload button and progress/completion feedback | ZIP submission control and backend-driven analysis progress |
| `Icon-Animation-Style.mp4` | Bold outline icon set, restrained hover feedback | Inline SVG icons across dock, theme control, profile settings and sign-out |
| `Navigation-Tab-UI.mp4` | Floating pill navigation and dark active tab | Bottom floating dock is the only primary navigation; the side rail, upper navigation bar and horizontal tab row are absent |
| `PDF-UI-Summary.mp4` | Paper preview, subtle reveal, compact controls | Data-driven on-screen report preview, three preview sections, pagination and real PDF download |
| `login page(1).mp4` | Light grey surround, centered white canvas, compact sign-in form left, animated geometric cubes right | Sign-in/signup/verification/password-reset page with animated cube illustration and a centered workspace card |

## Functional boundaries

- Existing analysis submission, progress polling, finding state updates, history, architecture map, Ask Sentinal, and PDF download remain connected to the current API.
- Demo/sample-project buttons were removed from the user-facing workflow. A user starts with their own public repository URL or source ZIP.
- ZIP selection is checked in the browser for `.zip` extension and a 5 MB maximum; backend validation remains authoritative.
- The on-screen report paper is a summary preview generated from current analysis data. The Download PDF action retrieves the actual generated report from the API.
- Share Summary shares/copies an analysis summary and snapshot ID; it does not create a public URL or share the PDF itself.
- The floating dock is the only primary navigation. On compact screens it exposes Home, New analysis, Findings, and History directly, with secondary routes and PDF download in a labeled More menu. No top navigation bar, extra tab strip, or side rail is rendered in the authenticated workspace.
- Light, Dark and System preferences are saved in browser storage. System follows OS preference changes and the resolved theme applies to the sign-in page and workspace.
- Cognito-backed sign-in, sign-up confirmation, and password reset are wired in the frontend. They require a real Cognito User Pool ID and app client ID. In Vite development only, when Cognito is not configured, local workspace access remains available and is clearly identified as unauthenticated development access. A production build never exposes that bypass.

## Design tokens

- Typeface: Poppins as specified by the supplied font reference, with sans-serif fallbacks.
- Light workspace: cool neutral canvas, white cards, subtle texture, thin borders, blue primary actions and small warm accents only where they communicate meaning.
- Dark workspace: cool neutral surfaces (`#080A12` and `#101320`), blue selection accents and high-contrast text. The printable report preview intentionally stays paper-white for legibility.
- Interaction: CSS perspective transforms for restrained pointer tilt, short page/detail transitions, persistent selected states, visible disabled controls, and progress derived from actual analysis-job status. Interactions respect `prefers-reduced-motion`; a WebGL scene was intentionally not added because these interactions do not require a 3D renderer.

## Verification

- The backend API suite covers profile persistence and URL validation alongside the existing analysis/report behavior.
- A complete Vite build must be verified on a machine where npm packages can be installed; the working container has no DNS access to the npm registry, so a clean dependency install could not complete.
