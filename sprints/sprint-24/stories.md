# Sprint 24 — the website's identity and the Play editor (E-34)

**Dates:** planned 13 October 2026. **Goal:** the site looks like what funground is for (a sketchbook, not an API
manual), and the Play editor gives the code and the picture the screen. Work happens on branch
`design/site-identity` of funground-hq.github.io, a story per commit; nothing merges to its `main` (which deploys)
before the maintainer's decisions and sign-off.

**Brief:** `design/` on that branch (made in claude.ai, 13 Oct): `DESIGN.md`, `PLAY_EDITOR.md`, `BACKLOG.md`,
`tokens.json`, mockups (the acceptance pictures). Process for visual work: the `funground-design` skill there.

**Decisions:** D-096 identity, D-097 logo, D-098 hosted fonts, D-099 navigation: all **accepted (b)** on 13 Oct,
after the maintainer reviewed local previews. A second design package (13 Oct) rationed the shadows and added the
origin band; the maintainer's review then shaped the home page (three ways to run, the course card, "Made for
learning and teaching"), removed the Showcase, and made Play the editor alone.

**CI (D-095):** the site builds on a pull request (Linux, a few minutes, nothing deployed). The built site is
downloaded from that build and screenshotted locally with `tools/design_shots.mjs`; MkDocs is not installed here.

| Story | Value | Status |
|---|---|---|
| S-184 | (SITE-C-01) Play's duplicate id fixed; the editor test now carries the heading and fails on the old bug | built, verified locally (`test_editor.mjs` 10 of 10; the new check fails with the old id) |
| S-185 | (SITE-C-02) stylesheet, fonts, logo | done: verified on built previews (strict build, links, no sideways scroll, night sticker fixed) |
| S-186 | (SITE-C-03) the home page (install line updated for PyPI) | done: revised design plus the maintainer's changes; template links all resolve |
| S-187 | (SITE-C-04) the Play layout, with a design note | done: editor only (no sidebars, footer or tab row), split, zoom, messages above the picture, help popover, status with spinner, keys, restart notice; `design/Play_Layout_Note.md`; `test_editor.mjs` 12/12 |
| S-190 | (SITE-C-07) the gallery index | planned |
| S-191 | (SITE-C-08) sketch panels on example pages | planned |

Later: S-188 (picker with thumbnails), S-189 (Play layouts and phones). In funground's own backlog as candidates:
S-192 (square thumbnails and loops), S-193 (Try this notes).
