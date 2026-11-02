# Guarded batched reassociation

This is the emitted-program case study for Sections 6 and 7 and the appendix
“Recorded Reassociation Program.” It is separate from `../recorded-results.json`
and does not change the historical XLA aggregate.

`reassociate.tepl` is self-contained. It declares generalized dot and leaves
all eight replacement fields for inference. Input shape lists, batch lengths,
contraction lengths, and contraction positions are symbolic. The written guard
preserves the inner batch group and explicitly bounds the sum of input ranks by
2^63-1 to establish metadata representability. This is a bound on representation,
not a fixed-rank specialization or a condition inferred after verification.

The recorded compiler returned `status=proved`, `additional-guard: true`, and
exit code zero for check, compilation, and serialized-program validation.
`run.json` gives the exact commands, full compiler/source/output hashes, and
checkout revision. `implementation.patch` preserves the tracked working-tree
changes over that revision used to build this binary. `check.stdout.txt`
contains the full expressions and diagnostic output; `program.json` contains
the executable program. Empty stderr files are intentional.

To reproduce with a TEPL build, run from this directory, setting `TEPL_BIN` to
the desired executable. Use a fresh output location to preserve the record:

```sh
"$TEPL_BIN" check reassociate.tepl --semantic-policy algebraic --rule reassociate_preserve_batch
"$TEPL_BIN" compile reassociate.tepl --semantic-policy algebraic -o /tmp/reassociation-program.json
"$TEPL_BIN" validate /tmp/reassociation-program.json
```

The temporary mapping in the paper is checked against this output:

| Output | Paper |
| --- | --- |
| `auto#2`, `auto#3` | outer replacement, inner replacement |
| `m0`, `m2` | `i_X`, `j_Y` |
| `p0`, `p1` | the paired selections for I and J |
| `m4`, `m5` | `b_Z ++ z_J`, `f_Y` |
| `m6` | `b + len(f_Y) + range(len(f_Z))` |
| `m7` | `pos(f_Z, z_I)` |
| `m8` | `b + pos(f_Y, k_Y)` |

The printed `matched_positions(query, domain)` omits unmatched entries in
general. The proof establishes inclusion and distinctness before identifying
these particular calls with `pos(domain, query)`. Gathering a shifted range
then yields the displayed shifted position lists.

The handwritten proposition proves the displayed metadata program under its
written guard; the compiler diagnostics are implementation evidence, not an
independently checkable proof certificate or a compiler-completeness claim.

`guard-variants.json` preserves the exploratory checks as well. Two versions
with explicit empty-batch equalities returned `Unknown` on an intermediate
axis-set obligation, while the general group-preserving guard succeeded.
The compiler's incomplete search is therefore sensitive to guard form; the
case study does not claim that all stronger guards will also be accepted.
