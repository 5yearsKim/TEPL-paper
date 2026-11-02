PAPER := main
LATEX := pdflatex
BIBTEX := bibtex
LATEX_FLAGS := -interaction=nonstopmode -halt-on-error -file-line-error

.PHONY: all clean clean-all

all: $(PAPER).pdf supplement.pdf

$(PAPER).pdf: $(PAPER).tex $(wildcard sections/*.tex) figures/*.pdf acmart.cls ACM-Reference-Format.bst references.bib
	$(LATEX) $(LATEX_FLAGS) $(PAPER).tex
	@if grep -q '\\citation{' $(PAPER).aux; then $(BIBTEX) $(PAPER); fi
	$(LATEX) $(LATEX_FLAGS) $(PAPER).tex
	$(LATEX) $(LATEX_FLAGS) $(PAPER).tex

supplement.pdf: $(PAPER).pdf supplement.tex $(wildcard supplement/*.tex)
	$(LATEX) $(LATEX_FLAGS) supplement.tex
	$(LATEX) $(LATEX_FLAGS) supplement.tex

clean:
	$(RM) $(PAPER).aux $(PAPER).bbl $(PAPER).blg $(PAPER).cut \
		$(PAPER).fdb_latexmk $(PAPER).fls $(PAPER).log $(PAPER).out \
		$(PAPER).synctex.gz $(PAPER).toc comment.cut
	$(RM) supplement.aux supplement.log supplement.out supplement.toc

clean-all: clean
	$(RM) $(PAPER).pdf supplement.pdf
