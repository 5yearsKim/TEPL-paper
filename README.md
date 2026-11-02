# TEPL Paper

The active manuscript starts in `main.tex`, using the ACM `acmsmall` review
layout. Files in `sections/` follow the current section numbering (01–11).
Letter suffixes identify additional fragments belonging to the same section,
such as `05a-correctness-completeness.tex` and `08a-limitations.tex`.
Appendix files use `appendix-a`, `appendix-b`, and `appendix-c` prefixes;
numbered suffixes match their subsection order. Only appendices included in
the current paper are retained in `sections/`.

The `nonacm` class option suppresses publication metadata while drafting.
For submission, remove it and add the required venue metadata, CCS concepts,
and keywords.

## Build

Install TeX Live, BibTeX, and Make. On Ubuntu/Debian:

```bash
sudo apt install make texlive-latex-base texlive-latex-extra \
  texlive-fonts-recommended texlive-fonts-extra
```

Build from the repository root:

```bash
make
```

The result is `main.pdf`. Add bibliography entries to `references.bib` and cite
them with `\cite{key}`. The build runs BibTeX once citations are present.
Use `make -B` to force a rebuild, `make clean` to remove auxiliary files,
or `make clean-all` to also remove the generated paper PDF.

`make` also builds `supplement.pdf`, cited by the paper. It contains declaration
sketches, a worked token-counting procedure, and the complete 15-row certified scalability table.

## Code and figure layout

Write code directly in `lstlisting`; do not wrap it in a float or minipage.
A listing can continue across pages automatically, including its existing
caption and label.

For a small figure, place this command before ordinary paragraphs:

```latex
\sidefigure{figures/example.pdf}
  {Figure caption.}{fig:example}{Accessible description.}

Normal prose continues here and flows around the figure.
```

The default figure width is 45% of the text width; an optional argument such
as `\sidefigure[0.3]{...}` changes it. There is no accompanying text environment
or manual line count. Prose continues wrapping across headings, and returns
to full width below the figure. Code, lists, display equations, and floats
end the wrap automatically. Side figures never become full-width floats:
when the figure and caption cannot fit, LaTeX starts them with the following
prose on the next page, keeping an immediately preceding heading attached.
This can leave space at the bottom of the preceding page. A figure with too
little accompanying prose before full-width material can also leave space
below that prose; use `\paperfigure` for large or unsuitable artwork.

This uses `wrapstuff`, included in the `texlive-latex-extra` dependency above.

## Writing resources

- `draft/paper_outline.md`: detailed paper outline.
- `draft/figures/`: figure storyboards.
- `figures/`: TEPL figure PDFs, ready to include as needed.
- `tools/figure_style.md`: shared figure conventions.
- `reference_study.md` and `distributed-monoid.md`: research notes.
- `acmart.cls` and `ACM-Reference-Format.bst`: required ACM formatting files.

## Expanded proof integration

The active paper keeps the full mathematical development in the main text,
before symbolic axis mapping and program generation. It adopts the notation
of `draft/complete_attribute_synthesis_proof_kr.md`.

- `sections/03-problem.tex`: definitions, fragment, and the TEPL contract.
- `sections/04-axis-model.tex`: axis representation and exactness.
- `sections/05-attribute-synthesis.tex`: canonical axes, ordering, construction.
- `sections/05a-correctness-completeness.tex`: full correctness and completeness proofs.
- `sections/06-symbolic-compilation.tex`: symbolic mapping and metadata programs.
- `sections/07-candidate-validation.tex`: compile-time validation of completed attribute programs.
- `sections/07a-validation-details.tex`: validation contract, algorithm and soundness theorem.
- `draft/proof_integration_map.json`: content-preservation and notation checklist.

The appendices follow the main paper's progression and use the same notation:

- **A. Mathematical Foundations: Examples and Proofs**
  (`sections/appendix-a-foundations.tex`): axis exactness, the mandatory and
  retained axes example, canonicalization, and correctness and completeness.
- **B. Symbolic Compilation Details**
  (`sections/appendix-b-compilation.tex`): Axes IR, mapping and synthesis
  invariants, operation declaration adapters, and the core
  validation calculus and supporting proofs (`sections/appendix-b4-validation.tex`).
- **C. Current Evaluation Protocol and Evidence**
  (`sections/appendix-c-evaluation.tex`): coverage, specification-size
  accounting and implementation checks.

The active draft consolidates repeated guarantee explanations and reassociation
derivations; detailed protocols and module correspondence remain in the appendix.
Unused appendix source files have been removed from `sections/`.
`draft/paper_outline.md` records the older shortened structure and is not the
outline of the expanded draft.

## Current evaluation artifacts

`evaluation/README.md` maps the retained evidence to the active paper and
supplement. Experiments omitted from the current paper have been removed,
including superseded coverage runs, the explicit/automatic outcome study,
external TASO tests, target screening, the old transpose-folding integration,
and historical default-backend scalability and native metadata timing.

- `evaluation/unified-construction/`: Section 9.1 and Appendix C coverage and validation.
- `evaluation/xla-rewrite-count/` and `evaluation/xla-rewrite-count-models/`:
  the four workload counts in Table 5 and their semantic review.
- `evaluation/current/specification_size/`: Section 9.3 and Table 6 token accounting.
- `evaluation/certified-scalability/`: Figure 7, Section 9.4 and Supplement S3.
- `evaluation/reassociation/`: Appendix B's recorded implementation example.
- `evaluation/source-line-count/`: the introduction's 269-line XLA example.
- `evaluation/supplementary-materials/`: explanatory source snapshots cited by the appendix.

`evaluation/recorded-results.json` retains the frozen 123-case input inventory
needed by the coverage runner. Shared scalability rule inputs and the dialect
are retained with the certified experiment. The workload-count package retains
its ResNet baseline and original workflow provenance without the unused workflow
experiment.

Regenerate Figure 7 from saved measurements without rerunning compilation:

```sh
python3 tools/plot_current_scalability.py
```

Reproduction commands and measurement limits accompany each retained experiment.
The four-workload counting artifacts record native XLA application counts and
semantic classifications; they do not establish TEPL delegation or numerical
output agreement. The current prose's 28-test integration and output-agreement
claims require separate evidence beyond these count-only artifacts.
