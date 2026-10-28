# Core and libraries (D-120, pending)

**Status:** proposed 28 October 2026, for the maintainer's decision. No code has changed.

## Problem

Every public name lives on `f`: 211 of them (`funground._PUBLIC_NAMES`, 28 Oct). The maintainer asked (28 Oct) whether
funground should, like Processing and p5.js, keep a core and put fields such as sound, the camera and machine learning
in libraries of their own, and what else could be separate.

## What Processing and p5.js teach

- **Processing** keeps drawing, input and type in the core. Sound, Video, PDF, Serial and Network are libraries a sketch
  imports. The import line is a small lesson: this sketch now uses sound. The libraries existed mainly because of
  heavy native dependencies (GStreamer for Video) and separate maintainers.
- **p5.js** kept p5.sound as a separate file. It went largely unmaintained for years, and p5 2.0 left it out of the
  default bundle. ml5.js is a separate project because TensorFlow.js is large and moves at its own pace.
- **The cost they paid:** learners meeting "library not found", versions that do not match the core, documentation in
  several places, and a library that falls behind the core.

## funground today (measured 28 Oct)

- **Install:** the desktop needs pygame-ce for its window anyway, and sound and the camera use it, so splitting them
  saves nothing to install. The heavy, optional pieces are already extras: `funground[video]` (imageio-ffmpeg) and
  `funground[extras]` (Pillow).
- **Play:** the browser runner already loads packages only when a sketch calls for them (`runner/worker.js`,
  `ON_DEMAND`: pygame-ce and Pillow for pictures and sound analysis). The download benefit of splitting is mostly there.
- **So the reason to split is concepts, not bytes:** a smaller `f.` for a beginner (in completions, the reference and
  `llms.txt`), a clear line that says "this sketch uses sound", and fields that grow at their own pace. Heavy
  dependencies (machine learning) are the exception: those must not reach every install.
- **0.1.0 is released** (20 Oct). Of the names that might move, everything except the camera's shipped in 0.1. Moving
  them breaks released code unless the old names keep working for a while.
- `funground/sound.py`, `funground/synth.py` and others are **internal modules** that are already reachable as
  `f.sound` and `f.synth`. A public library called `sound` must take over that name, so the internal module is renamed
  first.

## What makes a library

A group of names becomes a library when at least two of these hold:

1. **A field of its own** that a learner chooses to step into (sound, the camera), not part of every sketch.
2. **Its own dependency or platform path** (Web Audio in Play, a camera's permissions, a large ML runtime).
3. **Enough names to crowd `f.`**, or a field likely to grow.

## Every name, grouped

Usage counts are files that call the names: gallery and course examples / guide pages / tests.

### Proposed libraries (27 names)

| Library | Names | Tests 1-3 | Use (ex / guide / tests) | In 0.1 |
|---|---|---|---|---|
| **sound** (18) | `create_sound`, `load_sound`, `tone`, `note`, `pluck`, `drone`, `melody`, `sequence`, `mix`, `chord_notes`, `note_to_frequency`, `frequency_to_note`, `microphone`, `microphones`, `draw_wave`, `draw_spectrum`, `draw_pitch_line`, `spectrogram` | yes, yes (Web Audio, the microphone worklet), yes | 19 / 8 / 8 | all |
| **Indian music** (6) | `raga`, `ragas`, `match_ragas`, `tala`, `tala_info`, `talas` | yes, no (pure Python, built on sound), a field that will grow (Carnatic, more talas) | 3 / 4 / 1 | all |
| **camera** (3) | `camera`, `cameras`, `load_clip` | yes, yes (permissions, `camera.js` in Play), small but growing (takes, the photo booth) | 10 / 1 / 2 | none |
| **ml** (new) | pose, hands, face, person mask, classifiers (E-37) | yes, yes (MediaPipe, ONNX, transformers.js), yes | — | — |

### Kept in the core (184 names), and why the borderline ones stay

- **Window and time:** `size`, `run`, `show`, `loop`, `no_loop`, `is_looping`, `redraw`, `frame_rate`, `frame_count`,
  `delta_time`, `frame_duration`, `full_screen`, `resize_canvas`, `exit`, `stop`, `cursor`, `no_cursor`, `width`,
  `height`, `smooth`, `no_smooth`, `millis`, `second`, `minute`, `hour`, `day`, `month`, `year`.
- **Shapes and paths:** `arc`, `circle`, `ellipse`, `line`, `point`, `quad`, `rect`, `square`, `triangle`, `polygon`,
  `bezier`, `curve`, `curve_tightness`, `begin_shape`, `end_shape`, `vertex`, `bezier_vertex`, `quadratic_vertex`,
  `curve_vertex`, `begin_contour`, `end_contour`, `path`, `draw_path`, `area`, `bezier_point`, `bezier_tangent`,
  `curve_point`, `curve_tangent`, `ellipse_mode`, `rect_mode`, `load_svg`, `svg_paths`.
- **Colour and style:** `background`, `clear`, `fill`, `no_fill`, `stroke`, `no_stroke`, `stroke_width`, `stroke_cap`,
  `stroke_join`, `stroke_dash`, `no_dash`, `miter_limit`, `color`, `color_mode`, `hsb`, `hsl`, `cmyk`, `lerp_color`,
  `opacity`, `blend_mode`, `erase`, `no_erase`, `shadow`, `no_shadow`, `linear_gradient`, `radial_gradient`,
  `ground`, `COLORS`, `CONSTANTS`.
- **Transforms:** `translate`, `rotate`, `scale`, `shear_x`, `shear_y`, `push`, `pop`, `saved_state`, `apply_matrix`,
  `reset_matrix`, `clip`, `no_clip`.
- **Type:** `text`, `text_box`, `text_size`, `text_font`, `load_font`, `system_font`, `current_font`, `text_align`,
  `text_leading`, `text_tracking`, `text_style`, `text_features`, `font_variations`, `text_fallback`, `text_width`,
  `text_ascent`, `text_descent`, `fit_text_size`, `text_on_path`, `text_path`, `text_to_points`, `FormattedString`.
  Type and print are what set funground apart (posters, the book), so they are core, not a library.
- **Pictures:** `create_graphics`, `load_image`, `image`, `image_mode`, `tint`, `no_tint`, `get`, `set`, `set_pixel`,
  `pixels`, `load_pixels`, `update_pixels`, `filter`, `apply_filter`. The cut-out (`remove_color`,
  `remove_background`, and S-245's `tidy=`, `at=` and `outline()`) are methods of any picture, a drawing as much as a
  camera frame, so they stay with pictures.
- **Print, pages and saving:** `page_size`, `new_page`, `page_count`, `mm`, `inch`, `grid`, `layer`, `show_layer`,
  `hide_layer`, `save`, `save_frames`, `save_gif`, `save_movie`. `save_movie` keeps its `funground[video]` extra: one
  function does not make a library.
- **Input:** `mouse_x`, `mouse_y`, `pmouse_x`, `pmouse_y`, `is_mouse_pressed`, `mouse_button`, `key`, `key_code`,
  `is_key_pressed`, `key_down`.
- **Controls:** `create_slider`, `create_button`, `create_checkbox`. Borderline: Processing uses a library (ControlP5),
  p5.js keeps them in its core. They stay: they are how a beginner makes any sketch interactive (11 guide pages use
  them), they need no dependency, and three names do not crowd `f.`.
- **Studio:** `variations`, `keep`, `mark`. Borderline: they are the course's way of working, used in every lesson and by
  Play's Keep this button, not a field a learner steps into. They stay.
- **Maths, randomness and noise:** `lerp`, `map_range`, `constrain`, `norm`, `mag`, `distance`, `degrees`, `radians`,
  `random`, `random_number`, `random_choice`, `random_gaussian`, `random_seed`, `noise`, `noise_seed`, `noise_detail`,
  `Vector`.

## Options

- **Keep current behaviour:** everything on `f`; the reference, completions and `llms.txt` only group the names under
  headings.
- **a. One install, libraries imported as modules.** `pip install funground` brings the core and the sound, Indian music
  and camera libraries. A sketch writes `from funground import sound` and calls `sound.note("C4")`. Only a library with a
  heavy dependency is a separate package (`pip install funground-ml`), still imported the same way
  (`from funground import ml`); without it, that line gives one plain sentence saying what to install.
- **b. One install; importing a library adds its names to `f`.** `import funground.sound` once, then `f.note(...)` as
  today. Processing's style, but a hidden side effect in Python: completions cannot tell whether `f.note` exists, and an
  example copied without its import line fails far from the cause.
- **c. A separate package for every library** (`funground-sound`, `funground-camera`). The p5 route, with its costs:
  versions to match, "not found" errors, a release for each.

## Trade-offs

| | Keep | a | b | c |
|---|---|---|---|---|
| Beginner's `f.` | 211 names | 184 | 184 until an import | 184 |
| Says "this sketch uses sound" | no | yes, and every call says it (`sound.`) | the import line only | yes |
| Breaks 0.1 code | no | yes, softened by aliases for one version | yes, softened the same way | yes |
| Installs and versions | one | one, plus `funground-ml` | one | one per library |
| Completions and `llms.txt` | as now | per module, exact | unclear before the import | per package |
| Play | as now | can load a library's packages from its import line | the same | each package published to the runtime |
| Work | none | one sprint (estimated, not measured): rename internal modules, move 27 names, aliases, about 30 examples, 13 guide pages, 11 tests, the reference, completions, `llms.txt`, Play's runner | about the same | a and more: packaging, CI and releases per library |

## Recommendation

**a**, with these rules:

1. **Three libraries now:** `sound`, Indian music and `camera`; `ml` as the first separate package (E-37). The core keeps
   the other 184 names, controls and studio included.
2. **Old names keep working in 0.2** with one line, printed once: "f.note() has moved: add `from funground import sound`
   and write sound.note()". They go in 0.3. The camera's names were never released, so they move without aliases.
3. **Each library meets the core's rules:** the same file runs on the desktop and in Play; it has contract rows, golden
   pictures, a reference page, completions, its own part of `llms.txt`, a gallery area and Since markers.
4. **A forgotten import gives a plain sentence**, never a bare `AttributeError`.
5. **Names are designed, not just moved.** The library names must not be public function names (the naming trap), and
   moving gives a chance to drop a prefix where the module already says it: `camera.open()` rather than
   `camera.camera()`, for example. The names of each library go to the maintainer before building.

**Why:** it gives the learner Processing's import line and a smaller `f.` while keeping p5's lesson in view: one install
and one version for everything the course uses. Every call saying `sound.` is honest about where a name lives, and
completions, the reference and `llms.txt` stay exact. What would change it: if learners found the module prefix harder
than the import line alone, b would be the fallback; the course's first sound lesson is the place to see.

## Open questions for the maintainer

1. The name of the Indian music library: `music` (broad, may later hold Western theory too), `hindustani` (exact, but
   Carnatic is planned) or `indian_music`.
2. Whether the course's lessons that use sound teach the import line from the first sound lesson (recommended), or
   whether early lessons keep `f.` names until 0.3.
3. Whether the alias period is one version (0.2) or two.

## Where this lands if accepted

A story per library move (sound with Indian music, then camera), an ADR recording the split, the Architecture section on
modules updated, and E-37's models spike designed as the `ml` package.
