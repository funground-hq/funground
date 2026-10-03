# Sprint 13 — Reviewer's guide

For the maintainer. Budget: about 40 minutes, mostly hands-on.

**What this sprint claims:**
- funground makes music: tones, notes, melodies and sargam with Sa and just tuning.
- It listens through the microphone.
- It saves text that stays live and editable in SVG, or as shapes for handoff.

Nothing that existed before changed.

## 1. Hands-on checks (everything only a person can do, in one place)

In the gallery browser (`python -m funground.gallery`):

1. **Sound → Write a tune:** you should hear a melody and a chord. Check the wave drawing and the note bars follow it.
2. **Sound → Sargam over a drone:** check the phrase sounds right to you (just tuning, Sa = D4) and the pitch line climbs the swara ladder.
3. **Sound → Tuner:** sing or play a note, then check the name and the sharp/flat needle. On a Mac, also check the permission prompt.
4. **Saving → A poster file:** run it, then press **O** to open the folder where it saved its files. Open:
   - `poster.pdf` in Acrobat or Illustrator: four layers, "notes" off; the text selectable and searchable;
   - `poster.svg` in Inkscape and in Illustrator: the text editable. In Illustrator, use the World-Ready Paragraph Composer for the Hindi line. Install the fonts first if you want the same look; guide chapter 13 says where they are;
   - `poster_final.svg`: identical look, letters as shapes, not editable.
5. **Gallery browser layout:** check the new "Folder" button sits well next to "Copy".

Then try a few lines of your own:

```py
import funground as f

f.melody("S R G m P D N S'", sa="C4", tuning="just").play()        # Bilawal, roughly
f.melody("C4 E4 G4 [C4 E4 G4]:2 - C5", tempo=100, wave="triangle").play()
f.pluck("A3", 2).play()
```

## 2. Verify

```powershell
.venv\Scripts\python -m pytest -o addopts="" -q          # expect: 2028 passed
git diff -M --diff-filter=MD 9d63d7a..HEAD -- tests/golden tests/snapshots docs/gallery/images docs/reference/images   # expect: empty
```

Check CI is green on all 12 cells for the latest commit.

## 3. Decide

- **D-058** (microphone API): decided by Claude under D-034. Accept or overturn.
- **Layer default style:** keep funground's defaults in a new layer, or start from the canvas's current fill and stroke?
- **`tuning="just"` without `sa`:** an error (as built), or ignore the tuning?

## 4. Sign-off checklist

- [ ] Tune, sargam and tuner sound and look right
- [ ] The poster's PDF layers and live SVG text work in real programs; the shapes copy looks identical
- [ ] Suite green; checkpoint diff empty; CI green
- [ ] D-058 acceptable; the layer-style and just-tuning questions answered
- [ ] Sprint 13 closed
