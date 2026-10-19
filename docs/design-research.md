# Sentinal visual and interaction research

Research completed on 2026-10-19 before the implementation updates in this workspace.

## Visual references

- [Dribbble developer dashboard search](https://dribbble.com/search/developer-dashboard) was used to compare several current dashboard directions, including API tooling, developer workspaces, and analytics views. The useful pattern was a deliberate focal area supported by compact information blocks. Sentinal keeps that hierarchy while grounding every metric in the analyzer output.
- [Behance developer dashboard search](https://www.behance.net/search/projects?search=developer%20dashboard%20design) was reviewed as a second visual direction for portfolio-level identity and editorial composition. Its project results are a changing gallery; Sentinal borrows the idea of a recognizable visual signature without reproducing a specific project.
- [Mobbin web app discovery](https://mobbin.com/browse/web/apps) was opened for production interaction patterns, but the dynamic results did not load in this session. No Mobbin screen is used as implementation evidence.

## Component and accessibility references

- [Material Design 3 navigation bar guidance](https://m3.material.io/components/navigation-bar/guidelines) recommends a small, labeled set of top-level destinations on compact screens and moving overflow destinations into a menu or another navigation pattern. The mobile workspace now keeps four frequent routes on the dock and puts secondary routes and PDF download under More.
- [Apple Human Interface Guidelines: Tab bars](https://developer.apple.com/design/human-interface-guidelines/tab-bars) treats tab bars as top-level navigation, recommends labels, and cautions against overflow. The responsive dock retains explicit labels and an active state.
- [shadcn/ui component catalog](https://ui.shadcn.com/docs/components) was used as a reference for composable controls, dialogs, progress, tables, and clear component states. The application keeps its current React/CSS implementation and did not add shadcn as a dependency.
- [W3C WCAG 2.2](https://www.w3.org/TR/WCAG22/) informed keyboard-operable controls, explicit status text, and focusable modal actions. This is a design reference, not a claim of full WCAG conformance.
- [MDN reduced-motion guidance](https://developer.mozilla.org/en-US/docs/Web/CSS/Guides/Media_queries/Using_for_accessibility) informed the existing reduced-motion rules and the tour's optional, user-started playback.

## Decisions applied

- Keep one primary navigation system and preserve the existing analysis, findings, repository map, history, settings, profile, and export workflows.
- Use a paper-and-ink base with blueprint blue and restrained violet, orange, coral, teal, and lime. Reserve the warm/cool signal colors for their documented roles.
- Limit comic-lab motifs to illustration, annotations, halftone, and the tour stage. Keep dense data surfaces neutral and readable.
- Use a three-step interactive product tour to explain repository intake, evidence review, and the four-page report. Every tour illustration is labeled as illustrative UI rather than scan data.
- Give the PDF explicit four-page composition with the required charts and engineering-intelligence map. Use the same analysis snapshot for counts, paths, and recommendations.
