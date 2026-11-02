# DLRM: distinct rewrite variants and total applications

One normal XLA CPU compilation of the original FP32 DLRM training-step HLO
(batch 6,272) applied **32 distinct AlgebraicSimplifier rewrite variants** a
total of **201 times**, across **eight pass invocations**. No executable was
run, and no timing repetitions were performed. No paper text was changed.

## Counting unit and scope

The scope is every AlgebraicSimplifier invocation during this compilation,
including later invocations that see graphs changed by other passes. Other
XLA optimization passes are outside this count. This is not the total number
of transformations made by the whole CPU compiler.

A rule ID is a successful transformation branch, identified by function and
line in the archived original source file. Equivalent branches remain separate
variants (for example, removing unit dimensions from a dot with and without
an output reshape). These IDs are not a canonical count of mathematical rules
or the paper's curated catalog schema IDs.

Counters record successful replacements and explicit in-place rewrites.
Failed compatibility checks are excluded. Nested replacement helpers are
suppressed so that a call through a compatibility helper is one application.
A broadcast-sinking rewrite counts each affected user. The source instrumentation
covers 322 potential notification sites; only successful observed sites count.

The source audit found a redundant visitor-state marker at original line 9009
immediately preceding the actual reduce/reshape replacement at line 9023.
The raw run records five of each; the completed compilation guarantees that
each of those five branches also completes its replacement. `summarize.py`
checks their paired counts and excludes the five state-only notifications.
Thus 206 raw notifications at 33 sites become 201 rewrite applications at
32 transformation sites. Both raw and normalized data are retained.

## Breakdown

| Transformation category | Distinct variants | Applications |
|---|---:|---:|
| reshape | 4 | 63 |
| broadcast | 5 | 37 |
| reduce | 3 | 28 |
| divide | 3 | 21 |
| multiply | 4 | 20 |
| tuple | 1 | 12 |
| transpose | 4 | 10 |
| dot | 3 | 4 |
| compare | 2 | 2 |
| select | 1 | 2 |
| boolean | 1 | 1 |
| constant | 1 | 1 |

`rules.csv` lists every observed rule ID, a descriptive name, original source
location, and count. A static semantic audit is now available in `semantic-support.md` and
`semantic-support.csv`: 14 direct representations, six unit-view porting
candidates, six conditional variants and six outside the profile. Successful
TEPL validation/delegation remains unmeasured; operation presence alone is
insufficient to establish rule support.

## Validation and reproduction

A positive control has two separate `add(x, 0)` nodes: it reports two
applications of one rule ID. A negative control reports no applications.
Both resulting control graphs pass XLA verification. The model's final canonical
HLO is byte-identical to the previously frozen uninstrumented DLRM baseline;
see `validation.json` for both hashes. The counter is opt-in and does not
change optimizer decisions. Source headers and optimizer options are unchanged.

`plan.json` records workload choice and counting scope before model results.
`raw-results.json` contains the unprocessed counter output; `summary.json` and
`rules.csv` are the audited result. Source, the instrumentation patch, compiler
options, controls and stderr are retained. The model input is byte-identical
to the pinned XLA CPU benchmark file. `provenance.json` records exact versions,
hashes and commands.

To rebuild, place the archived driver, BUILD file and instrumentation script
in `research/rewrite_count/` of the pinned XLA checkout. Run the instrumentation
script (the archived original source must match the checkout), then use the
recorded Bazel command. The driver accepts `--self-test` or
`input.hlo output_directory`. Save its model stdout as `raw-results.json` and
run `python3 summarize.py` here to regenerate the audited tables. Human-readable
labels in that script cover this observed workload; new source sites need review.

## Reusable automation

The counting was automated; the initial semantic assessment was manual.
A reusable pipeline now joins counts to a version-pinned review registry.
The live tool is `/home/onion/Projects/tepl/labs/xla_workload_count/run.py`;
`automation/` retains a runnable source snapshot with the audited profile.

```bash
python3 /home/onion/Projects/tepl/labs/xla_workload_count/run.py count --hlo /path/to/model.hlo --out /tmp/model-rewrite-count
```

This counts one model compilation, without execution or timing repetitions.
No implicit XLA build occurs. Known semantic assessments are reused; newly
observed source branches appear in `review-needed.csv` with source excerpts.
Add one review entry per new variant and replay saved counts instead of
recompiling. Conditional variants remain conditional; actual application-level
TEPL proof/guard/delegation checks are not implemented by this report.
The six offline reuse checks pass and reproduce the saved DLRM totals without
another model compilation. See `automation/README.md` for setup and replay.
