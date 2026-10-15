# Sprint 27 — Play: fast and yours (E-35)

**Dates:** planned 15 October 2026. Work in `funground-hq.github.io` (the editor), `funground-run.github.io` (the
preview, for S-212) and `funground-web` (the runner, for S-210 and S-211). Each story ships when it is checked, then
is looked at on the live site, at a phone width too (Sprint 26 review, findings 1 and 2).

**Goal:** a learner who comes back finds Play quick, and leaves with their work: the picture shows before Python is
ready, a repeat visit starts from the device, a saved file reaches their computer, and their sketches stay listed.

**Decisions:** all taken in the Play roadmap (14 Oct): work stays on the learner's device, with no account or server;
the runtime is cached, with the update rule in `design/Play_Roadmap.md`. No new public funground name. The preview gets
one new message (`file`), ignored by older editors.

| Story | Value | Status |
|---|---|---|
| S-209 | The picture before Python is ready | done (site PR #17, live): the example's gallery picture, tagged, with the loading status over it; only when the code is the example's own |
| S-210 | The runtime kept on the device, replaced when a new version is ready | **rolled back, 15 Oct**: built and tested locally (preview PR #6, site PR #22, checks 51-54; repeat visit 5-6 s against about 14 s); on GitHub Pages it first never installed (Cache.addAll failed), then, once installed (preview PR #7), a first visit hung while loading Python, not reproduced locally even with compression. Reverted (#8), then a pass-through worker (#9) that caches nothing and frees stuck browsers. Next: find the cause with logging from the live preview before bringing it back |
| S-211 | Fonts fetched only when a sketch draws text | built, not effective on GitHub Pages yet (funground-web PRs #9, #10): fonts are lazy files with a fail-safe; GitHub Pages compresses them in transit, so the size check fails and Play loads them at start-up (as before, nothing broken). Option B (a small private funground change, fetching a font when first opened) awaits the maintainer |
| S-212 | `f.save()` in Play gives you the file; a Save picture button | done (funground-web PR #9, preview PR #5, site PR #19, live): "Saved poster.png - Download" lines, replaced when saved again, no automatic downloads; Save picture downloads the frame; Pillow loads for GIF saves |
| S-213 | My sketches: a list kept in this browser, download and open `.py` | done (site PR #20, live): a My sketches group in the picker; New, Open .py, Rename, Duplicate, Download .py, Delete with Undo, Keep as my sketch; one localStorage key; a line if storage fails |

Order: S-209 and S-212 first (the editor and the preview), S-211 alongside in funground-web; then S-210 (it caches
what S-211 changes); then S-213. One builder at a time per repository.

Acceptance for the sprint: `test_editor.mjs` green with a check for each story; a repeat visit measured against the
3 s budget; the maintainer's trial on the live site.

- [x] S-209
- [ ] S-210
- [ ] S-211
- [x] S-212
- [x] S-213
