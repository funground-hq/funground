# Spike S-227: help for the cut-out (tidy mask, editable outline, edges)

Evidence for D-115. S-218 shipped `remove_color` and `remove_background`. Their cut-out leaves **specks** (bits of the
room that look like you) and **holes** (bits of you that look like the room). This spike measures three helps. It builds
a prototype and measures it. It does not recommend; that is for the main session.

Everything is in this folder. Nothing outside it was changed. Run order:

```
FUNGROUND_HEADLESS=1 .venv/Scripts/python spikes/14_cutout/make_photos.py     # scenes/  (already made)
FUNGROUND_HEADLESS=1 .venv/Scripts/python spikes/14_cutout/measure.py         # results.json, out/*.png, about 1 minute
FUNGROUND_HEADLESS=1 .venv/Scripts/python spikes/14_cutout/check_editor.py    # runs the demo headless, simulates one drag
```

## Questions and pass criteria (fixed before the work)

| | Question | Pass |
|---|---|---|
| (a) | Tidy the mask: keep the largest connected part, fill its holes, with `pygame.mask`. | Removes the specks S-218 leaves, **under 5 ms at 640 x 480** (median of 50 runs, not counting the conversion to and from the mask, which is timed and reported separately). |
| (b) | Editable outline: `Mask.outline()` of the tidied mask, thinned (Ramer-Douglas-Peucker, pure Python) to **at most 200 points**, drawn as an `f.path()`; the learner drags a point; the path cuts the picture out with `clip`. | A demo sketch **under 60 lines** (not counting the prototype module) does this, and the outline's fit is measured. |
| (d) | Edges: move each outline point to the strongest edge within a few pixels along the outline's normal. | Optional (D-115). Report only whether it improves the fit, and by how much. |

## Method

**Photos** (`make_photos.py`, original, drawn with pygame, CC0; `scenes/`). Three scenes at 640 x 480. Each has an empty
room shot (`*_empty.jpg`), a person shot (`*_person.jpg`) and the true mask (`*_truth.png`, from the shapes drawn, with a
2 x 2 supersample for soft edges). Made hard on purpose:

- per-pixel noise (about +-8 per channel, different in the two shots), a lighting change on the person shot (+3, up to +9
  on the right), and a JPEG round trip (the files are the round-tripped JPEG);
- a soft shadow: `plain_wall` has one on the wall beside the person and one on the floor, both **attached** to the body;
  `striped_wall` has a big one **detached** on the wall to the right; `busy_background` has a faint one;
- clothes close to the wall: `plain_wall` has a pocket and a collar band in the wall's colour, and the stripes of
  `striped_wall` are repeated on the trousers (so the legs vanish); `busy_background` has a thin raised arm (16 pixels
  wide) and a moved book and a rolled ball (specks far from the person).

**Moving take.** 30 frames of the person walking across `plain_wall`, fresh noise and a light flicker in every frame, made
in memory (`make_take`), as a stand-in for a camera.

**Stages**, each measured against the truth:

1. **S-218**: `picture.remove_background(empty, tolerance=...)`, the real funground method.
2. **(a) tidy**: `cutout.tidy(mask)`: `Mask.connected_component()` (the largest part), then the holes are filled by
   flooding the outside from a one-pixel frame (`Mask.erase`, `connected_component((0, 0))`) and taking everything the
   flood did not reach. All C. An option `at=(x, y)` keeps the part under a pixel instead of the largest (a click on
   yourself); it is reported as `@click`.
3. **(b) outline**: `Mask.outline()` thinned to at most 200 points by Ramer-Douglas-Peucker order (one pass records how
   far each point was from its chord; keep the 198 biggest, plus two end points). Drawn and cut out with funground's own
   `f.path().polygon(points)` and `Picture.mask` (public API only).
4. **(b)+(d) snapped**: each point moves along the outline's normal, up to 4 pixels, to the strongest brightness change
   (measured over 2 pixels, on a lightly blurred grey copy of the photo). Same idea as `filter("edges")`, but evaluated
   at the 200 points only.

Tolerances: 30 (the default), 50 (what the docs tell a learner to raise to) and 15 (below the lighting change plus noise;
a stress case). Timings are the median of 50 runs (10 for the slower conversion back to a picture and for the snapping)
on the maintainer's Windows machine, pygame-ce 2.5.8, Python 3.14. IoU is intersection over union of the person's
pixels. FP is pixels kept that are not the person (specks and shadow). FN is person pixels lost (holes). Parts is the
number of connected parts of the mask.

## Results (tolerance 30 and 50; the full table, with 15 and `@click`, is `out/table.txt` and `results.json`)

"ms" is the stage's own time. For (a) it is `tidy(mask)` alone.

| scene | tol | stage | IoU | FP | FN | parts | ms | points |
|---|---|---|---|---|---|---|---|---|
| plain_wall | 30 | S-218 | 0.690 | 11829 | 3883 | 47 | 16.1 | |
| plain_wall | 30 | (a) tidy | 0.731 | 11409 | 2092 | 1 | 2.1 | |
| plain_wall | 30 | (b) outline | 0.731 | 11249 | 2220 | 1 | 5.4 | 200 |
| plain_wall | 30 | (b)+(d) | 0.741 | 11364 | 1637 | 1 | 22.4 | 200 |
| plain_wall | 50 | S-218 | 0.284 | 4069 | 26607 | 152 | 29.4 | |
| plain_wall | 50 | (a) tidy | 0.290 | 3059 | 26662 | 1 | 3.5 | |
| plain_wall | 50 | (b) outline | 0.290 | 3045 | 26634 | 3 | 12.2 | 200 |
| plain_wall | 50 | (b)+(d) | 0.296 | 2811 | 26449 | 4 | 52.5 | 200 |
| striped_wall | 30 | S-218 | 0.478 | 20103 | 10653 | 234 | 29.6 | |
| striped_wall | 30 | (a) tidy (largest) | 0.000 | 17265 | 38777 | 1 | 3.6 | |
| striped_wall | 30 | (a) tidy (@click) | 0.564 | 503 | 16636 | 1 | 3.9 | |
| striped_wall | 30 | (b) outline | 0.000 | 17292 | 38777 | 5 | 8.3 | 200 |
| striped_wall | 30 | (b) outline @click | 0.563 | 382 | 16723 | 1 | 6.7 | 200 |
| striped_wall | 30 | (b)+(d) | 0.000 | 17392 | 38777 | 3 | 55.1 | 200 |
| striped_wall | 30 | (b)+(d) @click | 0.560 | 338 | 16870 | 1 | 44.2 | 200 |
| striped_wall | 50 | S-218 | 0.628 | 306 | 14224 | 50 | 29.2 | |
| striped_wall | 50 | (a) tidy | 0.509 | 144 | 18958 | 1 | 1.9 | |
| striped_wall | 50 | (b) outline | 0.509 | 135 | 18977 | 1 | 2.2 | 200 |
| striped_wall | 50 | (b)+(d) | 0.505 | 214 | 19078 | 1 | 21.9 | 200 |
| busy_background | 30 | S-218 | 0.874 | 5470 | 167 | 19 | 30.2 | |
| busy_background | 30 | (a) tidy | 0.967 | 1183 | 157 | 1 | 4.4 | |
| busy_background | 30 | (b) outline | 0.978 | 574 | 293 | 3 | 15.2 | 200 |
| busy_background | 30 | (b)+(d) | 0.965 | 851 | 545 | 1 | 46.9 | 200 |
| busy_background | 50 | S-218 | 0.869 | 4540 | 1167 | 36 | 29.3 | |
| busy_background | 50 | (a) tidy | 0.958 | 505 | 1182 | 1 | 3.5 | |
| busy_background | 50 | (b) outline | 0.954 | 469 | 1363 | 1 | 14.5 | 200 |
| busy_background | 50 | (b)+(d) | 0.950 | 776 | 1217 | 2 | 40.7 | 200 |

The person is 38 777 pixels in `plain_wall` and `striped_wall` and 39 166 in `busy_background`.

**Conversions** (not counted in the 5 ms of (a)): picture to mask (`load_pixels`, then `Mask.from_surface`) 5 to 9.5 ms;
mask back to a cut-out picture (pixels written in Python and `update_pixels`) 17 to 35 ms. The path route
(`f.path().polygon(...)` drawn into a stencil, then `Picture.mask`) gives the same IoU as the pygame polygon within 0.003
(column `iou_funground_path` in `results.json`).

**Outline fit.** The 200-point polygon matches the tidied mask it was made from at IoU 0.916 to 0.999 (0.975 to 0.988 in the
busy scene; `iou_vs_tidy_mask`). IoU against the truth by number of points, `busy_background`, tol 30:
20 points 0.884, 40 0.954, 80 0.981, 120 0.978, 200 0.978, 400 0.971. Beyond about 80 points more points do not help.
The demo uses 80 because 200 handles are hard to drag.

**Moving take, tol 30, 30 frames** (median / max ms): `remove_background` 29.8 / 53.3; picture to mask 9.1 / 16.7;
**tidy 3.8 / 7.6**; outline 12.6 / 23.2. IoU median: raw 0.702, tidy 0.737, outline 0.736.

Pictures (`out/`): `<scene>_tol<tolerance>.png` is a contact sheet, left to right: the shot; S-218; (a) tidy; (b) the
outline (yellow line, red points) cutting the photo out; (b)+(d). A green checkerboard shows the see-through parts.
`<scene>_tol<tolerance>_click.png` is the same with the part chosen by a click. `take_frame*.png` are three frames of the
moving take. `editor_after_drag.png` is the demo after a simulated drag of the first point (the hand) to the top left.

- `out/plain_wall_tol30.png`: the pocket and collar holes are filled; the attached shadow stays.
- `out/striped_wall_tol30.png` and `out/striped_wall_tol30_click.png`: the "largest part" is the shadow.
- `out/busy_background_tol30.png`: the moved book and the ball are removed; the thin arm survives.

## What passed and failed

- **(a) time: pass on a quiet machine.** `tidy` median 1.9 to 4.4 ms for the nine scene and tolerance runs, 3.8 ms for the
  take (max 7.6). A first run while the machine was busy gave 5 to 9 ms for the same code, so the margin is thin on a slow
  machine. The conversion round trip is not small (5 to 9 ms in, 17 to 35 ms out), so a whole tidy step costs more than the
  5 ms. **Rerun by the main session (28 Oct, machine busier):** every quality number (IoU, FP, FN, parts) was identical;
  every time was about twice as long, S-218's own `remove_background` included (16 to 64 ms): `tidy` 4.5 to 8.7 ms, the
  take's median 6.2 ms (max 11.5). `out/table.txt` is that rerun. In both runs `tidy` cost about an eighth of
  `remove_background`, so it is cheap next to the step it follows, but under 5 ms only on a quiet machine.
- **(a) removes specks: pass for loose specks, fail for attached ones.** Parts fall from 19 to 234 to **1** in every
  case. FP falls a lot where the specks are detached: `busy_background` tol 30 from 5470 to 1183 (the moved book and the
  ball). Where the shadow touches the person (`plain_wall`) it stays: FP 11829 to 11409. Holes are filled only when
  enclosed: `plain_wall` FN 3883 to 2092 (the pocket and collar).
- **(a) failure mode: "largest part" can be the wrong part.** Two cases. In `striped_wall` tol 30 the legs and half the
  head are separate parts (the wall-coloured stripes cut them off) and the detached shadow is larger than the shirt, so the
  tidy keeps the shadow: IoU 0.000. Picking the part under a click (`at=`) gives IoU 0.564 and FP 503. Also, parts of you
  cut off by wall-coloured areas are dropped, not filled (`striped_wall` tol 50 FN rises 14224 to 18958).
- **(a) does not help a wrong tolerance.** `plain_wall` tol 50: the shirt and head vanish with the wall, and tidy keeps a
  fragment (IoU 0.290). Tidy fixes noise, not a wrong key.
- **(b) demo: pass.** `outline_editor.py` is **57 lines** in all (the file's own docstring and blank lines included). It loads a
  scene, cuts it out with `remove_background` and `tidy`, shows 80 points as red handles, drags the nearest point with the mouse
  and draws the photo clipped by the path over a new background. It ran headless as a script for 5 frames with one simulated
  press, drag and release (`check_editor.py` posts the events to the headless platform; only the first point moved; the clip
  followed). It was **not tested with a real mouse**.
- **(b) fit: pass.** 200 points reproduce the tidied mask to IoU 0.92 to 0.999. The polygon is a bit smoother than the mask and
  in the busy scene scores slightly higher against the truth than the mask (0.978 against 0.967). The outline does not
  cure what (a) got wrong: it copies it. A thin part is kept when it is connected (the arm, 16 pixels wide), but the polygon
  can pinch it, which may be why some `b_outline` rows count 3 parts.
- **(d) edges: no consistent gain.** IoU change from (b) to (b)+(d): `plain_wall` tol 30 +0.010 (FN 2220 to 1637),
  `busy_background` tol 30 -0.013, tol 50 -0.004, `striped_wall` @click tol 30 -0.003. Shadow edges and the noisy photo
  pull points off the person's edge. It also costs 22 to 80 ms per picture here (one `get_at` pair per sample, in pure
  Python, plus the grey and blur copy), against 2 to 15 ms for (b).
- **Moving take.** (a) is cheap enough per frame (median 3.8 ms), but `remove_background` itself (30 ms) and the mask
  conversion (9 ms) already use the budget of a 24 fps frame (41 ms). (b) is for a kept frame, as the design note says: the
  outline step costs 12.6 ms median and changes every frame.

## Limits

- **Synthetic photos.** Flat-coloured figures on drawn rooms, with simulated noise, light and shadow. Real photos have
  smoother colour and texture, camera white balance, and auto-exposure that moves; real results may be better or worse. The
  figures are the same shape in every scene, so the numbers do not show how outlines behave on hair or loose clothes.
- **No real camera.** Chrome's fake camera shows only a test pattern, so the 30-frame moving take stands in for the camera.
  Its frames are not compressed the way a camera stream is.
- **Browser and Play timing is unverified.** All timings are desktop pygame-ce on one Windows machine, with other programs
  running (the numbers move by 2 x between runs). pygame-ce in Pyodide, the pure Python outline thinning and the Python
  loops in the conversions were not measured there.
- One run of each of three scenes: no spread across many photos. The click for `@click` is a fixed point on the shirt.
- Pure Python for thinning (10 ms or so) and snapping; no numpy. Not tuned.

## Observations on API shape (for the main session to weigh; no recommendation here)

- Two kinds of object appear: a **mask** (pygame's, a bit per pixel) and a **point list** (the outline). A learner does not
  need to see the mask: the steps could stay on the picture, for example `me.remove_background(empty)` then a tidy option or
  step, and an outline taken from the picture's see-through part. The prototype's names are only placeholders:
  `mask_from_picture`, `tidy`, `outline_points`, `snap_to_edges`, `cut_out_with_path`.
- Tidy as a plain step is easy to explain ("keep the biggest bit, fill the gaps"). Its failure (the wrong biggest part) has
  a natural fix that is also learner-friendly: say which part is you, by a click or a point (`at=`).
- The outline as an ordinary list of `(x, y)` points fits what a learner already knows (`f.path().polygon(points)`, a list they
  can print, edit, draw and `clip` with). Nothing new is needed on `f.path`, `f.clip` or mouse events to drag a point; the
  demo uses only existing names. The number of points is a real choice (about 80 was as good as 200).
- The demo needed no `async` and no new names on `f`. A helper that returns the cut-out picture from a point list was written
  with `create_graphics`, `draw_path` and `Picture.mask`, all existing.
- Hole filling and "keep one part" are separable: filling holes alone needs no choice of part.
- (d) would be one more argument or step with no clear gain here.

## Files

- `make_photos.py`, `scenes/` (3 empty shots, 3 person shots, 3 truth masks; about 220 KB in all)
- `cutout.py` (the prototype), `measure.py`, `results.json`, `out/` (contact sheets, `table.txt`)
- `outline_editor.py` (the demo, 57 lines), `check_editor.py` (headless test of the demo)

## Review and recommendation (main session, 28 Oct)

Reviewed: the code of `cutout.py` and the demo, the contact sheets, and a full rerun of `measure.py` and
`check_editor.py` (both exit 0; quality numbers reproduced exactly). The builder's timings were from a quieter moment;
see "(a) time" above.

**Recommendation for D-115: a and b, not d.**

1. **(a) as two keywords on the existing methods**, not a new method: `g.remove_background(empty, tolerance=30,
   tidy=False, at=None)`, and the same two on `remove_color`. `tidy=True` keeps one part and fills its holes; `at=(x, y)`
   is a point on you and keeps the part there (it implies `tidy=True`). Why keywords: once `remove_background` has made a
   pixel see-through its colour is gone (alpha 0, colour 0, contract P12), so a separate `g.tidy()` afterwards could not
   fill a hole with the photo's real colour; inside the method the original pixels are still there. `at=` matters because
   "the largest part" was the wrong part in one scene of three (the detached shadow, IoU 0.000; with a click 0.564).
   Defaults keep today's behaviour, so no golden changes.
2. **(b) as `g.outline(points=80)`**: the border of the picture's visible part (its largest part) as a list of `(x, y)`,
   at most `points` long. A learner draws it with `f.path().polygon(points)`, drags points with the mouse events they
   already know, and cuts the photo out with `f.clip(...)`: the demo needs no other new name and is 57 lines. 80 by
   default because 80 points fitted as well as 200 (busy scene 0.981 against 0.978) and 200 handles crowd each other.
   For a photo or a kept frame, not live video (12 to 22 ms a frame, and the outline changes every frame).
3. **Not (d).** Snapping to edges gained at most 0.010 IoU, lost up to 0.013, and cost 22 to 80 ms.

**Before building (for the story, not for D-115):** the product version works on the picture's bytes in `imaging.py`
(already allowed to import pygame-ce, and Play already loads pygame-ce for these methods), with no Python loop per
pixel: the prototype's conversions (5 to 25 ms in, 17 to 70 ms out) are the real cost and must go. Measure it in Play
too: pygame-ce in Pyodide is unmeasured here. Thin the outline to points spread more evenly (the prototype bunches them
at the hands and head). And check it on a few real photos: these scenes are drawn.

**What this does not fix:** a wrong tolerance (tidy keeps a fragment), and parts of you that the key cut off from the
rest (the striped trousers): tidy drops them rather than joining them back. The outline is the remedy for those: drag
the points out over the lost part, since the clip shows the original photo.
