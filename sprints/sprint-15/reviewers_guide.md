# Sprint 15 — Reviewer's guide

For the maintainer. Budget: about 40 minutes, mostly trying projects and reading a few guide pages.

**What this sprint claims:** funground is easy to learn from. Every example explains itself; the guide is a
path with exercises, an errors page and a glossary; there are eight projects with their own pages; the
developer docs match the code.

## 1. Hands-on (`.venv\Scripts\python -m funground.gallery`)

**Projects** (top of the sidebar):

1. **Voice game.** The setup screen comes first. Stay quiet for a second, then say "aaah" softly and
   loudly. Move the marks with the arrow keys or sliders until the practice bird feels right. Enter to
   play. S on the ready or game-over screen returns to setup. Does it feel right now?
2. **Typographic portrait.** Move the cell-size slider; change letters (try the Devanagari word); invert;
   save a PDF and open it with **O**.
3. **Kinetic type.** Move the mouse through the word. Press Enter, type a word, Enter. Press G to record a
   GIF and open it.
4. **Scratch card.** Scratch with the mouse held down. Are the chimes pleasant? Press N for new cards
   (cards 1, 3 and 4 win).
5. **Flow-field print.** Try the sliders and R; press P and open the A3 PDF.
6. **Event posters.** Type a headline, toggle layers, save the SVG pair.

**Explanations:** pick any three examples in other areas and read their **Explain** tab (E).

## 2. Read

7. `docs/guide/README.md`: does the learning path make sense to you?
8. `docs/guide/errors.md`: skim; is anything a learner meets missing?
9. `docs/guide/glossary.md`: especially the Indian-music terms.
10. `docs/guide/18_projects.md` and one project page, for example `projects/07_scratch_card.md`.
11. One chapter's "Try it" section, for example chapter 3 or 10.

## 3. Optional

- `docs/developer/Architecture.md`: the new subsystem sections and the two invariants.
- `docs/design/README.md`: the index of design notes.

## 4. Questions

See "Questions for the maintainer" in `review.md`: hiding the voice game's sliders, splitting chapter 9,
and the open Sprint 14 sign-off.
