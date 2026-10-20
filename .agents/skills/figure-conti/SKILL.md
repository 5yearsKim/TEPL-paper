---
name: figure-conti
description: Create or revise concise YAML storyboards (conti) for academic paper figures. Use for figure concepts, layouts, labels, and specifications.
---

# Figure conti

Read the relevant paper context and existing figure. Keep only the core idea, essential labels, examples, layout, and visual relationships; follow the user's scope and notation.

Read [the shared figure style](../../../tools/figure_style.md) for this paper's axis palette, chips, inline group colors, underscore notation, and contextual dimming. Apply it to styling requirements; keep figure-specific semantic emphasis explicit. When revising style alone, preserve content and the user's frame dimensions.

- Save storyboards in `draft/figures/<descriptive_name>.yaml`; avoid figure numbers in filenames.
- Plan for readable text at the intended frame width; follow `figma-figure` sizing for Figma output. Simplify or increase height instead of shrinking labels.
- Specify semantic colors and arrow meanings when needed, keeping them consistent across graphs, code, and tables.
- For requested Figma rendering, use `figma-figure`.

## YAML format

- `title`: figure name, metadata only; `concept`: core idea; optional `purpose`: reader takeaway.
- `requirements`: concise drawing or styling instructions.
- `children`: elements with `name`, `type`, and `pos`; nest for subelements.
- `type: text`: exact visible text in `content`; use `|-` for multiple lines.
- `type: image`: diagram described by `requirements`, not necessarily a raster image.
- `pos: [xmin, xmax, ymin, ymax]`: normalized bounds relative to the immediate parent, with a top-left origin; require `0 ≤ xmin < xmax ≤ 1` and `0 ≤ ymin < ymax ≤ 1`.

```yaml
title: Attribute binding
concept: Capture an operation's attributes.
children:
  - name: label
    type: text
    pos: [0.1, 0.9, 0.2, 0.8]
    content: 'dot[@d]: capture attributes'
```

Use two-space indentation and quote strings containing `: ` or starting with `#`. Check YAML syntax, coordinate bounds, and agreement between examples, arrows, and tables.
