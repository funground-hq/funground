#!/bin/sh
# Spike 19: the whole suite in random order (pytest-randomly) across 4 xdist workers, one seed after another.
# As CI: no FUNGROUND_HEADLESS. Each run sits under an outer hard timeout. Usage: run_seeds.sh OUTDIR SEED...
OUT=$1; shift; mkdir -p "$OUT"
export SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy PYTHONFAULTHANDLER=1; unset FUNGROUND_HEADLESS
for s in "$@"; do
  timeout -s KILL 900 .venv/bin/python -m pytest -o addopts="" -q -p no:cacheprovider -n 4 --timeout=300 \
    --randomly-seed=$s --junitxml="$OUT/seed$s.xml" tests > "$OUT/seed$s.log" 2>&1
  echo "seed $s exit $?" >> "$OUT/codes.txt"
done
