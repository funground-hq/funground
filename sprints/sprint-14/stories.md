# Sprint 14 — release 0.1: seeing sound (music for teaching)

**Dates:** planned 3 Oct 2026 (D-056); starts after Sprint 13's features. The release (S-073) moves after this sprint.

**Goal:** funground's strength is drawing, so make sound visible. Learners see waves, pitch, notes, chords, beats and
ragas, and build the teaching scenarios of `docs/design/Music_Research_Note.md` §5 that pure Python can do.

**Rules:**
- pure Python, no new dependency;
- each scenario is a gallery example in a new `music/` area and a section of a new guide chapter;
- contract rows are pinned before building.

## Story set (contract rows to pin per story)

### S-111 Seeing sound — E-17
- [ ] Drawing helpers for analysis results: wave view (`samples`), spectrum bars, a scrolling pitch line, a spectrogram picture. Decide which are library functions and which are just examples

### S-112 Onsets and tempo — E-17
- [ ] `sound.onsets()` (spectral flux), `sound.tempo()` (beats a minute), the beat times; "tap along" example

### S-113 Chroma, key and chords — E-17
- [ ] `sound.chroma()` (12 pitch classes), chord name for a moment (major, minor, seventh templates), key of a whole sound; "see a chord" example

### S-114 Teaching scenarios — E-22
- [ ] Gallery `music/` and guide chapter: draw a wave and hear it; compose and save; tuner (microphone + `pitch`); ear training; see a chord; tap along; piano roll of a composed tune
- [ ] Ragas: sing with a drone (tanpura made with `tone`/`pluck`, a pitch line against Sa and Pa); a swara histogram; compose in a raga from its aroha and avaroha (a small raga table)

## Not in 0.1
Piano roll or transcription from a recording (needs machine learning); real-time synthesis (ADR-003/006).
