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

Single calls: 3 768 ran cleanly, 6 341 raised a good learner error, 1 417 were findings
(`{"ok": 3768, "learner-error": 6341, "finding": 1417}`). Wild programs: 3 000 run, 7 findings of
class 2 (all `f.arc`) and 1 of class 4. Sane programs: no finding in the part that had finished at
write-up time (see the end). The full groups are in `groups_calls.jsonl` (one line per group: class,
count, exception, top funground frame, names, shortest repro, message); every case of class 1 to 3 is in
`severe_calls.jsonl`.

### Class 1: crash (segfault or abort)

**None.** No child died on a signal in any run, including lone surrogates, 100 000-character strings and
2**63-pixel canvases going into Cairo.

### Class 2: hang over 10 s, or memory over 2 GB

| Group | Cases | Shortest repro | What happens |
|---|---|---|---|
| A. `f.arc` with a huge or infinite angle | 6 calls + 7 programs | `f.size(200, 150)` / `f.arc(100, 100, 80, 80, 1e12, 270, "pie")` | `while stop < start: stop += 360` in `Sketch.arc` (`funground/sketch.py:1860`) runs 2.8 billion times for 1e12, and for ever when `start` is inf or 1e308 (adding 360 changes nothing). **Fixed.** |
| B. `f.circle`/`f.ellipse` with an infinite size | 1 | `f.size(200, 150)` / `f.circle(200, 150, float("inf"))` / `f.save("x.pdf")` | Drawing returns at once; Cairo then spends 6.6 s on the PDF and 2.1 s on the SVG (measured once each), and more than 10 s for all three files. **Fixed.** |
| C. One long unbroken word in a text box | 3 (text_box, text_path, text_to_points at 100 000 chars) | `f.size(200, 150)` / `f.text_box("x" * 2000, 20, 60, 280, 100)` | `FormattedString.wrap` (`funground/formatted.py:362`) finds the break in a word wider than the box by trying every shorter prefix from the longest down, measuring each: roughly cubic. Measured: 250 chars 0.06 s, 500 0.21 s, 1 000 1.02 s, 2 000 6.99 s; 16 000 chars of spaced words 0.03 s. A pasted URL or a row of letters reaches this. Not fixed: a faster search (upward, or a bisection) gives the same break only while prefix widths grow with length, which kerning can break, so it could move a line break. **Maintainer.** |
| D. Sound with a huge duration | 3 | `sound.tone(440, 10 ** 12, "square").play()` | `MemoryError` at the 2 GB limit (`funground/sound/_synth.py:242`, `:340`). Without the limit it would take the machine's memory. A cap on duration is a meaning change. **Maintainer.** |
| E. `f.text_to_points` with a tiny spacing | 1 | `f.text_to_points("hi", 20, 20, 1e-308)` | `MemoryError` (`funground/sketch.py:1923`). **Maintainer** (a minimum spacing). |
| F. `sound.melody` with a very slow tempo | 2 | `sound.melody("C4 E4 G4:2 -", tempo=1).play()` | Over 10 s; tempo 1 is a valid edge. Probably minutes of audio synthesised before playing (unverified). |

### Class 3: corrupt output

| Group | Cases | Shortest repro | What happens |
|---|---|---|---|
| G. Gradients with nan or inf | 25 | `f.background(f.radial_gradient(float("nan"), 200, 300, ["white", "navy"]))` / `f.save("x.svg")` | `nan` or `inf` written into the SVG and PDF (pypdf: `Invalid Elementary Object ... [ 320 200 0 320 200 inf ]`). `paint._number` checks the type but not finiteness. **Fixed** for nan and inf. Finite but huge values (`1e308`) still overflow to `inf` in the SVG: **maintainer** (a range). |
| H. `f.stroke_dash` with nan, inf or 1e308 | 3 | `f.stroke_dash(float("nan"))` / `f.line(20, 50, 300, 50)` / `f.save("x.pdf")` | The PDF cannot be read by pypdf (`Could not read Null object`, `Invalid Elementary Object`, `LimitReachedError` for 1e308). **Fixed** for nan and inf; 1e308 remains. |
| I. Transforms with nan or inf | 33 (seen as class 4: `cairo.Error: invalid matrix (not invertible)` on saving PNG) | `f.translate(float("nan"), 0)` / `f.circle(50, 50, 20)` / `f.save("x.svg")` | The SVG gets `nan` coordinates; PNG and PDF raise a raw `cairo.Error` at save time, far from the line that caused it. **Fixed** for translate, rotate, scale, shear and apply_matrix. |
| J. A layer named with a lone surrogate | 1 | `with f.layer("\ud800"): f.background("skyblue")` / `f.save("x.svg")` | SVG is not well-formed XML (`reference to invalid character number`). Not fixed (time). Suggest refusing the name: `f.layer(): the name has a character that cannot be saved in a file ("\ud800")`. |
| K. A huge bleed | 1 | `f.size(200, 150)` / `f.save("poster.pdf", bleed=1e308, marks=True)` | Cairo writes `/MediaBox [ 0 0 inf inf ]`; funground's print step then fails with pypdf's `Expected an array of four values for /MediaBox, got None`, and the half-written file is left. Not fixed (time). |
| (false alarm) `f.new_page()` then save PNG | 3 | | Pages save as `out_1.png`, `out_2.png`, as documented; the first harness run looked for `out.png`. Harness fixed. |

### Class 4: raw errors a learner cannot act on (a list; wording is the maintainer's)

Grouped by cause, worst count first. The suggested sentences follow the house style of `Sketch._whole`
(`f.get(): x must be a number, not ''`).

| # | Cases | Names | Example call | What the learner sees now | Suggested sentence |
|---|---|---|---|---|---|
| 1 | about 640 | `curve`, `curve_vertex`, `bezier_vertex`, `bezier_point`, `map_range`, `lerp`, `norm`, `mag`, `radians`, `degrees`, `rotate`, `shear_x`, `arc`, `text_path`, `text_to_points`, `text_box` (x, y), `random_gaussian`, `random`/`random_number` | `f.map_range("", 0, f.width, 0, 255)` | `TypeError: unsupported operand type(s) for -: 'str' and 'int'` (also `must be real number, not str`, `can only concatenate str`) | `f.map_range(): value must be a number, not ''` |
| 2 | 156 | `sound.load`, `f.load_font`, `f.load_image`, `f.load_svg`, `f.svg_paths`, `camera.load_clip` | `f.load_image(0)` | `TypeError: expected str, bytes or os.PathLike object, not int` | `f.load_image() needs a file name in quotes, such as "photo.png", not 0` |
| 3 | 81 | `apply_matrix`, `shadow`, `curve_tightness`, `lerp_color` (amount), `noise_seed` | `f.shadow("", 6, blur=8)` | `ValueError: could not convert string to float: ''` / `invalid literal for int() with base 10: ''` | `f.shadow(): x must be a number, not ''` |
| 4 | 24 | `fill`, `stroke`, `background`, `color`, `lerp_color`, `mark`, `hsb` | `f.stroke(float("inf"))` | `OverflowError: cannot convert float infinity to integer` (`color.py:403`); `f.hsb(inf, ...)`: `cannot convert float NaN to integer` | the existing `colour component inf must be a number from 0 to 255` |
| 5 | 25 | `size`, `resize_canvas`, `create_graphics`, `inch` (as a size) | `f.size(f.inch(2 ** 63), f.inch(4))`; `f.size(f.inch(1e-308), 288)`; `f.resize_canvas(800, float("nan"))` | `OverflowError: Python int too large to convert to C long` (`cairo2d.py:86`); `AttributeError: 'NoneType' object has no attribute 'get_matrix'` (`sketch.py:384`); `cannot convert float NaN to integer` | `f.size(): the width must be a number of pixels from 1 to 32767, not 6.6e+20` (Cairo's limit) |
| 6 | 18 + 4 | `polygon`, `random_choice` | `f.polygon(0)`; `f.polygon([1, 2])` | `TypeError: 'int' object is not iterable` | `f.polygon() needs a list of points, such as [(10, 10), (90, 10), (50, 80)]` |
| 7 | 13 | `random_seed` | `f.random_seed(())`; `f.random_seed("\ud800")` | `The only supported seed types are: None, int, float, str, bytes, and bytearray.`; `UnicodeEncodeError` | `f.random_seed() needs a whole number, such as f.random_seed(7)` |
| 8 | 10 | `text_to_points` | `f.text_to_points("hi", float("nan"), 20, 6)` | `OverflowError`/`ValueError: cannot convert float ... to integer` (`geometry.py:462`) | `f.text_to_points(): x must be a finite number, not nan` |
| 9 | 9 | `sound.tone`, `sound.note`, `sound.pluck`, `sound.melody` | `sound.tone(440, float("inf"))`; `sound.melody("C4", tempo=1e-308)` | `OverflowError: cannot convert float infinity to integer`; `cannot fit 'int' into an index-sized integer` | `sound.tone(): seconds must be a finite number above 0, not inf` |
| 10 | 6 | `apply_filter`, `filter` | `f.apply_filter("blur", 1e308)` | `OverflowError: Python int too large to convert to C long` (`imaging.py:522`) | `f.apply_filter(): the blur radius must be a number from 0 to N, not 1e+308` |
| 11 | 6 | `noise`, `noise_seed`, `noise_detail` | `f.noise(float("inf"))` | `OverflowError: cannot convert float infinity to integer` (`noise.py:47/56/67`) | `f.noise(): x must be a finite number, not inf` |
| 12 | 4 | `text`, `text_box` | `f.text_box("A story", 1j, 60, 280, 100)` then save | `cairo.Error` at save time | `f.text_box(): x must be a number, not 1j` |
| 13 | 3 | `rotate`, `shear_x`, `radians` | `f.rotate(f.degrees(1e308))` | `ValueError: math domain error` (`geometry.py:41`) | `f.rotate(): the angle must be a finite number, not inf` |
| 14 | 2 | `stroke_width` | `f.stroke_width(float("nan"))` | `ValueError: cannot convert float NaN to integer` (`sketch.py:1340`) | `f.stroke_width() needs a finite number of 0 or more, not nan` |
| 15 | 2 | `keep` | `f.keep("\ud800", gap=35)` | `UnicodeEncodeError` (`exploring.py:445`) | `f.keep(): the name has a character that cannot be saved ("\ud800")` |
| 16 | 2 | `linear_gradient`, `radial_gradient` | `f.radial_gradient(320, 200, 300, ["white", "navy"], 7)` | `TypeError: 'int' object is not iterable` (`paint.py:67`) | `radial_gradient: stops must be a list of numbers from 0 to 1, one for each colour` |
| 17 | 1 each | `stroke_dash`, `create_slider`, `variations` | `f.stroke_dash(1j)`; `f.create_slider(10, 100, 40, step=1e-308)`; `f.variations(study, gap=[1, 2])` | `'complex' object is not iterable`; `OverflowError`; `unsupported operand type(s)` | name the argument and the kind of value wanted |

Also seen, not a finding but worth a look: `f.size("A6")` is refused (`unknown page size 'A6'`), and the
three-digit hex colour `"#fff"` is refused (`unknown colour '#fff'`) although CSS and p5 accept both. The
state errors met by the program fuzzer read well: `f.layer() cannot be used inside another layer block`,
`f.end_shape() called outside a shape`, `f.begin_shape() called again before f.end_shape()`,
`No drawing window yet. Call f.size(...) first.`

