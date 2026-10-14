# ACM `acmsmall` conference template

This directory contains the files needed to compile the upstream
`acmsmall-conf.tex` sample without the rest of the `acmart` source tree.

- `acmsmall-conf.tex`: upstream conference sample
- `acmart.cls`: ACM document class
- `ACM-Reference-Format.bst`: BibTeX bibliography style
- `sample-base.bib`: bibliography used by the sample
- `sample-franklin.png` and `sampleteaser.pdf`: figures used by the sample

For conference review, copy or rename `acmsmall-conf.tex` for the paper and use:

```latex
\documentclass[acmsmall,review,screen]{acmart}
```

The remaining packages loaded by `acmart.cls` are standard dependencies that
should be installed through a current TeX distribution.
