# Design system reconstructed from supplied references

This is a manual reconstruction from the screenshots and animation samples. Exact CSS tokens and source components were not embedded in the reference images, so pixel-for-pixel equivalence cannot be guaranteed.

## Typography

- Primary typeface: **Poppins** (the provided font note cites the Google Fonts family).
- Use Poppins for navigation, labels, tables, dashboard headings, buttons and body content. System sans-serif is a fallback if network font loading is unavailable.
- Maintain distinct title/body hierarchy without oversizing minor labels.

## Color tokens

| Token / role | Value | Use |
|---|---|---|
| Light canvas | `#F6F8FB` | Main page background |
| Light surface | `#FFFFFF` | Cards, forms and overlays |
| Primary blue | `#1F6FEB` | Primary actions, focus and active navigation |
| Dark canvas | `#080A12` | Dark-mode page background |
| Dark panel | `#101320` | Dark-mode cards and dialogs |
| Dark surface | `#121A29` | Secondary cards and menu surfaces |
| Border | `#DCE3EC` / `#263143` | Neutral separation in light and dark modes |
| Muted text | `#627087` / `#9EACC0` | Secondary labels in light and dark modes |
| Severity accents | Severity-specific | Reserved for real severity meaning in charts and findings |

Dark mode deliberately uses cool, near-neutral surfaces with blue interaction accents. Severity colors may still include warm hues to communicate a finding's severity, but warm hues are not used as ambient dark-mode backgrounds. The Light, Dark and System preference is centralized in CSS tokens and follows the operating-system preference when System is selected.

## Components and composition

- Prefer rounded rectangular cards and pill controls with quiet neutral outlines.
- Primary actions use a clear blue accent; warm orange is reserved for selected emphasis rather than spread across every component. Active states use a restrained fill/border rather than glow.
- The bottom floating dock is the only primary navigation system. There is no workspace top bar, horizontal tab bar, or left sidebar. Desktop shows all eight destinations; compact layouts show Home, New analysis, Findings, and History with Architecture, Ask Sentinal, Settings, Profile, and PDF download under More.
- Data visualizations use solid flat colors, clear labels and legends, and actual analysis data. Empty states must not invent counts.
- Navigation, progress, form states and theme choices are explicit, keyboard-operable and accessible.
- Use 1 px outlines, moderate corner radii, generous spacing and short, functional transitions. At widths up to 980 px the dock shows four frequent destinations and a More menu for secondary routes and PDF download; focus indicators remain visible.
- Appearance supports Light, Dark and System with three visual previews in Settings and a compact segmented control elsewhere. System follows `prefers-color-scheme`; the preference is persisted in local storage and applies to sign-in and authenticated workspace surfaces.

## Deliberate exclusions

No neon gradients, glowing cards, floating orbs, excessive glass blur, decorative 3D scenes, or fake metrics. The 3D cubes in the login reference are treated as a narrow illustration within that page, not a license to decorate the application with unrelated effects.


## Motion and 3D implementation

The interaction requirements are a shallow pointer-responsive card tilt, stage/detail transitions, and short dock/login state changes. These are implemented with CSS `perspective()`/`transform` and controlled CSS transitions instead of a WebGL canvas. MDN documents CSS transforms in 2D/3D space and recommends honoring `prefers-reduced-motion` for interaction-driven transforms ([CSS transforms guide](https://developer.mozilla.org/en-US/docs/Web/CSS/Guides/Transforms/Using), [transform accessibility notes](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/transform)).

Three.js uses a scene, camera, and renderer for a rendered 3D scene ([Creating a scene](https://threejs.org/manual/pages/creating-a-scene.html)); its geometries, materials, and textures also require deliberate resource cleanup when no longer needed ([disposal guide](https://threejs.org/manual/pages/how-to-dispose-of-objects.html)). React Three Fiber adds declarative React integration but still needs deliberate rendering/performance choices and resource reuse ([scaling performance](https://github.com/pmndrs/react-three-fiber/blob/master/docs/advanced/scaling-performance.mdx), [performance pitfalls](https://github.com/pmndrs/react-three-fiber/blob/master/docs/advanced/pitfalls.mdx)). Since Sentinal's requested 3D effects are limited to interaction depth and do not require a continuously rendered scene, CSS is the simpler and lower-overhead fit; no Three.js/R3F dependency was added.

## Current comic-engineering direction

Sentinal combines a readable engineering workstation with a restrained comic-lab visual language. The comic cues live in bounded surfaces such as the sign-in illustration, the home analysis scene, and the product tour; findings, tables, charts, and forms stay quiet enough for extended use.

| Role | Token | Use |
|---|---|---|
| Paper | `#FFFDF8` | Report pages and light surfaces |
| Ink | `#17182B` | Main text and dark work surfaces |
| Blueprint blue | `#3155F5` | Primary actions, focus, and information |
| Violet | `#8355D9` | Architecture and secondary analysis cues |
| Signal orange | `#E68A34` | Highlights and medium-severity signals |
| Signal coral | `#E25360` | High-severity signals |
| Signal teal | `#17877F` | Low-severity signals |
| Lab lime | `#B7D953` | Positive workflow states and sparse illustration accents |

Severity is always paired with a label. Red wine marks critical signals; color is not used as the only status indicator. Halftone dots, blueprint lines, and offset panels are used sparingly, with no decorative glow on routine data cards.

Space Grotesk is used for editorial headings, Poppins/DM Sans for interface text, and DM Mono for paths and technical identifiers. ReportLab embeds its bundled DejaVu Sans font when available and keeps the same color and severity mapping as the dashboard.

The interactive product tour presents three labeled illustrative scenes. Its example panels are marked as illustrative and are not presented as scan results. Keyboard arrows and Escape work, and the tour can be paused or advanced manually.

## Four-page report contract

1. Project identity, scan metadata, representative repository tree, and the five summary metrics.
2. Finding severity pie chart and severity count bar graph, both derived from the same finding list.
3. A prioritized remediation playbook using actual finding paths, descriptions, remediation, verification, and triage status.
4. A directory-level finding concentration map, fix-first sequence, evidence and confidence notes, and a scoped engineering conclusion.

The report renderer uses explicit canvas page boundaries on A4. It does not depend on automatic flow pagination to decide the page count.
