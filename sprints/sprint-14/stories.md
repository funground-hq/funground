# Sprint 14 — release 0.1: seeing sound (music for teaching)

**Dates:** planned 3 Oct 2026 (D-056); opened 4 Oct 2026 after Sprint 13's sign-off. The release (S-073) follows this sprint.
**Decisions:** D-061 analysis and drawing API, D-062 raga API (Claude, D-034); D-063 capstones (maintainer).

**Goal:** funground's strength is drawing, so make sound visible. Learners see waves, pitch, notes, chords, beats and
ragas, and build the teaching scenarios of `docs/design/Music_Research_Note.md` §5 that pure Python can do.

**Rules:**
- pure Python, no new dependency;
- each scenario is a gallery example in a new `music/` area and a section of a new guide chapter;
- contract rows are pinned before building.

## Story set

### S-111 Seeing sound — E-17 *(D-061; contract A7)*
- [ ] Drawing helpers for analysis results: wave view (`samples`), spectrum bars, a scrolling pitch line, a spectrogram picture. Decide which are library functions and which are just examples

### S-112 Onsets and tempo — E-17 *(D-061; contract A5)*
- [x] `sound.onsets()` (spectral flux), `sound.tempo()` (beats a minute), the beat times; "tap along" example

### S-113 Chroma, key and chords — E-17 *(D-061; contract A6)*
- [x] `sound.chroma()` (12 pitch classes), chord name for a moment (major, minor, seventh templates), key of a whole sound; "see a chord" example

### S-114 Teaching scenarios — E-22
- [ ] Gallery `music/` and guide chapter: draw a wave and hear it; compose and save; tuner (microphone + `pitch`); ear training; see a chord; tap along; piano roll of a composed tune
- [ ] Ragas: sing with a drone (tanpura made with `tone`/`pluck`, a pitch line against Sa and Pa); a swara histogram; compose in a raga from its aroha and avaroha (a small raga table)

### S-115 Ragas for learners — E-17 *(D-057, D-062; contract A8)*
- [ ] Synthesis:
  - a tanpura drone;
  - meend (glides between swaras) and a simple gamaka in `melody`;
  - a tala sequencer (teentaal, rupak, …) with simple synthesised percussion and bol names;
  - a small raga table (thaat, aroha/avaroha, vadi/samvadi, pakad) that drives examples.
- [ ] Analysis:
  - a pitch contour against Sa;
  - a tonic (Sa) estimate;
  - a swara histogram;
  - a basic raga match of a recording or the learner's singing against the table, histogram-based, with its limits stated.
- [ ] Teaching:
  - a gallery `music/` raga set;
  - a guide chapter section written for learners of Indian music;
  - sources checked as in `Music_Research_Note.md`.

### S-117 Project capstones — E-22 *(D-063; `docs/backlog/Project_Ideas.md`)*
- [ ] A `projects/` gallery area and a Projects guide chapter, each project in stages (make it work, make it yours, make it shine), with challenge cards:
- **Music and sound:** 1 Raga explorer. It uses S-115 and is the most distinctive.
- **Design and print:** 10 Event poster series.
- **Games and interactive:** 16 Voice-controlled game.
- **Generative art:** 19 Rangoli and mandala generator.

## Not in 0.1
Piano roll or transcription from a recording (needs machine learning); real-time synthesis (ADR-003/006).
