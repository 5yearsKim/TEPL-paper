

| Work | Key generalization |
|---|---|
| **EqiForge (Sep 2026)** | Equality saturation over a **unified tensor-expression + tiled-computation IR**. Equality rules compose into sophisticated implementations such as FlashAttention-style kernels; uses early compaction and subgraph composition to control explosion. ([arXiv][1]) |
| **Axon (2026)** | Goes further than fixed rewrite rules: derives transformations by **propagating operators through graphs**, using semantic specifications and SMT over unbounded tensors to verify legality. ([arXiv][2]) |
| **Prism (2026)** | Represents **families of tensor programs symbolically** instead of enumerating every concrete graph; uses symbolic pruning and later parameter instantiation/autotuning. ([arXiv][3]) |
| **Mirage, OSDI 2025** | Generalizes optimization across levels: algebraic rewrites + scheduling + custom kernels using hierarchical μGraphs, with abstraction-based pruning. ([USENIX][4]) |
| **TensorRight, POPL 2025** | Makes rewrites **rank- and size-polymorphic**, with symbolic axes and explicit preconditions. Very relevant if you want StableHLO-like generic rules. ([DOI][5]) |
| **Constable / “Mind the Abstraction Gap,” OOPSLA 2025** | Shows why local rewrite profitability is inadequate: layout, fusion, scheduling, etc. can change downstream. Uses equality saturation plus a more global performance model inside XLA. ([Illinois Experts][6]) |
| **EinNet, OSDI 2023** | Replaces fixed operator-pattern substitution with **derivation over general tensor algebra**, even generating new operators required by a derivation. ([USENIX][7]) |
| **Unity, OSDI 2022** | Treats algebraic transformations **and parallelization** as substitutions in one parallel computation graph. This is the closest older work to your rewrite+sharding direction. ([USENIX][8]) |

[1]: https://arxiv.org/abs/2609.12330?utm_source=chatgpt.com "Unleashing the Power of Equality Saturation for Tensor Program Superoptimization"

[2]: https://arxiv.org/abs/2606.26344?utm_source=chatgpt.com "Axon: A Synthesizing Superoptimizer for Tensor Programs"

[3]: https://arxiv.org/abs/2604.15272?utm_source=chatgpt.com "Prism: Symbolic Superoptimization of Tensor Programs"

[4]: https://www.usenix.org/conference/osdi25/presentation/wu-mengdi?utm_source=chatgpt.com "Mirage: A Multi-Level Superoptimizer for Tensor Programs | USENIX"

[5]: https://doi.org/10.1145/3704865?utm_source=chatgpt.com "TensorRight: Automated Verification of Tensor Graph Rewrites | Proceedings of the ACM on Programming Languages"

[6]: https://experts.illinois.edu/en/publications/mind-the-abstraction-gap-bringing-equality-saturation-to-real-wor/?utm_source=chatgpt.com "Mind the Abstraction Gap: Bringing Equality Saturation to Real-World ML Compilers - Illinois Experts"

[7]: https://www.usenix.org/conference/osdi23/presentation/zheng?utm_source=chatgpt.com "EINNET: Optimizing Tensor Programs with Derivation-Based Transformations | USENIX"

[8]: https://www.usenix.org/conference/osdi22/presentation/unger?utm_source=chatgpt.com "Unity: Accelerating DNN Training Through Joint Optimization of Algebraic Transformations and Parallelization | USENIX"


TASO → TENSAT → Unity → EinNet → Mirage/Prism/Axon/EqiForge gives a useful conceptual evolution:

---
TASO: automatically detecting graph substitution
- operatot property

->

TENSAT: 
- TASO + E-saturation

EinNet:
- don’t restrict graph optimization to a fixed vocabulary of operators (Conv, Matmul)
