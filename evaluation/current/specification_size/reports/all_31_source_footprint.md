# Source footprints of all 31 inference-successful rules

This is a static recount of saved source variants, selected by the current coverage run. It is not a new compilation or validation experiment. All 31 rule identities are included regardless of the historical explicit-baseline outcome.

| Responsibility | Original explicit TEPL | Inferred TEPL |
|---|---:|---:|
| Matching (LHS) | 407 | 391 |
| Legality checks | 1,159 | 1,207 |
| Attribute reasoning | 985 | 518 |
| Replacement construction | 308 | 288 |
| Other syntax | 155 | 155 |
| **Total** | **3,014** | **2,559** |

The difference is 455 tokens (15.1%). Saved inferred forms include normalization and compaction; the difference is not attributed solely to inference.

- Five original explicit variants and one compact variant did not validate in the historical size run; no validation claim is added here.
- Saved inferred forms include unit-axis normalization and unused-label/empty-block cleanup. Two normalized cases add 48 legality tokens relative to the original forms.
- The historical XLA excerpt comparison is not used in the current 31-rule source-footprint evaluation.

The JSON contains all counted source bytes, hashes, responsibility counts and historical acceptance flags. Original measurement files remain unchanged.
