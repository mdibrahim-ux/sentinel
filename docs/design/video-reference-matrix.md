# UI reference matrix

This matrix records the supplied UI references used for the Sentinal redesign. The eight clips in `Desktop/Dash` were inspected from four rendered frames each (roughly 0.25 s, one-third, two-thirds, and the final 0.3 s). The local clips are portrait recordings at 720 × 1280. The three supplementary clips were also sampled. Observations below distinguish visible states from behavior suggested by a title or code panel.

## Eight primary video references

### `Button-UI.mp4` — Download and Share Button UI

- **Observed composition:** White title area, two pale-gray preview cards side by side, then a dark code panel with a thin purple outline. The cards have rounded corners and restrained shadows.
- **Controls:** A blue Download pill with a small download glyph and a near-black Share pill with a share glyph. Each sits centered in its own card.
- **Type and color:** Narrow black display text, blue and charcoal controls, pale-gray surfaces, black code panel, and violet editor border.
- **Interaction evidence:** Four sampled frames show the same preview, with the pointer by Download. The code panel names `whileHover`/`whileTap`; the clip does not show a completed download or share result.
- **Implementation note:** Use the clear icon-plus-label treatment and a brief press response for real report actions. Do not copy the purple editor frame into the product palette.

### `Dashboard-UI-Style.mp4` — Dashboard V14

- **Observed composition:** Portrait presentation with a black title/code background and a pale dashboard canvas between them. A tiny header row has a brand mark, long central control/search shape, a short action area, and a user marker.
- **Widgets:** The sampled dashboard body remains nearly blank and white. No populated metrics, charts, or widget positions are visible in the supplied clip.
- **Type and color:** White title text with orange “V14”, very light gray dashboard surfaces, and a dark code sample. The code references Framer Motion and Lucide icons.
- **Interaction evidence:** The four sampled frames do not reveal a populated dashboard state or a page transition.
- **Implementation note:** Treat the actual widget layout as undetermined from this clip. Use the supplied dashboard screenshots for card proportions and data hierarchy; keep repository metrics data-driven.

### `Dock-Animation.mp4` — Apple Dock Animation

- **Observed composition:** A small dark slate floating pill centered on a white canvas, with a broad soft shadow. A code example sits below it.
- **Items:** Four compact icons: selected Home, Search, Heart, and a cart with a small red count badge. The active Home tile has a cyan icon and a contained circular highlight.
- **Interaction evidence:** The sampled frames show the same selected state; the editor describes smooth motion and active-icon scaling. The clip does not make the full hover trajectory legible.
- **Implementation note:** Keep a compact floating dock, clear selected state, short hover lift, and a visible count only when real data exists. Sentinal uses destination icons and labels appropriate to its pages.

### `File-Upload-Style.mp4` — File Upload

- **Observed composition:** White page with a pale lavender upload region and a centered white card. The drop target is inset, rounded, and outlined with a fine dashed violet border; a dark editor panel is below.
- **Controls and copy:** Overlapping file/media glyphs, directional arrows, “Drag & drop images, videos, or any file”, a browse link, and a subdued Upload button.
- **Interaction evidence:** The four sampled frames remain on the resting state; no successful file selection or completion is shown.
- **Implementation note:** Reuse the roomy drop surface, dashed boundary, browse action, and selected-file summary. Sentinal restricts input to ZIP archives and should state that constraint.

### `File-Upload-Ui.mp4` — File Button Animation

- **Observed composition:** Warm cream and peach backdrop, with a white rounded file row and a coral upload button. A code panel occupies the lower portion.
- **States:** Resting state shows a paperclip, `Document.pdf`, and Upload. A later sampled state replaces it with a wide coral “Uploading…” control and a thin dark progress line near its bottom edge.
- **Interaction evidence:** The sampled progression shows a clear transition from selected file to in-progress upload. A completion state is not visible.
- **Implementation note:** Keep file name and action together; show progress only while a real request is running, then report the request result.

### `Icon-Animation-Style.mp4` — Icon SVG Animation

- **Observed composition:** White canvas, centered five-item row, labels under each outline icon, one enlarged colored Folder state below, and a dark code panel.
- **Icons:** Home, Folder, Heart, Bell, and User use consistent thin black outline strokes. The selected Folder preview is colored and slightly dimensional.
- **Interaction evidence:** Sampled frames show the same selection; the code uses an icon component with a transition on hover. No detailed motion path is visible.
- **Implementation note:** Keep icon stroke weight and sizing consistent. The Sentinal dock uses a stronger stroke for contrast and native button labels for keyboard and screen-reader access.

### `Navigation-Tab-UI.mp4` — Navigation Tabs V4

- **Observed composition:** A faint dotted white canvas presents three alternatives: a small icon row with an active black “Explore” pill, a longer row of circular icon buttons, and a black floating status capsule with a wordmark and workspace context.
- **Type and color:** Mostly white/gray surfaces, black selected state, small dark line icons, subtle shadows, and sparse spacing.
- **Interaction evidence:** The sampled frames show the same active Explore item; no full page change is demonstrated.
- **Implementation note:** The pill and distinct active treatment transfer to the Sentinal dock. The request for one navigation system takes precedence over the video’s multiple alternative rows; Sentinal has no header tabs or duplicate global nav.

### `PDF-UI-Summary.mp4` — Receipt Animation

- **Observed composition:** Pale gray grid canvas, a centered receipt/print slot, and a floating white action pill near the bottom.
- **Controls:** PRINT is selected in a dark capsule, followed by TEAR, FEED, RESET, and AUDIO controls with compact icons. The caption says to use it after payment confirmation.
- **Interaction evidence:** The sampled frames show the same PRINT selection and receipt slot. The clip does not show a PDF document preview or completed export.
- **Implementation note:** Borrow the compact, labeled action-pill treatment for report tools where it fits. The receipt printer metaphor is unrelated to code analysis and should not be copied literally.

## Supplementary clips

### `login page.mp4`

- A pale gray browser surround contains a wide white sign-in panel. The form is on the left and a geometric stack of outlined cubes, with orange, teal, and magenta blocks, is on the right. The title is “Sign in to Rehau Analysis Dashboard”. Small labels and input text are not legible at the sampled scale.
- All four sampled frames are visually static; no form focus or submission result is visible.
- Sentinal retains its requested product slogan and real Cognito flow, while using the clear split layout and restrained geometric illustration.

### `Animation1.mp4`

- The supplied 2666 × 1500 clip shows a broad gray field and a thin, bright horizontal progress line with a tiny centered mark. The mark is too small to read at the source scale.
- The four sampled frames show the same simple loading-bar composition. Use an indeterminate/progress treatment only when it reflects real analysis progress.

### `Loading animations.mp4`

- The file is only 150 × 90 pixels. The sampled render is blank white at the four time points; no specific animation can be identified reliably.
- Its visual design is therefore unverified and is not used as a styling source.

## Supplied still references

- **`6352246.jpg`:** A component sheet on a warm cream field using deep navy, orange, and teal. The examples repeat rounded capsules, circular icon buttons, outlined controls, toggles, progress indicators, compact tabs, and thick navy outlines. This is the primary color and control reference.
- **`Dashboard.jpg`:** A pale aqua CoachPro dashboard with a narrow navigation rail, upcoming-match and statistics panels, standings, metric tiles, and a promotional card. Its hierarchy is useful; its sports content and sidebar are not.
- **`dashboard1.jpg`:** A light-blue inventory dashboard with a dark teal navigation rail, four summary tiles, a customer metric, donut chart, ranked store bars, and a wide time-series chart. It supports a restrained summary-row plus analytical-grid layout.
- **`flowcharts.webp`:** Dark canvas with a root node and colored curved branches. It supports clearly connected nodes and category color, while Sentinal's ordered workflow remains grounded in actual analysis stages.
- **`framemork.jpg`:** Grayscale application wireframe showing a large main surface, narrow tools rail, and supporting cards. Useful only as a proportion/layout sketch.
- **`Fonts.txt`:** Names Poppins. The interface uses Poppins for UI text and a monospace face for code and technical identifiers.
- **`Dashboard Data Visualization animations.lottie`:** A dotLottie archive containing `Lottie dashboard`, 1920 × 1080, 29.97 fps, and 240 frames (about 8 seconds). Its metadata was inspected; the project has no Lottie renderer, so it is not embedded. The dashboard charts continue to use real analysis data.
- **`6352344.ai` and `6352346.eps`:** These local vector files are present. The `.ai` file has a PDF 1.5 container and the EPS is binary; neither was rendered to a visual preview in this environment, so their artwork is not assumed or copied into the interface.

## Cross-reference decisions

- The clips are portrait tutorial-style presentations with dark code panels below light component previews. Repeated patterns are rounded controls, compact line icons, one obvious active state, quiet shadows, and code-oriented presentation.
- The supplied stills add the usable dashboard hierarchy and the cream/navy/orange/teal palette. These are combined with the requested developer workflow, without copying irrelevant sports or receipt content.
- Sentinal's workflow is an interactive six-stage diagram; completed analysis metrics and findings come from the backend. Empty states do not invent repository counts.
- The authenticated app uses one floating dock for Home, analysis, findings, architecture, Ask Sentinal, history, settings, and profile. The videos show alternate navigation concepts, not an app-specific required route map.
- Some clips do not show interaction outcomes, and `Dashboard-UI-Style.mp4` does not show a populated dashboard in the sampled frames. Those details remain unknown rather than being inferred as facts.
