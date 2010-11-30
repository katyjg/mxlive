#!/bin/sh
# build a pdf file with PostScript code
# Herbert Voss 2003-03-10
# usage: ps4pdf.sh file (without suffix tex)
#export TEXINPUTS=':/var/website/lims-website/imm/tex//'
latex $1.tex
dvips -Ppdf -o $1-pics.ps $1.dvi
ps2pdf $1-pics.ps $1-pics.pdf
pdflatex $1.tex
bibtex $1
pdflatex $1.tex

