# Specification-size evidence for the current paper

`specification_size/results/all_31_source_footprint.json` and
`specification_size/reports/all_31_source_footprint.md` contain the current
31-rule static source comparison: 3,014 original explicit versus 2,559
inferred tokens (15.1% fewer). This recount includes all inference-successful
rule identities regardless of the historical explicit-baseline outcome.
Normalization and compaction are included; it is not a new compiler run.
Regenerate it with `python3 tools/summarize_all_31_source_footprint.py`.
`specification_size/results/` retains the complete historical measurement and
responsibility records used to recount the 31 source pairs. The earlier
reports in `specification_size/reports/` preserve their original cohorts;
the current paper uses `all_31_source_footprint` for the 31-rule comparison.
Table 6 separately restores the historical audited 25-case XLA comparison
from `responsibility.json`, including its original numbers and percentage colors.

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
