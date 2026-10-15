# Sprint 26 — Play helps first (E-35)

**Dates:** planned 15 October 2026. Work in `funground-hq.github.io` (branch `sprint-26`), `funground-run.github.io`
(the preview, for S-202) and `funground-web` (the extension, S-205). Runs while 0.1.0 waits for the maintainer's Mac
test; the site ships as soon as stories are done (maintainer, 15 Oct: Play work need not wait for a release).

**Goal:** the first ten minutes in Play. A newcomer opens Play on a starter sketch that says what to change, sees the
arguments of a function while typing it, sees where the mouse is in the sketch's own pixels, and an error points at
the word that is wrong. In github.dev, the funground extension suggests what to type.

**Decisions:** the order is the maintainer's (Play roadmap, 14 Oct: help first). No new public funground name. The
preview gets one new message (`guides`), ignored by older previews; the protocol is otherwise unchanged.

| Story | Value | Status |
|---|---|---|
| S-200 | Play's first visit: a starter sketch with three "change this" comments, a "New to funground? First steps" link | done (site PR #13, live): `starter.py` (14 lines, three "Change ..." comments, runs unchanged on a computer); the help opens with First steps; check 35 |
| S-201 | The arguments while typing, and help on hover | done (site PR #10, live): the hint shows the signature with the current argument in bold (keywords, nested brackets, strings, `*radii`); hover shows signature, sentence, Reference link; checks 22-24 |
| S-202 | Guides: the mouse's x and y over the picture, and a grid (with the preview) | done (site PR #13, preview PR #4, live): a Guides button; the preview draws a 50-pixel grid and "x 312, y 140" in sketch pixels (right at any zoom and HiDPI), the sketch keeps the mouse; the caption no longer shows a stale size after an early error; checks 34, 36 |
| S-203 | Errors where they happen: the line marked, the wrong name underlined, a link to the errors page | done (site PR #12, live): line wash, wavy underline under the named name, "What this means" to seven errors-page sections (anchors checked); cleared by editing the line |
| S-204 | Play at night in the site's code colours | done (site PR #10, live): one highlight style from the code tokens, day and night (day colours changed too); all code colours AA in both schemes (`check_code_contrast.py`); fixed `--code-keyword`/`--code-string` keeping day colours at night site-wide; the gutter keeps the editor's background (PR #11, check 26) |
| S-205 | Suggestions in github.dev from the funground extension (S-197 route B) | done (funground-web PR #8): completion, hover, signature help, COLORS/CONSTANTS, colours and option words in quotes, from the runtime's `completions.json`; 13 tests with a stand-in API; end-to-end (site mode) passes; extension 0.2.0, `.vsix` 64 KB. Real github.dev check (P1) and Marketplace publish: the maintainer |
| S-206 | Gallery example pages: a breadcrumb, Previous and Next, back to the gallery (maintainer, 15 Oct) | done (site PR #9, deployed): breadcrumb, Previous/Next top and bottom, back to the topic; guide links to an example's heading now go to its page (two were dead anchors); 1710 links OK, strict build clean, 1366 and 390 wide checked |
| S-207 | Play: Previous and Next beside the example picker (maintainer, 15 Oct) | done (site PR #12, live): ‹ › through the 115 examples, named in tooltips, drafts kept, hidden for blank and shared sketches |
| S-189 | Play on phones, the core (pulled in, maintainer, 15 Oct: "In the mobile size, the Play loses the editor completely and the sketch size is too small"; measured: editor 0 px tall, picture 68 x 44 at 390 wide): stacked layout under 900 px, picture first at the full width, editor below at a usable height | in progress |
| S-168 | Polish: toolbar buttons sized for the page; Reset shown only when the code differs (check what S-187 already did) | done (site PR #12): status one line with an ellipsis, toolbar one row (50 px) at 1366, nothing overflows at 390; Reset after an edit was already so, now tested |

Order: S-201 and S-204 (the editor bundle), then S-203, S-202 and S-200 (the page and the preview); S-205 alongside, in
its own repository; S-206 alongside (only `tools/assemble.py`); S-207 after S-202. One builder at a time on the site, because the stories share `play.js` and `test_editor.mjs`.

Acceptance for the sprint: `test_editor.mjs` green with a check for each story; the preview's README and the site's
README list the `guides` message; the extension's `.vsix` builds and its test passes; a local trial by the maintainer
before sign-off (Sprint 25 finding 1).

- [x] S-200
- [x] S-201
- [x] S-202
- [x] S-203
- [x] S-204
- [x] S-205
- [x] S-206
- [x] S-207
- [x] S-168
- [ ] S-189
