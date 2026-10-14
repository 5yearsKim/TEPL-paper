# Residual E-Graph Paper

This repository uses the ACM `acmsmall` proceedings format. The main LaTeX
source is `main.tex`, and the generated paper is `main.pdf`.

## Initial LaTeX setup (Ubuntu/Debian)

Refresh the package index:

```bash
sudo apt update
```

Install the base TeX Live distribution and common LaTeX packages:

```bash
sudo apt install texlive-latex-base texlive-latex-extra
```

Install the recommended and extra font collections. These provide fonts used
by many papers and prevent missing-font or missing-metric errors during PDF
generation:

```bash
sudo apt install texlive-fonts-recommended texlive-fonts-extra
```

Install `latexindent` and its supporting TeX utilities:

```bash
sudo apt install texlive-extra-utils
```

The complete setup can also be installed in one command:

```bash
sudo apt update
sudo apt install \
  texlive-latex-base \
  texlive-latex-extra \
  texlive-fonts-recommended \
  texlive-fonts-extra \
  texlive-extra-utils
```

Confirm that the required commands are available:

```bash
pdflatex --version
bibtex --version
latexindent --version
make --version
```

## Compile the paper

Run all commands from the repository root.

```bash
make
```

`make` runs `pdflatex`, `bibtex`, and the additional `pdflatex` passes needed
to resolve the bibliography and cross-references. The result is `main.pdf`.

Make skips compilation when `main.pdf` is newer than all of its declared
inputs. To force a rebuild:

```bash
make -B all
```

Alternatively, remove all generated files and rebuild:

```bash
make clean-all
make
```

## Clean generated files

Remove auxiliary files while keeping the generated PDF:

```bash
make clean
```

Remove auxiliary files and generated PDFs:

```bash
make clean-all
```

LaTeX build files are excluded through `.gitignore`, including artifacts
created inside `base_templates/`.

## Format `main.tex` with latexindent

The formatting rules are stored in `.latexindent.yaml`. They use two spaces
per indentation level, wrap prose at 80 columns, preserve blank lines, and
avoid adding another indentation level inside `table`, `tabular`, and
`tabularx` environments.

Format `main.tex` in place:

```bash
make format
```

`latexindent` creates a backup such as `main.bak0`. These backups are ignored
by Git and removed by `make clean`.

Check whether formatting is needed without modifying the source:

```bash
make format-check
```

An exit status of `0` means the file is already formatted. An exit status of
`1` means `latexindent` would change it.

The `-m` option used by the Makefile enables the configured line wrapping and
blank-line handling. To invoke the formatter directly, use:

```bash
latexindent -s -w -m -l=.latexindent.yaml main.tex
```

## Reference

- [How to install pdflatex on Ubuntu](https://gist.github.com/yspkm/f33d59181b7f6f5c8701360995c07418)
