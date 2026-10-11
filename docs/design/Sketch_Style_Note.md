# Design note: a less verbose sketch style (D-088, revised proposals)

**Status:** proposals for the maintainer, 11 October 2026. Nothing is built. Constants are decided
(D-090: capitals holding the words, story S-174) and are used below.

## The complaint

The maintainer: "f.circle(), f.fill() etc. is too verbose", and "f.run()" is boilerplate. The `f.` prefix and
`f.run()` were never decided: both came from the v0.5 design (`import playground as p`, `p.run()`) and survived
the rename (D-020). A learner's sketch today:

```python
import funground as f

x = 50
speed = 3


def setup():
    f.size(640, 400)


def draw():
    global x, speed
    f.background("white")
    f.fill("tomato")
    f.circle(x, f.height / 2, 40)
    x += speed
    if x > f.width - 20 or x < 20:
        speed = -speed


f.run()
```

The noise is: `f.` on every call (7 here), `f.run()`, quoted option words (now D-090), and `global` (Python's
rule for changing a variable from inside a function).

## Ruled out, with reasons

| Idea | Why not |
|---|---|
| Chaining (`f.fill("red").circle(...)`) | Removes `f.` only by putting many steps on one line; an error points at the whole line; calls that return a value (`text_width`, `random`) cannot chain, so learners meet two kinds of call; not how Python, p5 or Processing read |
| A sketch class (`class Poster(f.Sketch)`) | Python requires the object explicitly in methods: `self.circle(...)` is as long as `f.circle(...)`. The name `self` is only a convention, but the object cannot be left out. Tricks that hide it (rewriting a method's globals, executing the body in the object's namespace) break debuggers, tracebacks and autocompletion: hacks under our clean-code rule. It also asks learners to understand classes before drawing a circle |
| Integer constants | No speed gain (a string check is 25 ns, an int 25 ns); worse messages (D-090) |

## Proposal 1: a global style, made safe

```python
from funground import *

x = 50
speed = 3


def setup():
    size(640, 400)


def draw():
    global x, speed
    background(WHITE)
    fill(TOMATO)
    circle(x, height / 2, 40)
    x += speed
    if x > width - 20 or x < 20:
        speed = -speed


run()
```

This is how Processing and p5 read, and how DrawBot (`from drawBot import *`) and Processing's Python mode work.
`from funground import *` exists today, with two traps that the proposal removes:

1. **It would hide Python's own names.** funground exports `set`, `filter` and `exit`, which shadow Python's
   built-ins, and `random`, which shadows the `random` module (checked 11 October). They stay out of `*`
   (available as `f.set`, or under a clear name), and a test keeps `*` free of any built-in or common
   standard-library name.
2. **Live values would freeze.** `width`, `height`, `mouse_x`, `frame_count`, `key` and the rest are copied once
   at import. funground already knows the sketch's own globals (that is how `run()` finds `setup` and `draw`),
   so before each `draw()` and each event callback it writes the current values there. A helper module
   imported by the sketch does not get them refreshed: it uses `f.mouse_x` (the guide says so).

`import funground as f` stays fully supported and documented; a teacher chooses. Colour constants
(`TOMATO`, `WHITE`) come from D-090's colour set; under `*` they need care to avoid clashing with names
learners choose (a spike question).

## Proposal 2: fewer lines for one idea

Keyword styling on drawing calls, and a state block that takes its transforms:

```python
with saved_state(translate=CENTRE, rotate=angle):
    text(char, radius, 0, size=12, fill=(255, 255, 255, alpha))
```

instead of `push`, two transforms, `text_size`, `fill`, `text` and `pop`. Keywords set the style for that one
call only (the current style is untouched afterwards), so they never surprise the next line. Candidates:
`fill=`, `stroke=`, `stroke_width=` on shapes; `size=`, `font=`, `fill=` on `text`;
`translate=`, `rotate=`, `scale=` on `saved_state`. The long forms stay.

## Proposal 3: `run()` optional where it is reliable

funground already notices a file that defines `draw()` but never calls `run()` (it prints a reminder when
Python exits). It could start the sketch there instead. The catch: IDLE, common in schools, keeps Python
running after the file ends, so the automatic start may never come. The spike checks IDLE, Thonny,
VS Code, the terminal, the website editor and github.dev. If it is reliable everywhere, `run()` becomes
optional (still allowed); if not, it stays, and the reminder stays.

## `global x, speed`

This is Python's rule, not funground's: a function that assigns to a file's variable must say `global`. Two
ways around it exist without tricks, both optional: keep changing values in a small object
(`ball = Ball(x=50, speed=3)` and `ball.x += ball.speed`), which the guide already teaches for more than two
values, or funground's own `state = f.state(x=50, speed=3)` holder. The note does not propose removing
`global`.

## The same lines from the poster example, before and after

Before (today):

```python
f.push()
f.translate(*CENTRE)
f.rotate(p["angle"])
f.translate(p["radius"], 0)
f.rotate(90)
f.fill(255, 255, 255, max(p["alpha"], 0))
f.text_size(p["size"])
f.text(p["char"], 0, 0)
f.pop()
```

After (proposals 1 and 2, and a small class for the letter's data):

```python
with saved_state(translate=CENTRE, rotate=letter.angle):
    translate(letter.radius, 0)
    rotate(90)
    text(letter.char, 0, 0, size=letter.size, fill=(255, 255, 255, max(letter.alpha, 0)))
```

## The spike that would decide it (proposed S-175)

Question: do proposals 1 to 3 make sketches clearly shorter and still safe for learners? Before work: the
pass criteria (every rewritten example shorter, no built-in shadowed, live values correct in callbacks,
`run()` behaviour per editor recorded). Work, no product code: rewrite ten gallery examples in the new style
(using D-090 constants), a prototype of the live-value refresh and of the `*` exclusions on a branch, the
editor checks for proposal 3. Deliverable: the examples side by side, the measurements, a recommendation.
