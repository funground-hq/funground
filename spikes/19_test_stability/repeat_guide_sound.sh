#!/bin/sh
# Spike 19: run the 16_sound guide examples N times as CI does (no FUNGROUND_HEADLESS), each pytest under an
# outer hard timeout, with pytest-timeout's thread method (as on Windows) and faulthandler.
# Usage: repeat_guide_sound.sh PYTHON N OUTDIR [EXTRA_LOAD]
PY=$1; N=$2; OUT=$3; mkdir -p "$OUT"
export SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy PYTHONFAULTHANDLER=1; unset FUNGROUND_HEADLESS
seq 1 "$N" | xargs -P 3 -I{} sh -c "timeout -s KILL 90 $PY -m pytest -o addopts='' -q -p no:cacheprovider -p no:randomly \
  --timeout=15 --timeout-method=thread -o faulthandler_timeout=30 tests/test_guide.py -k 16_sound > $OUT/run{}.log 2>&1; echo \"{} \$?\" >> $OUT/codes.txt"
