# Sprint 10 — Reviewer's guide

For the maintainer, before you close Sprint 10. Budget: about 30 minutes.

**What this sprint claims:**
- Text can be tracked, styled with OpenType features, set in variable fonts, and mixed in one
  string.
- `rect` can round its corners.
- SVG files load as vector drawings.
- **PDFs now carry real text** that you can select, search and copy, and they look the same as before.

Nothing that existed before changed, apart from one snapshot that had recorded a bug.

## 1. Try it (15 minutes)

In the gallery browser (`python tools/gallery_browser.py`):
- **Shapes → Rounded corners**
- **Text → Tracking and features** and **Text → Formatted text**
- **Images → SVG drawings**

Then run this script and open `card.pdf` in Chrome, Edge or Acrobat. Select the text, search for
"office", and copy a line:

```py
import funground as f

f.size(420, 220)
f.background("ivory")
f.fill("navy")
f.text_size(26)
f.text("An office for difficult fish", 20, 30)
s = f.FormattedString()
s.append("Bold ", style="bold", color="tomato")
s.append("and plain, in one line", color="black")
f.text(s, 20, 90)
f.rotate(8)
f.fill("seagreen")
f.text_tracking(4)
f.text("Turned and tracked", 40, 140)
f.save("card.pdf")
f.show()
```

The text in the PDF should be real, and it should look as it does in the window.

Then read `docs/developer/README.md` and one design note, for example
`docs/design/PDF_Text_Note.md`. Do they explain the code well enough for a new contributor?

## 2. Verify (10 minutes)

```powershell
.venv\Scripts\python -m pytest -o addopts="" -q          # expect: 1518 passed
git diff -M --diff-filter=MD 15e35c3..HEAD -- tests/golden tests/snapshots docs/gallery/images docs/reference/images
# expect: only tests/snapshots/gallery/images-04_filters.json (picture names shift by one; review finding 3)
```

GitHub was unreachable when the last commits were made. Check that `git status` says the branch
is up to date with `origin/main`, then check that CI is green on all 12 cells.

## 3. Decide

- **D-042, D-044:** decided by Claude under D-034. Accept them or overturn them.
- **Review fixes:** stroke width keeps fractions, and picture names no longer repeat. Both
  restore the contract. Are you happy for them to be bug fixes rather than v0.5 changes?
- **PDF text limits:** accept the known limits for 0.1, or ask for the `0 Tr` follow-up first.
  - Rectangular letters can look one device pixel heavier in Chrome and Edge.
  - Acrobat, Preview and Firefox are untested.
- **Layers (S-095/S-096):** after 0.1, as planned, or pull S-095 into Sprint 11?

## 4. Sign-off checklist

- [ ] The gallery examples and the script above work; the PDF text selects, searches and copies
- [ ] The suite is green, the checkpoint diff is as described, and CI is green
- [ ] Developer docs and design notes read well
- [ ] D-042 and D-044 are acceptable
- [ ] The PDF text limits are accepted, or a follow-up is requested
- [ ] Sprint 10 closed
