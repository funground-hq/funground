# Sprint 9 — Reviewer's guide

For the maintainer, before closing Sprint 9. Budget: about 20 minutes.

**The claim:** funground paths can now be combined, cleaned, outlined, measured, tested and
moved, and text can become a path. All of it uses exact curves, through one new library
(skia-pathops). Nothing that existed before changed.

## 1. Try it (10 minutes)

In the gallery browser (`python tools/gallery_browser.py`):
- **Paths and clipping → Combining shapes:** union, intersection, difference, xor, remove overlap.
- **Paths and clipping → Outlines, tests and moving paths.**
- **Text → Letters as shapes.**

Then this script:

```py
import funground as f

f.size(400, 300)
f.background("white")
f.text_size(90)
word = f.text_path("HOLE", 40, 80)               # the letters at the current text size
card = f.path().rect(20, 40, 360, 160)
f.fill("tomato")
f.draw_path(card - word)                         # the letters cut out of the card
f.show()
```

## 2. Verify (5 minutes)

```powershell
.venv\Scripts\python -m pytest -o addopts="" -q          # expect: 1286 passed
git diff -M --diff-filter=MD bd35897..HEAD -- tests/golden tests/snapshots docs/gallery/images docs/reference/images   # expect: empty
```

## 3. Decide

- **D-038 and D-039:** decided by Claude under D-034. Accept or overturn them.
- **Rounded corners:** should `f.rect(x, y, w, h, radius)` and `f.square(x, y, s, radius)` take an
  optional corner radius, as p5's do? That changes two frozen v0.5 signatures by adding an optional
  argument; old code keeps working.

## 4. Sign-off checklist

- [ ] Gallery examples and the script above work
- [ ] Suite green; checkpoint diff empty
- [ ] D-038, D-039 acceptable
- [ ] Rounded corners: yes / no / later
- [ ] Sprint 9 closed
