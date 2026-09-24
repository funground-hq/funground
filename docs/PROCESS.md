# Playground SDLC process

How work on Playground is planned, tracked, built and reviewed from Sprint 0 onward.

## Hierarchy

```
Theme  (TH-n)   a long-lived area of value, e.g. "Teaching Core Stability"
 └─ Epic  (E-nn)   a deliverable outcome inside a theme, usually spanning several sprints
     └─ Story (S-nnn)  a unit of learner- or maintainer-visible value, finishable in one sprint
         └─ Task  (S-nnn.k)  a concrete engineering step; the checklist that proves the story done
```

IDs never change or get reused. A story belongs to exactly one epic; an epic to exactly one theme.

## Folders

| Path | Holds |
|---|---|
| `docs/PROCESS.md` | This document |
| `docs/backlog/themes_and_epics.md` | Themes, epics, the phase each epic belongs to, status |
| `docs/backlog/stories.md` | Every story with its tasks, epic, sprint assignment and status — the single backlog |
| `docs/design/` | Architecture document, architecture review, semantic contract, ADRs (`ADR-nnn-*.md`), design notes |
| `docs/qa/` | Test strategy, golden-image policy, CI matrix, QA checklists |
| `docs/reference/` | Learner-facing and historical material: Quick Reference, v0.5 README |
| `sprints/sprint-NN/` | One folder per sprint: `stories.md` (the sprint's story set with task status), `review.md` (what shipped, what didn't, findings, decisions, retro). A sprint may add its own docs here |
| `spikes/` | Time-boxed experiments with their own venvs; results in `spikes/RESULTS.md`, conclusions promoted into `docs/design/` |
| `src_v0.5/` | Pristine v0.5 baseline, never edited; the thing the compatibility contract is measured against |

## Phases and sprints

Phases come from the architecture document and give the roadmap its shape; sprints are the
time-boxes that deliver them. A phase spans one or more sprints and ends when its exit criterion
(recorded in `themes_and_epics.md`) is met, not when its sprints run out.

| Phase | Goal | Sprints |
|---|---|---|
| 0 — Stabilise v0.5 | Freeze the API and semantics as executable tests | Sprint 0 |
| 1 — Refactor core | `Sketch`, platform split, `GraphicsState`, draw-op IR — no learner-visible change | Sprints 1–2 |
| 2 — First vector rasteriser | ADR-001 executed: Cairo via the IR, transforms/paths/export | Sprints 3–4 |
| 3 — Creative media | Images, typography, SVG, sound, document model | Unscheduled (directional) |
| 4 — GPU / 3D | OpenGL renderer, shaders, 3D | Unscheduled (directional) |

Sprint length is set by the maintainer; default one week. Sprint numbering is global (`sprint-00`, `sprint-01`, …).

## Sprint lifecycle

1. **Planning** — copy the chosen stories from the backlog into `sprints/sprint-NN/stories.md`
   with their tasks unchecked; record the sprint goal and any DECISION rows that must be resolved.
2. **Build** — tasks are checked off in the sprint's `stories.md` as they land; the backlog's
   status column is updated when a whole story completes.
3. **Review** — `sprints/sprint-NN/review.md` records: stories done / not done and why, test
   results (counts, CI), measurements, decisions taken (with links to ADRs or contract rows),
   findings that change later sprints, and a short retrospective.
4. **Carry-over** — unfinished stories return to the backlog with a note, never silently slide.

## Definitions

**Ready** — a story has an epic, a one-sentence value statement, tasks, and a testable acceptance
line. Any DECISION it depends on is named.

**Done** — all tasks checked; tests added or updated and the whole suite green on the CI matrix;
`docs/design/Semantic_Contract.md` updated in the same change if a semantic moved; goldens
regenerated only as a deliberate, reviewed act.

## Rules that outrank the documents

- The v0.5 source and the test suite are authoritative when a document disagrees with them.
- Learner code in `examples/session1/` never changes to make a test pass.
- A change to a pinned semantic is a contract change: ADR or contract row first, then code.
- Backend types (`pygame.Surface`, `cairo.Context`, …) never appear in `playground/api.py` or in tests of public behaviour.
