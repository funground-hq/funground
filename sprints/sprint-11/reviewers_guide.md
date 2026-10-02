# Sprint 11 — Reviewer's guide

For the maintainer, after Sprint 10's guide. Budget: about 30 minutes, plus the desktop checks
in the release checklist.

**What this sprint claims:** funground plays and analyses sound, records GIFs and MP4s, and has
sliders, checkboxes and buttons. The gallery and guide read as one finished whole for 0.1. The
package builds and installs cleanly. Nothing that existed before changed.

## 1. Try it (20 minutes, on a real desktop)

In the gallery browser (`python tools/gallery_browser.py`):
- **Sound → Visualiser.** You should hear a short tune, and the bars should move with it.
- **Interaction → Controls.** Drag the sliders, tick the checkbox and press the button. Clicks on the
  panel must not count as clicks on the canvas.
- **Documents → Flip book.** Then open the GIF it saves.
- Open `docs/gallery/SHOWCASE.md` on GitHub, or in any Markdown viewer.

Then this script, which records three seconds of an animation:

```py
import funground as f

def setup():
    f.size(300, 200)
    f.save_gif("spin.gif", 3)      # needs: pip install funground[extras]

def draw():
    f.background("ivory")
    f.translate(150, 100)
    f.rotate(f.frame_count * 3)
    f.fill("tomato")
    f.rect(-40, -40, 80, 80, 12)

f.run()
```

If ffmpeg is installed, change the line to `f.save_movie("spin.mp4", 3)` and play the file.

## 2. Verify (10 minutes)

```powershell
git push                                                   # 13 commits were waiting
.venv\Scripts\python -m pytest -o addopts="" -q            # expect: 1649 passed, 1 skipped
git diff -M --diff-filter=MD 6dca498..HEAD -- tests/golden tests/snapshots docs/gallery/images docs/reference/images   # expect: empty
```

Then check CI: all 12 cells should be green, and the real-ffmpeg test should pass where a runner has
ffmpeg.

## 3. Decide

- **D-045, ffmpeg.** I recommend B. MP4 already works with an ffmpeg on the PATH; B adds
  `pip install funground[video]` for learners who have none.
- **D-046, D-047, D-048:** decided by Claude under D-034. Accept or overturn them.
- **Release questions:** see `release_checklist.md`.
  - Should the examples and the gallery browser ship in the package?
  - The manual macOS/Linux run.
  - The PyPI account.
  - The go-ahead to publish.

## 4. Sign-off checklist

- [ ] Sound plays and analyses; controls work by hand; the GIF records
- [ ] Suite green; checkpoint diff empty; CI green on 12 cells
- [ ] Guide, Quick Reference and showcase read well
- [ ] D-045 answered; D-046, D-047, D-048 acceptable
- [ ] Sprint 11 closed (after Sprint 10)
