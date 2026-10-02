# Sprint 10 review — Phase 3d: typography, SVG and real PDF text

**Dates:** 1–2 October 2026. **Draft for the maintainer's sign-off.**

**Goal:**
- richer text: tracking, OpenType features, variable fonts, mixed styles in one text;
- rounded corners;
- SVG files loaded as vector drawings;
- a spike on searchable PDF text, which became real PDF text (D-043 = D).

## Outcome

All six stories are done, and nothing is carried over.

**Checkpoint met, with one deliberate exception.** No golden image or gallery image that existed
before the sprint changed. One IR snapshot changed, on purpose:

```
git diff -M --diff-filter=MD 15e35c3..HEAD -- tests/golden tests/snapshots docs/gallery/images docs/reference/images
 tests/snapshots/gallery/images-04_filters.json | 22 +++++-----
```

The snapshot had recorded a bug. Two pictures were both named `graphics-1`, which P3 forbids. The
fix renumbers them, and nothing else in the file changed (finding 3).

**New dependencies, both decided by the maintainer:**

| Dependency | Decision | Why | Imported only in |
|---|---|---|---|
| `svgelements` | D-041 | SVG import | `funground/svg.py` |
| `pypdf` | D-043 | real PDF text | `funground/export/` |

Both are pure Python. The boundary test enforces where each may be imported.
`pypdfium2` is a dev-only dependency, used by the tests to render PDFs.

**Public surface:**
- 146 → 152 names: `text_tracking`, `text_features`, `font_variations`, `FormattedString`,
  `load_svg`, `svg_paths`.
- One approved v0.5 change: `rect` and `square` take corner radii (D-040).

| Story | Result | Built by |
|---|---|---|
| S-089 Rounded corners | `rect`/`square` with 1 or 4 radii in p5's order; the path builder's `rect` too | Sonnet sub-agent |
| S-090 Tracking, features, variations | `text_tracking`, `text_features(**tags)`, `font_variations(**axes)`. Shaping and outlines use the same variation location | Sonnet sub-agent |
| S-091 Mixed styles in one text | `f.FormattedString` (DrawBot's API), drawn with `text` and `text_box` | Sonnet sub-agent |
| S-092 SVG import | `f.load_svg` gives a vector picture; `f.svg_paths` gives path builders | Sonnet sub-agent |
| S-093 Spike: searchable PDF text | Cairo cannot embed our fonts; routes measured; D-043 raised | Sonnet sub-agent |
| S-094 Real text in PDFs | Fonts embedded as subsets; text selectable, searchable and copyable; same stacking, clip, blend and gradient as before | Opus sub-agent, in its own worktree |

Developer documentation was also written: `docs/developer/` and seven design notes, the newest being
`PDF_Text_Note.md`. PROCESS.md now requires a design note for every new subsystem.

## Test results

```
1518 passed   (Sprint 9 close: 1286)
CI: not checked for the last pushes - GitHub was unreachable from this machine on 2 Oct (see Sign-off)
```

## Measurements

- **PDF text size:** a page of 50 lines × 73 characters is 59.7 KB with real text, against 620 KB
  as outlines.
- **PDF text look:** pdfium renders at 4×, compared with the outline PDF. The mean difference is at
  most 0.11, against a limit of 0.3. A half-pixel shift scores at least 0.66, so the test catches it.
- **Script cost of `get()`:**
  - Before the fix, 20 000 shapes with a `get()` every ten shapes took 0.36 s, rising to 0.99 s as
    the script grew.
  - After the fix it takes a flat 0.26 s.

## Findings

1. **The decision on real text came after the spike, and the maintainer's question shaped it.**
   - The spike recommended an invisible text layer.
   - The maintainer asked what *real* text would involve, then chose it.
   - A one-minute Cairo experiment in review found that each text run, drawn as a group, keeps its
     clip, transform, blend and opacity in the PDF. That made real text an M-sized story instead of
     an L.
2. **The builder departed from the brief three times, each forced by evidence:**
   - **The marker shape:** Cairo rewrites a rectangle as `re` and loses its corners, so the marker
     is a four-sided shape that carries its own run id.
   - **Right-to-left text:** it needs `/ActualText`, or pdfium swaps the words in two-word Hebrew and
     Arabic.
   - **Clusters of several glyphs:** these need `/ActualText` too.

   All three are recorded in `PDF_Text_Note.md`.
3. **Fixed in review: bugs that broke the contract.**
   - **`stroke_width(2.5)` drew as 2,** against S6. Fractions are now kept, and whole numbers stay
     ints, so no snapshot moved.
   - **Picture names repeated.** A picture made before `f.size()` or `f.run()` and the first one
     made after it were both `graphics-1`, against P3. A picture made before the run now keeps its
     number in that run.
   - **`f.svg_paths`** returned even-odd shapes with their holes filled. It now returns the
     converted outline (P11).
   - **Scripts slowed down as they grew.** They copied every op on each `get()` and save; they now
     copy only the new ones (`Frame.ops_since`).
4. **Pinned in review, with no code change:**
   - P11: in the window, SVG pictures stay sharp up to about 2× and soften beyond that; SVG's own
     defaults apply.
   - R16: `new_page` inside an open `push` keeps the outermost saved style.
   - T13: variable fonts use their default metrics for ascent, descent and leading.
   - Five contract wordings were corrected to match the code. They covered:
     - quarter circles;
     - which filters use pygame;
     - when a picture's history restarts;
     - the even-odd paths;
     - an old function name.
5. **Two known limits of PDF text:**
   - In Chrome and Edge, rectangular glyphs such as "l" and "I" can look one device pixel heavier.
   - Acrobat, macOS Preview and Firefox are untested.

   Both are recorded as follow-ups.
6. **Running two builders in parallel worked.** The PDF builder ran in its own git worktree while
   SVG import was built in the main folder. The merge was clean.

## Decisions

| ID | Outcome | By |
|---|---|---|
| D-040 | Rounded corners for `rect`/`square` (approved v0.5 signature change) | maintainer (Sprint 9) |
| D-041 | `svgelements` for SVG import | maintainer |
| D-042 | Typography names: `text_tracking`, `text_features`, `font_variations` | Claude, under D-034 |
| D-043 | **D: real, visible text in PDFs**, `pypdf` in the base install | maintainer |
| D-044 | Mixed styles: DrawBot's `FormattedString` | Claude, under D-034 |

Review fixes were made under D-034. Each restores the pinned contract and needs no new decision.

## Backlog added (after 0.1)

- S-095: named layers.
- S-096: PDF layers that can be switched on and off.
- S-097: real text in SVG.

## Sign-off

*Awaiting the maintainer.* Before closing, CI must be checked on the commits from `ced4386` to
`eaa4574`. They were made while GitHub was unreachable, and some may still need pushing.

## Retrospective

- **Went well:**
  - Six stories, a spike and a full developer-docs pass were done in two days.
  - Every builder's departure from its brief came with evidence.
  - Review caught four contract bugs.
- **Went badly:**
  - A snapshot had recorded the duplicate-name bug since Sprint 7, unnoticed. Snapshots pin
    behaviour, wrong behaviour included.
  - S6 had been broken since Sprint 0.
- **Change for Sprint 11:** when a builder reports that code and contract disagree, fix it or pin it
  in the same review. Never leave it as a note.

## AI-USAGE log entry

Added to `AI-USAGE.md` under Sprint 10.
