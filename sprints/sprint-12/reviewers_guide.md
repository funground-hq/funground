# Sprint 12 — Reviewer's guide

For the maintainer. Budget: about 30 minutes, most of it the hands-on checks that CI cannot do.

**What this sprint claims:**
- Emoji, Hindi and symbols draw with the bundled fallback fonts.
- Layers persist on screen and become real layers in PDF and SVG files.
- Text can become points, and fonts can be asked about.
- `erase()` cuts holes.
- `python -m funground.gallery` shows every example from the installed package.
- Nothing that existed before changed.

## 1. Try it (20 minutes)

```powershell
.venv\Scripts\python -m funground.gallery              # the browser, from the package itself
```

- Open **Text → Fallback**, **Text → Text dots**, **Compositing → Layers** and **Compositing → Scratch card**.
- In any example, press **C**, then check that the example and its data files were copied into the current folder.

Then run this script, and open `layers.pdf` in Acrobat or Illustrator and `layers.svg` in Inkscape. Each should show three
layers, with "notes" switched off:

```py
import funground as f

f.size(400, 260)
f.background("ivory")
with f.layer("sky"):
    f.no_stroke(); f.fill("lightskyblue"); f.rect(0, 0, 400, 130)
with f.layer("ground"):
    f.fill("olivedrab"); f.rect(0, 130, 400, 130)
with f.layer("notes"):
    f.fill("black"); f.text_size(20); f.text("Hello नमस्ते 👋", 20, 20)
f.hide_layer("notes")
f.save("layers.pdf")
f.save("layers.svg")
f.show()
```

## 2. Verify (5 minutes)

```powershell
.venv\Scripts\python -m pytest -o addopts="" -q          # expect: 1829 passed
git diff -M --diff-filter=MD 0c5195c..HEAD -- tests/golden tests/snapshots docs/gallery/images docs/reference/images   # expect: empty
```

Check that CI is green on all 12 cells for the latest commit.

## 3. Decide

- **D-050 and D-051:** decided by Claude under D-034. Accept or overturn them.
- **Erase and images:** in funground, `image()` erases by its alpha; p5 ignores erase for images. Keep the difference?
- **The layer PDF in a real viewer:** do the layers appear and switch on and off as expected?

## 4. Sign-off checklist

- [ ] Fallback text, layers, dots and scratch card look right; the gallery runs from the package; copy works
- [ ] The layered PDF and SVG show named layers in a real program, with "notes" off
- [ ] Suite green; checkpoint diff empty; CI green on 12 cells
- [ ] D-050, D-051 and the erase difference acceptable
- [ ] Sprint 12 closed
