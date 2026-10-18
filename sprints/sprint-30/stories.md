# Sprint 30 — Video pieces and pictures (E-33, E-35, E-14, E-22)

**Dates:** planned 17 October 2026 (the maintainer away; built autonomously inside decided scope). Work in funground,
`funground-web` and `funground-hq.github.io`. Each story ships when it is checked.

**Goal:** a take moves between sketches without leaving the browser, the words piece plays a take with its sound, the
camera gains an edge view, and learners get a step-by-step route from pixels to marks.

**Decisions:** D-107, D-108, D-109 (takes, My files, load_clip), D-110 (pixels project, no new API), D-111 (edges).
Pending: D-106 (S-218 names; a proposal is written for the maintainer), D-113 (course and studio vocabulary).

| Story | Value | Status |
|---|---|---|
| S-224 | `f.filter("edges")`: the outlines in a picture or the camera | done, live 18 Oct (funground PR #16; gallery images-09) |
| S-221 | My files in Play: files a sketch saves are kept and usable by any sketch; Add file; download stays | building (a Sonnet subagent) |
| S-222 | Blow the words loads a take (video and sound) and stays simple | planned (after S-221) |
| S-223 | From pixels to marks: a six-step project opening in Play | planned |
| S-218 | Replace the background behind you | waits for D-106 (proposal in `docs/design/Background_Note.md`) |

Order: S-224 (small, funground) and the S-218 proposal first; S-221 (site and runner, a builder); then S-222; S-223
alongside. One heavy job at a time on this machine.
