# AGENTS.md

For AI coding agents (and people) who change funground itself. If you are *writing sketches* with
funground, read [llms.txt](llms.txt) instead.

funground is a Python library for drawing, animation, typography, print and sound, made for learning.
`import funground as f`; every public name is in `funground._PUBLIC_NAMES` and documented in
[docs/reference/API.md](docs/reference/API.md). Licence: LGPL-2.1-only; example code is CC0.

## Set up and test

```sh
python -m venv .venv
.venv/Scripts/python -m pip install -e ".[dev]"      # Windows
.venv/bin/python -m pip install -e ".[dev]"          # macOS and Linux
.venv/Scripts/python -m pytest -o addopts="" -q      # the whole suite, a few minutes
```

- **Always call the virtual environment's Python by its path.** Never a bare `python`, `py` or `python3`:
  on the maintainer's Windows machine those can start an installer.
- Run without a window: `FUNGROUND_HEADLESS=1`. Linux needs the Cairo library first
  (`sudo apt install libcairo2-dev pkg-config python3-dev`).
- Run the tests you touched first, then the whole suite before you call a change done. Report failures
  with their output; do not skip or weaken a test to make it pass.
- CI on GitHub is not a test runner for you: it runs one Windows job per push and the three systems only
  for a release ([CI_Guidance.md](docs/developer/CI_Guidance.md)). Reproduce problems locally.

## Rules that must not break

- **The provider boundary.** A backend library (pygame-ce, Cairo, pypdf, skia-pathops, svgelements,
  imageio-ffmpeg) is imported only by the module that provides that capability. `tests/test_boundaries.py`
  holds the table ([Architecture.md](docs/developer/Architecture.md), section 3).
- **The naming trap.** A submodule must never have the name of a public function: importing it would
  replace `f.<name>` with the module. Check a new file's name against `_PUBLIC_NAMES`.
- **Goldens and snapshots are the reference.** Never edit, delete or regenerate a file in `tests/golden/`,
  `tests/snapshots/` or `docs/gallery/images/` to make a test pass. A changed picture means changed
  behaviour: find out why ([Testing.md](docs/developer/Testing.md)).
- **The semantic contract.** A change to what a public name means is a decision for the maintainer, and
  updates [Semantic_Contract.md](docs/design/Semantic_Contract.md) in the same change.
- **Learner code never changes shape for a platform:** no `async`/`await` in sketches, the same file runs
  on a computer and in the browser.

## Documentation is part of the change

- **Docstrings** follow the format in `tools/make_api_reference.py` (summary sentence, prose, `Arguments:`,
  `Returns:`, `Raises:`, `Example:`, `See also:`). After changing one, run
  `.venv/Scripts/python tools/make_api_reference.py`: it regenerates `docs/reference/API.md`, `llms.txt`
  and `llms-full.txt` (at the root and in the package). Never edit those by hand; the rules for assistants
  are in `docs/reference/llms_rules.md`.
- A new public feature gets its Quick Reference row, a gallery example with its golden, and a guide
  section ([Adding_a_feature.md](docs/developer/Adding_a_feature.md)).
- Learner-facing text is plain English: short sentences, British spelling in prose, American spelling in
  API names (`color=`). Examples are original: never copied or translated from another project.

## How work is organised

Stories (`S-nnn`), sprints and decisions (`D-nnn`) are recorded in the repository; see
[PROCESS.md](docs/PROCESS.md) and the [developer documentation](docs/developer/README.md). Work on a
branch. Do not push to `main`, tag, publish, or change goldens on purpose without the maintainer.
