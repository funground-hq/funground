# Spike S-225: drawing without coordinates (proposal D-121)

**Status:** decided 28 Oct 2026 (D-121): **keep current behaviour.** The maintainer: "even a gets complex soon. I do not
want to introduce more parameters. If really needed, creating a new package is the better cleaner option, but not now."
No shape gains keywords. The spike's `make/nocoords.py` stays as spike evidence only. The test chapter's sketches print
the proposed spelling, and must be rewritten with today's calls before any page is shown as the book. How Chapter 1 meets
the brief ("no x and y") is open again for the book's writing. A separate package for the book's drawing is possible later,
as a new decision. The proposal below is kept as it was asked.

## The brief

The maintainer, 18 Oct, set the book's Chapter 1: "drawing shapes of different colours with no x and y". A shape is drawn
at the centre by default, or at a random place when asked. It comes in variations of shape, colour, size and stroke. The
aim is to break the idea that programming is mostly mathematics: the first page should not start with a coordinate
system.

## funground today

**Every shape needs a position and a size:**
- `f.circle(x, y, diameter)`;
- `f.ellipse(x, y, w, h)`;
- `f.rect(x, y, w, h)`;
- `f.square(x, y, size)`;
- `f.triangle(x1, y1, ..., y3)`.

A first sketch therefore writes `f.circle(f.width / 2, f.height / 2, 200)` or `f.circle(300, 300, 200)`: three numbers
before anything is seen. Calling `f.circle()` today gives Python's own message, `TypeError: circle() missing 3 required
positional arguments`.

## Options

**Keep current behaviour.** The book starts with `f.circle(300, 300, 200)` and explains the numbers on page 1.

**a. Shapes callable with no position** (recommended):
- `f.circle()` draws at the centre of the canvas, at a default size.
- Two keywords:
  - `size=`, the shape's size;
  - `at="center"` or `at="random"`, where the shape goes.
- A call gives either no position at all or the full set of positional arguments, as today. A partial set, such as
  `f.circle(100)`, gives a plain `TypeError` that names both forms.

**b. A small book module:** `from funground import book`, then `book.circle()`.
- Nothing about `f.circle` changes.
- But the reader learns names they must later leave behind, and there are two ways to draw a circle.
- It is not a field of its own, so under D-120 it is not a library.

**c. Placement as state:** `f.place("random")` before the shapes, like `rect_mode`.
- Shapes still need sizes, so it is half a solution.
- The state is hidden: a shape's position depends on a line far above it.

## The proposed rules (a)

**Which shapes:** `circle`, `ellipse`, `square`, `rect` and `triangle`. `text` may follow later as a separate decision.
`line`, `point`, `arc`, `quad`, `polygon` and the path calls are left alone, because their points are what they are.

**Size:** `size=` defaults to one third of the smaller side of the canvas: 200 on a 600 x 600 canvas.
- `circle` and `square`: `size=` is the diameter or the side.
- `ellipse` and `rect`: `size=` is the width, and the height is the same unless `height=` is given. So
  `f.rect(size=200, height=100)` is a long rectangle. Alternatively, `width=` and `height=` could be given together.
- `triangle`: an equilateral triangle, point up, `size=` wide.

**Place:**
- `at="center"` puts the shape's centre at the canvas's centre, in the current coordinates. After `f.translate()`, it
  is wherever `f.width / 2, f.height / 2` would be. `rect_mode` and `ellipse_mode` don't apply: the shape is centred.
- `at="random"` picks a place where the whole shape, with half its stroke, stays inside the canvas. It uses
  `f.random`, so `f.random_seed()` repeats it. If the shape is bigger than the canvas, it is centred.
- Any other value for `at=` gives a `ValueError` that lists the two words.
- Points such as `at=(100, 100)` are left out. The full positional form already does that job.

**Style is unchanged:** `f.fill()`, `f.stroke()` and `f.stroke_width()` as today.

**Errors:**
- Mixing the two forms, such as `f.circle(100, 100, size=50)`, gives a `TypeError`: "f.circle() takes either no
  position, or x, y and a diameter".
- `size=` of zero or less behaves as a zero or negative diameter does today.

## What Chapter 1 looks like

```python
import funground as f

f.size(600, 600)
f.background("oldlace")
f.fill("tomato")
f.circle()
f.show()
```

```python
f.fill("turquoise")
f.square(size=300)
f.fill("gold")
f.circle(at="random", size=80)
```

Coordinates arrive later, in a chapter of their own, as a way to say *exactly where*. The reader already knows what
`f.circle()` does by then.

## Trade-offs

| | Keep | a | b | c |
|---|---|---|---|---|
| Chapter 1 shows numbers | yes, from line 1 | no | no | sizes only |
| Ways to draw a circle | 1 | 1, with optional parts | 2 | 1, with hidden state |
| Effect on existing sketches and goldens | none | none: every current call is unchanged | none | none |
| Public API change | none | 5 shapes gain 2 keywords (`size=`, `at=`) and `height=` | a new module | a new function |
| Play, completions, `llms.txt` | as now | signatures regenerated | a new module everywhere | one more name |
| Work (estimated, not measured) | none | one story: the five shapes, contract rows, tests, a gallery example and its golden, guide 03, Quick Reference | about the same, plus duplicated docs | about half of a, but still sizes |

## Recommendation: a

**Why:** a is the smallest change that gives Chapter 1 what the brief asks for, without teaching the reader names to
unlearn. Every existing call keeps its meaning, so no golden changes. "Either nothing or everything" keeps one clear
rule: a beginner never meets a half-positioned shape.

**What would change it:** if the maintainer wants Chapter 1 to show positions by name (for example
`at="top left"`), then `at=` grows a short list of words. That is still a, with more words.

**Open questions:**
1. Should `rect` and `ellipse` take `size=` with `height=` (proposed), or `width=` and `height=`?
2. Should `at=` also take a point `(x, y)`, as S-245's `at=` does for the cut-out? That gives a bridge from words to
   numbers, but a second way to place a shape.
3. Should `f.text("Hello")` follow, drawn at the centre?
