# Evaluation evidence included in the current paper

| Directory or file | Use in the paper |
| --- | --- |
| `unified-construction/` | Section 9.1, Figure 6 and Appendix C: 123 modeled cases, 38 inference tasks, backend outcomes and validation checks. |
| `xla-rewrite-count/` | Section 9.2, Table 5: DLRM native XLA rewrite counts and counter source. |
| `xla-rewrite-count-models/` | Section 9.2, Table 5: reviewed GPT-2, ViT and ResNet counts, plus the reviewed DLRM classification. |
| `current/specification_size/` | Section 9.3, Table 6 and Appendix C: lexical token accounting over 25 common cases and the larger attempted cohort. |
| `certified-scalability/` | Section 9.4, Figure 7 and Supplement S3: all 15 configurations and saved phase measurements. |
| `reassociation/` | Appendix B: recorded semantic check, compilation and portable validation of the displayed program. |
| `source-line-count/` | Introduction: 269 nonblank C++ code lines in the pinned XLA routine. |
| `supplementary-materials/` | Explanatory snapshots, module correspondence and guard details referenced by the appendix. |
| `recorded-results.json` | Frozen task sources, original outcomes and source hashes consumed by the retained coverage runner. |

The paper includes its appendices and the separately built supplement for this
inventory. Historical compiler comparisons, TASO, paired-axis outcome tests,
target screening, emission/acceptance timing, native metadata timing, old default
scalability, the TransformerLM workload count and the older transpose-folding
workflow/integration experiment are omitted.

Shared inputs were preserved before removing their original experiment:
`certified-scalability/source/original-inputs/` and `source/tensor.tepl` contain
byte-identical scalability inputs and dialect; the workload-count package's
`reference-baselines/` contains the ResNet baseline and workflow provenance.
Per-case measurements and compiler/source provenance remain unchanged. The
workload-count aggregate now contains only the four workloads in Table 5.

The retained workload artifacts establish native XLA counts and semantic
classifications. They do not establish the prose's 28-test AlgebraicSimplifier
integration or four-workload numerical agreement; no matching evidence for those
claims was found in this directory. The removed 25-test TransposeFolding study
was a different experiment.

`xla-rewrite-count-models/manifest.json` and
`supplementary-materials/manifest.json` inventory the retained file subsets after
cleanup; per-run manifests and original provenance retain their recorded hashes.
