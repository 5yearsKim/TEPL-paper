# Additional workload rewrite counts

Three additional model compilations were performed with the existing, hash-pinned
instrumented XLA CPU counter. No XLA rebuild, model execution, numerical testing,
or timing repetitions were performed. The earlier DLRM measurement is reused.
The results are in [results.md](results.md), [summary.csv](summary.csv), and
[summary.json](summary.json). The retained four workloads supply the counts in the current paper.

## Workloads and scope

- ViT: the existing upstream XLA `vit_keras_jax_bf16.hlo`, batch 1,
  224-by-224 RGB input, mixed BF16/FP32. The original input is retained under
  `vit/input.hlo`; no source-model re-export was needed.
- DLRM: the previously recorded FP32 training-step workload, batch 6272, from
  `../xla-rewrite-count`. It was not recompiled for this comparison.
- ResNet-50: the existing upstream XLA `resnet50_keras_jax_f32.hlo`, FP32;
  the original input is retained under `resnet/input.hlo`.
- GPT-2 small: public Hugging Face `FlaxGPT2LMHeadModel` from Transformers
  4.55.4, standard 12 layers, 12 heads, width 768, vocabulary 50,257 and
  124,439,808 parameters. Batch 1, sequence length 16, FP32, deterministic
  forward logits with no KV cache or generation loop. Parameters, token IDs,
  attention mask and position IDs are runtime inputs. Abstract parameter
  shapes are used; no model weights were initialized or downloaded.
  `gpt2-export/` retains the pinned upstream configuration, effective config,
  model source snapshots, exporter, input HLO and export provenance.

Counts cover **AlgebraicSimplifier only**, across all of its invocations in each
normal CPU compilation: 8 for DLRM and the count recorded
in each reviewed summary for other models (7 for GPT-2). They do not cover every XLA pass.
A rule variant is a successful transformation branch identified by original
source line and function, not a canonical mathematical rewrite schema.

`vit/`, `resnet/`, and `gpt2/` preserve the initial raw runs, input/final HLOs,
logs, counter provenance, semantic profiles, registry snapshots and manifests.
Their initial classifications precede review of newly observed source branches.
Use **`reviewed/` for final classifications**, produced by replaying saved raw
counts with the updated registry; no recompilation occurs during replay.

## Semantic assessment

The combined metric uses the user's chosen DLRM definition: direct semantic
representations plus restricted unit-axis normalization candidates. It gives
20/32, 9/17, 5/10 and 6/14 for DLRM, ViT, ResNet-50 and GPT-2, respectively.
It does not measure successful TEPL verification or delegation. Application
counts attached to those variants (103/201, 809/1850, 483/1027 and 795/1693) are native XLA
activity, not measured successful TEPL applications. Per-application dtype,
guard, zero-extent, scalar-operation and reducer eligibility are not checked.
Algebraic semantic representation does not establish strict IEEE equivalence.

Six newly observed branches were reviewed against the pinned original source
and semantic profile, and added to the reusable registry:

| ID | Transformation | Assessment |
|---|---|---|
| AS-5690 | broadcast(iota) to remapped iota | Outside: iota lacks value semantics |
| AS-934 | constant + x to x + constant | Direct: algebraic Add commutativity |
| AS-2311 | uniform literal to scalar broadcast | Conditional: literal payload adapter needed |
| AS-9050 | move retained-dimension reshape after reduction | Outside: general reshape and generic reduction |
| AS-9835 | select(true, x, y) to x | Direct: fixed-predicate select, retaining host literal recognition |
| AS-10505 | fold input pad into convolution window | Outside: missing pad and padded-convolution value contracts |

All observed variants have a recorded assessment; conditional entries remain
conditional. Source excerpts are available in the initial run directories;
final per-rule reasons and frozen registries are under `reviewed/`.

## Validation and reproduction

The counter source/binary hashes and semantic-profile hashes matched the pinned
registry. All six existing offline classification checks passed. Frozen report
manifests and per-rule totals were validated. ResNet-50's final HLO matches its earlier uninstrumented baseline byte for byte.
That baseline and the original workflow provenance are retained in
`reference-baselines/`; the separate transpose-folding experiment is omitted. No separate
uninstrumented ViT/GPT-2 compilation or numerical comparison was performed.

Run `python3 summarize.py` to regenerate the combined summary and check saved
manifests and totals without compiling a model. The reusable counter is at
`/home/onion/Projects/tepl/labs/xla_workload_count/run.py`. For example, replay
the saved ViT data to a new directory with:

```bash
python3 /home/onion/Projects/tepl/labs/xla_workload_count/run.py replay \
  --raw vit/raw-results.json \
  --registry reviewed/vit/support-registry.json \
  --out /tmp/vit-count-replay
```

Each final frozen registry references its adjacent semantic-profile snapshot.
For a new model, use the counter's `count --hlo PATH --out NEW_DIRECTORY`
command. This performs one compilation, never an implicit XLA rebuild.

## GPT-2 export reproduction

The upstream configuration is pinned to model repository revision
`607a30d783dfa663caf39e06633721c8d4cfcd7e`. The model implementation is pinned
to Transformers 4.55.4; no custom GPT-2 operator implementation was written.
The exporter uses `_do_init=False` and JAX shape inference to obtain the full
parameter tree, then lowers forward logits with that abstract tree. The
resulting HLO contains runtime parameter arguments, rather than large embedded
weight constants. This measures graph compilation opportunity, not pretrained
inference accuracy or performance. The short input length does not change the
12-layer architecture or its parameter dimensions.

The existing Python 3.12, JAX 0.7.2 and Flax 0.12.0 environment was reused.
Transformers and extra dependencies were installed into an isolated target
directory, preserving the existing environment. Package versions and imported
NumPy version are recorded in `gpt2-export/`.

```bash
uv pip install --python /tmp/tepl-xla-workflow-venv/bin/python \
  --target /tmp/tepl-gpt2-count-deps 'transformers==4.55.4'
/tmp/tepl-xla-workflow-venv/bin/python gpt2-export/export.py \
  --dependency-dir /tmp/tepl-gpt2-count-deps
```

GPT-2 fired only previously reviewed variants; no registry changes were
required. Its six semantic candidates comprise two direct representations and
four unit-axis normalization candidates. Four variants remain conditional and
four are outside the current profile. Full per-rule reasons are frozen in
`reviewed/gpt2/rules.csv`.
