# Sprint 16 review — release 0.1 (the maintainer's last requests)

**Dates:** 6–8 October 2026, on `main`. Written on 14 October, when the sprint was signed off; its two
unfinished stories had already moved to Sprint 23. **Signed off 14 October 2026.**

## Outcome

| Story | Result | Commit |
|---|---|---|
| S-127 Hide and show controls (D-067) | `visible()` / `visible(flag)` on every control; a hidden control is not drawn or usable, keeps its value, and the panel keeps its height (U1); the voice game shows its sliders only on the setup screen | `b18e03b` |
| S-128 Credits and sources | `CREDITS.md` (people and AI, software, sound libraries and methods, raga and tala sources, fonts, images); credits in chapters 16–17, project pages, README and the documentation front door; every external citation checked | `bff7fd1`, `604b76a` |
| S-132 Studio vocabulary: Ground, Mark, Rules, Play (D-069, D-070, D-071) | Ground (G1), Mark (K1–K3), Area and Grid (G2), Play as `f.variations` and `f.keep` with a recorded seed for every run (E1, E2); six studios written twice, guide chapter 19, an assessment | `b13919b`, `33c5a26`, `6a9b7e0`, `9c02bd5`, `d17d838` |
| S-129 Documentation for AI assistants | carried to Sprint 23; done there (13 Oct) | — |
| S-073 Release 0.1 | carried to Sprint 23; the alpha (0.1.0a1) shipped on 12 Oct; 0.1.0 is prepared in funground PR #5 | — |

**Tests:** each story's commit ran the full suite; the counts are in the commits.

## Decisions

D-067 (hide and show), D-068 (credits in one line in the README), D-069 and D-070 (the vocabulary), D-071 (Play
in 0.1): all accepted during the sprint.

## Retrospective

- The review was not written when the work finished, because the release was overtaken by the 0.2 web
  work (D-091). A sprint whose last story moves elsewhere should be reviewed and closed at that moment.
- S-132's four parts were merged one by one for review, which kept a large vocabulary change easy to check.

## Sign-off

**Signed off by the maintainer, 14 October 2026** ("Sign off pending sprints"). Sprint closed; S-073
continues in Sprint 23.
