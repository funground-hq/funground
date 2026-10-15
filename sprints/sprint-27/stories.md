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
| S-209 | The picture before Python is ready | planned |
| S-210 | The runtime kept on the device, replaced when a new version is ready | planned |
| S-211 | Fonts fetched only when a sketch draws text | planned |
| S-212 | `f.save()` in Play gives you the file; a Save picture button | planned |
| S-213 | My sketches: a list kept in this browser, download and open `.py` | planned |

Order: S-209 and S-212 first (the editor and the preview), S-211 alongside in funground-web; then S-210 (it caches
what S-211 changes); then S-213. One builder at a time per repository.

Acceptance for the sprint: `test_editor.mjs` green with a check for each story; a repeat visit measured against the
3 s budget; the maintainer's trial on the live site.

- [ ] S-209
- [ ] S-210
- [ ] S-211
- [ ] S-212
- [ ] S-213
