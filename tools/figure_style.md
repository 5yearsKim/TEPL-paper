# Academic Figure Style

Use [figure-conti](../.agents/skills/figure-conti/SKILL.md) for YAML storyboards and [figma-figure](../.agents/skills/figma-figure/SKILL.md) for Figma rendering and visual conventions.

## Scope and notation

These conventions apply to this paper's contis and editable Figma figures. Preserve the requested content and existing frame dimensions during style-only revisions. Explicit user choices take precedence.

Use literal underscore notation for qualified group names such as `I_sel` and `J_rem`; do not construct typographic subscripts or outline text. Preserve concrete axis labels and the mathematical meaning of expressions.

## Axis-group palette

Color identifies axis origin, including when an axis changes its role in a replacement operation. Subgroups inherit their parent's color. Composite groups such as `G`, `D`, and `S` stay neutral unless the figure explicitly establishes another meaning.

| Origin | Border / connector | Pale chip fill | Inline text |
| --- | --- | --- | --- |
| B | `#5479A8` | `#ECF2F8` | `#3F608A` |
| I, I_sel, I_rem | `#6A9F88` | `#EEF5F1` | `#396F59` |
| K | `#D4A65C` | `#FBF4E7` | `#9A702B` |
| J, J_sel, J_rem | `#9076AD` | `#F3EFF8` | `#71538F` |
| H / neutral axes | `#A7B2BB` | `#F3F5F7` | `#52616B` |

Tensor identities are separate from axis-group names: a tensor named `B` does not receive the batch group's color.

## Group representations

- Standalone groups and concrete axis tokens use a pale fill, 1 px origin-colored border, 3 px corner radius, and dark `#263238` text. Use editable monospace text, normally 16 px with 20 px line height in compact chips. Use consistent horizontal padding of 5–6 px and a minimum chip height of 24 px. Preserve equal-width axis strips or cards when their geometry conveys the example.
- Group labels in mapping tables use the same chip treatment, inset within neutral cells. Table grid lines are structural, not substitutes for group borders.
- Groups inside prose, equations, code-like semantic expressions, or mapping queries use the palette's darker inline text color without chip backgrounds. Keep operators, position values, and ordinary expression text neutral. Retain the established font size of the surrounding expression.
- `sel` and `rem` use the same base chip style. Their suffixes, labels, positions, and connectors explain their distinction. Do not dim every remaining subgroup.
- Dim a group only for a stated contextual reason. In U inference, `I_rem` is absent from U's inputs: use a white fill, pale `#CCD8D2` outline, and readable muted `#73847C` text in its X/O reference rows. Active appearances of `I_rem` elsewhere use the normal I style.
- Group-role overview cards may retain their larger group-letter headings; their borders and fills follow the same palette.

## Other semantic categories

Use neutral graph-operation boxes and supporting cards. Attribute-record badges use explicit `node.attrs` labels (for example, `tr.attrs`, `u.attrs`, and `out.attrs`) and their figure's declared capture/manual/inferred colors; they are not axis groups. Name operations with `(node: op ...)`; field reads use `node.attrs.field`. Omitted RHS attributes request inference unless supplied by `derive` or inline reuse such as `(op[source.attrs] ...)`. Do not display the removed `[@name]` or `[auto]` syntax.

Scope colors and compiler/manual status colors are local categories with explicit labels. Keep scope bodies and borders neutral when colored axis groups occur inside; retain restrained colored title bands or accents to identify the scopes. Never recolor an axis group to match its surrounding scope or compiler stage.

In pattern/replacement syntax, highlight operation tokens such as `dot`, `transpose`, and `add`. Keep node labels (`d1:`, `tr:`, `out:`), tensor inputs, punctuation, and rewrite arrows neutral. Use each figure or panel's declared theme color; consistency means highlighting the same syntactic category, not imposing one hue everywhere. For example, explicit/manual rules may use amber and inferred rules green. Attribute expressions in `derive`, concrete attribute values, badges, and symbolic axis groups retain their separate semantic colors.

Keep purposeful emphasis such as a contraction row or newly derived mapping cells, with an explanatory label or established context. Such emphasis does not change the group's token style.

## Typography, containers, and arrows

- Use shared 22 px section headings, 18 px primary labels/expressions/table text, and 16 px compact annotations and chips. Use Arimo/Arial-compatible text for labels and Cousine/compatible monospace for code and group chips. Preserve existing shared Figma text styles where applicable.
- Keep text editable. Use neutral text `#263238`, secondary text `#65727B`, white backgrounds, neutral fills `#F3F5F7`, and card borders `#DCE2E7`.
- Supporting cards use 0.8 px borders and 4 px corner radii. Use 1 px result outlines where needed. Use consistent local spacing, usually 8–12 px gaps and 8–12 px card padding, within the user's frame-size constraint.
- Use thin neutral tensor/dependency arrows, solid for transformations and dependencies and dashed for correspondence or explicitly inferred relationships. Axis-pairing connectors may use their origin colors. Keep arrowheads and weights consistent within equivalent contexts.

## Verification

Check the same group across chips, table labels, and inline expressions in neighboring figures. Verify contextual dimming, readable text, clipping, connector alignment, and the original frame dimensions. Synchronize conti instructions with Figma styling so regeneration preserves the convention.

## Formal-model notation

Use `M_U` for mandatory axes and `I_T` for the symbolic ordered interface of
tensor T (typeset as sans-serif I in the paper). Reserve P for input ports and
P_v for canonical live sets. Use H for the example's final free-axis group,
D for its outer contraction group, and F for the full target output order.
Use `pos(I, G)` for ordered position lookup and `ι(G)` for `range(|G|)`.
The constructor reads `m = (s, α)`; individual captured descriptors are parts
of α. Language code still uses its actual builtins and `++` syntax.
