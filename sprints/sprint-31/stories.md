# Sprint 31 — Fonts from the web, help for the cut-out, a book's first pages (E-32, E-33, E-36)

**Dates:** planned 23 October 2026. Scope chosen by the maintainer on 23 Oct ("Will go with your proposal for Sprint 31
scope"). Work in funground, `funground-web` and `funground-hq.github.io`. Each story ships when it is checked.

**Goal:** a sketch can use a font from a web address on the desktop and in Play, and keeps working offline; the
background cut-out gets the measured evidence for its next step (D-115); the book has a written page system and a
first chapter to look at.

**Decisions:** D-117 a (fonts: web addresses; a provider is an option, never a function). Needed during the sprint,
brought to the maintainer before building: the argument's name and the provider words for S-230, and its row in the
semantic contract; D-115 answered from S-227's results; how the book draws without coordinates (S-225's proposal).

| Story | Value | Status |
|---|---|---|
| S-230 | Fonts from the web: `load_font()` and `text_font()` take a `.ttf` or `.otf` address, kept for offline runs, also in Play | live 28 Oct (funground #23, funground-web #17) |
| S-227 | Spike: help for the background cut-out (tidy mask, an editable outline, edges), the evidence for D-115 | planned 23 Oct |
| S-225 | Spike: a layout model for a funground book, alongside (a study, a page system, one chapter as a PDF) | planned 23 Oct |
| S-237 | Moving the paper: a step-by-step project for translate, rotate, push and pop, with exercises (added 27 Oct by the maintainer) | built 27 Oct |

Order: S-230's measurements first (which hosts serve fonts with CORS, WOFF2 support, what no network gives), then its
proposal to the maintainer; S-227 while the proposal waits; S-225 alongside, in pieces between heavy jobs. One heavy job
at a time on this machine.

Next after this sprint: S-231, the models spike (E-37, added 23 Oct), which may also inform D-115.

## S-230 tasks

- [x] Measure: hosts that serve TTF/OTF with CORS (Google's fonts repository on GitHub, fonts.gstatic.com, others)
- [x] Measure: whether Cairo/FreeType and HarfBuzz read WOFF2 (unverified), on the desktop and in Pyodide
- [x] Measure: what a missing network gives today, and the one clear line it should give
- [x] Proposal to the maintainer (D-119, `Web_Fonts_Note.md`, 27 Oct): the argument's name, the provider words (`f.CONSTANTS.PROVIDERS.GOOGLE_FONTS`?), the contract row
- [x] Build after the answer: desktop download and cache, Play through the runner (S-211's route), `f.keep()` records the address
- [x] Tests, gallery example with its golden, Quick Reference row, guide section, Since marker

## S-227 tasks

- [x] (a) Tidy the mask: largest connected part, holes filled; under 5 ms at 640 x 480
- [x] (b) The outline as an `f.path()` over the picture, points a learner drags, cut out with `clip`; at most 200 points, a sketch under 60 lines
- [x] (d) Edges pulling the outline to the picture's own outlines
- [x] Three test photos and the fake camera; results in `spikes/`; a recommendation with API names for D-115

## S-225 tasks

- [x] A study of at least six books (chosen in the spike, with reasons): what each teaches, what funground takes or leaves (`spikes/15_book/study.md`, ten books)
- [x] A page system: trim with bleed, grid, type from the site's fonts, colour, components (`spikes/15_book/page_system.md`)
- [x] The production route chosen and why (funground as the layout engine; page_system.md section 7)
- [x] One chapter of 8 to 12 pages as a PDF, pictures by funground, a chapter opener drawn by a sketch (`spikes/15_book/make/`, RESULTS.md)
- [ ] A night (midnightblue) version of the screen PDF, closer to Play (maintainer, 28 Oct)
- [ ] The spreads on the site with Previous and Next
- [ ] A proposal for drawing without coordinates, as a decision for the maintainer; the effort of a whole book
