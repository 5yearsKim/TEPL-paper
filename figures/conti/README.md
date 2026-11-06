# Figure storyboards

Store figure YAML files here. Name them with short, descriptive title keywords in
lowercase, joined by underscores: `attribute_binding.yaml`,
`symbolic_axis_groups.yaml`, or `why_tepl.yaml`. Avoid figure numbers and generic
names such as `figure_1.yaml`; filenames should remain meaningful when figures
are reordered. Update links in [paper_outline.md](../paper_outline.md) when renaming.

## YAML format

- `title`: figure name (metadata; not automatically drawn).
- `concept`: core idea; optional `purpose` states the reader's takeaway.
- `requirements`: concise drawing or styling instructions.
- `children`: visual elements with `name`, `type`, and `pos`; children may nest.
- `type: text`: `content` gives exact visible text; use `|-` for multiple lines.
- `type: image`: `requirements` describe a diagram element, not necessarily a raster image.

Use two-space indentation. Quote strings containing `: ` or starting with `#`.
Follow the shared [figure style](../../tools/figure_style.md).

## Position notation

`pos: [xmin, xmax, ymin, ymax]` gives normalized bounds relative to the immediate
parent; the root is the full canvas. The origin is top-left, with x increasing
rightward and y downward. Keep `0 ≤ xmin < xmax ≤ 1` and
`0 ≤ ymin < ymax ≤ 1`. For example, `[0.1, 0.9, 0.2, 0.6]` spans 10–90% of the
parent's width and 20–60% of its height.

```yaml
title: Attribute binding
concept: Capture a matched operation's attributes.
requirements:
  - Highlight the captured descriptor.
children:
  - name: pattern
    type: text
    pos: [0.1, 0.9, 0.2, 0.6]
    content: |-
      (dot[@d] A B)
      @d captures the attributes.
```
