# Specification-size evidence for the current paper

`specification_size/results/` retains the complete measurement and responsibility
records; `specification_size/reports/` contains the generated tables. These support
Section 9.3, Table 6, Appendix C and Supplement S2: 32 attempted cases, 28 expanded
explicit/automatic pairs and 25 audited common XLA/TEPL cases. The common cohort
has 9,188 XLA tokens, 2,224 explicit TEPL tokens and 1,829 inferred TEPL tokens.

`provenance.json` and `implementation.patch` retain the original compiler identity
and source changes. The specification-size compiler hash differs from the current
coverage compiler; the measurements have not been rerun during cleanup.

Reproduce in an isolated checkout of the recorded implementation, using the
specification-size scripts under `labs/xla_rewrite/specification_size/scripts/`:

```sh
python3 labs/xla_rewrite/specification_size/scripts/measure.py --run --compiler ./bin/tepl --jobs 4
python3 labs/xla_rewrite/specification_size/scripts/responsibility.py --run --compiler ./bin/tepl --jobs 4
```

Run measurement before responsibility accounting. Lexical tokens exclude comments,
whitespace, imports and shared declarations; responsibilities partition each
included token exactly once. Historical corpus, family, runtime and default-backend
scalability runs have been removed. The active coverage and scalability evidence
are in `../unified-construction/` and `../certified-scalability/`.
