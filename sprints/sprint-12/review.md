# Sprint 12 review — release 0.1, widened: text depth, layers, the gallery in the package

**Dates:** 2–3 October 2026, under D-034 and D-049. **Draft for the maintainer's sign-off.**

**Goal:**
- missing letters come from fallback fonts;
- learners get the examples with `pip install funground`;
- text as points, font information and `erase()`;
- layers, kept as pictures in the window and as real layers in PDF and SVG.

## Outcome

All stories are done. S-105 needed nothing: `text_box` had already returned its overflow since S-053.

**Checkpoint met.** No golden, snapshot or gallery image that existed before the sprint changed:

```
git diff -M --diff-filter=MD 0c5195c..HEAD -- tests/golden tests/snapshots docs/gallery/images docs/reference/images
```

That diff is empty.

**Base install:** +1.8 MB of bundled OFL fonts (D-052 = C). No new dependency.

**Wheel:** 4.4 MB, up from about 2.6 MB. The extra is the gallery examples and pictures (R18) plus the fallback fonts.

**Public surface:** 159 → 168 names: `text_to_points`, `current_font`, `erase`, `no_erase`, `text_fallback`,
`system_font`, `layer`, `hide_layer`, `show_layer`. No v0.5 API change.

| Story | Result | Built by |
|---|---|---|
| S-102.0 Spike: font fallback | Cluster-itemised fallback chain; sizes and licences measured; D-052 raised | Sonnet sub-agent |
| S-102 Font fallback | Noto Emoji, Symbols 2 and Devanagari bundled; `text_fallback`, `system_font`. Text that needs no fallback is shaped exactly as before | Sonnet sub-agent, worktree |
| S-103 Gallery in the package | `python -m funground.gallery`, with examples and pictures in the wheel; "copy to folder"; one example list shared with the tools | Sonnet sub-agent, worktree |
| S-104 Text to points | `f.text_to_points()`: points along `text_path` at an even spacing (curves to 0.01 px) | Sonnet sub-agent |
| S-105 Text-box overflow | Already done (T10) | — |
| S-106 Font information | `f.current_font()`, with `family`, `style`, `variations`, `features`, `contains` | Sonnet sub-agent |
| S-107 Erase | `f.erase()`/`f.no_erase()`, as p5 | Sonnet sub-agent, worktree |
| S-095 Layers | `f.layer(name)`: persistent picture layers, hide and show, stacked in order | Sonnet sub-agent |
| S-096 Layers in files | PDF optional content groups and SVG Inkscape layers; hidden layers kept but switched off | Opus sub-agent |

## Test results

```
1829 passed   (Sprint 11 close: 1649)
CI: green on 12 cells up to 86ea1ca; the Sprint 12 pushes are running at the time of writing
```

## Findings

1. **Four bugs fixed in review:**
   - **Layer settings piled up between blocks.** Each layer block is now an implicit `push`/`reset_matrix`…`pop`.
   - **A PDF/SVG save of a picture that did `push`, `background`, `pop` crashed.** This dates from Sprint 6. Picture history now stops at a reset made inside an open push, and files use the picture's pixels.
   - **A `push` left open on the canvas moved the layers in files**, though not on screen. Fixed, with a test.
   - **A flaky PDF-stream regex** in four tests, which had made CI fail at random, was fixed earlier in the sprint (`86ea1ca`).
2. **Builders made several choices, now pinned in the contract:**
   - **T17:** names are reported as the font stores them ("Book").
   - **F15:** erase ignores blend, opacity and shadow. Images erase by their alpha, a deliberate difference from p5. Erasing straight on the canvas does not show in a PDF.
   - **F16:** one optional content group per layer name, or two when the name is hidden on some pages.
   - **R18:** the real wheel layout and sizes.
3. **New design notes:** `Layers_Note.md`, a font-fallback section in `Typography_Note.md`, `PDF_Text_Note.md`, and the music research note.
4. **Not checked in real programs:**
   - Layered PDFs in Acrobat, Illustrator and pdf.js; layered SVGs in Inkscape.
   - The gallery browser's "copy" action by hand.
   - Pdfium is the only viewer we test with. It honours the layers, and their hidden state.
5. **Machine hygiene:** unexplained install windows led to a new rule (PROCESS.md and the agent files): no plain `python`, no default-app opens and no installers. Nothing was installed.

## Decisions

| ID | Outcome | By |
|---|---|---|
| D-049 | 0.1 widened; Sprints 12–13 added | maintainer |
| D-050 | Text-to-points and font information API | Claude, under D-034 |
| D-051 | Erasing, as p5 | Claude, under D-034 |
| D-052 | **C:** Noto Emoji, Symbols 2 and Devanagari in the base install | maintainer |
| D-053 | Layers as pictures and as real PDF/SVG layers, in 0.1 | maintainer |
| D-055 | Tones, notes and pan in 0.1 (ADR-006); built in Sprint 13 | maintainer |

## Sign-off

*Awaiting the maintainer.*

## Retrospective

- **Went well:**
  - Parallel builders in worktrees, three at a time, with one trivial conflict.
  - Spikes before decisions: font fallback gave the maintainer measured sizes and licences.
  - Review caught four real bugs.
- **Went badly:**
  - A plain `python` call opened install windows on the maintainer's machine.
  - The real-program checks keep piling up for the maintainer.
- **Change for Sprint 13:** put every "check by hand" item in one list in the reviewer's guide, so the release
  check is a single session.

## AI-USAGE log entry

Added to `AI-USAGE.md` under Sprint 12.
