# Sprint 8 — Reviewer's guide

For the maintainer, before closing Sprint 8. Budget: about 20 minutes.

**The claim:** a script can now make a document of several pages of any size, save it as one PDF,
and show it with the pages flipping under the arrow keys. Nothing that existed before changed.

## 1. Try it (10 minutes)

Save this as `booklet.py` in any folder and run it:

```py
import funground as f

f.new_page("A5")
f.background("ivory")
f.fill("navy")
f.text_size(40)
f.text("Page one", 40, 60)

f.new_page("A5Landscape")
f.background("gold")
f.fill("black")
f.text("Page two, landscape", 40, 60)

f.save("booklet.pdf")
f.show()          # Left / Right flip the pages, Esc closes
```

Open `booklet.pdf`: two pages, the second landscape. Also open the gallery browser and look at
**Documents and pages**.

## 2. Verify (5 minutes)

```powershell
.venv\Scripts\python -m pytest -o addopts="" -q          # expect: 1166 passed
git diff -M --diff-filter=MD 675e889..HEAD -- tests/golden tests/snapshots docs/gallery/images docs/reference/images   # expect: empty
```

## 3. Read (5 minutes)

- `docs/design/Semantic_Contract.md` rows R14 (the full-screen and memory sentences), R16, R17, D1.
- `docs/design/Decision_Log.md` D-036 (decided by Claude) and **D-037 (pending, yours)**.
- `docs/guide/13_saving_your_work.md`, "Documents and pages".

## 4. Sign-off checklist

- [ ] The booklet script works; the PDF has both pages at their sizes
- [ ] Suite green; checkpoint diff empty
- [ ] D-036 acceptable
- [ ] D-037 answered (needed before Sprint 9)
- [ ] Sprint 8 closed
