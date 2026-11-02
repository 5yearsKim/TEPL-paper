# Supplementary walkthroughs and exhaustive tables

This directory preserves the appendix material moved out of the PDF during
consolidation. These are explanatory source snapshots, not new experiments.
The main PDF retains the central supporting proofs, core inference rules,
guard arguments, and current evaluation protocol. Historical XLA integration
inventories remain in their evaluation artifacts.

- `appendix-language.tex`: full transpose/slice attribute-declaration sketches.
- `appendix-extended.tex`: full declaration examples, addition/dot mapping,
  reassociation partition and synthesis walkthroughs, and tutorial figure
  references. Figures remain in the repository's `figures/` directory.
- `appendix-canonical-axes.tex`: expanded row-sum worked example and its
  original two tables; the PDF retains the rules and compact example.
- `appendix-token-counting.tex`: explicit/inferred transpose listings,
  48/22 token example, and slice-definedness diagnostic example. Counting
  methodology remains in the PDF's current-evaluation appendix.
- `appendix-reassociation.tex`: full source-inclusion and recorded execution
  account. Exact runnable inputs and logs remain in `../reassociation/`;
  the PDF retains the complete attribute program, full mathematical proof,
  and a brief execution summary.

The TeX snapshots are fragments using the paper's macros and historical
cross-references; they are readable sources, not standalone TeX projects.
Build the consolidated paper from the repository root with `make`.
`manifest.json` records SHA-256 hashes of these snapshots retained here.
`protected-proofs.json` records the proof-source hashes before consolidation.

## November 2026 reduction snapshots

`appendix-reduction-2026-11/` preserves the exact source state before the
latest reduction, with its own SHA-256 `manifest.json`. These fragments use
the old section numbering and are not independently buildable. In particular:

- `appendix-extended.tex` contains the removed producer-first mapping
  pseudocode and expanded reassociation partition walkthrough.
- `appendix-reassociation.tex` contains the compiler temporary correspondence.
- `appendix-compilation.tex` contains the implementation-check table.
- `appendix-validation.tex` and `appendix-condition-suggestions.tex` preserve
  the transpose validation example, repeated obligation summaries, and the
  worked guard-suggestion example.
- `appendix-current-evaluation.tex` preserves the historical acceptance
  progression and detailed development-test inventory.
- `appendix-accepted-core.tex` and `appendix-axis-extensions.tex` preserve
  detailed implementation correspondence, module paths, and work limits.
- Other snapshots preserve the surrounding program, proof, and reference
  context. The mathematical foundations and schema soundness proofs remain
  in the active paper; the validation proof prose has been tightened.

These are editorial snapshots, not new experimental results. The earlier
root-level manifests continue to describe the earlier consolidation only.
