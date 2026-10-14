# Monoid-Guided Equality Saturation for Distributed Tensor Programs

## 1. Abstract

Distributed tensor compilers typically optimize parallel execution using operator-specific sharding rules, predefined parallelization templates, or searches over explicitly enumerated strategies. Systems such as GSPMD and Shardy propagate tensor shardings according to per-operation semantics, while Alpa searches over inter- and intra-operator parallelism. Unity additionally searches jointly over algebraic transformations and distributed execution.

This proposal investigates a complementary question:

> **Can a compiler derive distributed implementations directly from an operator's mergeable algebraic state instead of requiring distribution strategies to be explicitly defined for every operator?**

We propose to represent suitable tensor computations using a **summary algebra**

$$
\mathcal{A}=(S,\otimes,e,\phi,\psi),
$$

where \(S\) is a partial-result state, \((S,\otimes,e)\) is a monoid, \(\phi\) maps local input partitions into partial states, and \(\psi\) converts a completed state into the logical operator result.

A distributed computation then follows from the homomorphism

$$
H(X_1\cup X_2)
=
H(X_1)\otimes H(X_2),
$$

allowing the compiler to transform a global computation into local computation followed by a collective over \(\otimes\).

Rather than selecting a single derived implementation immediately, we insert alternatives into an e-graph. Equality saturation explores choices of partition dimension, partial-state representation, collective realization, reassociation, resharding, and producer/consumer fusion. A topology-aware extractor then chooses a physical implementation.

The core hypothesis is that **algebraic summaries can serve as a reusable semantic interface between tensor operators and distributed execution**, reducing operator-specific distribution logic while exposing optimization opportunities unavailable to purely sharding-driven approaches.

---

# 2. Motivation

Consider matrix multiplication

$$
C=AB,
$$

with

$$
A\in\mathbb{R}^{M\times K},
\qquad
B\in\mathbb{R}^{K\times N}.
$$

If the contracting dimension \(K\) is partitioned across \(P\) devices,

$$
A=[A_0,A_1,\ldots,A_{P-1}],
$$

and

$$
B=
\begin{bmatrix}
B_0\\
B_1\\
\vdots\\
B_{P-1}
\end{bmatrix},
$$

then

$$
AB
=
\sum_{p=0}^{P-1} A_pB_p.
$$

Each device can therefore compute

$$
S_p=A_pB_p
$$

locally and combine the partial results using addition:

$$
C=S_0+S_1+\cdots+S_{P-1}.
$$

The distributed implementation is consequently

```text
Device 0: A0 @ B0 ─┐
Device 1: A1 @ B1 ─┼── AllReduce(+)
Device 2: A2 @ B2 ─┤
Device 3: A3 @ B3 ─┘
```

This transformation follows from algebraic structure:

$$
S=\mathbb{R}^{M\times N},
$$

$$
\otimes=+,
$$

$$
e=0,
$$

$$
\phi(A_p,B_p)=A_pB_p,
$$

$$
\psi(S)=S.
$$

The compiler does not fundamentally need to know a rule called:

```text
K-sharded-matmul -> local-matmul + all-reduce
```

if it already knows

$$
\boxed{
AB=\bigoplus_p \phi(A_p,B_p)
}
$$

with

$$
\oplus=+.
$$

This motivates replacing part of the operator-specific distribution interface with an algebraic one.

---

# 3. Problem Statement

Modern tensor partitioners already provide sophisticated sharding machinery. GSPMD automatically propagates partitioning through computation graphs from limited annotations. Shardy factors operation-specific sharding semantics into an `OpShardingRule`, including relationships among batching, non-contracting, and contracting dimensions.

This substantially reduces duplicated partitioning logic, but the compiler must still know the distribution semantics of an operation.

For example, the compiler effectively needs to understand that the contracting dimension of MatMul produces a partial output requiring reduction.

A hypothetical new operator

```text
FooReduce(x)
```

may require additional knowledge describing:

```text
how x can be partitioned
what partial result is produced
how partial results are merged
what collective is required
whether finalization is necessary
how the partial result interacts with consumers
```

The central problem of this proposal is therefore:

$$
\boxed{
\text{Can these distributed semantics be derived from a compact algebraic description?}
}
$$

More precisely, the project addresses three problems.

### Problem 1 — Distribution rules are tied to operator semantics

Compilers must understand how each operator behaves under partitioning.

Even generic sharding-rule representations ultimately encode operator-specific relationships.

We want to derive a significant subset of this information from a reusable algebraic interface.

### Problem 2 — A legal decomposition does not uniquely determine its implementation

Suppose we know

$$
C=\sum_p S_p.
$$

The reduction might be implemented as

$$
\operatorname{AllReduce},
$$

or

$$
\operatorname{ReduceScatter}+\operatorname{AllGather},
$$

or a hierarchical reduction, tree reduction, ring reduction, or fused producer-reduction implementation.

Selecting the algebraic decomposition first and the collective independently can therefore be suboptimal.

### Problem 3 — The best partial representation may differ from the logical operator output

Some operations require a richer partial state than their final result.

Mean provides a simple example:

$$
S=(s,n)
$$

with

$$
(s_1,n_1)\otimes(s_2,n_2)
=
(s_1+s_2,n_1+n_2),
$$

and

$$
\psi(s,n)=s/n.
$$

Variance requires a richer state such as

$$
(n,\mu,M_2).
$$

Log-sum-exp can use

$$
(m,\ell).
$$

Streaming attention can use a state resembling

$$
(m,\ell,O).
$$

Thus the communication object can be a **semantic summary state**, rather than an ordinary tensor intermediate.

The compiler should therefore search not only over tensor shardings but over **state representations**.

---

# 4. Main Research Hypothesis

The proposal is based on the following representation.

For an operator \(F\), define

$$
\mathcal A_F =
(S,\otimes,e,\phi,\psi).
$$

Here:

$$
(S,\otimes,e)
$$

forms a monoid,

$$
\phi:X_{\text{local}}\rightarrow S
$$

constructs a local summary, and

$$
\psi:S\rightarrow Y
$$

produces the logical result.

For a partition

$$
X=X_1\uplus X_2\uplus\cdots\uplus X_P,
$$

we require

$$
F(X)
=
\psi\left(
\phi(X_1)
\otimes
\phi(X_2)
\otimes
\cdots
\otimes
\phi(X_P)
\right).
$$

Equivalently, define

$$
H(X)=\operatorname{fold}_{\otimes}(\phi(X)).
$$

Then

$$
H(X_1\uplus X_2)
=
H(X_1)\otimes H(X_2).
$$

This is precisely the homomorphic property that enables divide-and-conquer parallelization. Homomorphism-based parallelization has a long history in functional programming and automatic parallelization, so the mathematical fact itself is not the proposed novelty.

The proposed novelty is using this structure as a **tensor-distribution synthesis interface** and coupling the resulting alternatives with equality saturation.

---

# 5. Compiler Architecture

The compiler pipeline is

$$
\boxed{
\text{Tensor Program}
\rightarrow
\text{Summary Algebra}
\rightarrow
\text{Distribution Synthesis}
\rightarrow
\text{Equality Saturation}
\rightarrow
\text{Topology-Aware Extraction}
}
$$

The key separation is:

```text
Summary algebra:
    What decompositions are semantically legal?

E-graph:
    What equivalent distributed programs exist?

Physical state:
    Where and in what form does each value live?

Cost model:
    Which equivalent implementation is cheapest?
```

This distinction prevents the monoid abstraction from becoming merely another cost-model heuristic.

---

# 6. Summary Specification

A first prototype could expose an operator description such as:

```rust
struct SummarySpec {
    state_ty: StateType,

    identity: Expr,

    lift: LiftFn,

    combine: CombineFn,

    finalize: FinalizeFn,

    partition_axis: AxisConstraint,
}
```

Conceptually:

```rust
SummarySpec {
    state_ty: Matrix(M, N),

    identity: zeros(M, N),

    lift: |a_tile, b_tile| matmul(a_tile, b_tile),

    combine: |x, y| add(x, y),

    finalize: |x| x,

    partition_axis: ContractingDimension,
}
```

For MatMul this describes

$$
\phi(A_k,B_k)=A_kB_k
$$

and

$$
S_1\otimes S_2=S_1+S_2.
$$

The compiler can derive

```text
matmul(A, B)
```

into

```text
finalize(
    distributed_reduce(
        combine,
        local_map(lift, shard(A, K), shard(B, K))
    )
)
```

which becomes

```text
all_reduce(
    add,
    local_matmul(A_local, B_local)
)
```

for a replicated output.

---

# 7. Examples Beyond MatMul

A major requirement of the paper is demonstrating that the abstraction generalizes.

| Operation         | Summary state \(S\) | Combine                | Finalize       |
| ----------------- | ------------------- | ---------------------- | -------------- |
| Sum               | \(s\)               | \(s_1+s_2\)            | \(s\)          |
| Max               | \(m\)               | \(\max(m_1,m_2)\)      | \(m\)          |
| Mean              | \((s,n)\)           | \((s_1+s_2,n_1+n_2)\)  | \(s/n\)        |
| MatMul over \(K\) | \(P\)               | \(P_1+P_2\)            | \(P\)          |
| LogSumExp         | \((m,\ell)\)        | stable state merge     | \(m+\log\ell\) |
| Variance          | \((n,\mu,M_2)\)     | Welford-style merge    | \(M_2/n\)      |
| Attention         | \((m,\ell,O)\)      | online attention merge | \(O/\ell\)     |

The important examples are not `sum` and `max`; those mainly validate the framework.

The stronger demonstrations are operations for which

$$
\boxed{
\text{partial state} \neq \text{final output}
}
$$

such as variance, log-sum-exp, and online attention.

---

# 8. Equality Saturation

After semantic decomposition, the compiler should not immediately commit to a communication strategy.

Instead, it introduces equivalent plans into an e-graph.

For example,

```text
DistributedReduce(Add, partials)
```

may expand into

```text
AllReduce(Add, partials)
```

or

```text
AllGather(
    ReduceScatter(Add, partials)
)
```

or

```text
HierarchicalReduce(Add, partials)
```

subject to output-state requirements.

Likewise,

```text
AllReduce(Add, LocalMatMul(...))
```

might interact with downstream consumers.

Suppose the next operation can consume a sharded result. Then

```text
AllReduce
```

might be replaced by

```text
ReduceScatter
```

and the output remain distributed.

This is exactly where equality saturation becomes useful: communication decisions, state representation, sharding, and consumer fusion are mutually dependent.

Tensat demonstrates the usefulness of equality saturation for tensor-graph rewrite ordering, while the recent EqiForge work places high-level tensor algebra and tiled execution strategies within one equality-saturation framework.

This proposal instead targets the distributed dimension:

$$
\boxed{
\text{summary representation}
\times
\text{partition}
\times
\text{collective}
\times
\text{consumer state}
}
$$

---

# 9. Proposed E-Graph Representation

A minimal language could contain:

```rust
define_language! {
    enum DistLang {
        Num(i64),
        Symbol(Symbol),

        "add" = Add([Id; 2]),
        "mul" = Mul([Id; 2]),
        "matmul" = MatMul([Id; 2]),

        "lift" = Lift([Id; 2]),
        "combine" = Combine([Id; 2]),
        "finalize" = Finalize(Id),

        "shard-k" = ShardK(Id),

        "local-matmul" = LocalMatMul([Id; 2]),

        "all-reduce" = AllReduce(Id),
        "reduce-scatter" = ReduceScatter(Id),
        "all-gather" = AllGather(Id),

        "reshard" = Reshard(Id),
    }
}
```

The MatMul decomposition rule could conceptually be:

```rust
rewrite!(
    "matmul-to-summary";
    "(matmul ?a ?b)"
    =>
    "(finalize
        (all-reduce
            (local-matmul
                (shard-k ?a)
                (shard-k ?b))))"
);
```

But this rule alone is **not sufficient as the final design**, because it simply hardcodes the transformation.

The actual proposal is that this rewrite should be generated from:

```rust
MonoidSpec {
    operator: MatMul,
    split_axis: K,

    lift: LocalMatMul,

    state: PartialMatrix,

    identity: Zero,

    combine: Add,

    finalize: Identity,
}
```

The generated rewrite is then an instance of a generic theorem:

```text
GlobalOp(X)

    =>

Finalize(
    DistributedReduce<Combine>(
        LocalLift(Shard(X))
    )
)
```

rather than a MatMul-specific rewrite.

---

# 10. Physical State

Logical equality alone does not capture distributed execution.

An expression should therefore carry or be associated with physical state

$$
p=
(\sigma,\pi,\rho),
$$

where

$$
\sigma=\text{tensor sharding},
$$

$$
\pi=\text{device placement},
$$

and

$$
\rho=\text{representation type}.
$$

For example:

```text
PartialMatMul
{
    sharding = K-partitioned,
    placement = mesh.x,
    representation = partial<M,N>
}
```

and

```text
MatMulResult
{
    sharding = replicated,
    placement = mesh.x,
    representation = full<M,N>
}
```

Then

$$
(\text{PartialMatMul},p_{\text{partial}})
\xrightarrow{\operatorname{AllReduce}(+)}
(\text{MatMul},p_{\text{replicated}}).
$$

Alternatively,

$$
(\text{PartialMatMul},p_{\text{partial}})
\xrightarrow{\operatorname{ReduceScatter}(+)}
(\text{MatMul},p_{\text{sharded}}).
$$

The second result may be preferable if the consumer accepts the corresponding sharding.

This naturally connects the project to a **state-refined e-graph** formulation:

$$
(C,p)
$$

rather than storing only a logical equivalence class \(C\).

---

# 11. Soundness

The algebra specification must satisfy three properties.

First, identity:

$$
e\otimes s=s\otimes e=s.
$$

Second, associativity:

$$
(s_1\otimes s_2)\otimes s_3
=
s_1\otimes(s_2\otimes s_3).
$$

Third, decomposition correctness:

$$
F(X)
=
\psi
\left(
\bigotimes_i
\phi(X_i)
\right).
$$

If those conditions hold, reassociation and distributed combination preserve the logical operator semantics.

A compiler could support three verification modes:

```text
Trusted built-in specification

User-provided specification + property testing

Symbolically verified specification
```

Unity is relevant here because it automatically generates graph substitutions from operator specifications and verifies their correctness using theorem proving.

One additional issue is floating-point semantics.

Operations such as addition are mathematically associative but not bitwise associative in IEEE floating point:

$$
(a+b)+c
\neq
a+(b+c)
$$

in general.

The system therefore needs a semantic mode distinguishing:

```text
strict floating-point semantics
```

from

```text
reassociation-permitted numerical semantics.
```

This is not merely an implementation detail; it should be part of the soundness model.

---

# 12. Distribution Synthesis

Given a valid summary algebra, the compiler can generate candidate distributed programs.

For

$$
F(X)=
\psi\left(
\bigotimes_i\phi(X_i)
\right),
$$

one generic transformation is

$$
F(X)
\Rightarrow
\psi\left(
\operatorname{Collective}_{\otimes}
\left[
\phi(X_i)
\right]
\right).
$$

The form of the collective depends on the required physical output.

If every device needs the complete state:

$$
\operatorname{AllReduce}_{\otimes}.
$$

If devices can retain distinct portions:

$$
\operatorname{ReduceScatter}_{\otimes}.
$$

If only one device requires the result:

$$
\operatorname{Reduce}_{\otimes}.
$$

If the reduction hierarchy follows topology:

$$
\operatorname{HierarchicalReduce}_{\otimes}.
$$

This allows a separation between

$$
\text{semantic combine}
$$

and

$$
\text{physical collective implementation}.
$$

---

# 13. Topology-Aware Extraction

Each candidate expression is assigned a physical cost.

A simple first model is

$$
T=T_{\text{compute}}+T_{\text{communication}}.
$$

Communication can initially use an \(\alpha\)-\(\beta\) model:

$$
T_{\text{comm}}
=
N_{\text{messages}}\alpha
+
N_{\text{bytes}}\beta,
$$

where \(\alpha\) approximates communication startup latency and \(\beta\) represents transfer cost per byte.

A topology-sensitive version becomes

$$
T_{\text{comm}}
=
\sum_{e\in E}
\left(
n_e\alpha_e+
b_e\beta_e
\right).
$$

The extraction problem is then:

$$
\min_{x\in\mathcal E}
T(x)
$$

subject to:

$$
\operatorname{memory}(x)\le M_d
$$

for every device \(d\), along with compatibility constraints for layouts and shardings.

Profiling can later replace or calibrate the analytical cost model.

---

# 14. Concrete Example: MatMul

Input:

```python
C = A @ B
```

Suppose the mesh has four GPUs.

The summary specification tells the compiler that partitioning \(K\) produces additive partial results.

The e-graph may therefore contain:

```text
MatMul(A,B)

KShard:
    AllReduce(
        LocalMatMul(
            ShardK(A),
            ShardK(B)
        )
    )

KShard-RS:
    ReduceScatter(
        LocalMatMul(
            ShardK(A),
            ShardK(B)
        )
    )

MShard:
    LocalMatMul(
        ShardM(A),
        Replicate(B)
    )

NShard:
    LocalMatMul(
        Replicate(A),
        ShardN(B)
    )
```

If the next operation requires a replicated tensor, `AllReduce` may be preferable.

If the next MatMul consumes an \(M\)- or \(N\)-sharded tensor, the `ReduceScatter` result might avoid an additional communication step.

The important difference from a traditional local rule is that the extractor sees the entire chain.

For example:

```text
MatMul
  ↓
ReduceScatter
  ↓
ReLU
  ↓
LocalMatMul
```

may be cheaper than:

```text
MatMul
  ↓
AllReduce
  ↓
ReLU
  ↓
Reshard
  ↓
LocalMatMul
```

despite both being valid implementations.

---

# 15. Concrete Example: Mean

Consider

```python
y = mean(x)
```

Instead of requiring a built-in distributed mean implementation, specify

$$
S=(s,n).
$$

Local lift:

$$
\phi(X_i)
=
\left(
\sum_{x\in X_i}x,
|X_i|
\right).
$$

Combine:

$$
(s_1,n_1)\otimes(s_2,n_2)
=
(s_1+s_2,n_1+n_2).
$$

Finalize:

$$
\psi(s,n)=\frac{s}{n}.
$$

The compiler automatically obtains:

```text
Local:
    local_sum
    local_count

Collective:
    all_reduce((sum, count))

Finalize:
    sum / count
```

No `DistributedMean` rule is fundamentally required.

---

# 16. Stronger Example: LogSumExp

For numerical stability,

$$
\operatorname{LSE}(x)
=
\log\sum_i e^{x_i}.
$$

Define state

$$
S=(m,\ell),
$$

where

$$
m=\max_i x_i
$$

and

$$
\ell=\sum_i e^{x_i-m}.
$$

For two states

$$
S_1=(m_1,\ell_1),
\qquad
S_2=(m_2,\ell_2),
$$

let

$$
m=\max(m_1,m_2),
$$

$$
\ell=
e^{m_1-m}\ell_1+
e^{m_2-m}\ell_2.
$$

Then

$$
S_1\otimes S_2=(m,\ell).
$$

Finally,

$$
\psi(m,\ell)=m+\log\ell.
$$

This example is important because the communicated state is not the logical output and the combination is not simple addition.

It demonstrates the purpose of the proposed abstraction much better than `sum`.

---

# 17. Attention as a Stretch Goal

Streaming attention maintains summary state approximately of the form

$$
S=(m,\ell,O),
$$

where \(m\) tracks the running maximum, \(\ell\) the normalized denominator, and \(O\) the weighted value accumulation.

Partial attention computations over distinct key/value partitions can be merged after correcting for their different maxima.

Thus a distributed attention implementation can potentially be described as:

$$
S
=
S_0\otimes S_1\otimes\cdots\otimes S_P.
$$

This creates an interesting opportunity:

$$
\boxed{
\text{communicate attention state rather than materialized attention scores}
}
$$

and allows the e-graph to search where state merging and communication occur.

This should be treated as a later demonstration rather than the first implementation target.

---

# 18. Research Questions

The evaluation should answer five concrete questions.

**RQ1: Expressiveness.**
How many useful distributed tensor patterns can be generated from summary specifications rather than operator-specific distribution rewrites?

**RQ2: Generalization.**
Can a new operator receive distributed execution support by defining only

$$
(\phi,\otimes,e,\psi)
$$

without adding collective-specific compiler rules?

**RQ3: Optimization quality.**
Does jointly exploring

$$
\text{summary state}
\times
\text{sharding}
\times
\text{collective}
$$

produce faster programs than committing to each decision independently?

**RQ4: Communication efficiency.**
Can alternative semantic states reduce communication volume, resharding, or intermediate materialization?

**RQ5: Search cost.**
Can equality saturation represent this search space without unacceptable e-graph growth or compilation time?

---

# 19. Evaluation Methodology

The initial experiments should use several levels of workload complexity.

### Microbenchmarks

Evaluate:

```text
Sum
Mean
Variance
LogSumExp
MatMul
batched MatMul
```

These isolate distribution behavior.

### Operator chains

Evaluate patterns such as

```text
MatMul -> ReLU -> MatMul

MatMul -> Reduce -> MatMul

LogSumExp -> consumer

MatMul -> normalization -> MatMul
```

These determine whether state-aware joint extraction provides benefits beyond isolated operators.

### Transformer components

Evaluate:

```text
MLP block
attention block
RMSNorm + linear
QK^T / softmax / V
```

The final experiment can use full transformer layers.

---

# 20. Baselines

The key baselines should distinguish the source of improvement.

| System                                    | Purpose                                      |
| ----------------------------------------- | -------------------------------------------- |
| Manual distributed implementation         | Performance upper/reference point            |
| XLA GSPMD / Shardy                        | Modern automatic sharding baseline           |
| Greedy monoid lowering                    | Tests monoid synthesis without global search |
| E-graph + hand-written distribution rules | Tests e-graph without algebraic synthesis    |
| Proposed monoid + e-graph                 | Full system                                  |

GSPMD is an especially important baseline because it automatically propagates tensor partitionings and lowers them to distributed computation.

Shardy is useful because its `OpShardingRule` provides a particularly direct comparison with the proposed algebraic operator interface.

Unity should primarily be discussed as a conceptual related-work comparison unless reproducing its system is practical. Unity already demonstrates joint search over algebraic transformations and parallelization, so the paper must clearly distinguish **distribution synthesis from algebraic summary semantics** from Unity's graph-substitution approach.

Alpa provides another important point of comparison because it automatically generates distributed execution plans spanning intra- and inter-operator parallelism.

---

# 21. Metrics

Performance alone is not enough.

The evaluation should report:

| Metric                           | Meaning                            |
| -------------------------------- | ---------------------------------- |
| Execution latency                | End-to-end performance             |
| Communication bytes              | Network cost                       |
| Number of collectives            | Communication structure            |
| Resharding bytes                 | Cost caused by incompatible states |
| Peak memory                      | Feasibility and efficiency         |
| Search time                      | Compiler overhead                  |
| E-nodes / e-classes              | Search-space growth                |
| Number of synthesized strategies | Expressiveness                     |
| Operator-specific rule count     | Engineering complexity             |
| Algebra specification size       | Abstraction compactness            |

One particularly valuable experiment would compare:

$$
\text{lines of operator-specific distribution rules}
$$

against

$$
\text{lines of summary specification}.
$$

The goal is not simply fewer lines of code but demonstrating that one semantic declaration generates multiple legal distributed strategies.

---

# 22. Ablation Studies

The full system should be compared against several restricted variants.

```text
A. Hardcoded sharding + greedy collective

B. Monoid-derived sharding + greedy collective

C. Hardcoded sharding + e-graph

D. Monoid-derived sharding + e-graph

E. D + topology-aware physical state
```

This separates three hypotheses:

$$
\text{Does algebraic synthesis help?}
$$

$$
\text{Does equality saturation help?}
$$

$$
\text{Does physical-state-aware extraction help?}
$$

A successful paper should not rely solely on showing that variant E is fastest.

---

# 23. Key Generalization Experiment

A particularly compelling experiment would be to hide one operator from the compiler.

For example, suppose the compiler initially knows:

```text
sum
matmul
max
```

but has no distributed implementation for `logsumexp`.

Provide only:

```text
state = (m, l)

lift = local_logsumexp_state

combine = stable_merge

finalize = m + log(l)
```

Then ask whether the compiler can automatically generate:

```text
local state computation
        ↓
distributed state reduction
        ↓
finalization
```

and choose among physical communication strategies.

This demonstrates that the system is performing **distribution synthesis**, rather than selecting among manually encoded templates.

---

# 24. Prototype Plan

A practical first prototype can be built in Rust using `egg`.

Phase 1 should support only:

```text
Tensor
MatMul
Reduce
Summary
Shard
Partial
AllReduce
ReduceScatter
AllGather
```

and two or three summary algebras.

The compiler input can initially be a tiny expression language rather than full MLIR.

Example:

```text
(matmul A B)
```

becomes an e-graph containing:

```text
(matmul A B)

(all-reduce
    (local-matmul
        (shard-k A)
        (shard-k B)))

(reduce-scatter
    (local-matmul
        (shard-k A)
        (shard-k B)))
```

The extractor uses measured compute and communication costs.

Once this works, connect the extracted representation to StableHLO or MLIR.

A reasonable later architecture is:

```text
StableHLO / MLIR
      ↓
summary analysis
      ↓
distribution e-graph
      ↓
physical extraction
      ↓
StableHLO collectives / Shardy annotations
      ↓
XLA
```

This minimizes the amount of backend infrastructure that must be reimplemented.

---

# 25. Expected Contributions

A successful project could claim four contributions.

**1. Algebraic distribution interface**

A semantic interface

$$
(S,\otimes,e,\phi,\psi)
$$

for describing mergeable tensor computations.

**2. Distribution synthesis**

A compiler procedure that derives sharded local computation and collective communication from that interface.

**3. Equality-saturation search**

An e-graph representation that jointly explores:

$$
\text{summary representation},
\text{sharding},
\text{collective},
\text{resharding},
\text{fusion}.
$$

**4. Experimental evidence**

Evidence that the approach reduces operator-specific parallelization logic and can discover efficient distributed implementations.

---

# 26. Novelty Positioning

The proposal must be positioned carefully.

The novelty is **not**:

> Monoids allow parallel reductions.

That is established theory.

It is also not:

> E-graphs optimize tensor programs.

Tensat and EqiForge already establish this direction.

It is not:

> Compilers automatically shard tensor programs.

GSPMD, Alpa, PartIR-derived work, and Shardy already address this problem.

And it is not:

> Search algebraic transformations and distribution jointly.

Unity already makes this a central contribution.

The proposed research question is narrower:

$$
\boxed{
\begin{aligned}
&\text{Can mergeable algebraic state serve as a semantic interface}\\
&\text{from which a compiler synthesizes distributed tensor}\\
&\text{implementations, and can equality saturation jointly}\\
&\text{optimize those states, shardings, and collectives?}
\end{aligned}}
$$

The distinction from Shardy is particularly important.

Shardy factors operation-specific sharding behavior into a generic `OpShardingRule`, allowing the propagation algorithm itself to remain operation-independent.

This proposal attempts to move one level further:

$$
\text{operator algebra}
\rightarrow
\boxed{\text{derive distribution semantics}}
\rightarrow
\text{generic search}.
$$

Rather than only providing relationships between tensor dimensions, the summary interface describes what a partition **means mathematically** and how independently computed states can be recombined.

---

# 27. Risks

The largest risk is that only a limited subset of tensor operations admit useful compact mergeable states.

That does not necessarily invalidate the work. The system can operate selectively:

```text
ordinary operation
    -> existing sharding mechanism

mergeable operation
    -> algebraic distribution synthesis
```

Another risk is search explosion. Physical states multiply the number of alternatives substantially. Compatibility pruning, Pareto pruning, state dominance, bounded saturation, and cost-guided expansion will likely be necessary.

A third risk is that sophisticated existing partitioners already produce essentially optimal strategies for simple operations such as MatMul.

The evaluation should therefore emphasize **composed programs and nontrivial summary states**, not attempt to claim that a monoid specification makes `AllReduce(MatMul)` fundamentally new.

---

# 28. Strongest Potential Result

The strongest experiment would look like this:

```text
New tensor operator
        ↓
No distributed implementation exists
        ↓
Developer provides only:
    state
    lift
    combine
    finalize
        ↓
Compiler automatically discovers:
    partition
    local computation
    collective
    state placement
    consumer-compatible result
        ↓
Generated program approaches or exceeds
manually engineered distributed implementation
```

That would demonstrate a genuine increase in compiler abstraction.

The most important metric would then not merely be

$$
1.2\times \text{ speedup}
$$

but:

$$
\boxed{
\text{new distributed strategy derived from semantic structure
rather than explicitly programmed into the compiler}
}
$$

---

# 29. Suggested Paper Thesis

A concise thesis statement is:

> **Distributed tensor compilers currently reason primarily about how tensors are sharded. We propose reasoning additionally about how operator semantics can be summarized and merged. By expressing mergeable operators through algebraic summary states, a compiler can synthesize legal distributed decompositions and use equality saturation to jointly optimize summary representation, sharding, collective communication, and downstream consumption.**

An even shorter version is:

> **Instead of teaching the compiler how to distribute every operator, teach it how partial results compose.**

---

# 30. References

**Xu et al. — GSPMD: General and Scalable Parallelization for ML Computation Graphs.** GSPMD automatically propagates partitioning decisions and generates SPMD computation from limited user annotations.

**Zheng et al. — Alpa: Automating Inter- and Intra-Operator Parallelism for Distributed Deep Learning. OSDI 2022.** Alpa searches distributed execution plans spanning inter- and intra-operator parallelism.

**Unger et al. — Unity: Accelerating DNN Training Through Joint Optimization of Algebraic Transformations and Parallelization. OSDI 2022.** Unity jointly optimizes algebraic and parallel transformations through substitutions over a unified parallel computation graph.

**OpenXLA — Shardy.** Shardy provides an MLIR-based tensor partitioning system with generic operation sharding rules, sharding propagation, and an SPMD partitioning architecture.

**Yang et al. — Equality Saturation for Tensor Graph Superoptimization. MLSys 2021.** Tensat applies equality saturation to tensor computation graphs to address rewrite phase-ordering problems.

**Zhan et al. — Unleashing the Power of Equality Saturation for Tensor Program Superoptimization. 2026.** EqiForge combines high-level tensor expressions and tiled computations within a unified equality-saturation framework.

**Geser and Gorlatch — Parallelizing Functional Programs by Generalization. 1999.** This work studies automatic discovery of homomorphic representations that enable divide-and-conquer parallel execution.

**Palkar et al. — Weld: Rethinking the Interface Between Data-Intensive Applications.** Weld uses parallel loops and mergeable builders to expose data-parallel computation and optimize across library boundaries, providing relevant precedent for mergeable intermediate states as a compiler abstraction.
