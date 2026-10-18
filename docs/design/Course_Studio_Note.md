# Design note: the course's experiments and funground's studio vocabulary

**Status:** accepted 18 October 2026 as option b (D-113; the maintainer will review the result and may change it);
built as S-226 in Sprint 30. Asked 17 Oct: "see if mark and variations have any usefulness and applicability for
experiments". Related: S-216 (the course in Play), D-104, D-071, D-073,
`Studio_Vocabulary_Note.md`, contract rows E1, E2, K1, K2.

## Why

The course's loop is Look, Predict, Make, Compare, Choose, Extend. funground already has a small studio vocabulary
made for exactly that kind of work:

| Course step | funground | What it does |
|---|---|---|
| Make several versions, Compare | `f.variations(fn, **values)` | Draws a labelled contact sheet: one cell per value (or per pair of values), each from the same random seed, so the versions differ only in what you vary |
| Keep, with a sentence | `f.keep(note, **settings)` | Saves the picture, a copy of the sketch and a record (note, settings, seeds, controls) as `studio/NNN.*` |
| A mark repeated, placed, varied | `f.mark()`, `m.place(x, y, scale=, rotate=, opacity=)` | Records a drawing once and places it many times |

Today the course sketches do this by hand. `01_positions.py` draws three framed panels with a loop and offsets;
`05_patterns.py` moves and rotates a rectangle inside `with f.saved_state()`; each "save version a, b, c" step asks the
learner to edit a variable and run three times.

## How each fits

- **Lesson 1 (positions, space, grouping):** the comparisons are one variable at a time (position, scale, gap), the
  shape `f.variations` takes: `f.variations(study, y=[150, 250, 285])`. The labels name what changed, which is the
  course's own advice ("change one thing, compare").
- **Lesson 3 (palettes):** `f.variations(card, palette=[PALE, DARK, SOFT])` lays the three treatments of one layout side
  by side, labelled.
- **Lesson 5 (rhythm, pattern):** "one mark, three rhythms" is a mark: draw it once in `with f.mark() as m:`, then place
  it along each rhythm with `m.place(x, y, rotate=...)`. Rotation and scale come from `place` instead of a transform
  block, and the mark can be swapped in one place. `f.variations(row, gaps=[...])` compares rhythms.
- **Keep (every lesson):** `f.keep("I kept version b because ...", gap=35)` is the course's keep note, with the
  settings beside it. In Play the files arrive as download lines today, and in My files once S-221 is built.

## What not to do

The course sketches are written for beginners and in the course's own voice: explicit loops and offsets are part of
what they teach. Rewriting them around `variations` or `mark` would hide the mechanics the early lessons want learners
to see, and change another author's material.

## Proposal

1. **Keep the course sketches as they are.**
2. **Add an "Extend" step to the experiments**, in `examples/course/play.json` and as small extra sketches
   (`01_positions_variations.py`, `03_palettes_variations.py`, `05_rhythm_mark.py`): the same experiment written with
   `f.variations` or `f.mark`, offered in Play's lesson panel after Compare ("Now let funground lay out the versions").
   That teaches the studio vocabulary at the moment the learner has felt the need for it.
3. **Play's "Keep this"** stays as built (a My sketch with the note at the top). Once My files exists (S-221), it could
   also run `f.keep(note)` so the picture and the record are kept beside the code.

Each step is small; 2 changes course material, so it is the maintainer's decision, and the text would be written in
the course's voice and checked against the lessons.

## Decision for the maintainer (proposed D-113)

Options: keep current behaviour (S-216 as built, no studio vocabulary in the course) · a the "Extend" variants of
proposal 2 for Lessons 1, 3, 5 · b a and Keep through `f.keep` once My files exists. Recommendation: **b**, after S-216
and S-221; it reuses what funground already has and leaves the course sketches untouched.
