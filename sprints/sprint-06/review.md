# Sprint 6 review — Phase 2c: text layout, compositing, pictures, and going public

**Dates:** 26–30 September 2026; closed by the maintainer 30 September 2026 ("Close sprint 5 and 6").
**Goal:** the remaining pieces a typical p5 sketch or DrawBot page needs, then the guide, the
gallery and release 0.1.

## Outcome

All ten feature stories are done. The release did not happen, by decision: on 30 September the
maintainer widened release 0.1 to include Phase 3 (**D-027**). So the release story and the
gallery showcase move to the release sprint. The sprint also turned the project into a public one:
- a new name, **funground** (D-020);
- a public GitHub repository (D-023);
- a licence (D-025, D-026);
- an AI disclosure (D-024).

**Checkpoint met.** No existing golden image, IR snapshot, gallery image or reference image
changed:

```
git diff --stat --diff-filter=MD cb15150..HEAD -- tests/golden tests/snapshots docs/gallery/images docs/reference/images
```

This is empty, even across the full rename. **22 public names added** (106 → 128).

| Story | Result | Built by |
|---|---|---|
| S-055 Vector | `f.Vector`, p5's in-place meaning, degrees | main session |
| S-049 Text alignment | `text_align`, `text_ascent`, `text_descent` | main session |
| S-053 Multi-line text | newlines, `text_leading`, `text_box` returning the overflow | main session |
| S-050 Gradients | `linear_gradient`, `radial_gradient`; vector in PDF/SVG | main session |
| S-051 Compositing | `blend_mode` (17 modes), `opacity`, `shadow` | main session |
| S-056 Frame sequences | `save_frames` | main session |
| S-057 Window | `resize_canvas`, `full_screen`, `cursor`, `no_cursor` | main session |
| S-075 Rename | `playground` → `funground`, `import funground as f` | **Sonnet sub-agent** |
| S-054 Fonts | `load_font`, `text_font`, `text_style`, bundled bold and italic | **Sonnet sub-agent** |
| S-052 Pictures | `create_graphics`, `image` | **Sonnet sub-agent** |
| S-071 Guide chapters 14–15 | "Coming from p5/Processing" with the table of deliberate differences; "Coming from DrawBot" with every claim checked against drawbot.com. One wrong row, about p5's `textSize`, was removed in review | **Sonnet sub-agent** |
| S-072 Gallery showcase | carried to the release sprint (D-027) | — |
| S-073 Release 0.1 | carried to the release sprint (D-027); `CHANGELOG.md` started | — |
| S-039 CI | carried to Sprint 7. The first run was on 26 Sept: Windows green, Linux and macOS red | — |

**S-071** was finished just after the maintainer closed the sprint and is counted in it.

## Test results

```
653 passed   (Sprint 5 close: 506)
```

Windows 11, Python 3.14. **CI:** Windows green on Python 3.11–3.14. Linux fails to build pycairo
(the Cairo system library is missing on the runner). macOS fails 9 IR snapshots on
last-digit float differences from the platform maths library. Both fixes are S-039, the first
Sprint 7 story.

## Measurements

- **Pictures:** 300 frames of the gallery trail take about 2.2 ms per frame, with no slowdown
  over time.
- **Package:** the wheel carries four DejaVu fonts (about 2.7 MB uncompressed) and three licence
  files.

## Findings

1. **Delegation works when the contract row comes first.** The three sub-agent stories matched
   their pinned rows. Review found and fixed three small things:
   - a duplicated list of style names;
   - a helper wrongly added to the picture method list, then reverted after review;
   - `PlaygroundError` missed by the rename.

   No sub-agent result needed rework of its design.
2. **CI found what a single machine cannot:** a Linux install dependency that learners will hit
   too, and macOS float rounding in snapshots.
3. **A public repository changes the stakes.** Irreversible and public actions now stay with the
   main session (PROCESS.md), and history was rewritten once, before the first push, to protect the
   maintainer's email.
4. **Licensing surfaced a real obligation.** `noise.py` is a translation of p5.js code, so it
   carries p5's LGPL-2.1. Choosing LGPL-2.1-or-later for funground (D-025) keeps that simple.
5. **Examples must be original to be CC0** (D-026). An originality check against the p5,
   Processing, DrawBot, py5, pygame-ce and Nature of Code collections was running when the sprint
   closed. Its result is committed with the CC0 notes, in `docs/qa/Example_Provenance.md`.

## Decisions

| ID | Outcome |
|---|---|
| D-019 | First PyPI release is 0.1 |
| D-020 | Name: funground, `import funground as f` |
| D-021 | One picture type, `create_graphics` |
| D-022 | Bundle DejaVu Sans bold and italic |
| D-023 | Public GitHub repository `funground-hq/funground`; noreply email in history |
| D-024 | `AI-USAGE.md` with a sprint log |
| D-025 | Licence LGPL-2.1-or-later; dependencies keep their own |
| D-026 | Example code CC0, examples checked to be original |
| D-027 | Release 0.1 includes Phase 3 |

## Sign-off

**Closed 30 September 2026** by the maintainer, by instruction. The reviewer's guide checklist
was not ticked item by item. Carried: S-039 to Sprint 7; S-072 and S-073 to the release sprint.

## Retrospective

- **Went well:**
  - Writing the gallery example first kept every feature visible.
  - Pinning contract rows before delegating made the sub-agents' work easy to review.
  - One decision per turn kept a long run of decisions clear.
- **Went badly:**
  - CI came late. Four sprints of "blocked on a remote" hid two cross-platform problems.
  - A long heredoc broke once more.
- **Change for Sprint 7:**
  - CI first, before any feature.
  - Run the originality check as part of every example-writing story.

## AI-USAGE log entry

Added to `AI-USAGE.md` under Sprint 6.
