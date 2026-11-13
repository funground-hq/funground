# Developer documentation

For people who maintain funground or want to contribute to it. If you want to *use* funground,
start with the [User Guide](../guide/README.md) instead.

The pages here explain the code as it is now. The decisions behind it are recorded by the maintainer;
the story (S-nnn) and decision (D-nnn) IDs in the code refer to them.

| Page | Read it when |
|---|---|
| [Code_Layout.md](Code_Layout.md) | You want to know where the code for something lives, which module may import which library, and which rules must never break. |
| [Adding_a_feature.md](Adding_a_feature.md) | You are about to build a story. It is the step-by-step recipe, with the review checklist. |
| [Testing.md](Testing.md) | You need to add a test, understand a failing one, regenerate a golden legitimately, or know what CI runs. |

## Quick start

You need Python 3.11 or newer and a copy of the repository.

1. Make a virtual environment and install funground with the development tools:

   ```sh
   python -m venv .venv
   .venv/Scripts/python -m pip install -e ".[dev]" --config-settings editable_mode=compat   # Windows
   .venv/bin/python -m pip install -e ".[dev]" --config-settings editable_mode=compat   # macOS and Linux
   ```

   `editable_mode=compat` keeps the install visible to editors: the default editable install hides the package
   behind an import hook that VS Code's Pylance cannot follow, so `f.` would suggest nothing (S-198).
   `[dev]` adds pytest, Pillow, pypdfium2, imageio-ffmpeg (a real ffmpeg for the MP4 test) and build
   (for the wheel test) to funground's own dependencies. A learner who wants MP4 files installs
   `funground[video]`; one who wants fast filters and GIFs installs `funground[extras]`.
2. **Linux only:** install the Cairo library first, for example
   `sudo apt install libcairo2-dev pkg-config python3-dev`. On macOS, if `pycairo` fails to build,
   run `brew install cairo pkg-config`. Windows needs nothing extra.
3. Run the whole test suite. It takes about 2 to 3 minutes:

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
| `python tools/make_gallery.py` | Renders every gallery example headless into `docs/gallery/images/` and rewrites the gallery index. Run it without `--force`: a time-dependent example keeps its committed picture. `--force` re-renders those too; `--index` rewrites the index only. |
| `python tools/make_reference_images.py` | Renders the Quick Reference pictures from `examples/reference/`. |
| `python tools/check_originality.py --corpus <path> [files]` | Checks that example code is original, by comparing it with corpora of well-known sketches. `--fetch <dir>` clones the corpora. Exit code 1 means something was flagged. |

## Map of the documents

Read the nearest one to your question. Each line says when.

### In this folder

- [Code_Layout.md](Code_Layout.md): where the code lives, the provider boundary and the rules that hold everywhere.
- [Adding_a_feature.md](Adding_a_feature.md): how to build a story from contract row to changelog.
- [Testing.md](Testing.md): kinds of test, how to add them, fakes for devices, regenerating a golden, and the CI matrix.

### Behaviour and decisions

- [Semantic_Contract.md](../reference/Semantic_Contract.md): the pinned meaning of every public
  behaviour, one row each. Read it before changing or adding behaviour. The source and tests win
  if the two disagree.

### Quality

- [Example_Provenance.md](../qa/Example_Provenance.md): where the examples came from and how their
  originality was checked.

### For learners (and what you must keep true)

- [User Guide](../guide/README.md): chapters for learners. Every complete code block is run as a
  test.
- [Quick Reference](../reference/Quick_Reference.md): every function on one page. Every public
  name must appear in it.
- [Examples Gallery](../gallery/README.md): every feature in a small sketch, with its picture. It is
  generated by `tools/make_gallery.py`.
- `funground/completions.json`: the list of names, signatures, option words and colours that editors suggest
  (the Play editor, a VS Code extension). `tools/make_api_reference.py` writes it with the API reference;
  never edit it by hand.

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
- Backend libraries are imported only by their provider (see [Code_Layout.md](Code_Layout.md)).
- The v0.5 public API is frozen. Changes to it go to the maintainer.
- `src_v0.5/` is history and is never rewritten.
