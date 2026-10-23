# Sprint 30 review — Video pieces and pictures, and the first release (E-33, E-35, E-31, E-14, E-22)

**Dates:** 17 to 23 October 2026. Work in funground (PRs #16 to #21), `funground-web` (PRs #13 to #16),
`funground-run.github.io` (PR #10) and `funground-hq.github.io` (PRs #27 to #29). Every story shipped when it was
checked. **funground 0.1.0 was released on PyPI on 20 October.** **Awaiting sign-off.**

## Outcome

Goal met. A take moves between sketches through My files; the words piece plays a take with its sound; the camera has
an edge view; learners have a six-step route from pixels to marks. Added during the sprint and also shipped: replacing
the background behind you, JPEG pictures checked with a tolerance in the browser, fonts that arrive only when a sketch
uses text, "Since 0.2" markers for everything newer than 0.1, and the course's Extend step with Keep this.

| Story | Result |
|---|---|
| S-224 `filter("edges")` | the outlines in a picture or the camera; gallery images-09 |
| S-221 My files in Play | files a sketch saves are kept and usable by any sketch; Add file; Delete with Undo; download stays |
| S-222 Blow the words loads a take | loads `take.gif` and `take.wav`; breath per frame from the sound; G saves one loop |
| S-223 From pixels to marks | a six-step project opening in Play; gallery area Pixels to marks; guide project 10 |
| S-218 Replace the background | `pic.remove_color(color, tolerance=40)` and `pic.remove_background(empty, tolerance=30)` (D-106); contract P12; gallery images-10; guide 09 "Stand in front of any picture" |
| S-228 JPEG in the browser | the runner check compares pixels with a tolerance for JPEG sources (mean ≤ 1, p99 ≤ 16) and fails a frame outside it (D-101 a) |
| S-211 Fonts when first opened | the browser host supplies a bundled font the first time funground opens it, checked by size and SHA-256 (D-114 b); the start-up font loading is gone |
| S-229 Available since | `funground/released_names.json` freezes 0.1.0's API; later names say "Since 0.2" in the API reference (a badge under the heading), completions, llms.txt, the guide, the gallery and the Quick Reference (D-116) |
| S-226 The course's studio step | Lessons 1, 3 and 5 offer an Extend sketch after Compare (`f.variations`, `f.mark`); Keep this runs `f.keep(note)` through the runner and keeps the picture, code and notes in My files (D-113 b) |

**Release 0.1.0 (D-116):** the 14 Oct candidate plus its changelog date, tag `v0.1.0` = ff88b9a. The release CI ran
10 of 10 jobs green (three systems); TestPyPI, then a smoke install on three systems, then PyPI after approval. A
fresh install from PyPI on this machine (Python 3.14.7) passed the smoke test: 98 gallery examples listed, Hindi
shaped, `f.camera` absent as expected. The site's Get started page says `python -m pip install funground`. The
`.github` profile has an Install section. Photo booth and background removal were kept out of 0.1, as the maintainer
asked.

**Tests:** funground's full suite in two halves without `FUNGROUND_HEADLESS`: 2756 and 1697 passed, 1 skipped
(21 Oct). CI green on every PR. `funground-web` `test_runner.py`: 17 frames, 12 of 12 checks, the 4 keep checks
included. Site `test_editor.mjs`: 68 of 74 on this machine; checks 72 to 74 (Extend, Keep this) are new and pass;
36 and 51 to 54 fail here on the untouched baseline too (this machine's Chrome and service worker), and 63 was a race in
the test (it now waits for the lesson panel) and passes.

## Measurements

| What | Result | How |
|---|---|---|
| `remove_color` / `remove_background` at 640 x 480 | 9.5 and 13.6 ms (antialiased picture; the Python step only for partly see-through pixels) | the builder's timing, reviewed |
| Fonts at Play's start-up | none fetched; `DejaVuSans.ttf.bin` (757 KB) only after a text sketch runs | the live site, browser network log |
| Release jobs | 10 of 10 green | GitHub Actions run 39472067389 |
| Fresh install from PyPI | smoke test passed | Python 3.14.7, new virtual environment |

S-211 has no clean "before" timing: the earlier report was overwritten, so the gain at start-up is shown by what is no
longer fetched, not by a number.

## Decisions

- Maintainer: D-101 a (accept the JPEG difference), D-106 (S-218 names), D-113 b (the course's studio step; the
  maintainer will review it and may have second thoughts), D-114 b (fonts when first opened), D-116 (release 0.1.0, the
  scope, Since markers), D-117 a (fonts from web addresses; a provider is an option word, never a function), the
  extension 0.2.0 published (19 Oct).
- Decided by Claude, for review: Since markers on a guide section only when its code needs a later name (a table row
  gets its own small marker); the API reference shows the marker as a badge right under the heading, after the maintainer
  could not see the plain sentence; the course's Extend sketches are placed at the end of each lesson; a failed font
  download is a plain `OSError` naming the font.
- Pending: D-115 (help for the cut-out; S-227 in Sprint 31, and the models spike S-231 may inform it).

## Findings that change later work

1. **A tag on a `[skip ci]` commit starts no release workflow.** `gh workflow run release --ref v0.1.0` started it;
   `Releasing.md` has the row. Never put `[skip ci]` on a commit that will be tagged.
2. **The site's install page outlived the release.** It still said "not on PyPI" after 0.1.0 was published; a release
   checklist should list every page that names the install command.
3. **A marker a reader cannot see does not count.** The plain "Since 0.2." sentence passed every test and was invisible
   on the live site; the badge was the fix. Check new reference text on the live site, not only in the markdown.
4. **Browser tests that check the page at once race with drawing.** Check 63 failed in a full run and passed alone; a
   check should wait for what it looks at.

## Built by subagents

S-218, S-221, S-211, S-229 and S-226 by Sonnet builders, each reviewed by the main session. Reviews changed S-218 (the
colour read under the colour mode, a resize made conditional), S-229 (sections marked by their code only; the v0.1.0 tag
as the reference), S-226 (line endings normalised, the beads made smaller, the course zips rebuilt) and parked a first
S-211 attempt that was redone. Everything else, the release and every commit by the main session.

## Retrospective

Shipping each story as it was checked kept the release separate from the work: 0.1.0 went out from its recorded
candidate while Sprint 30's stories kept merging. The maintainer's reading of the live site again found what the tests
missed (the invisible marker, the old install page).
