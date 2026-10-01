# Sprint 7 — Reviewer's guide

For the maintainer, before closing Sprint 7. Budget: about an hour.

**The claim:** funground now loads, tints, changes and filters pictures, runs DrawBot-style scripts,
and has p5's drawing modes, colour mode and colour numbers. Nothing that existed before changed
except the approved v0.5 colour change (D-032), and CI is green on all 12 cells.

## 1. Try it (20 minutes)

```powershell
.venv\Scripts\python tools\gallery_browser.py
```

Browse to **Pictures and images** and run each of its four examples. Then try **Colour → Colour
mode** and **Shapes → Placing shapes**.

Then write a five-line script in any folder and run it:

```py
import funground as f
f.size(400, 300)
f.color_mode("hsb")
f.fill(200, 80, 90)
f.circle(200, 150, 150)
f.show()
```

Load one of your own phone photos with `f.load_image("photo.jpg")` in a script and `f.show()` it.
It should be the right way up.

## 2. Verify the claim (10 minutes)

```powershell
.venv\Scripts\python -m pytest -o addopts="" -q          # expect: 1116 passed
git diff -M --diff-filter=MD 85fa41b..HEAD -- tests/golden tests/snapshots docs/gallery/images docs/reference/images   # expect: empty
gh run list --repo funground-hq/funground --limit 1      # expect: success
```

## 3. Read (20 minutes)

- `docs/design/Decision_Log.md`, D-027 to D-035. D-035 and the smaller review calls were decided by
  Claude under D-034. Say if you disagree with any of them.
- `docs/design/Semantic_Contract.md`:
  - rows R13–R15 (scripts);
  - P4–P10 (images, pixels, filters);
  - F10 (drawing modes);
  - S15–S16 (colour mode, grey numbers).
- `docs/guide/09_paths_and_clipping.md`, from "Pictures and images" to the end. Is it clear to a
  beginner?
- `docs/guide/14_coming_from_p5_processing.md`. Three "deliberate differences" are gone, because
  funground now matches p5.

## 4. Things I would flag

1. **The v0.5 change (D-032):** `fill`, `stroke` and `background` now take `(color, *more)`, and a
   bare number is grey. Any old code that relied on packed-integer colours would change colour.
   None of ours did.
2. **Known limits are pinned, not fixed:**
   - half-transparent `set` colours can read back a unit or two off;
   - in PDF/SVG, transparent `set` cannot erase, and tinted pictures are embedded as pixels;
   - `full_screen()` at the top of a script opens a window.
3. **The gallery browser is in `tools/`,** not in the installed package. Learners who `pip install`
   funground won't have it until the examples ship too, which is a question for the release.
4. **A sub-agent killed all `python.exe` processes once** (S-076). The rule against it is now in the
   builder instructions.

## 5. Sign-off checklist

- [ ] Gallery browser tried; image examples run; one of your own photos loads upright
- [ ] The script example above works
- [ ] Suite green; checkpoint diff empty; CI green
- [ ] D-035 and the review calls under D-034 acceptable
- [ ] Review and retrospective read
- [ ] Sprint 7 closed
