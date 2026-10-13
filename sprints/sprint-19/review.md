# Sprint 19 review — 0.2: a faster core, measured in the browser; the website

**Dates:** 8–9 October 2026, on `release-0.2-web`. **Not yet signed off.**

## Outcome

| Story | Result | Commit |
|---|---|---|
| S-060 Run loop as start/step/finish (L1, D-074) | merged from the S-136 spike | `e6371fe` |
| S-144 Style calls without `dataclasses.replace` | `draw()` −16 to −29 % on three heavy examples | `073a25e` |
| S-145 Colour strings parsed once (bounded cache) | `Color.parse("#336699")` 2.56 → 0.29 µs; −13 % `draw()` where strings are used | `4cd1ab4` |
| S-146 Plain int/float without the `Real` ABC | `Vector(1.5, 2.5)` 1.20 → 0.29 µs; kinetic_type −25 % | `bb6a4ad` |
| S-147 Glyph outlines scaled once, then placed | Cairo time −14 to −36 % on text-heavy examples; identical floats | `69d989c` |
| S-149 Public `Path.translated` (D-076) | replaces S-147's private helper; two follow-up fixes (float points; still refuses a non-number) | `91bab78`, `abc62a5`, `b14f011` |
| S-148 Both web routes re-measured in Chrome | Python `draw()` −28 % in Pyodide (Cairo route), −23 % (Canvas); route ranking unchanged | `funground-web` `f5e9b01` |
| S-150, S-141 The website and its gallery pages (D-077) | live at https://funground-hq.github.io, built daily from `funground` main | `funground-hq.github.io` PR #1 |

**Tests:** full suite `3648 passed` (after the S-149 fixes). No golden or snapshot changed in the sprint.

## Decisions

- **D-075 accepted — C** (9 Oct): Cairo draws in the browser in 0.2; Canvas 2D as a second renderer (C+B)
  is on the roadmap to revisit.
- **D-076 accepted:** public `Path.translated`.
- **D-077 accepted:** the website (home, docs, gallery, later the editor), MkDocs Material, at
  funground-hq.github.io (`funground.github.io` belongs to an unrelated organisation). Live as a preview.

## Findings that change later work

1. **Numeric colours are now the largest clean hotspot:** `fill(r, g, b)`, greys and tuples are re-parsed on
   every call (28–34 % of `draw()` in kinetic_type, text_dots, noise). S-145 cached strings only.
2. `Vector` checks remain 23 % of kinetic_type; `GraphicsState.with_` 5–14 %; glyph translation 21–48 % of
   Cairo time in text-heavy examples.
3. Browser timings on this machine are noisy (1.5–3× between repeats): decide on native and back-to-back
   Python profiles, use browser tables for direction only.
4. The editor's sandboxed previews need a second origin: every funground-hq.github.io project page shares one.
5. A GitHub repository named `<org>.github.io` turns Pages on by itself; the site was briefly public with
   a placeholder README before the first deploy.

## Built by

Sonnet subagents: S-144, S-145, S-146, S-147, S-149, S-148, S-150/S-141. Main session: S-060 merge, the
S-149 fixes, reviews, commits and the Pages switch.

## Retrospective

- **What went wrong:** S-149's float/int difference was caught only by the full suite, because the builder
  ran targeted tests while Chrome was busy; then the main session committed the first fix before its
  targeted run had finished, which broke the non-number test. Wait for the result before committing,
  even for a one-line fix.
- Two agents broke the "never plain python3" rule (one hung process, one harmless version check). The
  briefs now name `python3` explicitly; the agents' own definitions should too.
- S-143's estimates overstated two fixes (S-145, S-147): its profiles mixed string and numeric colours, and
  its baseline predates S-144–S-146. Prototype gains are upper bounds.
- Clean designs held: every fix is small, documented and output-identical.
