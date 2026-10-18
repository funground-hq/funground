# Design note: replacing the background behind you (S-218)

**Status:** proposal for the maintainer, 17 October 2026 (D-106: the approach is agreed, a colour key and an
empty-room snapshot; the names and the tolerance are to approve). Nothing is built.

## What a learner writes

```python
import funground as f

cam = f.camera()
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

## Proposed names (to approve)

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

## Decision for the maintainer (D-106)

Approve the names `remove_color` and `remove_background`, the tolerance meaning (largest channel difference, 0 to 255),
and in place with nothing returned — or choose other names. Recommendation: as above; they read as plain English and
say what happens.
