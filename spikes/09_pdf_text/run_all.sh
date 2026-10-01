#!/bin/sh
# Re-create the throwaway venv and run every experiment (from spikes/09_pdf_text).
[ -d .venv ] || { python -m venv .venv && .venv/Scripts/python -m pip install -q pypdf pikepdf fpdf2 reportlab pymupdf pdfminer.six fonttools uharfbuzz pycairo pypdfium2 numpy skia-python; }
export PYTHONUTF8=1
for e in exp0_baseline exp1_cairo_faces exp3_check_ligatures exp2_invisible_layer exp4_positions exp5_size exp6_library_overlays exp7_cairo_tags exp8_skia_pdf; do
  echo; echo "######## $e"; .venv/Scripts/python $e.py 2>&1 | grep -v "NOT subset"
done
