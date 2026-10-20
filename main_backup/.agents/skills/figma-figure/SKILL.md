---
name: figma-figure
description: Create or update editable academic paper figures in Figma from a storyboard or figure description. Use for Figma figure rendering, styling, and layout fixes.
---

# Figma figures

- Default workspace: [TEPL](https://www.figma.com/design/YQJMjTL8UuRL05QHkQr1Ge/TEPL), file key `YQJMjTL8UuRL05QHkQr1Ge`; use another destination when specified.
- Load `figma:figma-use` before Plugin API calls and other Figma skills when applicable. Inspect the existing figure and surrounding canvas; update its frame in place when requested.
- Follow the YAML conti or user's description using editable vector shapes and text. Use `figure-conti` when the storyboard itself needs revision.
- Read and apply [the shared figure style](../../../tools/figure_style.md). It defines the canonical axis-group palette and representations; keep it synchronized with contis rather than introducing per-figure chip variants. For style-only edits, preserve content and existing frame dimensions.

## Size and style

- Choose **500 px width** for half-width figures and **1000 px width** for full-width figures. Follow the user's choice; if unspecified, decide based on the intended paper placement and content. For auto-layout frames, set `maxWidth` to the chosen width.
- Use shared text styles: **18 px** labels/code/tables, **22–24 px** headings, **16 px minimum** for all text. Reflow or increase height instead of scaling the figure down.
- Use Arial or Liberation Sans for labels and monospace for code; preserve compatible existing fonts or use available equivalents.
- Use flat 2D diagrams, white backgrounds, and generous whitespace; avoid gradients, shadows, textures, and decoration.
- Keep semantic shapes, colors, operation names, and notation consistent across figures. Use neutral data boxes, lightly colored operations, solid transformation arrows, and dashed optional or inferred relationships.

## Palette

Text/outlines `#263238`; accents `#5479A8`, `#6A9F88`, `#D4A65C`; neutral fill `#F3F5F7`; background `#FFFFFF`.

Use the shared style's complete axis palette when axis origins are shown. Other figures may use their explicitly labeled semantic accents. Apply canonical chips to standalone groups and table labels, darker group-colored text inside expressions, and underscore notation. Selected and remaining groups share one base style; dim only contextually excluded groups.

Before finishing, inspect actual text sizes and a screenshot for clipping, overlaps, and arrow/label alignment. Compare recurring groups against the shared style across neighboring figures, including context-specific dimming, and confirm frame dimensions. Check readability at the intended paper size; Figma pixel sizes alone do not determine printed text size.
