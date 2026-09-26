# Sprint 5 — Reviewer's guide

For the maintainer reviewing Sprint 5 before closing it. Budget: about an hour. The sprint's
claim: **62 new learner-facing names, each with a contract row or semantic test, a gallery
example and a guide section; nothing that existed before changed except the two renames you
approved (D-016, D-018); every public name appears in the gallery.**

Diff under review: `git diff 980a056..HEAD -- playground` (14 files, +1 409 / −67).
Tests: `git diff 980a056..HEAD -- tests` (mostly new goldens and snapshots).
Documents: `git diff 980a056..HEAD -- docs sprints examples`.

## 1. Verify the claim first (10 minutes)

```powershell
.venv\Scripts\python -m pytest -o addopts="" -q                         # expect: 506 passed
git diff --stat --diff-filter=MD 980a056..HEAD -- tests/golden tests/snapshots docs/reference/images   # expect: empty
git grep -n "import cairo\|import pygame" -- playground | findstr /v "platform/ renderers/"             # expect: only playground/export/__init__.py
.venv\Scripts\python tools\make_gallery.py                               # then `git status`: expect nothing changed
.venv\Scripts\python examples\gallery\interaction\02_paint.py            # real window: drag to paint, wheel changes brush, r/g/b colour, c clears, right-click dots
.venv\Scripts\python examples\gallery\animation\04_pause.py              # starts paused; space runs/pauses, s steps one frame, q quits
.venv\Scripts\python examples\gallery\randomness\03_noise.py           # noise-driven drawing, identical on every run
```

Then read `docs/gallery/README.md` top to bottom, which lists every example with its picture. It is the sprint's showcase, and only you can
judge whether a beginner would learn from it.

## 2. Commits in reading order

| Commit | Story | Read | Why |
|---|---|---|---|
| 058bf03, 3b4a1a2 | S-068, S-069 | `tools/make_gallery.py`, `tests/test_gallery.py`, `tests/test_guide.py` | The machinery every later story relies on |
| f3ccf92 | S-041 | `sketch.py` shape verbs | Straightforward; check `arc` modes |
| 2365056 | S-042 | `sketch.py` `_stroke_op`, `cairo2d.py` | New style fields are omitted from snapshots when default, which is why old snapshots stayed identical |
| e2b1e72 | S-074 | `shapes.py` | Catmull-Rom maths and contour winding: the densest new code |
| e6aea81 | S-047 | `noise.py` | A literal port; compare against p5's `noise()` if you want |
| fae806e | S-048 | `sketch.py` run loop | The loop changed shape: draw runs when looping, after `redraw()`, or on frame 0 |
| 6a236c2 | S-044 | `color.py` | Colour objects and HSB/HSL conversions |
| 3ffbcb6 | fix | `export/__init__.py`, `_flush_saves` | PNG now saves the pixels on screen |
| f034a6e | S-045 | `platform/*.py`, `_dispatch_events` | Events: the one area touching the OS layer |
| a16eed2, 65c17c1 | D-019, S-058 | docs only | Release renumbering; ADR-003 |

## 3. What changed — the map

| Area | Files | New |
|---|---|---|
| Vocabulary | `sketch.py`, `api.py`, `shapes.py`, `geometry.py` | shapes, strokes, matrix, curves |
| Colour | `color.py` | `hsb`, `hsl`, `color`, `lerp_color` |
| Helpers | `noise.py`, `sketch.py` | maths, noise, clock |
| Loop and input | `sketch.py`, `platform/base.py`, `headless.py`, `pygame_platform.py` | loop control, events, callbacks |
| IR and renderer | `ir.py`, `cairo2d.py` | stroke style fields, `SetAntialias` |
| Teaching material | `examples/gallery/`, `docs/gallery/`, `docs/guide/` | 31 examples, 13 chapters |

## 4. What to scrutinise

- **`sketch.py` run loop.** `max_frames` now counts loop iterations, not drawn frames, so a
  paused sketch still ends. Check that this reads naturally.
- **`_dispatch_events`.** Callbacks run after input sampling and before `draw()`, so a callback
  sees this frame's mouse position. `mouse_clicked` fires on release; `key_typed` only for
  printable single characters.
- **`playground/__init__.py` `_RENAMED`.** Old names raise an error naming the new one. Try
  `p.mouse_pressed` in a sketch and read the message as a learner would.
- **`pygame_platform.py` key tracking.** Held keys come from key events and are cleared when the
  window loses focus. Alt-tab while holding an arrow key to see it.
- **`noise.py`.** Pure Python; the speed note is in the guide's chapter 11.

## 5. Things I would flag

1. **Input examples look blank in the gallery.** A headless render has no mouse, so the paint
   example shows only its status bar.
2. **PDF/SVG saves are still one frame.** PNG is now what is on screen; vector files are not and
   cannot be without recording every frame. The guide says so in chapter 13.
3. **HiDPI on macOS and Linux is still unverified** on real hardware.
4. **CI has never run.** Every count here comes from one Windows machine.

## 6. Open decisions

- **D-020 PyPI distribution name.** Presented in `sprints/sprint-06/stories.md`; needed before the
  release story, not now.

## 7. Sign-off checklist

- [ ] Suite green on your machine (506)
- [ ] Session-1 goldens, snapshots and reference images unchanged
- [ ] Gallery index read; examples make sense to a beginner
- [ ] Paint and pause examples tried in a real window
- [ ] Old-name error messages (`p.mouse_pressed`) read well
- [ ] Review and retrospective read
- [ ] Sprint 5 closed
