# S-175 spike: a less verbose sketch style (D-088)

Date: 11 Oct 2026. Branch `spike/s175-sketch-style` (from release-0.2-web). Nothing here is product code: it is
evidence. Tools: the project venv's Python 3.14.7, pytest, the headless platform; no editor was installed or opened.

## Question and criteria (set at the start; refined as the work showed what could be measured)

Question: do Proposal 1 (a safe global style: `from funground import *`) and Proposal 3 (`run()` optional), with the
D-090 constants, make sketches clearly shorter and still safe for learners? Proposal 2 (keyword styling) is an aside.

Pass criteria:

1. Each rewritten example has fewer characters and fewer `f.` than the original (code only, module docstring left out).
   "Clearly shorter" is read as: `f.` count falls to 0 and characters and lines fall in every example.
2. `from funground import *` brings in no name that is a Python built-in, a keyword or a standard-library module name.
3. Live values (`width`, `height`, `mouse_x`, `mouse_y`, `pmouse_x`, `frame_count`, `delta_time`, `key`,
   `is_mouse_pressed`, ...) are correct inside `setup()`, `draw()` and every event callback, every frame, in the global
   style. A negative control (refresh switched off) must fail, so the check is shown to bite.
4. Nothing changes for `import funground as f` sketches: the existing tests pass, and a variable called `width` in such a
   sketch is never overwritten.
5. Each rewritten example draws the same frame as its original (frame 30 bytes; frame 6 with scripted input for the
   interaction example), or the difference is explained.
6. `run()` behaviour is recorded per environment, with what was tested and what was only reasoned.

## Prototype design (small)

- `funground/__init__.py`: the old list is `_NAMES`; `__all__` (what `*` brings in) is `_NAMES` minus
  `STAR_LEAVES_OUT = ("exit", "filter", "random", "set")`, plus the option words and `colors`. The four names stay as
  `f.exit`, `f.filter`, `f.random`, `f.set`.
- `funground/constants.py` (D-090 prototype, only what the examples need): `CENTER LEFT RIGHT TOP BOTTOM BASELINE JUSTIFY
  NORMAL BOLD ITALIC` and `class colors` with a dozen colours; each holds the word funground already accepts.
- `funground/sketch.py`: `Sketch._publish_live_values()` writes the live values into the sketch's own globals (the dict
  `run_namespace` already has). It runs before `setup()`, after every `_attach()` (so after `size()`, `resize_canvas()`
  and `full_screen()` inside `setup()` or `draw()`), before each `draw()`, and before each event callback (`key` is set
  per event, so it cannot be done once per frame). Cost: 6 microseconds a call, a few calls a frame.
  A sketch counts as global style when its globals hold any of funground's own functions (checked by identity), and only
  the live names present in its globals are written. `import funground as f` sketches are not touched.
- `funground/api.py`: `start_unstarted_sketch()` (Proposal 3), registered at exit after `exit_hint`, so it runs first.
  Same conditions as the hint: no error, not interactive, not a script. An error in `draw()` is printed in the usual
  traceback form, not as "Exception ignored in atexit callback".
- `funground/web.py`: `Session.start()` starts a file that defines `draw()` and never called `run()`.
- Tests: `tests/test_global_style.py` (new, 7 tests); `test_api_contract.py` updated for the new `__all__`.
- Scripts: `compare.py` (counts and frame comparison, also runs the negative control), `clashes.py` (name clashes in the
  133 existing example files). The rewrites are in `global/`.

## The examples, before and after

The rewrites are written with `colors.X` and the option constants, and without `run()`. Two variants are derived
mechanically from each (`compare.py`): **strings** (quoted words, `"tomato"`, `"left"`: only the global style and
no `run()`) and **flat** (colours as flat capitals, `TOMATO`).

| Example | Version | Chars | Lines | `f.` | Frame |
|---|---|---:|---:|---:|---|
| session1/01_first_sketch (tiny) | before | 156 | 14 | 5 | |
| | strings | 140 (-10%) | 11 | 0 | |
| | `colors.X` | 150 (-4%) | 11 | 0 | identical |
| | flat | 136 (-13%) | 11 | 0 | |
| session1/07_bounce (state, `global`) | before | 255 | 22 | 6 | |
| | strings | 237 (-7%) | 19 | 0 | |
| | `colors.X` | 242 (-5%) | 19 | 0 | identical |
| | flat | 235 (-8%) | 19 | 0 | |
| gallery/interaction/02_paint (callbacks) | before | 1055 | 50 | 30 | |
| | strings | 993 (-6%) | 47 | 0 | |
| | `colors.X` | 1031 (-2%) | 47 | 0 | identical (6 frames, scripted input) |
| | flat | 975 (-8%) | 47 | 0 | |
| gallery/text/02_align (text_align, loops) | before | 901 | 37 | 20 | |
| | strings | 855 (-5%) | 34 | 0 | |
| | `colors.X` | 862 (-4%) | 34 | 0 | identical |
| | flat | 827 (-8%) | 34 | 0 | |
| gallery/text/12_justified_columns (84 lines with docstring) | before | 2161 | 60 | 28 | |
| | strings | 2129 (-1.5%) | 57 | 0 | |
| | `colors.X` | 2151 (-0.5%) | 57 | 0 | identical |
| | flat | 2109 (-2.4%) | 57 | 0 | |
| gallery/animation/03_clock (helpers, `saved_state`) | before | 951 | 36 | 31 | |
| | strings | 857 (-10%) | 32 | 0 | |
| | `colors.X` | 892 (-6%) | 32 | 0 | time dependent: not compared |
| | flat | 843 (-11%) | 32 | 0 | |

Notes on the numbers:

- Every rewrite is shorter in characters and lines, and every `f.` is gone: criterion 1 holds, but the character gain
  is small (0.5% to 13%). What shrinks is visual noise: 5 to 31 `f.` a sketch. Lines fall by 3 each, from the
  dropped `run()` and its blank lines (Proposal 3), which alone is about 9 characters.
- `colors.TOMATO` is 13 characters against 8 for `"tomato"`. Colour constants *add* characters; flat `TOMATO` (6)
  is shorter than the quoted word. In `12_justified_columns` the gain is 0.5% with `colors.X`, because of 9 long colour
  names (`colors.DARKSLATEGRAY` is 20 characters, `"darkslategray"` is 15) and a renamed variable (below).
  The original writes `"­"` (6 characters) where my copy holds the character itself (1), so that example's
  figures flatter the rewrite by about 5 characters.
- The frame check is real: with the refresh switched off (`compare.py`'s negative control, run once by hand) 07_bounce
  and 02_paint draw a different frame, and the new test fails. 02_align and 01 do not use live values and stay identical.

### Side by side

01_first_sketch, today, then global style with `colors.X`, then flat colours:

```python
import funground as f                            from funground import *                  from funground import *


def setup():                                     def setup():                             def setup():
    f.size(640, 400)                                 size(640, 400)                           size(640, 400)


def draw():                                      def draw():                              def draw():
    f.background("white")                            background(colors.WHITE)                 background(WHITE)
    f.fill("tomato")                                 fill(colors.TOMATO)                      fill(TOMATO)
    f.circle(320, 200, 80)                           circle(320, 200, 80)                     circle(320, 200, 80)


f.run()
```

07_bounce, today and global (the `global` line stays; `width`/`height` are live inside `draw()`):

```python
import funground as f                  |  from funground import *
x = 50                                 |  x = 50
speed = 3                              |  speed = 3
def setup():                           |  def setup():
    f.size(640, 400)                   |      size(640, 400)
def draw():                            |  def draw():
    global x, speed                    |      global x, speed
    f.background("white")              |      background(colors.WHITE)
    f.circle(x, f.height / 2, 40)      |      circle(x, height / 2, 40)
    x += speed                         |      x += speed
    if x > f.width - 20 or x < 20:     |      if x > width - 20 or x < 20:
        speed = -speed                 |          speed = -speed
f.run()                                |
```

02_paint, the callbacks (the live values are read inside event callbacks, which is where the refresh matters):

```python
def mouse_dragged():                                 def mouse_dragged():
    f.stroke(colour)                                     stroke(colour)
    f.stroke_width(brush)                                stroke_width(brush)
    f.line(f.pmouse_x, f.pmouse_y, f.mouse_x, f.mouse_y)  line(pmouse_x, pmouse_y, mouse_x, mouse_y)

def mouse_pressed():                                 def mouse_pressed():
    if f.mouse_button == "right":                        if mouse_button == RIGHT:
...
    colour = {"r": "tomato", "g": "seagreen",            colour = {"r": colors.TOMATO, "g": colors.SEAGREEN,
              "b": "navy"}.get(f.key, colour)                      "b": colors.NAVY}.get(key, colour)
```

02_align, the loop (`TOP`, `CENTER`, `LEFT` are the D-090 constants; the f-string still works because they hold the words):

```python
for row, vertical in enumerate(["top", "center", "baseline", "bottom"]):      for row, vertical in enumerate([TOP, CENTER, BASELINE, BOTTOM]):
    for column, horizontal in enumerate(["left", "center", "right"]):             for column, horizontal in enumerate([LEFT, CENTER, RIGHT]):
        f.text_align(horizontal, vertical)                                            text_align(horizontal, vertical)
        f.text(f"{horizontal} {vertical}", x, y)                                      text(f"{horizontal} {vertical}", x, y)
```

All six rewrites are in `spikes/12_sketch_style/global/`, full.

## Proposal 2 aside (clock example only, not implemented)

```python
def hand(angle, length, width, colour):                  def hand(angle, length, width, colour):
    with saved_state():                                      with saved_state(translate=(200, 200), rotate=angle - 90):
        translate(200, 200)                                      stroke(colour)
        rotate(angle - 90)             # 0 degrees ...           stroke_width(width)
        stroke(colour)                                           line(0, 0, length, 0)
        stroke_width(width)
        line(0, 0, length, 0)
```

Saves two lines (about 45 characters) in a four-line block, and loses the comment that explained `- 90`. The poster block in
the design note goes from nine lines to four. It is a gain only where a block is mostly transforms; most sketches have none.
The maintainer's unease is reasonable: the keyword form hides an order (translate, then rotate) that the long form shows.

## Safety findings

### What `from funground import *` must leave out

| Name | Why |
|---|---|
| `set`, `filter`, `exit` | Python built-ins (checked with `dir(builtins)`) |
| `random` | the standard-library module `random`; a learner's `import random` after the `*` would also replace funground's function silently |

No other exported name is a built-in, a keyword, or in `sys.stdlib_module_names` (checked 11 Oct, Python 3.14; the test
`test_star_hides_no_builtin_keyword_or_standard_library_module` keeps it so, and a new exported name that clashes fails it).
`path` and `grid` are not stdlib modules (`pathlib` is), but they are common learner variables, see below. The four
names still need a star-style spelling: `random` is the one learners reach for (`f.random(0, 10)` today). Options:
keep it as `f.random` and say so; or add a clearly named alias (`random_number`?). That is a naming decision for the
maintainer; the spike did not invent one.

### Names a learner is likely to choose themselves (not stdlib, but they shadow funground)

`clashes.py` over the 133 existing example files: module-level assignments or definitions of a star name in 17 files:
`note` 5, `drone` 4, `TOP` 4, `LEFT` 3, `grid` 3, `raga` 2, `circle` 2, `square` 2, `scale` 2, `size`, `line`, `push`,
`text` 1 each. Inside functions (locals and parameters), 19 star names are reused, most often `size` 12, `note` 9,
`width` 8, `height` 4, `point` 4, `text` 4, `scale` 4, `key` 3.

- A module-level clash silently replaces funground's function in that sketch (`size = 20` then `size(640, 400)` fails
  with "int is not callable"). With `import funground as f` the same sketch is fine. This is the main cost of the global
  style, and the one that cannot be tested away. A friendly check at `run()` start (a funground name rebound to a
  non-callable) would turn the cryptic error into a sentence; not prototyped.
- The D-090 capitals clash too: `TOP` is a layout constant in 4 existing examples. `12_justified_columns` has
  `TOP = 130` and `HEIGHT = 290`; in the rewrite `TOP` had to become `COLUMN_TOP` (seven more characters, six uses),
  because `TOP` is now funground's own. Flat colours (about 140 capitals) would add far more room for this.
- `colors` is itself a common variable name (`colors = ["red", "blue"]`; `linear_gradient` even has a parameter by that
  name). A learner's list called `colors` hides ours.
- Locals are harmless unless the function then calls the funground function of the same name; a parameter called `width`
  (as in 03_clock's `hand()`) is just the local one.
- Capitals are shared across features by design: `LEFT` serves `text_align`, `mouse_button` and `key_down("left")`
  (all three accept the word). That works, and also means a learner's `LEFT = 60` breaks all three together.

### Live values

- Correct in `setup()` (after `size()`), `draw()` every frame, and every callback, including `key` and `key_code`
  (set per event) and `mouse_button`: tested with scripted input, and by the frame comparison for 02_paint.
- Without the refresh the global style is wrong (the negative control): `width` stays 640 after `size(200, 120)`.
- A helper module that does `from funground import *` is **not** refreshed: its `mouse_x` is the value at its import. The
  test pins this. The guide must say: in a helper module use `import funground as f` and `f.mouse_x`, or pass the
  value in. This is the one trap that is quiet and confusing; no code can fix it without touching other modules' globals.
- A sketch that rebinds a live name (`width = 5` at top level) in the global style loses the value on the next frame.
  In an `import funground as f` sketch the same assignment is left alone (tested).
- Limit: the values are written at fixed points (before `setup()`, `draw()` and each callback, and after `size()`,
  `resize_canvas()` and `full_screen()`). Inside one function call the mouse, the key and `frame_count` do not change
  anyway, so this matches `f.mouse_x`; `load_pixels()` called inside `draw()` makes `pixels` current only at the next
  publish (use `f.pixels` there). `pixels` is published as a reference, not a copy.

### `import funground as f` sketches

Unchanged: `test_api_contract`, `test_boundaries`, `test_events`, `test_examples_golden` (the session-1 sketches, golden frames),
`test_web_session`, `test_web_reuse`, `test_script_mode` pass, except two consequences of the changes that are expected:

- `test_script_mode::test_a_real_program_that_forgot_run_gets_the_hint` now hangs (the program *starts*, headless, and
  never stops). Proposal 3 replaces the hint, so this test would be rewritten if P3 is adopted.
- `test_api_docs` (3 tests) fails: the reference generator walks `__all__` and does not know the constants. That is
  S-174's work (documenting `CENTER` and `colors`), not a defect of the idea.

## `run()` optional (Proposal 3)

| Where | Result | How known |
|---|---|---|
| Terminal, `python sketch.py` (venv Python, headless dummy driver) | Starts when the file ends; runs `setup()` and `draw()`; `stop()` ends it; exit code 0; no "never started" hint | **Tested** (subprocess test, plus manual runs) |
| Terminal, file with an error in `draw()` | Usual traceback printed, but exit code is **0** (Python ignores errors in exit hooks); with `run()` it is 1 | **Tested** |
| Terminal, `python -i sketch.py` | Does not start (interactive flag); nothing is said | **Tested** (file body ran, no frames) |
| Web runner, `funground.web.Session.start(source)` | Starts, host-driven: `step()` draws frames, `session.running` is True, mouse events reach the callbacks | **Tested** (test in test_global_style.py); the Pyodide page itself was not run |
| IDLE (F5) | The sketch **never starts**: F5 runs the file in the shell's process, which stays alive, so the exit hook does not fire until the shell closes, and by then `sys.ps1` is set so the hook stays quiet. Today (with the hint) is equally silent there, so no regression, but a sketch without `run()` gives a blank, silent result | Reasoned from how IDLE and Python work; `-i` shows the same logic |
| Thonny (Run) | Same as IDLE: its backend keeps the interpreter alive for the shell after the script | Reasoned, not run |
| VS Code, Run Python File (terminal) | Same as the terminal: `python file.py` | Reasoned (same command as the terminal test) |
| VS Code, debugger (F5), and "Run in Python REPL" (Shift+Enter) | Debugger: probably starts, as the process still ends normally, but breakpoints and stepping at exit time are unconfirmed. REPL: interactive, does not start | Reasoned, not run |
| github.dev | No Python process there; funground runs through the web runner, so as the Session row (and `run()` is still the same single call) | Reasoned from the Session test; the extension was not run |
| Jupyter / Colab | `sys.ps1` is not set, so a notebook defining `draw()` would try to start a window when the kernel shuts down | Reasoned, not run |

Other risks of starting at exit: a window opens after the file's last `print`, so output order surprises nobody but
errors lose the usual place ("Exception ignored" is avoided by catching and printing; exit code is still 0); a
`KeyboardInterrupt` during the sketch shows a traceback; atexit code may not use threads Python has already joined (not
met with the current sound and microphone threads, which are daemons; untested with real audio).

## Risks (summary)

1. Silent name clashes in the global style (17 of 133 existing examples clash on at least one name); the friendlier
   error is not built.
2. The helper-module trap (stale live values) is quiet; it is a documentation fix, not a code fix.
3. Colour constants lengthen code; flat colours shorten it but add 140 capitals to the namespace.
4. `run()` optional is not reliable in IDLE and Thonny (the schools' editors), so teaching "no `run()`" first risks a blank
   window with no message; and exit code 0 on errors.
5. Reference docs and the guide assume `import funground as f` everywhere (about 130 examples, the whole guide); two
   styles to maintain and teach. Golden/example tests would want both forms.
6. The star list is a contract: every new funground name must be checked against built-ins and stdlib (the test does).

## Recommendation

- **Proposal 1: adopt, as a second supported style, not a replacement.** It meets criteria 2 to 5: no built-in or
  stdlib shadowing once four names are left out, live values correct everywhere funground calls the sketch, nothing
  changes for `import funground as f`, frames identical. The honest gain is noise (every `f.` gone), not size
  (0.5% to 13% fewer characters). Ship with: the `*` list and its test, the refresh, the guide's helper-module
  rule, and the "your `size` hides funground's `size()`" friendly error.
- **D-090 colours: prefer flat capitals over `colors.X` only if the maintainer values length** (`TOMATO` is shorter than
  `"tomato"`; `colors.TOMATO` is longer than `"tomato"`). `colors.X` gets editor completion and keeps the namespace
  small, but in this spike it made code longer than leaving the colour as a quoted word. The decision belongs to the
  maintainer; the table gives both. The strings are still accepted in all cases.
- **Proposal 3: allow it, do not teach it.** Keep `run()` as the documented last line (it is one line, and it works in
  IDLE and Thonny). Auto-start is a safety net for terminal, VS Code and the web runner; it needs the exit-code
  caveat noted and one existing test rewritten. If IDLE and Thonny matter in classrooms, dropping `run()` from first
  lessons would cause silent blank runs there.
- **Proposal 2: not worth it** as a general feature; the saving is real only for transform-heavy blocks. If wanted,
  `saved_state(translate=, rotate=)` alone (no style keywords) is the small, explicit part.
