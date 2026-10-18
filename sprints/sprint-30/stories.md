# Sprint 30 — Video pieces and pictures (E-33, E-35, E-14, E-22)

**Dates:** planned 17 October 2026 (the maintainer away; built autonomously inside decided scope). Work in funground,
`funground-web` and `funground-hq.github.io`. Each story ships when it is checked.

**Goal:** a take moves between sketches without leaving the browser, the words piece plays a take with its sound, the
camera gains an edge view, and learners get a step-by-step route from pixels to marks.

**Decisions:** D-107, D-108, D-109 (takes, My files, load_clip), D-110 (pixels project, no new API), D-111 (edges).
Taken 18 Oct: D-106 (S-218 names approved), D-113 b (S-226), D-114 b (S-211, fonts when first opened), D-101 a (S-228). Pending: D-115 (help for the cut-out, S-227 in the backlog).

| Story | Value | Status |
|---|---|---|
| S-224 | `f.filter("edges")`: the outlines in a picture or the camera | done, live 18 Oct (funground PR #16; gallery images-09) |
| S-221 | My files in Play: files a sketch saves are kept and usable by any sketch; Add file; download stays | done, live 18 Oct (site PR #27, funground-web PR #13: a rewritten kept file is reported again; built by a Sonnet subagent, reviewed) |
| S-222 | Blow the words loads a take (video and sound) and stays simple | done, live 18 Oct (funground PR #17): loads take.gif + take.wav, breath per frame from the sound, G saves one loop |
| S-223 | From pixels to marks: a six-step project opening in Play | done, live 18 Oct (funground PR #17; gallery area Pixels to marks, guide project 10) |
| S-218 | Replace the background behind you: `pic.remove_color()` and `pic.remove_background()` | building (D-106 accepted 18 Oct) |
| S-226 | The course's studio step: Extend with `f.variations` and `f.mark`, Keep through `f.keep` (D-113 b) | planned 18 Oct |
| S-211 | Fonts on demand where the host compresses them: fetched the first time funground opens one (D-114 b) | carried in 18 Oct |
| S-228 | JPEG pictures in the browser checked with a tolerance (D-101 a) | planned 18 Oct |

Added 18 Oct, in this order: S-218, S-228 (small), S-211, S-226. Earlier order: S-224 (small, funground) and the S-218 proposal first; S-221 (site and runner, a builder); then S-222; S-223
alongside. One heavy job at a time on this machine.
