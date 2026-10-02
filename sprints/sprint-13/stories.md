# Sprint 13 — release 0.1, widened: microphone, SVG text, polish; then release

**Dates:** planned 2 Oct 2026 (D-049); starts after Sprint 12.

**Goal:**
- microphone input;
- real text in SVG output;
- the PDF-text polish;
- then the release checklist (`sprints/sprint-11/release_checklist.md`).

## Story set

### S-108 Microphone input — E-17 *(p5 `AudioIn`; explored 2 Oct, see below)*
- [ ] S-108.1 `f.microphone()` (name to pin) with `level()` and `spectrum()` as sounds have (A2); start/stop; a clear error with no device or no permission
- [ ] S-108.2 Headless and CI: a fake input, like the silent sound player

**Exploration (2 Oct 2026, Windows 11, pygame-ce 2.5.8 / SDL 2.32.10):**
- `pygame._sdl2.audio.AudioDevice(iscapture=True, callback=...)` opened the laptop microphone.
- It delivered 44 100 float samples a second in 512-sample callbacks; a quiet room measured RMS 0.0002.
- No new dependency is needed.
- Risks:
  - `pygame._sdl2` is pygame-ce's *experimental* module, so its API may change: pin a version range and wrap it in one provider module.
  - macOS asks the user for microphone permission.
  - CI has no input device.

### S-110 Tones, notes, pan — E-17 *(D-055, ADR-006; contract row to pin)*
- [ ] S-110.1 `f.create_sound(samples, rate)`; tones in sine/square/saw/triangle; named notes; a simple fade; sequences and chords by combining sounds; `sound.pan()`; `sound.save("x.wav")`
- [ ] S-110.2 Tests on generated samples (pitch by FFT, length, pan by channel levels); a gallery example that composes a short tune; guide chapter 16

### S-097 Real text in SVG output — E-15 *(from the backlog)*
- [ ] S-097.1 SVG files carry `<text>`/`<tspan>` with the font embedded (or referenced), placed where the outlines were; same fallbacks as T15

### S-109 PDF text polish — E-15 *(Sprint 10 known limit)*
- [ ] S-109.1 Solid-colour text written with fill mode (`0 Tr`) instead of clip mode, so pdfium no longer widens rectangular glyphs

### S-073 Release 0.1 — E-02 *(carried from Sprint 11)*
- [ ] The release checklist
