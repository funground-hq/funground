# funground SDLC process

How work on funground is planned, tracked, built and reviewed from Sprint 0 onward.

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
| `docs/Roadmap.md` | The arc to 1.0: phases, releases, what is directional, decisions ahead (D-014) |
| `docs/backlog/themes_and_epics.md` | Themes, epics, the phase each epic belongs to, status |
| `docs/backlog/stories.md` | Every story with its tasks, epic, sprint assignment and status — the single backlog |
| `docs/developer/` | Developer guide: set-up, architecture as built, adding a feature, testing |
| `docs/design/` | Architecture document, architecture review, semantic contract, ADRs (`ADR-nnn-*.md`), `Decision_Log.md`, design notes |
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
| 1 — Refactor core and replace the renderer | Three golden-verified checkpoints (D-007): **Sprint 1** `Sketch`, platform split, `GraphicsState`, `Color` under unchanged pygame drawing → **Sprint 2** draw-op IR with `LegacyPygameRenderer`, goldens byte-identical → **Sprint 3** `CairoRenderer` + contract changes D-003/4/5 + one golden regeneration, HiDPI, headless, export; legacy renderer deleted | Sprints 1–3 |
| 2 — Feature growth on the vector model | Public transforms, `save`/`restore`, paths, off-screen canvas, Quick Reference v0.6 | Sprint 4+ |
| 3 — Creative media | Images, typography, SVG, sound, document model | Unscheduled (directional) |
| 4 — GPU / 3D | OpenGL renderer, shaders, 3D | Unscheduled (directional) |

Sprint length is set by the maintainer; default one week. Sprint numbering is global (`sprint-00`, `sprint-01`, …).

## Sprint lifecycle

1. **Planning** — copy the chosen stories from the backlog into `sprints/sprint-NN/stories.md`
   with their tasks unchecked; record the sprint goal and any DECISION rows that must be resolved.
2. **Build** — tasks are checked off in the sprint's `stories.md` as they land; the backlog's
   status column is updated when a whole story completes.
   **Design notes:** a story that adds a subsystem, a new dependency or a non-obvious mechanism
   gets a design note in `docs/design/<Topic>_Note.md` (or an update to an existing one) in the same
   sprint: problem, design, rejected alternatives, invariants, limits, where the tests are. The
   developer guide (`docs/developer/`) is kept true to the code in the same change.
3. **Review** — `sprints/sprint-NN/review.md` records: stories done / not done and why, test
   results (counts, CI), measurements, decisions taken (with links to ADRs or contract rows),
   findings that change later sprints, and a short retrospective. Alongside it,
   `sprints/sprint-NN/reviewers_guide.md` tells the maintainer how to review the sprint's code in
   about an hour: how to verify the sprint's central claim first, which commits to read in what
   order, a map of what changed, what to scrutinise file by file, what the author would flag, the
   open decisions, and a sign-off checklist. **A sprint is closed only after the maintainer has
   reviewed the retrospective and signed off the guide's checklist.**
4. **Carry-over** — unfinished stories return to the backlog with a note, never silently slide.

## Definitions

**Ready** — a story has an epic, a one-sentence value statement, tasks, and a testable acceptance
line. Any DECISION it depends on is named.

**Done** — all tasks checked; tests added or updated and the whole suite green on the CI matrix;
`docs/design/Semantic_Contract.md` updated in the same change if a semantic moved; goldens
regenerated only as a deliberate, reviewed act. **From Sprint 5 (D-015):** a story that adds a
public feature also adds its Examples Gallery sketch (with golden and IR snapshot) and its User
Guide section, in the same story.

## Who does what: models and agents

Work is matched to the model it needs (maintainer, 26 Sept 2026). The main session plans, and
subagents defined in `.claude/agents/` do the routine parts, each on a fixed model:

| Agent | Model | Takes |
|---|---|---|
| main session | Opus | design, contract rows, decisions put to the maintainer, briefs, reviewing every subagent's diff, all commits |
| `story-builder` | Sonnet | a story whose design and contract row are pinned: code, tests, gallery example, guide and reference |
| `mechanical-editor` | Haiku | fully specified edits: renames, find-and-replace, status ticks, table updates |
| `test-runner` | Haiku | running the suite and summarising failures; changes no files |

Rules:

- **The main session writes the brief:** scope, files to touch and not to touch, and the command
  that proves it done.
- **Subagents never commit.** The main session reviews the diff, reruns the suite, and commits.
  Authorship and the quality gate are unchanged.
- **A subagent stops and reports** on ambiguity or on a failure it cannot explain; the main
  session takes over.
- **Anything irreversible or public stays in the main session, even when the steps are mechanical:**
  history rewrites, pushes, publishing a package, creating or changing remote repositories, and
  deleting data. A mistake there cannot be taken back after review (maintainer, 26 Sept 2026).
- **Edits of one or two commands stay in the main session.** Delegating them costs more than it
  saves.
- **Each sprint review names the stories built by subagents,** so their track record can be judged.
- **Each sprint review adds its entry to the sprint log in [AI-USAGE.md](../AI-USAGE.md):** what the
  maintainer asked for and what came of it, in a few lines (D-024). Nothing personal goes in it.

## Decisions

Two records are kept, and both are part of the definition of done for any story that needs a call
from the maintainer.

### Architecture Decision Records — `docs/design/ADR-nnn-<slug>.md`

For decisions that shape the code for a long time (a library, a boundary, a data model, a
non-obvious semantic). One file per decision, numbered in the order raised, never renumbered.
Sections, in this order: **Status** (Proposed → Accepted / Rejected / Superseded by ADR-mmm, with
dates) · **Context** · **Options** · **Decision** · **Consequences**. An ADR is never edited
after acceptance except to change its status; a change of mind is a new ADR that supersedes it.

### Decision log — `docs/design/Decision_Log.md`

One row for *every* decision put to the maintainer, large or small, including those whose reasoning
lives in an ADR, a contract row or a sprint document. Columns: ID (`D-nnn`), date asked, the
question, the options offered, the recommendation, the outcome, date decided, and where the
reasoning lives. A trailing **Open** list shows what is still pending. The log is the index; the
linked document is the argument.

### Decisions Claude may take (D-034, Phase 3)

The maintainer asked for minimal intervention during Phase 3. Routine design calls are made by Claude,
pinned in the contract, and logged as "decided by Claude (D-034)" with the reasons, for review at
sprint sign-off. Still brought to the maintainer, in the format below: new runtime dependencies or
changes to the base install; changes to the frozen v0.5 API; anything irreversible or public beyond
routine pushes to `main`; scope changes to release 0.1; closing a sprint.

### How a pending decision is presented

Whenever work needs a call the maintainer has not made, it is raised — in the sprint's `stories.md`,
in `review.md`, or in conversation — using this shape, every time, in this order:

1. **Context** — what the decision is about, why it has come up *now*, and what happens if it is not made.
2. **Options** — each one named, with a one-line description; the option that preserves current behaviour is always listed even if it is not recommended.
3. **Trade-offs** — a table or list comparing the options on the axes that matter for *this* decision (learner impact, install size, speed, compatibility, effort, reversibility …), with measurements where they exist.
4. **Recommendation** — one option, stated plainly.
5. **Why** — the reasons, and what would change the recommendation.

Then: add a `pending` row to the decision log before asking; when the maintainer answers, set the
outcome and date in the same change that applies it (contract row, ADR status, story status).
A recommendation the maintainer has not yet accepted is never applied to code.

### When something *is* a decision

Anything that changes a pinned row of `Semantic_Contract.md`; adds or removes a runtime
dependency; changes what the base install contains; changes a public name or signature; picks
between providers; or regenerates golden images. Routine engineering choices inside a story are not
decisions and are not logged.

## Rules that outrank the documents

- The v0.5 source and the test suite are authoritative when a document disagrees with them.
- **Examples are original** (D-026). Example code is published as CC0, which is only honest for code
  that is ours. So: never copy or translate an example from another project, website, book or
  tutorial, whatever its licence. Write each example from the feature it shows, not from a sketch
  seen elsewhere; an example "in the style of" p5 or DrawBot is written fresh. Ideas and standard
  algorithms are free to use; their written expression is not. Every new or changed example is
  checked with `tools/check_originality.py` before its story is done, and the sprint review
  records the result in `docs/qa/Example_Provenance.md`. If outside code is ever truly needed, it
  is a decision for the maintainer, and the file carries its source and licence in a header.
- **Commit as soon as a logical change exists** — one story or concern per commit, message states
  the context. Never let two stories' changes sit staged together (Sprint 1 retro).
- Learner code in `examples/session1/` never changes to make a test pass.
- A change to a pinned semantic is a contract change: ADR or contract row first, then code.
- Backend types (`pygame.Surface`, `cairo.Context`, …) never appear in `funground/api.py` or in tests of public behaviour.
- **Providers are selected per capability and workload, not per framework** (D-010). Interactive
  raster, vector export, shaping and font model may be different libraries behind the one IR;
  learners must never see the seam. An engine is chosen by measurement (a bake-off spike) and
  recorded in an ADR; "reference implementation" means the current best-measured consumer of the
  IR, not a commitment.
- **Internal capability first, public API later.** A concept (transform, path, clip, text run, state stack) enters the IR and the internal model in the sprint that needs it; its learner-facing vocabulary is a separate, later story. The architecture settles before the API grows.
- The test hierarchy, top to bottom: public API semantics → draw-op IR snapshots (the cross-backend contract) → per-backend semantic tests → per-backend golden images. Two correct renderers may differ in pixels; they may not differ in ops.
