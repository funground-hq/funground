# How AI is used to build funground

funground is built by one maintainer, Samir Joshi, working with Anthropic's Claude through
[Claude Code](https://claude.com/claude-code). This file says how, so that teachers, contributors
and reviewers can judge the work for themselves. The short version is in the
[README](README.md#ai-disclosure). This file was adopted by decision D-024.

## Who does what

| | The maintainer | Claude |
|---|---|---|
| Direction | Sets goals, scope and priorities; changes the plan | Proposes plans, backlogs and sprint scopes |
| Decisions | Takes every decision about behaviour, names, dependencies, releases and publishing | Presents each decision as context, options, trade-offs, a recommendation and the reasons ([process](docs/PROCESS.md#how-a-pending-decision-is-presented)) |
| Code, tests and docs | Reviews; asks for changes | Writes almost all of it |
| Checking | Reviews each sprint's review and reviewer's guide, and signs off before a sprint closes | Runs the full test suite before every commit; reports results as they are, failures included |
| Public actions | Approves (repository, release) | Carries them out only after approval |

Every decision, with the options offered and the outcome, is recorded in
[docs/design/Decision_Log.md](docs/design/Decision_Log.md). Longer arguments live in the
[architecture decision records](docs/design/).

## Models

| Model | Role | When |
|---|---|---|
| Claude Opus 5 | Main session | Planning to the end of Sprint 2 (24–25 Sept 2026) |
| Claude Fable 5.1 | Main session, including a multi-agent workflow for Sprint 4 and Spike 08 | End of Sprint 2 to the Sprint 4 review (25 Sept 2026) |
| Claude Opus 5.5 | Main session | End of Sprint 4 to mid-Sprint 6 (25–26 Sept 2026) |
| Claude Fable 5.1 | Main session again | Sprint 6, from 30 Sept 2026 |
| Claude Sonnet 5 | Sub-agent building well-specified stories (S-075, S-054, S-052), reviewed by the main session before commit | Sprint 6 onwards |

The model that helped with each commit is named in its `Co-Authored-By` line. During early planning
the maintainer also relayed reviews from a separate AI assistant; its points were weighed in the
design documents like any other review.

**Where funground started.** The starting point, *playground* v0.5, was itself written by a
different AI assistant at the maintainer's direction: the library, its examples and its Quick
Reference. funground's Session-1 sketches (`examples/session1/01`–`12`) follow that Quick
Reference topic by topic, and `examples/hello_visual.py` comes from the v0.5 package. No example
was copied from p5.js, Processing, DrawBot or any other project.

## Instructions that steer the work

- **Anthropic's Claude Code system instructions.** These are Anthropic's own and are not
  reproduced here.
- **This project's instructions,** all in the repository:
  - [docs/PROCESS.md](docs/PROCESS.md): the development process, the Definition of Done, how
    decisions are presented, and "Who does what", which says which work goes to which model.
    Irreversible or public actions always stay with the main session.
  - [.claude/agents/](.claude/agents/): the sub-agent definitions (story builder, mechanical
    editor, test runner), each with its model and rules. For example, sub-agents never commit.
  - [docs/design/Semantic_Contract.md](docs/design/Semantic_Contract.md): the pinned behaviour
    every change must keep.
- **Standing preferences given in conversation,** kept by Claude Code between sessions:
  - commit often, one story per commit;
  - present decisions one at a time;
  - send routine work to smaller models;
  - never publish or rewrite history without approval.

## How the output is checked

AI-written tests checking AI-written code is a real risk. funground reduces it in four ways:

1. **The v0.5 library was frozen as tests before any change** (Sprint 0). New code must keep the
   old behaviour unless a recorded decision changes it.
2. **Pixel-exact golden images and drawing-operation snapshots.** A change that moves a single
   pixel or operation fails, and regenerating one is a deliberate, reviewed act.
3. **Examples as tests.** Every public function has a gallery example that runs in the test suite,
   and every code block in the User Guide runs as a test. Writing examples found bugs that unit tests
   had missed (Sprint 5 review).
4. **Human review.** The maintainer reads each sprint's review and reviewer's guide, which are
   written to be checked in about an hour, and signs off before the sprint closes.

**Known limits:**
- CI runs every push on Windows, macOS and Linux with Python 3.11–3.14, all green since 30 Sept 2026. HiDPI on real macOS and Linux screens is still untested.
- The browser track is research only.
- AI-written code can occasionally echo code the model was trained on. For short teaching
  sketches the risk is small, and ideas such as a bouncing ball are not copyrightable, but it
  cannot be ruled out entirely.
- Copyright in purely AI-generated material is unsettled and differs between countries. The
  licences cover everything the maintainer can own. Anthropic's terms, like most AI providers',
  give the customer the rights in the output; no one else has a claim to funground's material.

## Sprint log

A few lines per sprint: what the maintainer asked for, and what came of it. From Sprint 6 on, each
sprint review adds its entry here.

### Planning (24 Sept 2026)
- The maintainer asked for a critique of the proposed architecture. The result was an
  [architecture review](docs/design/Playground_Architecture_Review.md) and a revised plan.
- The maintainer asked for spikes, each in its own virtual environment, run unattended during a
  break. Spikes 01–05 tested pygame's limits, Skia versus Cairo and install cost
  ([results](spikes/RESULTS.md)).
- The maintainer asked for a full SDLC: themes, epics, stories, tasks, sprints, backlog, design
  and QA. They also asked for decisions to be explained one at a time, and accepted D-001–D-008.
  ADRs, a decision log and a fixed format for presenting decisions became part of the process.

### Sprint 0: freeze v0.5
- The v0.5 behaviour became executable tests: API, semantics, the Session-1 sketches and golden
  images.
- The maintainer's standing rule: commit often, in logical groups, as Samir Joshi.

### Sprint 1: the Sketch and the platform split
- Spike 06 proved text could be drawn from a bundled font, identical everywhere.
- The maintainer required a retrospective review and a reviewer's guide before any sprint closes.
- They kept v0.5's undocumented colour forms: pygame's namespace is not ours to trim.
- D-009: DejaVu Sans as the bundled font.
- D-010: the renderer choice was reopened for a broader bake-off, after the relayed AI review raised
  Blend2D.

### Sprint 2: the drawing-operation IR
- Spike 07 compared Cairo, Skia and Blend2D on the real IR. D-011: Cairo renders and exports;
  Blend2D stays an option to revisit.

### Sprint 3: Cairo, HiDPI, headless, export
- D-012: `text_size(n)` is an n-pixel em, the CSS, p5 and DrawBot convention.

### Sprint 4: the public vocabulary
- The maintainer stepped back to check parity with p5/Processing and DrawBot. The result was the
  Feature Map, seven new epics, and a browser-mode study inspired by Pyxel (Spike 08).
- The sprint was run as a multi-agent workflow, at the maintainer's request.
- D-013: the maintainer asked for a more descriptive name, which became `with saved_state():`.
- D-014: 1.0 is desktop, Cairo and 2D; the browser is a post-1.0 direction.

### Sprint 5: vocabulary, events and helpers
- D-015: the release comes with a User Guide and an Examples Gallery covering every feature.
- The maintainer asked for no workflow, story by story.
- D-016: the maintainer approved a contract change for p5-aligned event names.
- D-017: clarity over portability, so no `color_mode()`. D-018: p5/Processing curve names.
- Five bugs were found and fixed, three of them by writing gallery examples.

### Sprint 6: text layout, compositing, pictures, release preparation
- D-019: the first public release will be 0.1 on PyPI.
- D-020: `playground` was taken on PyPI. The maintainer weighed a dozen names and chose
  **funground**, `import funground as f`.
- The maintainer asked for routine work to go to smaller models. The result was the sub-agent
  definitions and the "Who does what" rules. The rename, fonts and pictures stories were built
  by Sonnet sub-agents and reviewed before commit.
- D-021: one picture type made with `create_graphics`. D-022: bundled bold and italic fonts.
- D-023: a public GitHub repository under `funground-hq`. Before the first push, history was
  rewritten to use the maintainer's GitHub no-reply address.
- The maintainer asked for this disclosure: a README section and this file (D-024 = B).
- D-025: after reviewing the dependencies' licences, the maintainer chose LGPL-2.1-or-later,
  the p5/Processing family's licence, and asked for the dependencies' own licences to be listed
  ([THIRD_PARTY_LICENSES.md](THIRD_PARTY_LICENSES.md)).
- D-026: example code is CC0, so learners can reuse it freely. The maintainer made it a condition
  that examples are checked to be original, now and in future. That became a process rule and
  an originality check ([docs/qa/Example_Provenance.md](docs/qa/Example_Provenance.md)).

### Sprint 7: CI, scripts, images, p5 modes (30 Sept – 1 Oct 2026)
- The maintainer widened release 0.1 to include Phase 3 (D-027) and closed Sprints 5 and 6.
- The maintainer took a run of decisions:
  - D-028: pygame-ce reads images, Pillow optional;
  - D-029: animated sketches or DrawBot-style scripts;
  - D-030: p5's drawing modes;
  - D-031: revisit colour mode, which the maintainer raised;
  - D-032: p5-style colour numbers;
  - D-033: funground is final.
- The maintainer asked for a gallery browser; it was built in funground itself.
- The maintainer reported two gallery problems (a dot that ran off-screen, an example in the wrong
  area); both were fixed.
- The maintainer asked for minimal intervention for the rest of Phase 3 (D-034). Claude then took
  routine design calls itself (D-035 and smaller review calls) and logged them for sign-off.
- All nine stories were built by Claude Sonnet 5 sub-agents from pinned contract rows. The Opus main
  session reviewed each one, and changed or added something in most of them.
- One sub-agent stopped every `python.exe` on the maintainer's machine. A rule now forbids it.

### Sprint 8: documents and pages (1 Oct 2026)
- Under D-034, Claude planned the sprint and decided the page API (D-036: DrawBot names, pages
  belong to scripts, no v0.5 change).
- Both stories were built by Claude Sonnet 5 sub-agents and reviewed by the main session. One
  measured number, script memory, corrected an estimate Claude had pinned too early.
- The maintainer asked how macOS and Linux were checked. The honest answer (CI runs them headless
  only) led to a release prerequisite: a manual run on real desktops.
- D-037, a new dependency for path booleans, went to the maintainer as D-034 requires.

### Sprint 9: path depth (1 Oct 2026)
- The maintainer chose skia-pathops for path booleans (D-037) after asking what was inside the
  library. A check of the wheel showed it is smaller than first stated (1.8 MB on Windows), and the
  answer was corrected.
- Claude decided the path API (D-038) and one exactness trade-off (D-039) under D-034.
- Three stories were built by Claude Sonnet 5 sub-agents. A builder found in DrawBot's source that
  DrawBot writes difference as `%`; review added it.
- Rounded corners for `rect` (a v0.5 signature change) were left for the maintainer.

### Sprint 10: typography, SVG and real PDF text (1–2 Oct 2026)
- The maintainer chose `svgelements` for SVG import (D-041). After a Claude spike, they asked what
  real PDF text would involve and chose it (D-043 = D) over the spike's recommendation.
- Claude decided the typography names (D-042) and the `FormattedString` API (D-044) under D-034.
- Five stories and the spike were built by Claude Sonnet 5 sub-agents. Real PDF text was built by a
  Claude Opus 5.5 sub-agent in its own git worktree, from a design Claude checked with a one-minute
  Cairo experiment first.
- Sonnet sub-agents wrote the developer guide and six design notes from the code. Claude reviewed
  them and wrote the PDF text note.
- Review (Claude) fixed four bugs where the code broke the contract. One IR snapshot that had
  recorded a bug was regenerated, and this is stated in the sprint review.

