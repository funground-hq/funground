# Spike 22: memory soak

Branch: cloud/memory-soak. Started 2026-11-05 07:41 UTC, 15-minute budget.

## Plan
1. Soak gallery sketches with draw(), 4 processes at a time, warm-up then RSS samples, JSONL out.
2. Three stress sketches: load_image/load_font in draw, new layers/Pictures per frame, text with new size per frame.
3. Read _snapshot_cache (picture.py) and typography.py caches: bounded or not.
4. Peak ru_maxrss for A0@300dpi PNG/PDF, 60-page PDF, 300-frame 1080p GIF/MP4 (12 GB, 3 min limit).
5. Table + "For the main session".
