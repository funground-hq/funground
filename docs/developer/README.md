# Developer documentation

For people who maintain funground or want to contribute to it. If you want to *use* funground,
start with the [User Guide](../guide/README.md) instead.

The pages here explain the code as it is now. The decisions behind it are in the decision log and
the ADRs, which this folder links to rather than repeats.

| Page | Read it when |
|---|---|
| [Architecture.md](Architecture.md) | You want to know how a call becomes pixels or a file, which module may import which library, and which rules must never break. |
| [Adding_a_feature.md](Adding_a_feature.md) | You are about to build a story. It is the step-by-step recipe, with the review checklist. |
| [Testing.md](Testing.md) | You need to add a test, understand a failing one, or know what CI runs. |

## Quick start

You need Python 3.11 or newer and a copy of the repository.

1. Make a virtual environment and install funground with the development tools:

   ```sh
   python -m venv .venv
   .venv/Scripts/python -m pip install -e ".[dev]"      # Windows
   .venv/bin/python -m pip install -e ".[dev]"          # macOS and Linux
   ```

   `[dev]` adds pytest, Pillow and pypdfium2 to funground's own dependencies.
2. **Linux only:** install the Cairo library first, for example
   `sudo apt install libcairo2-dev pkg-config python3-dev`. On macOS, if `pycairo` fails to build,
   run `brew install cairo pkg-config`. Windows needs nothing extra.
3. Run the whole test suite. It takes about 3 minutes:

   ```sh
   .venv/Scripts/python -m pytest -o addopts="" -q
   ```

   The tests run without a window. They set the SDL dummy drivers themselves.
4. `FUNGROUND_HEADLESS=1` runs funground with no window at all (the headless platform). The tools
   and tests use it. A script that ends in `f.show()` returns at once in this mode. A sketch that
   ends in `f.run()` has no window to close, so run it through a test or a tool, which stop it after
   a number of frames (`tests/conftest.py::run_sketch`).

Other environment variables you may meet: `FUNGROUND_BACKING_SCALE` (force the HiDPI scale),
`FUNGROUND_RENDERER` (pick a renderer; only `cairo` exists), and
`FUNGROUND_UPDATE_GOLDENS` and `FUNGROUND_UPDATE_SNAPSHOTS` (regenerate the Session 1 goldens and
snapshots; a reviewed decision, see [Testing.md](Testing.md)).

## Tools

All tools are in `tools/`. Run them from the repository root.

| Tool | What it does |
|---|---|
| `python -m funground.gallery` | A browser for the Examples Gallery, written in funground; it ships in the package (S-103). Needs a window. Left and Right move between examples, Enter runs one, C copies one into the current folder. `--list` prints the examples with no window. `python tools/gallery_browser.py` still works in a checkout. |
| `python tools/make_gallery.py` | Renders every gallery example headless into `docs/gallery/images/` and rewrites the gallery index. `--index` rewrites the index only. |
| `python tools/make_reference_images.py` | Renders the Quick Reference pictures from `examples/reference/`. |
| `python tools/check_originality.py --corpus <path> [files]` | Checks that example code is original, by comparing it with corpora of well-known sketches. `--fetch <dir>` clones the corpora. Exit code 1 means something was flagged. |

## Map of the documents

Read the nearest one to your question. Each line says when.

### In this folder

- [Architecture.md](Architecture.md): how the code is built now.
- [Adding_a_feature.md](Adding_a_feature.md): how to build a story from contract row to changelog.
- [Testing.md](Testing.md): kinds of test, how to add them, and the CI matrix.

### Process and direction

- [PROCESS.md](../PROCESS.md): how work is planned, built, reviewed and decided. Read it before
  your first change. It also says who does what between the maintainer, the main session and the
  sub-agents.
- [Roadmap.md](../Roadmap.md): where funground is going, release by release. Read it to see
  whether an idea is in scope for 0.1 or later.
- [backlog/](../backlog/stories.md): every story with its tasks and status. Read it to find what is
  planned or done. `Feature_Map.md` there compares funground with Processing, p5.js and DrawBot.
- [sprints/](../../sprints/sprint-10/stories.md): one folder per sprint with its stories, review and
  reviewer's guide. Read the latest to see what is in flight. Older ones are history and are
  never rewritten.

### Behaviour and decisions

- [Semantic_Contract.md](../design/Semantic_Contract.md): the pinned meaning of every public
  behaviour, one row each. Read it before changing or adding behaviour. The source and tests win
  if the two disagree.
- [Decision_Log.md](../design/Decision_Log.md): every decision, with date, options and outcome
  (D-nnn). Read it to learn why something is the way it is.
- ADRs, one file per long-lived decision:
  [ADR-001](../design/ADR-001-renderer-topology.md) renderer topology,
  [ADR-002](../design/ADR-002-renderer-selection-reopened.md) Cairo as the reference renderer,
  [ADR-003](../design/ADR-003-out-of-scope.md) what is out of scope,
  [ADR-004](../design/ADR-004-image-provider.md) image files,
  [ADR-005](../design/ADR-005-path-operations.md) path booleans.
  Read them when you want to change a provider or a boundary. They are never edited after
  acceptance.
- Design notes in [docs/design/](../design/), one per subsystem. Read the one for the code you are
  touching: [Text_Subsystem_Note.md](../design/Text_Subsystem_Note.md),
  [Typography_Note.md](../design/Typography_Note.md),
  [Pictures_and_Images_Note.md](../design/Pictures_and_Images_Note.md),
  [Scripts_and_Pages_Note.md](../design/Scripts_and_Pages_Note.md),
  [Paths_Note.md](../design/Paths_Note.md),
  [SVG_Import_Note.md](../design/SVG_Import_Note.md),
  [Compositing_Note.md](../design/Compositing_Note.md) and
  [Browser_Mode_Note.md](../design/Browser_Mode_Note.md).
- [Playground_Technology_Architecture_v2.md](../design/Playground_Technology_Architecture_v2.md):
  the Sprint 2 architecture record. History only. Current code is in
  [Architecture.md](Architecture.md).

### Quality

- [Test_Strategy.md](../qa/Test_Strategy.md): the test layers and why they exist.
- [Example_Provenance.md](../qa/Example_Provenance.md): where the examples came from and how their
  originality was checked.

### For learners (and what you must keep true)

- [User Guide](../guide/README.md): chapters for learners. Every complete code block is run as a
  test.
- [Quick Reference](../reference/Quick_Reference.md): every function on one page. Every public
  name must appear in it.
- [Examples Gallery](../gallery/README.md): every feature in a small sketch, with its picture. It is
  generated by `tools/make_gallery.py`.

### About the project

- [AI-USAGE.md](../../AI-USAGE.md): how Claude is used on this project, the instructions that steer
  it and a sprint-by-sprint log.
- [THIRD_PARTY_LICENSES.md](../../THIRD_PARTY_LICENSES.md): every dependency and bundled file with
  its licence. Update it when you add one.
- [CHANGELOG.md](../../CHANGELOG.md): what changed, newest first.

## House rules in one list

- Plain English in anything a learner reads. British spelling in prose (colour), American spelling
  in names (`color=`).
- Examples are original and CC0. Never copy or translate from other projects (D-026).
- Golden images and IR snapshots are evidence. Never edit or regenerate an existing one to make a
  test pass.
- Backend libraries are imported only by their provider (see [Architecture.md](Architecture.md)).
- The v0.5 public API is frozen. Changes to it go to the maintainer.
- Historical records (`src_v0.5/`, `spikes/`, past sprint folders, the ADRs and the decision log's
  existing rows) are never rewritten.
