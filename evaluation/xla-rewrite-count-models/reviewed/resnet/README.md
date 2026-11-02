# ResNet-50 FP32

Scope: All AlgebraicSimplifier invocations in one normal XLA CPU compilation.

Distinct rewrite variants: **10**. Applications: **1027**.

Semantic model coverage (direct + unit-view candidates): **5/10**. This includes normalization candidates, not measured TEPL acceptance.

Known semantic classifications are reused from the reviewed registry. Unreviewed sites are not treated as supported or unsupported. Unit-view and conditional entries remain candidates, not accepted TEPL rewrites. Per-application types, guards and reducers are not checked by this report. No TEPL proof or delegation is measured.

See `rules.csv`, `families.csv`, `review-needed.csv`, and `conditional.csv`. New source sites have context excerpts when the pinned original source is available.
