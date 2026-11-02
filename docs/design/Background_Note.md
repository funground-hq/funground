# Design note: replacing the background behind you (S-218)

**Status:** accepted 18 October 2026 (D-106: the approach, a colour key and an empty-room snapshot, agreed 16 Oct; the
names, the tolerance and "in place" approved 18 Oct). Built in Sprint 30.

## What a learner writes

```python
import funground as f
from funground import camera

cam = camera.open()
beach = f.load_image("beach.jpg")
empty = None                                   # the room with nobody in it


def setup():
    f.size(640, 480)
    cam.start()


def key_pressed():
    global empty
    if f.key == "e":                           # step out of view, press E
        empty = cam.picture()


def draw():
    f.image(beach, 0, 0)                       # the new background first
    me = cam.picture()
    if empty is not None:
        me.remove_background(empty, tolerance=30)    # what looks like the empty room becomes see-through
    f.image(me, 0, 0)                          # you, in front of the beach
```

With a green cloth instead: `me.remove_color("green", tolerance=60)`.

The idea is **see-through**, not "replace": the method makes the matching pixels transparent, and the learner draws
whatever they like behind. That keeps it one small step that fits what pictures already do (P1 to P10): any picture,
not only the camera, and any background, including a moving sketch.

## Names (approved, D-106)

| Call | Does |
|---|---|
| `pic.remove_color(color, tolerance=40)` | Pixels close to `color` become see-through. `color` takes anything `fill()` takes |
| `pic.remove_background(empty, tolerance=30)` | Pixels close to the same pixel of `empty` (a picture of the same size, such as the empty room) become see-through |

**Tolerance** is how different a pixel may be and still count as "the same", from 0 (exactly the same) to 255
(everything). A pixel matches when each of its red, green and blue differs from the other by at most `tolerance`
(the largest channel difference). A camera's picture flickers by a few steps even in a still room, so 0 rarely works;
the defaults come from trying a laptop camera and will be checked before they are pinned.

Changes the picture in place and returns nothing, as `filter()` does. The canvas gets no version (`f.remove_color`)
at first: the camera picture is where it is needed.

## Alternatives considered

- **`replace_color(color, tolerance, with_picture)`** (the first idea): one call does the whole job, but it mixes two
  steps, works only with a picture behind, and does not compose with drawing.
- **A mask** (`me.mask(...)` exists, P9): powerful but a two-step idea (make a mask, then apply) that is harder to
  explain; the new methods could be described in the guide as "a mask made for you".
- **Machine-learning person masks** (video-call quality): a spike later (D-106), not this story.

## How it works

pygame-ce compares in C: `pygame.mask.from_threshold(surface, color, (t, t, t, 255))` for a colour, and
`pygame.transform.threshold(..., search_surf=empty)` for the snapshot; the mask's pixels set alpha to 0. About a few
milliseconds for 640 x 480 (to be measured), on the desktop and in Play (pygame-ce loads on demand there, so these names
join the on-demand list). Edges are hard; a soft edge (`soften=` with a small blur of the mask) can come later.

## Tests

Known pixels: exact and near colours removed, others kept, alpha of kept pixels unchanged; tolerance 0 and 255; a
background of a different size → `ValueError`; the same in Play's runner (`test_runner.py` case). A gallery example
with the fallback photo and a drawn "empty room" so the golden is deterministic.

## Decision (D-106)

Accepted 18 October 2026, as proposed below.


Approve the names `remove_color` and `remove_background`, the tolerance meaning (largest channel difference, 0 to 255),
and in place with nothing returned — or choose other names. Recommendation: as above; they read as plain English and
say what happens.

## Next steps: help for the cut-out (D-115, pending; spike S-227)

The maintainer asked (18 Oct) whether edge detection could help, or whether the cut-out shape could be laid over the
picture as a path whose points are moved to correct the mask. The colour key and the snapshot leave two kinds of fault:
specks of room that look like you, and holes in you that look like the room.

- **Edges alone cannot decide it.** `filter("edges")` shows where outlines are, but not which side of an outline is you.
  It is useful only after there is a mask: to pull its border onto the nearest real outline (option d).
- **Tidy the mask (a).** pygame-ce's `Mask.connected_component()` keeps the largest connected part (you) and drops the
  specks; filling the holes of that part removes the holes. Both are C, a few milliseconds.
- **An editable outline (b).** `Mask.outline()` gives the border as points; thinned to some dozens, they become an
  `f.path()` drawn over the picture. A learner drags a point to correct it, and the path cuts the picture out
  (`clip`), which also teaches what a path is. Good for a still picture; for live video the outline changes every frame,
  so (b) is for a photo or a kept frame.

Recommendation: a and b as a spike after S-218 (S-227), with the names for the maintainer; d only if b's outline is
visibly off. Machine-learning person masks stay a later spike.

**Spike S-227 (28 Oct), the evidence:** `spikes/14_cutout/README.md`. On three drawn scenes with noise, light and
shadow, tidying raised IoU from 0.874 to 0.967 where the specks were loose, kept attached shadows, and chose the wrong part
once in three (a detached shadow larger than the cut-up person; a point on the person fixed it). An 80-point outline fits
as well as 200 and a 57-line sketch drags and clips with it using only existing names. Snapping to edges did not help.
Accepted by the maintainer on 28 Oct (D-115): a and b as `tidy=` / `at=` keywords and `g.outline(points=80)`; not d. Built as S-245.
