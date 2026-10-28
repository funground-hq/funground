# Sprint 31 review — Fonts from the web, help for the cut-out, a book's first pages (E-32, E-33, E-36)

**Dates:** 23 to 28 October 2026. Work in funground (PRs #22 to #40), `funground-web` (PR #17) and
`funground-hq.github.io` (S-237's menu entry, and the book's pages). Every story shipped when it was checked.
**Awaiting sign-off.**

## Outcome

Goal met. A sketch can use a font from a web address on the desktop and in Play, and keeps working offline. The
cut-out has its measured evidence, and D-115 is answered. The book has a study, a page system, a 12-page test chapter
built by funground at two trims in a day and a night version, and its spreads on the site. Added during the sprint by
the maintainer and shipped: the Moving the paper project. Two decisions taken during the sprint shape the next one:
D-120 (core and libraries) and D-122 (book building lives on an external content platform; funground keeps print).

| Story | Result |
|---|---|
| S-230 Fonts from the web | `load_font()` and `text_font()` take a `.ttf` or `.otf` address, or a family name with `provider=f.CONSTANTS.PROVIDERS.GOOGLE_FONTS` (D-119); downloaded once and kept for offline runs; in Play through the runner; `f.keep()` records the address. Live 28 Oct |
| S-227 Spike: help for the cut-out | (a) the tidy mask passes on a quiet machine (median 1.9 to 4.4 ms), (b) the dragged outline passes, (d) edges do not help. D-115 accepted: `tidy=`, `at=` and `g.outline()`, built as S-245 |
| S-225 Spike: a book | `spikes/15_book/`: a study of ten books, the page system, the test chapter (Square and B5, day and night, print and screen PDFs) with its grid and contrast checks, the spreads on the site (`docs/book/`, a spread a page with Previous and Next), an effort estimate. D-121: keep current behaviour (no new shape keywords). D-122: book building moves out; S-248 and S-249 follow |
| S-237 Moving the paper | a step-by-step project for `translate`, `rotate`, `push` and `pop` with exercises; guide project 11; gallery area with its goldens |

**Tests:** the full suite in two halves without `FUNGROUND_HEADLESS` before each product merge: S-237 (#22) 2796
and 1697 passed, 1 skipped; S-230 (#23) 2812 and 1749 passed, 1 skipped; its browser scenario 3 new checks, passing. The rest of the sprint
changed spikes, documents and the site, not product code: `test_api_docs.py`, `test_guide.py` and `test_since.py` pass
(951) with the book's pages added, and the site's `assemble.py` and `check_links.py` pass (2319 relative links, OK).

## Measurements

| What | Result | How |
|---|---|---|
| Test chapter build | Square and B5 about 8 to 11 s each, a theme | `make/out/timing.json`, this machine |
| Grid | every vertical position on the 15 pt line | `make/measure.py` |
| Contrast | day and night at least 4.5:1; night's lowest 4.7:1 | `make/measure.py`, WCAG formula |
| Day output after the night version | identical (MD5 of every page PNG) | before and after #37 |
| Effort of the test chapter | about 2 hours elapsed; `build.py` about 620 lines of engine and 190 of chapter | RESULTS.md |
| `tidy` (S-227 a) | median 1.9 to 4.4 ms quiet, 4.5 to 8.7 ms busy, at 640 x 480 | `spikes/14_cutout/measure.py`, 50 runs |

## Decisions

- Maintainer: D-115 (the cut-out: a and b, not d), D-119 (fonts from the web, as proposed), D-120 (libraries `sound`,
  `sangeet`, `camera`; `ml` a separate package; no aliases; ADR-007), D-121 (keep current behaviour: no `size=`/`at=`
  on shapes), D-122 (book building on an external content platform; funground keeps and improves print PDF).
- Decided by Claude, for review: the book's pictures are placed as 300 dpi PNG, because the SVG loses its background
  (a funground bug, in S-249); the site shows the Square trim until the maintainer chooses one; the night version keeps
  the sketches' oldlace paper, with a midnightblue comparison on spread 2.
- Pending: D-118 (Play's sketchbook on GitHub; spike S-238 first); the book's trim (Square or B5) and the night
  sketch's background.

## Findings that change later work

1. **The maintainer's eye found what the checks could not.** The pictures looked cut off and the pages plain, with every
   grid and contrast check passing. A test page goes to the maintainer before it is polished.
2. **The book found seven gaps in funground's PDF** (S-249): an SVG loses its `background()`, no hairlines below 1, no
   `variations` in a box, no baseline grid, no text flow between boxes, no page masters, no text highlight.
3. **New keywords on core names meet resistance** (D-121). A need is met first with today's calls, then by a separate
   package.
4. **Public records name no private project.** S-248 and D-122 say "an external content platform" (#39).

## Built by subagents

Parts of S-230, the S-227 spike and the S-225 study and chapter build were done by Sonnet subagents. The main
session reviewed each diff and changed what the review found: the cut-out's timings were rerun, the study got two
corrections, and the chapter was rebuilt three times after the maintainer read it. Every commit was made by the main
session.

## Retrospective

Two spikes ran beside a shipping story without blocking it, and both ended in decisions the maintainer took the same
day. The book took more rounds than planned, each prompted by the maintainer looking at the PDF; showing the first
pages earlier, rough, would have saved one rebuild.
