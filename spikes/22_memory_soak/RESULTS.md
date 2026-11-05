# Spike 22: memory soak

Branch: cloud/memory-soak (as asked). 2026-11-05, 07:41 to 07:56 UTC, a 15-minute session.
Linux container, 4 CPUs, Python 3.11.18, pygame-ce 2.5.8 (SDL 2.32.10), pycairo 1.29.1, funground at origin/main bc651ca.
Seed: `random.seed(0)` in every process. Nothing in `funground/` was changed; no tests added.

## Plan
1. Soak gallery sketches with draw(), 4 processes at a time, warm-up then RSS samples, JSONL out.
2. Three stress sketches: load_image/load_font in draw, new layers/Pictures per frame, text with new size per frame.
3. Read _snapshot_cache (picture.py) and typography.py caches: bounded or not.
4. Peak ru_maxrss for A0@300dpi PNG/PDF, 60-page PDF, 300-frame 1080p GIF/MP4 (12 GB, 3 min limit).
5. Table + "For the main session".

## How
- `soak_one.py SKETCH OUT.jsonl SECONDS WARMUP EVERY`: runs the sketch unchanged, with the approach of
  `run_sketch` in tests/conftest.py (swaps `f.run`, calls `run_namespace` at fps=1000), wraps `draw` to count
  frames, reads RSS from `/proc/self/statm` at the end of warm-up and every EVERY frames after, stops after SECONDS.
- `soak_all.sh 10 gallery_soak.jsonl`: every `examples/gallery/**.py` with `def draw`, not `models/`, 4 at a
  time (`xargs -P 4`), warm-up 100 frames, sample every 200, about 10 s after warm-up, `timeout 90` each.
- `stress_soak.jsonl`: the three stress sketches, warm-up 100, sample every 200, 30 s each.
- `trace_one.py SKETCH 100 600`: tracemalloc snapshot after warm-up and after 600 more frames, top 5 lines
  by growth. Output in `trace_results.txt`.
- `peak.py CASE OUTDIR peak.jsonl` under `timeout 180 prlimit --as=12884901888`, one process per case;
  `ru_maxrss` at exit. Output files went to the scratchpad and are not committed.
- `table.py` makes the tables below from the JSONL. "2nd half" is the slope over the second half of the samples:
  a rise is only a finding if that stays positive.

**Caveat: the runs are short.** Gallery sketches ran about 10 s after warm-up (600 to 4,100 frames); the
stress sketches 30 s (500 to 2,500 frames). These are not hour-long soaks. Several 1 to 3 MB/1,000 rises
below are within allocator noise at this length and are unverified as leaks.

## 1. Gallery soak (96 of 102 measured)

Six sketches wrote no record: they hit `timeout 90` before 10 s of sampling or never reached the
warm-up (unmeasured, reason not checked): animation/04_pause, images/03_pixels, images/04_filters,
text/12_justified_columns, transforms/02_saved_state, transforms/03_shear_and_matrices.
No sketch raised an error. Sorted by second-half slope; full rows in `gallery_soak.jsonl`.

| sketch | frames | secs after warm-up | MB at warm-up | MB at end | MB per 1,000 frames | 2nd half MB/1,000 | error |
|---|---:|---:|---:|---:|---:|---:|---|
| examples/gallery/animation/05_record_a_gif.py | 2100 | 35.5 | 72.3 | 989.8 | 458.74 | 744.63 |  |
| examples/gallery/basics/02_setup_and_draw.py | 602 | 0.6 | 45.7 | 48.5 | 6.9 | 6.35 |  |
| examples/gallery/paths/06_outlines.py | 500 | 13.0 | 48.9 | 50.3 | 3.65 | 2.19 |  |
| examples/gallery/projects/08_flow_field_print.py | 900 | 11.3 | 58.0 | 60.0 | 2.46 | 1.85 |  |
| examples/gallery/sound/03_sargam_over_a_drone.py | 700 | 13.2 | 177.3 | 178.8 | 2.49 | 1.72 |  |
| examples/gallery/compositing/01_blend_opacity_shadow.py | 700 | 13.6 | 45.8 | 47.7 | 3.05 | 1.5 |  |
| examples/gallery/music/08_draw_a_wave.py | 700 | 13.1 | 57.3 | 58.7 | 2.21 | 1.43 |  |
| examples/gallery/animation/03_clock.py | 4100 | 10.3 | 45.7 | 55.2 | 2.37 | 1.41 |  |
| examples/gallery/images/05_svg.py | 900 | 11.3 | 51.2 | 53.0 | 2.33 | 1.2 |  |
| examples/gallery/music/10_ear_training.py | 700 | 13.5 | 76.0 | 76.4 | 0.72 | 1.15 |  |
| examples/gallery/text/02_align.py | 1100 | 10.5 | 46.9 | 48.2 | 1.28 | 0.85 |  |
| examples/gallery/text/01_text.py | 3300 | 10.8 | 45.8 | 51.3 | 1.72 | 0.81 |  |

(The other 84 rows are at or under 0.7 MB/1,000 in the second half; see `gallery_soak.jsonl` or run `table.py`.)

- **animation/05_record_a_gif.py rises to 990 MB in 2,100 frames.** It calls `save_gif("spinner.gif", 2)`.
  The harness runs at fps=1000, so 2 seconds may be 2,000 frames held in memory before writing, not the
  60 the sketch means at fps=30. Likely a harness artefact, but it shows a recording holds every frame
  in memory with no cap other than seconds × fps (unverified at fps=30).
- **typography is the common small riser.** tracemalloc for animation/03_clock and
  compositing/01_blend_opacity_shadow over frames 100..700 names `funground/typography.py:279`
  (`_placed`, the tuple of placed glyph segments: +1.3 MB, +8,000 objects in 600 frames) and, for the clock,
  `typography.py:262-263` (new entries in the shape cache, `_shaped`, because the clock text changes each
  second). The shape cache is bounded (below). What keeps `_placed` results alive is not found in the time:
  **needs a look**. music/08_draw_a_wave's trace did not finish in time.

## 2. Stress sketches (30 s each)

| sketch | frames | secs after warm-up | MB at warm-up | MB at end | MB per 1,000 frames | 2nd half MB/1,000 | error |
|---|---:|---:|---:|---:|---:|---:|---|
| spikes/22_memory_soak/stress_new_pictures.py | 500 | 34.0 | 135.0 | 520.8 | 964.51 | 964.49 |  |
| spikes/22_memory_soak/stress_text_sizes.py | 900 | 32.1 | 53.0 | 96.3 | 54.11 | 54.7 |  |
| spikes/22_memory_soak/stress_load_in_draw.py | 2500 | 31.9 | 84.0 | 92.4 | 3.53 | 11.01 |  |

- `stress_new_pictures.py` (a new `create_graphics(200, 150)` and a new `f.layer("trail N")` each frame):
  **+964 MB per 1,000 frames, steady to the end (520 MB at 500 frames).** tracemalloc names
  `funground/picture.py:343`, the `bytes(pixels.data)` copy in `Picture._snapshot`, 466 KiB each =
  one 400 x 300 RGBA canvas per frame. Each new layer name makes a layer that lives for the whole run (by
  design), and each keeps a full-canvas snapshot. A learner who builds a layer name from frame_count runs
  out of memory in minutes. Whether create_graphics pictures are freed was not separated in the time.
- `stress_text_sizes.py` (400 characters, a new size and new text each frame): **+54 MB per 1,000 frames,
  steady over 900 frames.** tracemalloc names `typography.py:263` (shape-cache entries, ~45 KB each). The
  key is (text, features, location), not size, so the rise here is the changing text. With a bound of
  2,048 entries per font it should level off near 90 MB at about frame 2,050: **not reached, unverified.**
- `stress_load_in_draw.py` (`load_image` and `load_font` of the same files every frame): flat within
  noise (84 to 92 MB over 2,500 frames, with RSS falling as well as rising). No finding.

### Cache bounds (read from the code at bc651ca)
| cache | where | bound |
|---|---|---|
| `Picture._snapshot_cache` | picture.py:202, 307, 336-347, 633 | Cleared on every flush that bumps `_version`, so at most one snapshot per picture. Bounded per picture, but one full canvas copy per live picture/layer. |
| `FontResource._shaped` | typography.py:138, 253-270 | LRU, `SHAPE_CACHE_SIZE = 2048` entries per font. Entry size grows with text length; no byte bound. |
| `_ITEMISE_CACHE` | typography.py:522-558 | 2,048 entries, cleared when full. Bounded. |
| `FontResource._outlines` | typography.py:208-218 | No bound; keyed by (location, glyph id), so bounded by glyphs × variation locations used. Unbounded for an animated variable-font axis. |
| `FontResource._located` | typography.py:195-205 | No bound; one HarfBuzz font per variation location. Unbounded for an animated axis (unmeasured). |
| `_registry`, `_path_to_key` | typography.py:670-700, 984-999 | Keyed by resolved path, so loading the same file again reuses it (stress result agrees). Grows only with distinct files. |
| `_bundled_cache` | typography.py:420, 492 | One per bundled font file. Bounded. |

## 3. Peak memory of big jobs (`peak.jsonl`)

| case | peak MB (ru_maxrss) | seconds | result |
|---|---:|---:|---|
| A0 (2384 x 3370 pt) at 300 dpi, PNG | 58.5 | 0.2 | **Refused**: 9933 x 14042 = 139 million pixels, over the 120 million limit (by design; the message says to save a PDF) |
| A0, PDF | 68.2 | 0.4 | 124 KB file |
| 60-page A4 PDF, a photo on each page | 216.3 | 2.2 | 3.8 MB file |
| GIF, 300 frames, 1920 x 1080 | **4,886** | **126** | 16.6 MB file. Nearly 5 GB and over 2 minutes |
| MP4, 300 frames, 1920 x 1080 | 1,869 | 50.8 | 5.4 MB file |

Also: `f.size("A0")` is refused ("unknown page size 'A0'"); A0 to A2 are not named pages. A first run
recorded that error; the A0 rows above use points.

## For the main session

**Found**
1. A new layer name each frame grows about 1 GB per 1,000 frames at 400 x 300 (picture.py:343 snapshot copy,
   and the layer itself). Layers are kept by design, but there is no warning or cap.
2. A 300-frame 1080p GIF peaks at 4.9 GB and takes 126 s; an MP4 1.9 GB. Recording seems to hold every
   frame in memory. A learner on an 8 GB laptop could fail here.
3. `typography.py:279` (`_placed`) objects grow about 2 MB per 1,000 frames in text sketches; the holder is unknown.
4. Shape cache: bounded by count (2,048), not bytes; long changing text can hold about 90 MB per font (estimate).
5. `_outlines` and `_located` have no bound for animated variable-font axes (read, not measured).
6. `"A0"` is not a page name; A0 at 300 dpi PNG is refused by the 120 million pixel limit.

**Fixed**: nothing (as asked).

**Needs the maintainer**: whether to cap or warn on layer count, whether recording should stream frames to
the encoder, a byte bound for the shape cache, a bound for variation caches, and longer soaks (an hour) for
the 1 to 3 MB/1,000 rises, which these 10 s runs cannot separate from noise.

**Commits to review**: on cloud/memory-soak, every commit starting "Spike 22". Files: this folder only.
