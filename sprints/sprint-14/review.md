# Sprint 14 review — release 0.1: seeing sound, ragas, sound quality, projects

**Dates:** 4 October 2026, under D-056, D-057, D-061 to D-064. **Signed off 6 October 2026.**

**Goal:**
- make sound visible;
- teach Indian ragas;
- make every generated sound pleasant;
- add the teaching examples and the first project capstones.

Funground's strength is drawing, so this sprint turns sound into pictures (D-056).

## Outcome

All stories are done. Added during the sprint: sound quality (S-118, after the maintainer's listening),
font collections for Telugu and other scripts (S-119), the sargam pitch-trace fix, and the release workflow
and `Releasing.md`.

**Checkpoint met.** The only existing image that changed is the gallery picture of the time-dependent
sargam example, re-rendered after its fix:

```
git diff -M --diff-filter=MD f2b5ab3..HEAD -- tests/golden tests/snapshots docs/gallery/images docs/reference/images
 docs/gallery/images/sound-03_sargam_over_a_drone.png
```

The one regenerated golden, `music-07_a_songs_fingerprint`, was made in this sprint (by S-111) and then
re-made after the sound changed (by S-118).

**No new runtime dependency.** Everything is pure Python on pygame-ce's mixer.

**Public surface: 179 → 191 names.** The new ones are:
- `chord_notes`;
- `draw_wave`, `draw_spectrum`, `spectrogram`, `draw_pitch_line`;
- `ragas`, `raga`, `talas`, `tala_info`, `tala`, `drone`, `match_ragas`.

Sounds and microphones also gained `onsets`, `tempo`, `beats`, `is_onset`, `chroma`, `chord`, `key`,
`tonic`, `swara_histogram` and `reverb`. `load_font` gained `face=`.

| Story | Result | Built by |
|---|---|---|
| S-112, S-113 Rhythm and harmony | Tempo within 0.4 BPM; onsets and beats within 9 ms; chords and key named correctly on every test case. Key profiles checked against two published sources | Sonnet sub-agent |
| S-115 Ragas for learners | 13 ragas and 6 talas, each fact with at least two cited sources and disagreements noted; drone, meend and kan, tala playback; tonic within 6 cents; `match_ragas` right on 12 of 13 phrases (Khamaj shares Bilawal's swaras) | Opus sub-agent with web search, worktree |
| S-111 Drawing sound | Wave, spectrum, spectrogram and pitch-line views | Sonnet sub-agent, worktree |
| S-118 Sound quality | Headroom, band-limited waves (aliasing from 5–8% down to under 1e-12), ADSR and legato, `soft` voice, warmer pluck, reverb; every example retuned; one clipping example fixed | Opus sub-agent |
| S-119 Font collections | `.ttc`/`.otc` in `load_font` and `system_font`; Nirmala UI gives Telugu, Tamil and Bengali on Windows | Sonnet sub-agent |
| S-114 Teaching examples | Draw a wave and hear it, compose and save, ear training, piano roll | Sonnet sub-agent |
| S-117 Project capstones | Event poster series, rangoli generator, raga explorer, voice game; guide chapter 18 | Sonnet sub-agents (two parts, one in a worktree) |

## Test results

```
2338 passed   (Sprint 13 close: 2028)
CI: green on b8dfbc9 (all of Sprint 14's code); later pushes are docs only
```

## Findings

1. **The maintainer's ears found what tests could not.** Sound was "not pleasant across the board". Measurement then
   showed one example clipping badly and every non-sine wave aliasing. Listening is now a release check.
2. **Network drops cost one round.** Three builders were stopped by an API outage and restarted cleanly, because none
   had changed files yet.
3. **Merges were the main cost of parallel builders.** Every builder created the `music/` gallery area and numbered
   its examples from 01, so the review renumbered them (01–11). Future briefs should name each builder's file numbers.
4. **Two builders hit the same trap:** a submodule with the same name as a public function (`ragas`, `microphone`)
   replaces that function when it is imported. The modules were renamed (`hindustani.py`, `microphone_input.py`).
   This is worth a line in `Architecture.md`.
5. **Not verified by people:**
   - real singing into the raga explorer and the voice game;
   - the tuning constants of the voice game;
   - the raga data against the classic books (cited only second-hand).

   All of these are on the release checklist.

## Decisions

| ID | Outcome | By |
|---|---|---|
| D-061 | Music analysis and drawing API | Claude, under D-034 |
| D-062 | Raga API: a cited built-in table; matching is a learning aid | Claude, under D-034 |
| D-063 | Four project capstones | maintainer |
| D-064 | Sound quality across the board | Claude, under D-034, after the maintainer's report |
| D-065 | Sprint 15 for documentation, examples and projects, before 0.1 | maintainer |

## Questions for the maintainer

- **More bundled Indian-script fonts?** For example Noto Telugu, Tamil, Bengali and Kannada, about 0.2–0.5 MB each.
  Today they work through `system_font("Nirmala UI")` on Windows, or through a downloaded font.
- **Melody legato.** Full overlap is the most legato option and lowers raga-analysis margins slightly.
  The alternative is `LEGATO_LEAD = 0.2`.

## Sign-off

**Signed off by the maintainer, 6 October 2026.** Sprint closed.

## Retrospective

- **Went well:**
  - The sprint was led by the maintainer's domain knowledge (Indian music, design hand-offs, listening).
  - Facts were checked on the web with citations.
  - Measuring before changing sound paid off.
- **Went badly:**
  - Merge renumbering.
  - The submodule-name trap, hit twice.
  - The sound examples shipped before anyone listened to them.
- **Change for Sprint 15:**
  - Each parallel brief names its files and numbers.
  - Every sound-producing change gets a listening check before it is marked done.
  - Architecture notes record the naming trap.

## AI-USAGE log entry

Added to `AI-USAGE.md` under Sprint 14.
