# TEPL Paper

Start writing in `main.tex`. It contains a minimal ACM `acmsmall` review
skeleton with section placeholders matching the paper outline. Replace the
author and affiliation placeholders, write the abstract, and fill in the sections.

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

## Writing resources

- `draft/paper_outline.md`: detailed paper outline.
- `draft/figures/`: figure storyboards.
- `figures/`: TEPL figure PDFs, ready to include as needed.
- `tools/figure_style.md`: shared figure conventions.
- `reference_study.md` and `distributed-monoid.md`: research notes.
- `acmart.cls` and `ACM-Reference-Format.bst`: required ACM formatting files.
