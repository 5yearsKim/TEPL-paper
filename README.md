# TEPL Paper

The active expanded draft starts in `main.tex`, using the ACM `acmsmall`
review layout. The original 38-page draft is a standalone project in
`main_backup/`, with its own `main.tex` and all supporting files.

## Restore the original draft

Copy all contents of `main_backup/` into the project folder, replacing existing
files. From the project root, the equivalent command is:

```bash
cp -a main_backup/. .
```

This restores `main.tex` and its dependencies together. You can also open
`main_backup/` as a separate project and run `make` there. The expanded draft remains active at the root until you restore.

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

- `sections/04-problem.tex`: definitions, fragment, and the TEPL contract.
- `sections/04a-axis-model.tex`: axis representation and exactness.
- `sections/04b-mathematical-synthesis.tex`: canonical axes, ordering, construction.
- `sections/04c-formal-correctness.tex`: full correctness and completeness proofs.
- `sections/05-method.tex`: symbolic mapping and metadata programs.
- `sections/05e-tepl-integration.tex`: adapters, symbolic correspondence, conditions, and broader operations.
- `draft/proof_integration_map.json`: content-preservation and notation checklist.

The appendices follow the main paper's progression and use the same notation:

- **A. Mathematical Foundations: Examples and Proofs**
  (`sections/appendix-foundations.tex`): axis exactness, the mandatory and
  retained axes example, canonicalization, and correctness and completeness.
- **B. Symbolic Compilation Details**
  (`sections/appendix-compilation.tex`): Axes IR, mapping and synthesis
  derivations and algorithms, and operation declaration adapters.
- **C. Scalability Evaluation** (`sections/appendix-scalability.tex`):
  experimental setup, results, and measurement limits.

The 20-page reduction is deferred; this version is the content-complete draft.
`draft/paper_outline.md` records the older shortened structure and is not the
outline of the expanded draft.
