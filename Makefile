PAPER := main
LATEX := pdflatex
BIBTEX := bibtex
LATEXINDENT := latexindent
LATEX_FLAGS := -interaction=nonstopmode -halt-on-error -file-line-error

.PHONY: all format format-check clean clean-all

all: $(PAPER).pdf

$(PAPER).pdf: $(PAPER).tex acmart.cls ACM-Reference-Format.bst sample-base.bib \
		sample-franklin.png sampleteaser.pdf
	$(LATEX) $(LATEX_FLAGS) $(PAPER).tex
	$(BIBTEX) $(PAPER)
	$(LATEX) $(LATEX_FLAGS) $(PAPER).tex
	$(LATEX) $(LATEX_FLAGS) $(PAPER).tex

format:
	$(LATEXINDENT) -s -w -m -l=.latexindent.yaml $(PAPER).tex

format-check:
	$(LATEXINDENT) -s -k -m -l=.latexindent.yaml $(PAPER).tex

clean:
	$(RM) $(PAPER).aux $(PAPER).bak* $(PAPER).bbl $(PAPER).blg $(PAPER).cut \
		$(PAPER).fdb_latexmk $(PAPER).fls $(PAPER).log $(PAPER).out \
		$(PAPER).synctex.gz $(PAPER).toc comment.cut indent.log \
		base_templates/acmsmall-conf.aux \
		base_templates/acmsmall-conf.bbl \
		base_templates/acmsmall-conf.blg \
		base_templates/acmsmall-conf.fdb_latexmk \
		base_templates/acmsmall-conf.fls \
		base_templates/acmsmall-conf.log \
		base_templates/acmsmall-conf.out \
		base_templates/acmsmall-conf.synctex.gz \
		base_templates/acmsmall-conf.toc base_templates/comment.cut

clean-all: clean
	$(RM) $(PAPER).pdf base_templates/acmsmall-conf.pdf
