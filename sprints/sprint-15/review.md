# Sprint 15 review — release 0.1: documentation, examples that explain themselves, more projects

**Dates:** 4–5 October 2026, under D-065. **Draft for the maintainer's sign-off.**

**Goal:** before 0.1, make funground easy to learn from:
- every example explains itself;
- the guide reads as a path, with exercises, an errors page and a glossary;
- more projects, each with its own page;
- the developer docs match the code.

## Outcome

All four stories are done. Added during the sprint, after the maintainer tried things:
- the event posters became an interactive poster designer;
- quiet laptop microphones are heard (`pitch()` down to −60 dB; the voice game measures dB above the room);
- the voice game was made less sensitive (15 dB to lift, 30 dB more to the top), then given a
  "set up your voice" screen before play;
- layers keep vectors when a block wipes itself (`f.clear()` or `background` inside `with f.layer`);
- the gallery browser's sidebar scrolls, with Projects listed first;
- gallery pictures of scripts composite their layers (the poster picture had been blank).

**Checkpoint.** Images changed since the sprint began (`53215a4`), each an intended change:

```
git diff -M --diff-filter=MD --stat 53215a4..HEAD -- tests/golden tests/snapshots docs/gallery/images docs/reference/images
```

| Image | Why |
|---|---|
| `projects-01_event_posters` (golden, picture) | Poster designer; picture was blank before the layer-compositing fix |
| `projects-04_voice_game` (golden, snapshot, picture) | Microphone bar, then the setup screen |
| `music-10_ear_training` (golden, snapshot, picture) | Shows it is hearing you |
| `music-03_sing_with_the_drone`, `music-06_see_your_voice`, `sound-04_tuner` (pictures) | Show they are hearing you |

**No new dependency. Public surface unchanged at 191 names.** Library changes are small: the layer-wipe
marker (`ir.Save.layer_block`), the quiet-microphone thresholds, and the gallery browser.

| Story | Result | Built by |
|---|---|---|
| S-120 Examples explain themselves | All 83 examples have what you see / how it works / make it yours; the browser's Explain and Code tabs; a test enforces it (now 87 with the new projects) | Sonnet sub-agents, pilot first |
| S-121 More projects | Typographic portrait, kinetic type, scratch card, flow-field print; chapter 18 is an index of eight project pages, each with "How it works" | Sonnet sub-agents (three in parallel, numbers pinned per builder) |
| S-122 The guide, solidified | Learning-path README; See also and Try it in chapters 1–17; errors page (about 40 cases, from real messages); glossary (63 terms) | Sonnet sub-agent |
| S-123 Developer docs | Architecture for Sprints 11–15 (sound, controls, motion, text in files, layers, gallery package), naming trap, layers rule; Testing and Adding a feature re-checked; design-note index | Sonnet sub-agent |
| Voice game setup screen | Room check, live meter with movable lift/full marks, practice bird; 9 new tests | Sonnet sub-agent |

## Test results

```
2561 passed in 470.56s   (Sprint 14 close: 2338)
```

The guide test now also checks links on the errors, glossary and project pages, and runs `python` fences
on project pages.

## Findings

1. **The maintainer's hands-on tries drove most of the sprint's code changes:** blank poster picture,
   static posters, a silent-looking voice game, then a too-sensitive one. Each was a quick fix once seen.
   Quiet laptop microphones (room RMS about 0.0005) were not covered by any test before; now they are.
2. **Pinning file numbers per builder worked.** Three parallel S-121 builders and the chapter split merged
   with no renumbering. The only shared file, `docs/gallery/README.md`, is generated.
3. **Tests that hard-code counts break when content grows.** Two browser tests assumed four projects; they
   now count the folder.
4. **One builder ran plain `python` once by mistake** (the install stub), and stopped it itself. The rule
   stands; it is in every brief.
5. **A false alarm of mine:** I took a quiet test run (output piped through `tail`) for a stuck one.
   Background runs should write progress to a file.
6. **Not verified by people:**
   - the four new projects by hand (scratch-card sounds, kinetic-type typing, the flow-field PDF at A3);
   - the voice setup screen with a real microphone;
   - the errors page's Linux pycairo wording, which varies by distribution.

## Decisions

None new. Work was under D-065 (maintainer) and D-034 (routine design).
Small design choices made under D-034:
- kinetic type: Enter toggles typing, so G can record;
- voice setup: Left/Right moves "full height", as keys have no Shift;
- the voice game's sliders stay visible in play, as controls cannot be removed.

## Questions for the maintainer

- **Hide the voice game's sliders during play?** It needs a small library addition: removing or hiding
  controls. Backlog, or 0.1?
- **Chapter 9 is 750 lines.** Split into shapes and pictures after 0.1?
- **Sprint 14 sign-off** is still open (its own questions: more Indic fonts, melody legato).

## Sign-off

*Awaiting the maintainer.*

## Retrospective

- **Went well:** pinned file numbers per builder; the docs test making explanations stick; the maintainer's
  hands-on checks finding what tests could not.
- **Went badly:** hard-coded counts in tests; one plain-`python` slip; my false "stuck" alarm.
- **Change for the release:** background test runs log progress to a file; tests count content rather than
  fix it.
