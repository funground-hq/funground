#!/bin/sh
# Soak every gallery sketch with a draw() (not models/), 4 at a time. Usage: soak_all.sh SECONDS OUT.jsonl
cd "$(dirname "$0")/../.."
grep -rl "def draw" examples/gallery --include=*.py | grep -v /models/ | sort | \
  xargs -P 4 -I{} timeout 90 env FUNGROUND_HEADLESS=1 SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy \
  .venv/bin/python spikes/22_memory_soak/soak_one.py {} "$2" "$1"
