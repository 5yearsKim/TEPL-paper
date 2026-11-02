# Static semantic support of the 32 observed variants

This is a source/dialect audit, using the paper's current HLO value/axis
contracts and the singleton-axis view normalization. Existing XLA literal,
type, precision and applicability checks are retained at the integration boundary.
It is not a claim that the 32 native rules have been ported to standalone TEPL
matching, passed validation, or been delegated during the measured workload.
No XLA recompilation/run or TEPL proof check was performed for this audit.

| Classification | Variants | Applications attached to those variants |
|---|---:|---:|
| Directly representable with current semantic operations | 14 | 55 |
| Candidates using restricted unit-axis view normalization | 6 | 48 |
| Conditional on context, reducer, or additional frontend facts | 6 | 31 |
| Outside the current semantic profile | 6 | 67 |
| Total | 32 | 201 |

Use **14/32** as the direct semantic-representation assessment. The six
unit-view candidates make **20/32 a porting target**, not an accepted-rule count.
The associated application totals are weights from the native XLA counter;
they are not measured successful TEPL applications.

Direct examples include multiplication identities, moving a scalar multiply
through a broadcast, transpose composition, transpose of dot, and sum/negate
movement. The divide-by-broadcast rule is representable, but its existing TEPL
counterpart has an unresolved proof: semantic representation alone does not
establish acceptance. Pointwise constant rules assume the host's existing
literal/splat recognition, as in the original attribute-only integration.

Unit-view candidates include eliminating a no-op reshape, removing unit dot
axes, and broadcast transformations that insert/remove only unit axes. General
reshape semantics is absent. These entries need view-normalized ports and
explicit applicability checks, including zero-element cases; they are not
already validated general reshape implementations.

Conditional entries are:

- Scalar-broadcast indexing/permutation: the same source branch handles both
  modeled operations and unsupported operations, and the five event records
  do not name the affected operation.
- Elementwise broadcast sinking: the concrete scalar operation for its single
  application is not logged; not every generic elementwise operation has a
  semantic declaration.
- Two compare-with-zero branches: the operations are modeled, but arbitrary
  nonnegative-value analysis facts need frontend/guard support.
- Constant reciprocal materialization: arithmetic expressions are modeled,
  while general constant-payload inspection/materialization needs support.
- Trivial generic reductions: unit-axis zero-initialized sums can be modeled;
  arbitrary reducers cannot. The 22 events do not identify reducers/initializers.

Outside entries include arbitrary reshape composition, general reshape around
broadcast/reduce, tuple projection, literal-to-iota conversion, and reshape of
iota. The frozen semantic profile declares general reshape, iota and generic
reduce structurally without value semantics, and has no tuple-value model.

`semantic-support.csv` gives every rule ID, category, evidence and limitation.
`semantic-support-summary.json` contains machine-readable totals.
`classify_semantics.py` reproduces the classification without executing XLA.
The profile files used for this audit are retained under
`source/semantic-profile/`; matched representative rules remain in the sibling
`../unified-construction/inputs/` artifact. Algebraic arithmetic policy applies;
this is not a new strict-IEEE floating-point guarantee.
