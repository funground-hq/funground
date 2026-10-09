# funground compared with p5 and DrawBot

funground borrows from two tools that came before it: **p5** (p5.js and Processing) and
**DrawBot**. This note puts the three side by side. It is the big picture. It is for a teacher,
a learner, or anyone choosing a tool.

It is meant to be fair. Each of the three is good at something the others are not.

If you already use one of them and want to move, you want a different page: chapter
[14, Coming from p5.js and Processing](../guide/14_coming_from_p5_processing.md) and chapter
[15, Coming from DrawBot](../guide/15_coming_from_drawbot.md) translate name by name.

**How this note was checked.** The funground column comes from the
[Semantic Contract](../design/Semantic_Contract.md) and the code. The p5 and DrawBot columns were
checked against their own source and documentation (p5.js 2.3.2, the p5.js reference text, the
Processing examples, the DrawBot README and docs). Where we could not confirm a claim, the note says
"as far as we know". Tools change. Check their own sites before you decide.

**Contents:** [The three tools](#the-three-tools) · [What funground shares](#what-funground-shares) ·
[Where it differs](#where-it-differs) · [What funground lacks](#what-funground-lacks) ·
[Why funground chose differently](#why-funground-chose-differently) ·
[Moving between them](#moving-between-them) · [Credits](#credits)

---

## The three tools

### p5 (p5.js and Processing)

p5.js is a free JavaScript library for creative coding. It runs in a web browser. You write
`setup()` and `draw()`, and the browser calls them. It has a large, friendly community, a web
editor, a big reference, and many add-on libraries. It also has a 3D mode (WebGL). Its sound
support lives in an add-on library called p5.sound, not in the core.

Processing is the older tool that p5.js grew from. It is written in Java, and it runs as a desktop
program with its own editor. It has the same `setup()` and `draw()` idea, and 2D and 3D drawing.
Both are for artists, designers, teachers and learners. They have been used in classrooms for
many years.

### DrawBot

DrawBot is a free application for macOS. You write a Python script, and it draws a picture or a
multi-page document. Its README names rectangles, ovals, Bezier paths, polygons, text, colours and
transparency, and lists PDF, SVG, PNG, JPEG, TIFF, animated GIF and MP4 as export formats.
DrawBot can also be installed as a Python module, but, as its README says, that only works on
macOS. It is made for designers, and typography is its strength: fonts, OpenType features, variable
fonts and formatted text. It runs your script once, from top to bottom. It has no animation loop.

### funground

funground is a Python library. You import it as `f` and call `f.circle(...)`, `f.fill(...)` and
so on. It is for learners and their teachers. It runs on Windows, macOS and Linux (see the notes
under [Where it differs](#where-it-differs)). It draws on the screen and saves PNG, PDF and SVG
files, and animated GIF and MP4 files. It also makes and listens to sound, and it has built-in
help for Indian ragas and talas.

funground has two styles, and a file is one or the other. An **animated sketch** has `setup()`
and `draw()`, like p5. A **script** draws from top to bottom and saves a file, like DrawBot.

This is funground's first release, version 0.1. See [What funground lacks](#what-funground-lacks).

### Other Python options

If you want Processing in Python, look at **py5** (Processing's Java core driven from Python, with
3D) and the **p5** Python package. Both follow Processing's names and conventions closely.
funground does not: it keeps its own Python-style names and semantics (see
[Why funground chose differently](#why-funground-chose-differently)).

---

## What funground shares

### With p5

- **The `setup()` and `draw()` loop.** `setup()` runs once. `draw()` runs again and again.
  `f.frame_count`, `f.no_loop()`, `f.redraw()` and `f.millis()` work as you expect.
- **Immediate-mode drawing words.** You set the state, then draw. `fill`, `stroke`,
  `stroke_width`, `circle`, `rect`, `ellipse`, `line`, `triangle`, `begin_shape` and the rest.
  What you set stays set until you change it.
- **`push` and `pop`.** They save and restore the transform and the style. funground adds a
  `with f.saved_state():` form that can never leave a `pop()` unbalanced.
- **Live mouse and keyboard values.** `f.mouse_x`, `f.mouse_y`, `f.key`, and callbacks such as
  `mouse_pressed()` and `key_pressed()`.
- **Noise.** `f.noise()` uses p5's own algorithm and seed generator. After `f.noise_seed(n)`, the
  values match p5's after `noiseSeed(n)` (Semantic Contract row H4).
- **A p5-style kit around the core.** `map_range`, `lerp`, `constrain`, `Vector`,
  `create_graphics`, `load_pixels`, `filter`, `tint`, `erase`, `text_to_points`, sliders,
  checkboxes and buttons, and rounded corners on `rect`.
- **A friendly tone.** Escape ends a sketch. Errors name the thing to fix.

### With DrawBot

- **The "script makes a file" model.** A script with no `draw()` and no `f.run()` draws from the
  top down, then calls `f.save("name.pdf")`. It writes at once (row R14).
- **Pages.** `f.new_page("A4")`, `f.page_count()`, `f.page_size("A4")`. A PDF with several pages
  is one `f.save("x.pdf")` (rows R16, R17).
- **`FormattedString`.** Mixed fonts, sizes, colours and tracking in one piece of text, drawn with
  `f.text` or `f.text_box`. `f.text_box` returns the text that did not fit, so it can flow into a
  second box (rows T10, T14).
- **Paths and booleans.** `f.path()` builds a path. `union`, `intersection`, `difference` and
  `xor` combine paths, in the spirit of DrawBot's `BezierPath` (row F11). `expand_stroke` and
  `text_path` work too (rows F12, F13).
- **Real text in the file.** A PDF holds real, searchable text. An SVG holds live, editable
  text (rows T15, T19). See [Vector output](#vector-output-and-text) below.
- **Variable fonts and OpenType features.** `f.font_variations(wght=700)`,
  `f.text_features(liga=False)` and `f.text_tracking(...)`, with names taken from DrawBot's
  `fontVariations`, `openTypeFeatures` and `tracking` (row T13).
- **Gradients, blend modes, opacity and shadow.** Same ideas, with a few spelling differences.
- **Pages as animation frames.** In a script, every page is a frame of a GIF or MP4, and
  `f.frame_duration(seconds)` sets how long it shows (row M1).

---

## Where it differs

Some of these rows are close to the same. Some are real differences. "p5" here means p5.js
unless a row says Processing.

### The basics

| | funground | p5 (p5.js, Processing) | DrawBot |
|---|---|---|---|
| Language | Python 3.11 or newer | JavaScript (p5.js); Java (Processing) | Python |
| Where it runs | A desktop window on Windows, macOS and Linux. Tested in CI on all three. The high-resolution screen support has been verified on Windows only (row C3) | A web browser (p5.js); the desktop (Processing) | macOS only. The app, or a Python module that needs macOS libraries |
| Install | `python -m pip install funground`. On Linux, Cairo's development files first | None for p5.js: a script tag, or the web editor. Processing is a download | Download the app. The module is installed from its repository |
| Naming style | `snake_case`, called as `f.circle(...)` | `camelCase`, global functions | `camelCase`, global functions, or `drawBot.` prefix as a module |
| Running a file | A sketch (`setup`/`draw`, then `f.run()`) or a script (no `draw`, no `f.run()`). One style per file | A sketch. It starts by itself | A script, run once, top to bottom |
| Animation loop | Yes, in a sketch. Default 60 frames a second | Yes. `draw()` is called about 60 times a second by default | No loop. Animation is many pages saved as GIF or MP4 |
| Editor | Any Python editor. No funground-specific editor | The p5.js web editor (editor.p5js.org); the Processing editor | The DrawBot app has its own code editor and live preview |

### Drawing conventions

| | funground | p5 | DrawBot |
|---|---|---|---|
| Origin and y | Top-left, y down (row C1) | Top-left, y down in 2D. In WEBGL mode the origin is the centre of the canvas | Bottom-left, y up |
| Angle units | **Degrees** for `rotate`, `arc`, `shear`, `Vector` (row F1). `f.radians()` and `f.degrees()` convert | **Radians** by default. `angleMode(DEGREES)` switches | Degrees (its `rotate` docstring says "with a given angle in degrees") |
| Colour numbers | 0 to 255 per channel, names, hex strings (row S1) | 0 to 255 by default (`colorMode(RGB)`) | 0.0 to 1.0 floats. No colour names. CMYK as well |
| Colour modes | `f.color_mode("rgb" / "hsb" / "hsl", ...)` with p5's defaults. `f.color_mode("rgb", 1)` gives DrawBot's 0 to 1 (row S15) | `colorMode(RGB / HSB / HSL, ...)` | No mode switch. RGB and CMYK are separate calls |
| One number as a colour | A grey; two numbers are grey and alpha (row S16) | The same | The same: `fill(0.5)` |
| Default fill and stroke | White fill, black stroke, width 1 (row S3) | The same, as far as we know. Its source starts with stroke width 1 | You set a fill before you draw a shape (its docs say so) |
| `rect` | `(x, y)` is the top-left corner. `f.rect_mode(...)` changes it | The same default. `rectMode(...)` | Bounding box corner, y up |
| `ellipse` and `circle` | `(x, y)` is the **centre**. `f.ellipse_mode(...)` changes it | The same default. `ellipseMode(...)` | `oval(x, y, w, h)` takes the bounding-box corner, like `rect` |
| Text anchor | `(x, y)` is the **top-left** of the text. `f.text_align(h, v)` changes it, and it can use `"baseline"` (rows T1, T7) | The text baseline (`textBaseline` default is BASELINE) | As far as we know, the baseline of the first line |
| Stroke | Centred on the edge (row S4) | Centred | Centred |

### Output and files

<a id="vector-output-and-text"></a>

| | funground | p5 | DrawBot |
|---|---|---|---|
| Vector output | PDF and SVG. PDF text is real, searchable text. SVG text is live and editable. `text="shapes"` writes outlines instead (rows T15, T19, T20) | The core saves canvas pixels. p5.js needs an add-on library for PDF or SVG, as far as we know; Processing has its official PDF Export library | PDF and SVG, with text as text |
| Raster output | PNG. A numbered PNG sequence with `save_frames` | PNG and JPG from the canvas | PNG, JPEG, TIFF and more |
| GIF and MP4 | `save_gif` and `save_movie` in a sketch. `save("x.gif")` and `.mp4` in a script. GIF needs Pillow. MP4 needs ffmpeg (row M1) | `saveGif` in p5.js. Video as far as we know needs something else | Animated GIF and MP4 from pages |
| Multi-page documents | Yes, in a script (rows R16, R17) | Not in core, as far as we know | Yes |
| Layers | `with f.layer("name"):`. In PDF each layer is an optional-content layer. In SVG each is a group that Inkscape and Illustrator show as a layer (row F16) | None built in. You draw into `createGraphics` buffers | None, as far as we know (guide chapter 15 says so) |
| Images and pixels | `load_image`, `get`, `set`, `pixels`, `filter`, `tint`, `mask`, `copy` and `resize`. Pixels are logical (density 1) (rows P4 to P10) | The same family of functions. `pixelDensity` is adjustable | Images, image objects and a large set of Core Image filters |
| Paths and booleans | `f.path()` with booleans and stroke outlines | Shapes and vertices. Booleans: as far as we know, not in core | `BezierPath` with booleans |
| Typography | Bundled fonts, `load_font`, font fallback, tracking, features, variable fonts, `FormattedString`, text boxes, text as a path or points | Fonts, text size and alignment, `textToPoints`, variable font axes in p5.js 2 | The deepest of the three: `FormattedString`, tabs, indents, baseline shift, installed fonts by name |
| CMYK | Left out for good ([ADR-003](../design/ADR-003-out-of-scope.md)) | No | Yes |
| 3D and WebGL | **No** | Yes (WEBGL in p5.js; P3D in Processing) | No |

### Sound and music

| | funground | p5 | DrawBot |
|---|---|---|---|
| Sound playback | In the core: `f.load_sound` (WAV, OGG, MP3) | The p5.sound add-on; Processing has its official Sound library | No |
| Making sound | `tone`, `note`, `pluck`, `melody`, `drone`, `mix`, `sequence`, `reverb`, all computed in Python before playing. No live oscillator (row A3) | p5.sound has live oscillators and envelopes | No |
| Sound analysis | `level`, `spectrum`, `pitch`, `onsets`, `tempo`, `chord`, `key` on a sound or a microphone (rows A2, A5, A6) | Amplitude and FFT in p5.sound | No |
| Microphone | `f.microphone()` gives level, spectrum, pitch and `capture(seconds)` (row A4) | `p5.AudioIn` in p5.sound | No |
| Indian ragas and talas | A small cited table of 13 ragas and 6 talas. `f.raga`, `f.tala`, `f.drone`, sargam in `melody`, `match_ragas` (row A8) | No, as far as we know | No |
| Draw the sound | `draw_wave`, `draw_spectrum`, `spectrogram`, `draw_pitch_line` (row A7) | You draw it yourself from the analysis | No |

### Controls, sharing and teaching

| | funground | p5 | DrawBot |
|---|---|---|---|
| UI controls | `create_slider`, `create_checkbox`, `create_button`, in a panel below the canvas (row U1) | `createSlider` and friends, as page elements | `Variable([...])` builds a panel and runs the script again on every change |
| The web and sharing | No browser mode. You share the `.py` file, and the PDF, SVG, PNG, GIF or MP4 it makes | A sketch is a web page. Easy to share by link. This is p5's great strength | You share the script and the files. The app is macOS only |
| Gallery and teaching material | A guide of 18 chapters, a Quick Reference, an error page, a glossary, a gallery of 87 examples, and eight project pages. A teacher can run the gallery with `python -m funground.gallery` (row R18) | A large reference, many tutorials, books and examples, and a wide community of teachers | Documentation, examples and a courseware page |
| Licence | Library: LGPL-2.1-only. Examples and guide code: CC0 (decisions D-025, D-026, D-084) | p5.js: LGPL-2.1. Processing: see its own site | BSD |
| Maturity and community | **First release (0.1).** A small project with a small team and no wider community yet | Many years old, many contributors, a large community | Many years old, a loyal community of type designers |

---

## What funground lacks

Be honest about these before you choose it.

- **No 3D.** There is no WEBGL or P3D. 3D is out of scope for 1.0 (decision D-014, and
  [ADR-003](../design/ADR-003-out-of-scope.md)).
- **No browser.** A funground sketch does not run in a web page. You cannot share one by link.
  Running in the browser was researched (see the
  [Browser Mode Note](../design/Browser_Mode_Note.md)) but is not planned for 0.1. If you need
  the web, use p5.js.
- **A first release and a small community.** Version 0.1. There are fewer books, forum answers
  and examples than for p5 or DrawBot. Expect rough edges.
- **No live-coding editor.** funground does not come with an editor, and it does not re-run your
  code as you type. You use your own editor and run the file. DrawBot's app, the p5.js web editor
  and the Processing editor are all easier at this.
- **Less verified on macOS and Linux.** CI runs the tests on Windows, macOS and Linux. But the
  maintainer has checked the high-resolution screen path on Windows only (Semantic Contract row C3).
- **No CMYK or print colour management.** DrawBot has them.
- **A smaller typography toolbox than DrawBot.** `FormattedString` takes its settings only in
  `append()`. It has no tabs, indents or baseline shift yet (guide chapter 15 lists the gaps).
- **No live oscillators.** funground builds a sound first, then plays it. p5.sound can change a
  tone while it plays.
- **Source compatibility is not a goal.** funground never runs p5 or DrawBot code unchanged.

---

## Why funground chose differently

Each paragraph names the decision. All the decisions are in the
[Decision Log](../design/Decision_Log.md), and the pinned meanings are in the
[Semantic Contract](../design/Semantic_Contract.md).

**Python and snake_case.** funground is for people who are learning Python. So names follow
Python style, and you call them through the module (`f.circle`). A helper called `map` would hide
Python's own `map`, so p5's `map` is `f.map_range` (guide chapter 14).

**Degrees, not radians (D-002, row F1).** Most learners think "a quarter turn is 90". Radians
add a second idea before the first one is clear. `f.radians()` and `f.degrees()` are there for
`math.sin` and friends. There is no angle-mode switch, so a sketch never has to ask which unit is
on. This is the change that catches p5 users most.

**Top-left origin, centre ellipses (rows C1, C4, C5).** It is the screen's own convention, and
it is p5's. DrawBot's bottom-left origin follows print and typography. If you want DrawBot's
ellipse placement, `f.ellipse_mode("corner")` gives it (D-030). Modes were added late, as a
saved-state setting, with the defaults unchanged.

**Text anchored at the top-left (row T1).** Every other shape in funground sits by its top-left
corner (or its centre, for round shapes). One rule for text matches that. p5's default is the
baseline. `f.text_align("left", "baseline")` gives it back (row T7).

**Colour: 0 to 255, with p5's `color_mode` (D-017, D-031, D-032).** Learners meet 0 to 255 and
names such as `"tomato"` first. One number is a grey, as in p5. For DrawBot's floats, call
`f.color_mode("rgb", 1)` once.

**Two styles of program (D-029, row R13).** A sketch is p5's model. A script is DrawBot's. Both
are useful for teaching: a sketch to see things move, a script to make a poster or a PDF. A file
is one or the other, so the rules stay simple. The sketch needs an explicit `f.run()` (Semantic
Contract rows R3 and R13), so the start of the program is visible.

**Real text in PDF and SVG (D-043, D-059, D-060; rows T15, T19, T20).** The first version drew
text as outlines. That looks right but cannot be selected, searched or edited. Designers need
editable text for work in progress and fixed outlines for hand-over, so `save(..., text=...)`
chooses.

**Layers (D-053, row F16).** Neither p5 nor DrawBot has them as a simple word. Layers make
one drawing easier to manage, and they show up in Inkscape, Illustrator and Acrobat as real layers.

**Sound and Indian music in the core (D-046, D-055, D-056, D-057, D-062).** The maintainer
wanted sound, and music from the Indian tradition, to be part of a creative tool.
funground uses one sound object with `level`, `spectrum` and `pitch`, instead of separate
Amplitude and FFT objects, and computes sounds before playing them. The raga table cites its
sources, and the guide says what the analysis cannot tell apart.

**UI controls as a panel (D-047, row U1).** A desktop window has no web page to put controls
on. They go in a panel below the canvas, outside the picture and the saved file.

**Choosing p5's and DrawBot's names (D-016, D-036, D-038, D-042, D-044).** Where p5 or DrawBot
already had a good name and a matching meaning, funground used it, in snake_case. Where the meaning
differs, the guide says so in a table.

---

## Moving between them

**From p5 or Processing:** read
[chapter 14](../guide/14_coming_from_p5_processing.md). **From DrawBot:** read
[chapter 15](../guide/15_coming_from_drawbot.md). The
[guide's learning path](../guide/README.md) and the [Quick Reference](Quick_Reference.md) are the
next stops. The [gallery](../gallery/README.md) shows each feature with code.

Four things catch people most.

**1. Radians and degrees.** In p5, `rotate(PI / 4)` is an eighth of a turn. In funground, the
number 0.785 turns by less than one degree, so a ported angle must be changed to degrees.

```py
f.rotate(45)                    # funground: degrees
```

**2. A missing `f.`.** Every name is called through the module. A bare `circle(...)` raises a
`NameError`. See [When something goes wrong](../guide/errors.md#nameerror-or-attributeerror-on-an-f-name).

```py
import funground as f
f.circle(100, 100, 50)          # not  circle(100, 100, 50)
```

**3. `snake_case`.** `strokeWeight` is `stroke_width`, `noFill` is `no_fill`, `mouseX` is
`f.mouse_x`, and `frameCount` is `f.frame_count`.

**4. `f.run()`.** A p5 sketch starts by itself. A funground sketch does not start until the last
line of the file says so. If the window never opens, check for it. funground prints a hint when it
sees a `draw()` and no `f.run()`.

```py
def draw():
    f.background("white")
    f.circle(f.mouse_x, f.mouse_y, 40)


f.run()                         # the last line of a sketch
```

If you come from DrawBot, add two more. The y axis points down, so a shape near the bottom has a
y close to `f.height`. And `f.ellipse(x, y, w, h)` is placed by its centre, not its corner.

---

## Credits

funground learned from all three tools.

- **p5.js and Processing** gave it the sketch model, the drawing words, the way of teaching with
  small visual programs, and the noise algorithm. funground's `noise.py` is a port of p5.js's
  noise code and keeps that code's LGPL-2.1 licence (decision D-025).
- **DrawBot** gave it pages, `FormattedString`, paths and booleans, the idea of a script that
  makes a file, and its typography vocabulary.
- **p5.sound and Processing's Sound library** shaped the first sound names.

funground is **not affiliated with, or endorsed by,** p5.js, the Processing Foundation or
DrawBot. The names p5.js, Processing and DrawBot are used here only to say what they are. No
logos or branding are used. Every example in funground is written from scratch, from the feature
it shows. The example code is published as CC0 ([D-026](../design/Decision_Log.md)).
