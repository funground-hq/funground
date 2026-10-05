# Sprint 15 — release 0.1: documentation, examples and projects

**Dates:** planned 4 Oct 2026 (D-065), after Sprint 14's features. The release (S-073) follows this sprint.

**Goal:** the documentation, user guide and examples are solid for 0.1. Every example and project
explains:
- **what it shows**;
- **how the core mechanics work**;
- **ideas to extend it**.

More capstone projects are added.

**Rules:**
- no new library features (fixes only);
- learner-facing text in plain English with British spelling;
- every code block still runs (guide tests), and every example is still original and CC0 (originality check).

## Story set

### S-120 Every example explains itself — E-22
- [x] S-120.1 A pilot on four examples, to fix one standard for an example's docstring, shown by the gallery browser and the gallery index:
  - a title line;
  - **What you see**;
  - **How it works** (the core mechanics in 3–6 points, naming the funground functions and the idea behind them);
  - **Make it yours** (3–5 extension ideas, from easy to harder).
- [x] S-120.2 Apply it to all 83 examples, area by area. A test enforces the three sections.
- [x] S-120.3 The gallery browser's detail view and `docs/gallery/README.md` show the three sections.

### S-121 More projects — E-22 *(from `docs/backlog/Project_Ideas.md`)*
- [x] Four more capstones, each a gallery example plus its own guide page:
  - 12 Typographic portrait;
  - 13 Kinetic type;
  - 15 Scratch-card reveal game;
  - 18 Flow-field print.

  Each page has **how it works**, three stages (make it work, make it yours, make it shine) and challenge cards.
- [x] Chapter 18 becomes an index of project pages, `docs/guide/projects/*.md`, one page per project, with the existing four moved there and each given a "How it works" section.

### S-122 The user guide, solidified — E-22
- [x] A full read-through for consistency, flow, cross-links between chapters, the gallery and the Quick Reference, and stale text.
- [x] Each chapter ends with a short "Try it" exercise or two.
- [x] A new page, "When something goes wrong": the common errors, what they mean and how to fix them, written from funground's own error messages.
- [x] A glossary of terms: sketch, frame, picture, layer, path, swara, …
- [x] The guide README becomes a learning path (beginner → intermediate → projects).

### S-123 Developer docs refreshed — E-23
- [x] `docs/developer/Architecture.md` covers the sound, analysis, raga, layers, text-in-files and gallery-package modules added in Sprints 11–14.
- [x] Design-note index; `Adding_a_feature.md` and `Testing.md` re-checked against the code.

### S-125 API reference from docstrings — E-23 *(added 5 Oct, D-066)*
- [ ] Every public function and live value, and the public methods of the objects funground returns (sounds, microphones, pictures, snapshots, vectors, paths, shapes, fonts, formatted strings, controls), has a structured docstring, so `help(f.circle)` is useful.
- [ ] `tools/make_api_reference.py` generates `docs/reference/API.md` from the code, grouped like the Quick Reference, with reference tables for constants and fixed words (colours, blend modes, keys, page sizes, waves, ragas and talas, file formats). A test checks every docstring and that the page is current.

### S-126 Documentation collection — E-23 *(added 5 Oct, D-066)*
- [ ] `docs/README.md` is the front door to all documentation: start here, guide, projects, gallery, Quick Reference, API reference, errors, glossary, comparison, developer and design docs.
- [ ] A note, `docs/reference/Compared_with_p5_and_DrawBot.md`: what funground shares with p5 and DrawBot, where it differs, and why.

### S-073 Release 0.1 — E-02 *(carried)*
- [ ] `sprints/sprint-11/release_checklist.md` and `docs/developer/Releasing.md`
