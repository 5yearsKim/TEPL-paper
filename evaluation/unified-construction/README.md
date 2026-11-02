# Shared canonical metadata-program construction

The admitted whole-axis constructor is now shared by ordinary symbolic
specialization and native portable execution. `inference::emit` constructs the
same residual metadata IR for both. Ordinary ordered synthesis emits it before
creating a proof context; `Result::metadata_program` survives bounded
specialization failure. The duplicate symbolic retained-axis, requirement and
layout recurrences are removed. The expression adapter uses established
mappings/partitions to specialize IR nodes, with independently verified joint
reindexing of paired contraction lists. Set enumeration is unobservable;
ordered traversals and positional outputs retain their order.

The completeness domain and guard requirements are unchanged. CLI `--core` and
`--certified` retain their admission/certification policies; broader general
construction and sound schemas remain outside the complete-constructor theorem.
Native execution supports residual IR; Rust/C++ exports still require successful
expression lowering. No complete guard prover, total expression exporter, or
broader completeness is claimed.

## Coverage regression

All 123 exact task sources and dialects are rerun with one copied optimized
compiler, four workers, and a 30-second command limit. Acceptance requires
`Proved` without extra guards, compilation, and public portable validation.

| Population | Tasks | Default | Core audit | Certified |
| --- | ---: | ---: | ---: | ---: |
| Inference | 38 | 31 | 10 | 31 |
| Verification only | 85 | 67 | 2 | 4 |
| All | 123 | 98 | 12 | 35 |

Every acceptance and first diagnostic equals the earlier certified snapshot.
`comparison.json` records the regression check. Operation family memberships in
`families.csv` overlap. This is a development regression, not held-out evidence;
command durations support no performance claim.

## Compiler snapshots and earlier runs

The coverage rerun uses optimized compiler SHA-256 prefix `f6437fc7366a`;
the specification-size run retains `24d933d91076`. Both use checkout
`494f2dac8273` with separately preserved changes. Full provenance and source
bytes accompany the corresponding experiment artifacts.

Every coverage acceptance and first diagnostic matches the earlier
`352e1fadd432` snapshot; `comparison.json` retains that comparison.
`cases.csv` contains all 123 modeled outcomes; `families.csv` records overlapping
operation memberships and the restricted `--core` audit. The paper's coverage
figure reports default acceptance, while its text separately reports certified
acceptance for inference tasks. The 86 unmodeled catalog cases are not executed
successes or failures.

All reported backends and the restricted-core audit use the same copied binary,
algebraic policy, four workers, and a 30-second per-command timeout. No source,
supplied field, or guard changes between variants. Certified portable programs
must carry `tepl.core-dag.v1`; extension schemas additionally require
`tepl.core-schemas.v1`. Command durations are diagnostic, not phase timings.

## Evidence

`provenance.json`, `implementation-source.tar.gz`, `implementation.patch`, and
`runner.py` preserve the optimized compiler hash, base checkout, source snapshot,
tracked changes and runner. Apply the patch to the recorded base and overlay the
source archive to preserve untracked files and deletions. `inputs/` contains exact
frozen task/dialect bytes, `logs/` all commands, and `programs.tar.gz` accepted
portable programs. `results.json` records their uncompressed hashes.

Eight constructor/acceptance test targets and three export test targets pass.
Generated C++ is compiled and executed under g++ and clang++ at O0/O2; generated
Rust is compiled and executed as well. Existing independent checks include 1,980 emitted
program comparisons, 1,584 exhaustive decisions, 387 exhaustive sum decisions,
685 dense/graph checks and 142 rejection checks; these populations are distinct
and must not be summed as one metric. New tests check shared IR identity,
residual emission with zero specialization budget, guard-independent predicate
agreement, and paired reindexing on anisotropic axes. `validation/` retains logs,
the modified test source, results and current PDF validation. Paper proofs remain
handwritten and rely on the explicitly stated implementation/frontend/backend TCB.

Reproduce into a fresh directory:

```sh
python3 tools/run_backend_comparison.py \
  --compiler /path/to/tepl/bazel-bin/tepl \
  --code-root /path/to/tepl \
  --dialects evaluation/unified-construction/inputs/dialects \
  --backends default core certified \
  --output /tmp/tepl-unified-rerun
```
