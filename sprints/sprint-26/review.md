# Sprint 26 review — Play helps first (E-35)

**Dates:** 15 October 2026. Work in `funground-hq.github.io` (site PRs #9 to #16), `funground-run.github.io` (preview
PR #4) and `funground-web` (PR #8). Every site story shipped as soon as it was checked (maintainer, 15 Oct: Play work
need not wait for a release). **Awaiting sign-off.**

## Outcome

Goal met: a newcomer opens Play on a starter sketch that says what to change; the editor suggests names, shows a
function's arguments while typing and its help on hover; an error marks the line and the wrong name and links to its
explanation; Guides shows where the mouse is in the sketch's own pixels; numbers change with Alt and the arrow keys;
and Play works on a phone. The gallery can be walked through. In github.dev the funground extension suggests what to
type (merged; it reaches learners when the maintainer publishes it).

| Story | Result |
|---|---|
| S-200 First visit | `starter.py` (14 lines, three "Change ..." comments, runs unchanged on a computer); help opens with "New to funground? First steps" |
| S-201 Hints and hover | the signature with the current argument in bold (keywords, nested brackets, strings, `*radii`); hover with signature, sentence, Reference link |
| S-202 Guides | a 50-pixel grid and "x 312, y 140" in sketch pixels, drawn by the preview (new `guides` message, ignored by older previews); the sketch keeps the mouse; no stale size caption after an early error |
| S-203 Errors | line wash, wavy underline under the named name, "What this means" to seven errors-page sections |
| S-204 Night colours | one highlight style from the code tokens, day and night; every code colour AA in both schemes |
| S-205 Extension suggestions | completion, hover, signature help, `COLORS`/`CONSTANTS`, colours and option words in quotes; extension 0.2.0 |
| S-206 Gallery walk | breadcrumb, Previous and Next top and bottom; then no empty left column (maintainer's report) |
| S-207 Previous/Next in Play | ‹ › through 115 examples, drafts kept |
| S-208 Numbers with Alt | pulled forward: Alt+Up/Down by the last digit's step, Alt+Shift ten, Alt+drag scrubs; Alt highlights the number or the line (maintainer's design) |
| S-189 Phones (core) | pulled in after the maintainer's report: one column, the picture as wide as the column, a usable editor, a floating Run, a one-line first-visit notice |
| S-168 Polish | the toolbar stays one row at 1366; Reset only after an edit (already so, now tested) |

**Tests:** `test_editor.mjs` 41 checks (from 21 at the start); the extension's 13 suggestion tests and its end-to-end
test in site mode; `check_links.py` and strict MkDocs builds for the gallery work; `check_code_contrast.py`.

## Measurements

| What | Before | After | How |
|---|---|---|---|
| Play on a phone (390 x 844): editor height | 0 px | 478 px | live page, headless Chrome (`shot_phone.mjs`) |
| Play on a phone: picture of a 640 x 400 sketch | 68 x 44 | 378 x 238 | the same |
| Phone first visit: where the picture starts | y 803 (help covered the screen) | within the first screen | check 41 |
| Editor bundle | 411.7 KB | 424.1 KB | file size |
| Extension `.vsix` | 39.8 KB | 64.4 KB | file size |
| Links checked on the site | 1310 | 1710 | `check_links.py` |

## Decisions

- Keys for numbers (maintainer, 15 Oct): Shift for ten steps, not Alt+Left/Right (Back in the browser, word jumps on a
  Mac); the step from the number's last digit; Alt highlights what it will move.
- Decided by Claude, for review: Play runs funground `main` (`RUNTIME_BRANCH`, approved by the maintainer when made);
  the extension's suggestions come from the runtime's `completions.json` (one source with the wheel); the hover box
  shows the typed signature, the hint the plain one; on phones the messages stay above the picture and the picture is
  not sticky (a sticky picture would leave about 350 px for the code).

## Findings that change later work

1. **The maintainer's look at the live site found three real problems in a few minutes** (the empty gallery column,
   Play on a phone, Alt opening the browser's menu); the tests had none of them. A trial on the live site after each
   deploy is now part of shipping, with a phone-width screenshot.
2. **Headless Chrome cannot show Chrome's own behaviour** (the Alt key and the menu, a pointer leaving a frame from
   another site); those need a real browser. The maintainer confirmed the Alt fix on Windows.
3. **The editor test is slow on this machine** (41 checks, more than 10 minutes, one check timing out when the machine
   was short of memory). Next: run it in groups, or speed up its loading.
4. **A test script's element click scrolled the editor sideways** and looked like a product bug; it exposed a real
   one (the transparent gutter), fixed. Tests click at points now.
5. The extension's suggestions and the github.dev check (P1) wait for the maintainer to publish 0.2.0.

## Built by subagents

All eleven stories by Sonnet builders, one at a time on the site; S-206 in its own worktree beside them. The main
session reviewed every diff, fixed the night colour aliases, the gutter, the test's race with the Run button and the
two dead guide anchors, ran the tests again, shipped, and checked each deploy on the live site.

## Retrospective

Kept: ship each story as soon as it passes, then look at the live page. Change: look at a phone width before calling
a page story done, and keep the editor test fast enough to run whole after every story.
