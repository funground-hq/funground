#!/bin/sh
# Re-create the throwaway venv, download the candidate fonts, run every experiment (from spikes/10_font_fallback).
# Never uses plain `python`; never installs or opens a font (fontTools reads the files only).
PY=.venv/Scripts/python
[ -d .venv ] || { echo "create the venv first with your full interpreter path: <python> -m venv .venv"; exit 1; }
$PY -m pip install -q fonttools uharfbuzz regex brotli pycairo pillow lxml
sh fonts/download.sh
export PYTHONUTF8=1
for e in exp1_inventory exp2_itemise exp3_coverage_sizes exp4_emoji exp6_system_fonts exp7_determinism_load exp8_colour_emoji_sizes; do
  echo; echo "######## $e"; $PY $e.py > out/$e.txt 2>&1; tail -3 out/$e.txt
done
# exp5 runs funground read-only from the PROJECT venv (it only writes into out/):
PYTHONDONTWRITEBYTECODE=1 C:/Projects/playground/.venv/Scripts/python exp5_pdf_embed.py
