---
name: funground-sdlc
description: How work is planned, built, recorded and reviewed in any funground-hq repository (funground, funground-web, funground-cairo-wasm, and later ones) - sprints, stories, ADRs, decision log, design notes, sprint reviews, model and agent economy, branch and push rules, what to decide alone and what to bring to the maintainer. Use at the start of every session in a funground-hq repository, before planning or changing anything.
---

# funground SDLC (portable)

Canonical copy: `funground-hq/funground` `.claude/skills/funground-sdlc/SKILL.md`. Sibling repositories
carry a copy; when the copies differ, the canonical one wins. The full process of the main project is
`docs/PROCESS.md` in `funground-hq/funground`; this skill is its portable core. Read the repository's
own `CLAUDE.md` for what is specific to it.

## 1. Working style

- **Work autonomously inside the process.** Plan, build, test, document and commit without asking,
  as long as each step follows this skill. Stop and ask only for the decisions in section 6.
- **Leave a trail a reviewer can follow in an hour:** every change is traceable to a story, every
  non-obvious choice to a design note, ADR or decision row.
- **Measure, do not assert.** Claims about speed, size, fidelity or compatibility come with a number
  and how it was measured, or are marked **unverified**.
- **Report honestly:** failures with their output, skipped steps as skipped, guesses as guesses.

## 2. Models and agents (use the backend economically)

| Who | Model | Takes |
|---|---|---|
| main session | the strongest available (Opus) | orchestration, design, ADRs, decisions, briefs, reviewing every subagent's diff, all commits and pushes, talking to the maintainer |
| builder subagent | Sonnet | a well-defined coding task whose design is pinned: code, tests, docs for one story |
| mechanical subagent | Haiku | fully specified edits: renames, ticks, table updates, find-and-replace |
| test runner | Haiku | running tests and summarising failures; changes nothing |
| researcher | Sonnet (Opus for judgement-heavy studies) | web or code research with sources |

Rules:
- The main session writes each brief: goal, files to touch and not touch, the command that proves
  it done, and when to stop and report.
- Subagents never commit or push. The main session reviews the diff, reruns the tests, commits.
- One- or two-command edits stay in the main session; delegating them costs more than it saves.
- Run independent subagents in parallel; never two agents on the same files.
- Use `.claude/agents/*.md` definitions when the repository has them.

## 3. Documents every repository keeps

Create what is missing on first use; keep them true in the same change as the code.

| Path | Holds |
|---|---|
| `CLAUDE.md` | What this repository is, its relation to funground, build and test commands, local rules |
| `docs/design/Architecture.md` | The architecture as built: components, boundaries, data flow, a diagram |
| `docs/design/<Topic>_Note.md` | One per subsystem or non-obvious mechanism: problem, design, rejected alternatives, invariants, limits, where the tests are |
| `docs/design/ADR-nnn-<slug>.md` | Long-lived decisions. Sections: Status · Context · Options · Decision · Consequences. Never edited after acceptance except its status; a change of mind is a new ADR that supersedes it |
| `docs/design/Decision_Log.md` | One row per decision: ID, date asked, question, options, recommendation, outcome, date decided, where the reasoning lives; an **Open** list at the end |
| `docs/backlog/stories.md` | Every story: ID, epic, one-sentence value, tasks, acceptance line, status |
| `sprints/sprint-NN/stories.md` | The sprint goal, its stories with task checkboxes, decisions it needs |
| `sprints/sprint-NN/review.md` | Done / not done and why, test results, measurements, decisions taken, findings, which stories subagents built, a short retrospective |
| `spikes/NN_name/` + `spikes/RESULTS.md` | Time-boxed experiments; conclusions promoted into `docs/design/` |
| `CHANGELOG.md` | User-visible changes, once there is anything to release |

**IDs.** Stories (`S-nnn`), epics (`E-nn`) and the maintainer's decisions (`D-nnn`) are numbered in
`funground-hq/funground` (`docs/backlog/stories.md`, `docs/design/Decision_Log.md`); refer to them by
those IDs. A sibling repository's own records use its prefix (e.g. `WEB-ADR-001`, `CW-D-001`); a new
story found there is written as a candidate in its own backlog and promoted to an `S-nnn` by the main
funground session. IDs are never reused or renumbered.

## 4. Sprint lifecycle

1. **Plan:** copy the chosen stories into `sprints/sprint-NN/stories.md` with tasks unchecked; state
   the goal and the decisions it needs. A story is *ready* when it has an epic, a value sentence,
   tasks and a testable acceptance line.
2. **Build:** tick tasks as they land; a story that adds a subsystem, dependency or non-obvious
   mechanism gets its design note in the same change.
3. **Review:** write `review.md`. *Done* means all tasks ticked, tests added and green, docs and design
   notes updated, decisions recorded.
4. **Close:** a sprint is closed only after the maintainer has read the review and signed it off.
5. **Carry over:** unfinished stories go back to the backlog with a note; nothing slides silently.

A spike is a story whose deliverable is evidence: a question, pass/fail criteria set *before* the
work, the measurements, and a recommendation. Spikes change no product code outside their branch.

## 5. Git

- Commit as soon as a logical change exists: one story or concern per commit; the message says why.
- Stage named paths only; never `git add -A`.
- **Work on a branch of the repository you were started in and push that branch.** Never push to
  `main` of another repository, never change a repository you were not asked to change (sibling
  repositories read `funground-hq/funground`; they do not write to it). Merging to `main` is by pull
  request, reviewed by the main session or the maintainer.
- Never rewrite published history, force-push, tag or publish a package without the maintainer.
- End commit messages with the co-author line the harness asks for.

## 6. Decisions

**Decide alone, and log it** (as "decided by Claude" with reasons, for review at sign-off): routine
design and engineering choices inside a story, tool and build choices inside a spike, test layout.

**Bring to the maintainer:** new runtime dependencies or changes to what users install; changes to
funground's public API or a pinned row of its `Semantic_Contract.md`; anything that changes golden
images on purpose; scope changes to a release; anything irreversible or public beyond pushing a work
branch (new repositories, publishing, tags, settings, secrets, costs); closing a sprint.

Present every pending decision in this order: **Context** (why now, what happens if not decided) ·
**Options** (always including "keep current behaviour") · **Trade-offs** (with measurements) ·
**Recommendation** · **Why** (and what would change it). Add a `pending` row to the decision log
before asking; when answered, record the outcome in the same change that applies it. A
recommendation not yet accepted is never applied to code.

## 7. Rules from the main project that always apply

- funground's semantic contract and its golden images are the reference; another implementation is
  measured against them, never the other way round.
- Learner code never changes shape to suit a platform (no `async`/`await` in sketches).
- Examples are original (D-026): never copy or translate an example from another project, whatever
  its licence.
- Learner-facing text is plain English: short sentences, British spelling in prose, American in API
  names (`color=`).
- No personal data (emails, names beyond the maintainer's chosen credit) in documents.

## 8. Where the session runs

- **The maintainer's Windows machine:** never run plain `python`/`py` (it starts an installer), never
  open files with their default app, never run installers or install fonts; use a venv's full path.
  The machine is slow and short of memory: run targeted tests, one heavy job at a time.
- **A cloud sandbox:** installing toolchains inside the sandbox is fine. Record every tool's exact
  version in the repository (README or RESULTS.md) so the build can be reproduced, and turn a
  working recipe into a CI workflow.
