# Sprint 11 — Phase 3e: sound, motion, controls, release 0.1

**Dates:** planned 2 Oct 2026 under D-034, while Sprint 10 awaits the maintainer's sign-off. Stories
that need no open decision may start; nothing here is released before the maintainer says so.
**Release context (D-019, D-027):** the last sprint before release 0.1.

**Goal:** sound playback and analysis; GIF and MP4 export; sliders, checkboxes and buttons; the
gallery and guide completed; release 0.1 prepared (publishing itself is the maintainer's act).

**Checkpoint:** existing goldens and snapshots unchanged; each new public name has a contract row,
tests, a gallery example, a guide section and a Quick Reference entry; CI green on 12 cells. Other
tools' API names are cited with where they were checked.

**Decisions:** D-046 sound API and D-047 controls API (Claude, D-034); **D-045 ffmpeg for MP4:
pending, the maintainer's call**.

## Story set

### S-098 Sound playback — E-17 *(D-046; contract A1)*
- [x] S-098.1 `funground/sound.py` (only pygame-ce's mixer; a silent clock-driven player without a device); `f.load_sound`; the sound object
- [x] S-098.2 Tests with WAV files written by the tests; gallery `sound/` area; guide chapter (new); Quick Reference; changelog

### S-099 Sound analysis — E-17 *(D-046; contract A2)*
- [x] S-099.1 `sound.level()`, `sound.spectrum(bands)`: pure-Python FFT, cached per frame
- [x] S-099.2 Tests with generated tones (a 440 Hz tone peaks in the right band); a visualiser gallery example

### S-100 GIF and MP4 export — E-19 *(D-048; contract M1; the ffmpeg extra waits for D-045)*
- [x] S-100.1 Scripts: pages become frames (DrawBot's model); animated sketches: record a number of seconds (p5 `saveGif`)
- [x] S-100.2 GIF through Pillow (`funground[extras]`) or ffmpeg; MP4 through ffmpeg as D-045 decides

### S-101 Controls — E-30 *(D-047; contract U1)*
- [x] S-101.1 `create_slider`, `create_checkbox`, `create_button`; the panel below the canvas (platform draws it; never in the canvas or the IR)
- [x] S-101.2 Tests headless; gallery example; guide; Quick Reference; changelog

### S-072 Gallery and guide completed — E-22 *(carried from Sprint 5)*
- [ ] S-072.1 Coverage of every public name; a curated showcase page; guide chapters read through end to end

### S-073 Release 0.1 prepared — E-02
- [ ] S-073.1 Version `0.1.0`, metadata, wheel and sdist built and installed in a clean venv on three systems (CI); changelog and Quick Reference for 0.1
- [ ] S-073.2 Release checklist for the maintainer: manual macOS/Linux desktop run, ship examples or not, publish. **Publishing is the maintainer's act**

## Out of scope this sprint
Layers (S-095, S-096), SVG text (S-097): after 0.1.
