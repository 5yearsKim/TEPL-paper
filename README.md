# TEPL Paper

The manuscript starts in `main.tex` and uses the ACM `acmsmall` review
layout. The main text and appendices build into a single PDF.

## Build

Install Make, pdfLaTeX, and BibTeX, with the LaTeX packages and fonts used
by `main.tex` and `acmart.cls`, including `wrapstuff`.

From the repository root, run:

```sh
make
```

The output is `main.pdf`.

- `make -B`: force a full rebuild.
- `make clean`: remove LaTeX auxiliary files.
- `make clean-all`: also remove `main.pdf`.

## Files

- [main.tex](main.tex): document setup and section order.
- [sections/](sections/): main text and appendix sources.
- [references.bib](references.bib): bibliography entries.
- [paper-style.tex](paper-style.tex): shared paragraph-heading style.
- [figures/](figures/): figure PDFs.
- [figures/conti/](figures/conti/): figure storyboards.
- [tools/figure_style.md](tools/figure_style.md): figure conventions.
- `acmart.cls` and `ACM-Reference-Format.bst`: ACM class and bibliography style.

## Layout conventions

Write code directly in `lstlisting` so listings can continue across pages.
Use `\paperparagraph{Heading.}` for run-in paragraph headings.

For a small figure beside ordinary text:

```latex
\sidefigure{figures/example.pdf}
  {Figure caption.}{fig:example}{Accessible description.}

Normal prose follows here.
```

The default width is 45% of the text width. Use an optional argument,
such as `\sidefigure[0.3]{...}`, to change it. Code, lists, display equations,
and floats end text wrapping. Use `\paperfigure` for a full-width figure:

```latex
\paperfigure{1}{figures/example.pdf}
  {Figure caption.}{fig:example}{Accessible description.}
```

## Evaluation artifacts

[evaluation/README.md](evaluation/README.md) lists the retained evidence,
reproduction notes, and limits. It covers inference coverage, native XLA
workload counts, the reassociation example, and the XLA source-line count.
