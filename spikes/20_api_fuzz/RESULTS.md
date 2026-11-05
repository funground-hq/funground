# Spike 20: fuzzing the public API like a thousand confused beginners

**Branch note.** The task named `cloud/api-fuzz`. This cloud session is pinned to the branch
`claude/nifty-sagan-2vk7nl` and may push only there, so all work is on that branch. Every commit carries
`[skip ci]`.

Started 07:28 UTC, 2026-11-05. Base: origin/main `bc651ca`. Linux, 4 CPUs, Python 3.11.18 (uv venv),
pygame-ce 2.5.8 (SDL 2.32.10), Hypothesis 6.170.14, pypdf 6.19.0, Pillow 12.3.0. funground-ml not installed.

## What was run

| Run | Command (from `spikes/20_api_fuzz`, with `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy FUNGROUND_HEADLESS=1`) | Cases | Time |
|---|---|---|---|
| Single calls | `../../.venv/bin/python harness.py calls OUT` | 11 526 | 348 s |
| Wild programs | `../../.venv/bin/python harness.py programs OUT 3000 0` | 3 000 | about 6 min |
| Sane programs | `FUZZ_SANE=1 ../../.venv/bin/python harness.py programs OUT 2000 0` | see below | |

**The harness** (`harness.py`). The parent imports funground once and forks one child per case, 4 at a time.
The child sets `RLIMIT_AS` to 2 GB, runs the case in a fresh temporary folder, and reports through a pipe.
The parent kills a child at 10 s. Each finding is appended to `findings.jsonl` as soon as it is known.
After every case that runs without an error, the child saves PNG, PDF and SVG and reads each back:
Pillow (`Image.load`), pypdf (`PdfReader(strict=True)` and text extraction), and ElementTree, and looks
for `nan`/`inf` tokens in the PDF and SVG. An animated program also saves a GIF with `f.save_gif`, read
back frame by frame with Pillow.

**Single calls.** For every public callable (`f.*`, `sound.*`, `sangeet.*`, `camera.*`), the harness takes
the docstring's `Example:` as the valid call, then rewrites the call to that name with `ast`: each
positional and keyword argument in turn is replaced by each of 36 beginner values (0, -1, 1, 1e308,
-1e308, 1e-308, 10**12, 2**63, 0.5, nan, inf, -inf, None, True, False, `'10'`, `'abc'`, `''`,
`'tomatoe'`, emoji, Hebrew, Devanagari, a lone surrogate, 100 000 characters, `[1, 2]`, `[[1, 2], [3]]`,
`(1, 2)`, `()`, `[]`, `{}`, `1j`, `object()`, `(255, 0)`, a 5-tuple, `'#12'`, `-0.0`), plus one argument
missing and one argument too many.

**Programs** (`programs.py`). Hypothesis (derandomised, so the same 3 000 come back) builds programs of
up to 20 steps from push/pop, begin/end_shape, contours, vertices of every kind, shapes, transforms, text
and text settings, font changes, fills and strokes, layers (as `with` blocks, nested, and left open by
`__enter__()`), `new_page`, saving partway, `size` again, `resize_canvas`, clip, shadow, blend modes,
erase, filters, pixels and dash. Half are scripts and half are animated sketches (`draw()` with
`f.run(max_frames=8)` and `f.save_gif` in `setup()`). The wild run uses beginner values; `FUZZ_SANE=1`
uses only valid numbers, colours and text (emoji, Hebrew and Devanagari included) so that programs live
long enough to reach the file checks.

**How an error is judged.** funground's own learner errors are `ValueError`, `TypeError`, `RuntimeError`
and `FungroundError` raised inside funground with a sentence that names the call (`f.size(): ...`,
`No drawing window yet. Call f.size(...) first.`). A finding of class 4 is any other exception type
(`OverflowError`, `AttributeError`, `cairo.Error`, `UnicodeEncodeError`, ...), or one of those four
types carrying Python's own wording (`unsupported operand type(s)`, `math domain error`,
`cannot convert float NaN to integer`, `could not convert string to float`, ...). Python's own
arity errors (`missing 1 required positional argument`) are raised at the learner's line and name the
function, so they are not counted. `NameError` from a docstring example that uses an undefined variable
is a harness artefact and is not counted.

### Skipped names

`f.run` (used only inside examples, with `max_frames`), `f.show` (waits for a window; replaced by `pass`
inside examples), `f.full_screen` (needs a display), `f.exit` and `f.stop` (end the sketch on purpose),
`camera.open` (needs a camera), `sound.microphone` (needs a microphone). 31 more names have no
`Example:` in their docstring and were not fuzzed as single calls (list in `skipped.json`): among them
`begin_contour`, `end_contour`, `pop`, `vertex`, `no_clip`, `hide_layer`, `show_layer`, `text_ascent`,
`update_pixels`, `sangeet.ragas`. The program generator covers `pop`, `vertex`, the contours,
`no_clip` and `update_pixels`.

## Results

STATUS: filled in below.
