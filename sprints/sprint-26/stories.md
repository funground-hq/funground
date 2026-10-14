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
| S-200 | Play's first visit: a starter sketch with three "change this" comments, a "New to funground? First steps" link | planned |
| S-201 | The arguments while typing, and help on hover | planned |
| S-202 | Guides: the mouse's x and y over the picture, and a grid (with the preview) | planned |
| S-203 | Errors where they happen: the line marked, the wrong name underlined, a link to the errors page | planned |
| S-204 | Play at night in the site's code colours | planned |
| S-205 | Suggestions in github.dev from the funground extension (S-197 route B) | planned |
| S-206 | Gallery example pages: a breadcrumb, Previous and Next, back to the gallery (maintainer, 15 Oct) | planned |
| S-207 | Play: Previous and Next beside the example picker (maintainer, 15 Oct) | planned |
| S-168 | Polish: toolbar buttons sized for the page; Reset shown only when the code differs (check what S-187 already did) | planned |

Order: S-201 and S-204 (the editor bundle), then S-203, S-202 and S-200 (the page and the preview); S-205 alongside, in
its own repository; S-206 alongside (only `tools/assemble.py`); S-207 after S-202. One builder at a time on the site, because the stories share `play.js` and `test_editor.mjs`.

Acceptance for the sprint: `test_editor.mjs` green with a check for each story; the preview's README and the site's
README list the `guides` message; the extension's `.vsix` builds and its test passes; a local trial by the maintainer
before sign-off (Sprint 25 finding 1).

- [ ] S-200
- [ ] S-201
- [ ] S-202
- [ ] S-203
- [ ] S-204
- [ ] S-205
- [ ] S-206
- [ ] S-207
- [ ] S-168
