# Sprint 13 review — release 0.1, widened: making sound, the microphone, text in files

**Dates:** 3–4 October 2026, under D-034, D-049, D-055 to D-060; closed by the maintainer 4 October 2026

**Goal:**
- tones, notes, melodies (sargam too) and pitch;
- microphone input;
- real text in SVG;
- the PDF-text polish;
- added during the sprint: text as shapes for handoff files, a poster example, and the gallery browser telling where saved files went.

## Outcome

All feature stories are done.
- **S-109 (PDF polish) closed without code.** Measurement showed the problem was the other way round (see Findings).
- **The release (S-073) moves after Sprint 14.** 0.1 was widened again by D-056 and D-057.

**Checkpoint met.** No golden, snapshot or gallery image that existed before the sprint changed:

```
git diff -M --diff-filter=MD 9d63d7a..HEAD -- tests/golden tests/snapshots docs/gallery/images docs/reference/images
```

That diff is empty.

**No new dependency.** Sound making is pure Python; the microphone uses pygame-ce's experimental `_sdl2.audio`, wrapped in one module.

**Public surface:**
- 168 → 179 names: `create_sound`, `tone`, `note`, `pluck`, `melody`, `sequence`, `mix`, `note_to_frequency`, `frequency_to_note`, `microphone`, `microphones`.
- Sounds gain `samples`, `pan`, `save` and `pitch`.
- `save(path, *, text=...)` is an approved additive change to a v0.5 signature (D-060).

| Story | Result | Built by |
|---|---|---|
| S-110 Making sound | Tones in 5 waves with attack and release, notes, pluck, melody strings with rests, chords and beats, **sargam with Sa and just tuning**, `sequence`, `mix`, pan, WAV save, `pitch()`. A 3 s tone takes under 0.1 s; pitch error is under 0.25% | Sonnet sub-agent |
| S-108 Microphone | `f.microphone()` with `level`/`spectrum`/`pitch` (shared code with sounds), `capture(seconds)`, a tuner example. Real device opened once (44.1 kHz) | Sonnet sub-agent |
| S-097 Live text in SVG | Every line is a live `<text>`/`<tspan>` naming its installed font; subsets embedded for browsers, keeping shaping; RTL in reading order. A text-heavy page is 50 KB instead of 2.8 MB | Opus sub-agent, worktree (after an option-B draft the maintainer replaced with A) |
| S-116 Text as shapes | `save(..., text="shapes")` for PDF and SVG, for handoff copies | Sonnet sub-agent |
| S-109 PDF polish | Closed without code; note and test comment corrected | Opus sub-agent (measurement) |
| Poster example | Layers, Hindi and emoji, saved live and as shapes, in PDF and SVG | Sonnet sub-agent |
| Gallery browser | A run folder per example; says where saved files went; O / Folder opens it | Sonnet sub-agent |
| Raga research | §6 of the music note; every outside library and dataset checked on the web | Sonnet sub-agent |

## Test results

```
2028 passed   (Sprint 12 close: 1829)
CI: green up to 8398dd4; the latest pushes are running at the time of writing
```

## Findings

1. **Measuring S-109 turned it round.** The real PDF text was already right. pdfium draws the *outline* PDF heavier, and our tests compared against the outlines, so they showed pdfium's error as ours. The planned fill mode was built, measured and dropped.
2. **SVG text changed twice, for good reasons.**
   - The builder first chose option B (invisible text). The maintainer chose A (live text) for editing between Illustrator and Inkscape.
   - Then the maintainer added the designers' handoff rule: shapes for distribution.
   - Result: live by default, shapes on request (T19, T20).
3. **Process slips, all corrected:**
   - A stale helper script in the shared scratch folder was run by accident. It duplicated `filter` in four files; the builder restored them, and the old scripts were deleted.
   - I staged `docs/design` broadly while a builder was writing there, which committed its half-written section early. It was harmless, and I now stage named files only.
   - A plain-`python` call from the day before had opened install windows; the rule was already in place.
4. **A test-harness gap fixed.** For scripts, the harness captured the canvas without layers, so the poster's first golden came out black. Scripts are now captured as `show()` sees them.
5. **Pinned in review:** A3 (pan law, fades, sargam rules), A4 (when errors appear, capture padding), T19 (one `<text>` per line, fonts and gradients), T20 (when the value is checked).

## Questions for the maintainer

- **Layer default style.** A layer starts with funground's default style (black stroke) rather than the canvas's current style. The poster's builder had to call `no_stroke()` in each layer. Consistent with pictures, but it may surprise beginners. Keep it, or start layers with the canvas's style?
- **`tuning="just"` without `sa`** raises `ValueError`. Keep it, or ignore the tuning?

## Decisions

| ID | Outcome | By |
|---|---|---|
| D-055 | Tones, notes and pan in 0.1 (ADR-006) | maintainer |
| D-056 | Music for teaching in 0.1: pluck, melody, pitch, teaching scenarios; Sprint 14 | maintainer |
| D-057 | Indian raga synthesis and analysis for learners in 0.1 | maintainer |
| D-058 | Microphone API | Claude, under D-034 |
| D-059 | **A:** live SVG text naming the installed font | maintainer |
| D-060 | Text as shapes for handoff files | maintainer |

## Sign-off

**Closed 4 October 2026** by the maintainer ("Signed off"). D-058 stands; the layer default style and the `tuning="just"`-needs-`sa` error stay as built.

## Retrospective

- **Went well:**
  - The maintainer's domain knowledge (designer handoffs, Illustrator and Inkscape editing, Indian music) shaped the features directly.
  - Measuring before fixing saved a wrong change (S-109).
- **Went badly:**
  - Several small process slips in one day; see Findings 3.
- **Change for Sprint 14:**
  - Every brief names its scratch scripts uniquely.
  - Every main-session commit stages named paths only.
  - Builders running in the main folder never overlap on files; parallel work goes to a worktree.

## AI-USAGE log entry

Added to `AI-USAGE.md` under Sprint 13.
