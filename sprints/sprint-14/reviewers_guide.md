# Sprint 14 — Reviewer's guide

For the maintainer. Budget: about 45 minutes, mostly listening and playing. Every hands-on check is in one list.

**What this sprint claims:**
- Funground makes sound visible: waves, spectra, pitch lines, beats, chords and keys.
- It teaches ragas and talas from a cited table.
- Its generated sound is pleasant.
- Learners have four project capstones and four new teaching examples.

## 1. Hands-on (`python -m funground.gallery`)

**Listening:** does it sound pleasant now?
1. Music → **Hear a raga**: pick a few ragas with the arrow keys.
2. Sound → **Sargam over a drone**: also check the pink pitch line now follows only the phrase.
3. Sound → **Write a tune**.

**Seeing sound:**

4. Music → **Tap along**: the light should flash on the beat.
5. Music → **See a chord**: the chord names should be right.
6. Music → **A song's fingerprint**.
7. Music → **See your voice**: speak or sing.

**Ragas:**

8. Projects → **Raga explorer**: listen to Yaman and Bhupali; then press *sing*, sing a few swaras, stop, and look at the match bars. Use headphones so the drone does not reach the microphone.
9. Music → **Tala**: teentaal and rupak. Do the bols and claps look right to you?
10. Skim `funground/data/ragas.json` and `docs/guide/17_ragas_and_talas.md`. You, or a music teacher, are the best check of the data.

**Projects and teaching:**

11. Projects → **Voice game**: say "aaah" to fly; the space bar works too. Does the feel need tuning?
12. Projects → **Event posters** and **Rangoli**: press S in the rangoli to save, then **O** to open the folder.
13. Music → **Draw a wave**, **Compose and save**, **Ear training**, **Piano roll**.

**Telugu:** try this in a script:
```py
import funground as f
f.size(400, 120); f.background("white"); f.fill("black"); f.text_size(36)
f.text_fallback(f.system_font("Nirmala UI"))
f.text("నమస్తే తెలుగు  தமிழ்  বাংলা", 10, 30)
f.show()
```

## 2. Verify

```powershell
.venv\Scripts\python -m pytest -o addopts="" -q          # expect: 2338 passed
```

Then check that CI is green.

## 3. Decide

- **D-061, D-062, D-064:** decided by Claude under D-034. Accept or overturn.
- **More bundled Indian-script fonts?** For example Telugu, Tamil, Bengali and Kannada, each 0.2–0.5 MB. Or leave it to `system_font` and downloads.
- **Melody legato:** keep full overlap, or use a lighter cross-fade?

## 4. Sign-off checklist

- [ ] Sound is pleasant in the three listening examples
- [ ] Pitch trace, tap along, chords and fingerprint look right
- [ ] Raga explorer and tala work; the raga data looks right to you
- [ ] Projects and teaching examples work
- [ ] Telugu renders through Nirmala UI
- [ ] D-061, D-062 and D-064 acceptable; the font and legato questions answered
- [ ] Sprint 14 closed
