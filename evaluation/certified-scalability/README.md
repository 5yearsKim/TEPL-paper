# Certified scalability rerun

Section 9.4 presents these results and the two-panel figure. Supplement S3
and this artifact record the protocol and complete timing table.
It measures automatic dot reassociation at depths 1–10, transpose composition
at ranks 2, 4, 8, 16, 32, and compile costs per API phase. Two panels share one
horizontal row: dot-chain phase bars with median total latency, and transpose
rank. All original automatic rule bodies and guards are kept;
no explicit or partially automatic baseline is timed by this certified-only run.

See `performance.md` for measured boundaries, results, and limits;
`performance.json` for every raw sample; `provenance.json` for source and binary
hashes; `cli-results.json` and `logs/` for all 45 public CLI commands. The C++
driver compares its phase pipeline with public compilation and validates a
portable roundtrip for each case, outside timing. The 60 independent dense
checks validate workload identities, not generated metadata execution.

Build in the TEPL implementation checkout:

```sh
bazel build -c opt //:tepl //labs/reasoning_scalability:certified_benchmark
```

Run in the paper checkout with NumPy and Matplotlib installed:

```sh
python3 tools/run_certified_scalability.py --code-root /path/to/tepl --output /path/to/fresh-results
python3 tools/plot_current_scalability.py --results /path/to/fresh-results/performance_summary.json
```

The runner refuses to overwrite saved measurements. For the retained run:

```sh
python3 tools/run_certified_scalability.py --report
python3 tools/plot_current_scalability.py
```

The source archive contains all production `src/` files plus the benchmark and
build inputs. Overlay it and apply the retained patch to the recorded base
revision to reconstruct the changed checkout. Frozen optimized binaries are in
`bin/`. The normal certified work budgets are used. There is no symbolic proof
search or old ten-second proof deadline; an external 300-second process timeout
bounds the benchmark driver. Source hashes are checked before and after the run.

Compilation excludes parsing/import loading, JSON serialization/loading, graph
rewriting, numerical kernels, process startup and result destruction. Unlike
the old default proof-only timer it includes resolution, type checking, plan
preparation, certified acceptance, materialization, lowering and executable
validation. The original rule inputs and dialect used by the runner are retained in
`source/original-inputs/` and `source/tensor.tepl`. Earlier default-backend
measurements are omitted from this current-paper artifact.
