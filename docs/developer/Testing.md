# Testing

A short, practical page. The thinking behind the layers is in
[docs/qa/Test_Strategy.md](../qa/Test_Strategy.md). Read that for the why. Read this for the how.

Run everything:

```sh
.venv/Scripts/python -m pytest -o addopts="" -q     # Windows
.venv/bin/python -m pytest -o addopts="" -q         # macOS and Linux
```

It takes about 3 minutes. Everything runs without a window: `tests/conftest.py` sets the SDL dummy
video and audio drivers before pygame is imported.

## The kinds of test

| Kind | What it proves | Where | Runs on |
|---|---|---|---|
| Unit and semantic | One behaviour, often one pinned contract row, checked on pixels or values | `tests/test_*.py`, for example `test_semantics.py`, `test_shapes.py`, `test_pictures.py` | all systems |
| Public API contract | Names and signatures never drift | `tests/test_api_contract.py` | all |
| Golden pixel | A sketch renders exactly the same pixels as before | `tests/golden/`, checked by `test_examples_golden.py` (Session 1) and `test_gallery.py` | **Windows only**; other systems skip the comparison |
| IR snapshot | A sketch asks for exactly the same ops as before | `tests/snapshots/`, checked by `test_ops_snapshot.py` and `test_gallery.py` | all |
| Gallery | Every example runs, matches its golden and snapshot, and together they use every public name; the index and images are up to date | `tests/test_gallery.py` | all |
| Guide | Every complete code block in the guide runs as printed; links resolve | `tests/test_guide.py` | all |
| Quick Reference | Every public name appears in the reference; each reference sketch is embedded verbatim | `tests/test_reference.py` | all |
| Coverage of public names | `__all__` equals the contract; every name has a gallery example and a reference entry | `test_api_contract.py`, `test_gallery.py`, `test_reference.py` | all |
| Boundaries | Backend libraries are imported only by their provider | `tests/test_boundaries.py` | all |
| Tools | The originality checker and the gallery browser (`funground/gallery.py`) | `test_check_originality.py`, `test_gallery_browser.py` | all |
| Gallery in the package | The examples, data, pictures and CC0 licence are in the wheel; the locator works from a checkout and an installed layout; Copy never overwrites | `test_gallery_package.py` (builds a wheel, about 10 s, needs the build tools) | all |

Notes on three of them:

- **Golden pixels are Windows only.** Font and anti-aliasing output differ a little between
  systems. On other systems the golden test still runs the sketch but skips the pixel comparison.
- **IR snapshots are tolerant JSON.** They are compared with
  `assert_json_documents_close` in `tests/conftest.py`: same keys, same lengths, floats equal to
  about 12 digits, ints and floats not mixed up. A failure writes the actual ops to
  `tests/snapshots/_actual/`.
- **Test fonts are made in the tests.** `tests/fontmaker.py` builds small fonts with fontTools.
  Never download a font in a test.

## Golden images and snapshots are evidence

Never edit, delete or regenerate an existing file in `tests/golden/` or `tests/snapshots/` to make a
test pass. If a golden or snapshot changes, the behaviour changed. Find out why. A deliberate
change to pinned behaviour is a decision (see [PROCESS](../PROCESS.md), "When something is a
decision"), and the regeneration is a reviewed act in the main session.

`tests/golden/_actual/` and `tests/snapshots/_actual/` are scratch folders where a failing test
leaves what it saw. Look at them. Do not commit them.

## How to add each kind

### A unit test

Add a test to the file that matches the subject, or a new `tests/test_<topic>.py`. Use the
fixtures in `tests/conftest.py`:

- `canvas`: a live 200 by 100 drawing surface; read pixels with `canvas.get_at((x, y))`.
- `frame_canvas`: the same, but it renders frame by frame, as a running sketch does.
- `sketch`: the active `Sketch`. Reach the recorded ops through `sketch.frame`.
- `run_sketch(path, frames=30)`: run a learner file unchanged and return its last frame.

The autouse fixture gives every test a fresh `Sketch`. Test public behaviour through `import
funground as f`. Backend types (`pygame.Surface`, `cairo.Context`) must not appear in tests of public
behaviour.

### The public API contract

For a new public name, add its signature to `ADDED_FUNCTIONS` in `tests/test_api_contract.py`.
`__all__` in `funground/__init__.py` must match the contract exactly, or
`test_public_all_is_exactly_the_contract` fails.

### A golden and an IR snapshot (gallery examples)

A new gallery example under `examples/gallery/<area>/NN_name.py` gets both files by running the
gallery tests twice:

```sh
.venv/Scripts/python -m pytest -o addopts="" -q tests/test_gallery.py     # writes the files, skips
.venv/Scripts/python -m pytest -o addopts="" -q tests/test_gallery.py     # must pass
```

The first run writes `tests/golden/gallery/<area>-<name>.png` and
`tests/snapshots/gallery/<area>-<name>.json`, and reports those tests as skipped. The second run
compares against them. Review the new picture by eye before you rely on it. A time-dependent
example (marked `# gallery: time-dependent`) is smoke-tested only and has no golden or snapshot.

You only ever create new files this way. You never overwrite one.

**Write new goldens on Windows only.** The first run writes a missing golden on any system, but CI
compares goldens only on Windows, and Windows pixels are the reference. A golden written on macOS
or Linux would be committed unchecked and then fail on Windows. If you are not on Windows, delete
the new `.png` before committing and ask a maintainer to generate it; the IR snapshot is fine to
keep, as snapshots are compared on every system.

### Session 1 goldens and snapshots

`tests/test_examples_golden.py` and `tests/test_ops_snapshot.py` cover `examples/session1/`. Those
sketches are the learners' first lesson and never change to make a test pass.
`FUNGROUND_UPDATE_GOLDENS=1` and `FUNGROUND_UPDATE_SNAPSHOTS=1` regenerate them. Using either is a
**deliberate, reviewed decision by the main session**, for example the single regeneration
when Cairo became the renderer in Sprint 3. A contributor or a sub-agent does not do it.

### A guide section

A fenced `python` block in `docs/guide/NN_*.md` must be a complete sketch or script. It must call
`f.run(` or `f.show(`, because `tests/test_guide.py` runs it for three frames. Use a `py` fence for a
fragment you only want to show. The guide's contents page must list every chapter file.

### A Quick Reference entry

`docs/reference/Quick_Reference.md` must contain `f.<name>` for every public name. Sketches in
`examples/reference/` must appear in it word for word, with their picture. Pictures are made with
`tools/make_reference_images.py`. See [Adding_a_feature.md](Adding_a_feature.md).

## When a test fails

1. Read the message. Golden and snapshot failures say where the actual output was saved.
2. Compare the actual file with the expected one. Decide whether the code or the expectation is
   wrong. For a golden or snapshot, the expectation is right until a decision says otherwise.
3. If you cannot explain the failure, stop and ask. Do not loosen a tolerance and do not skip a
   test.

## The CI matrix

`.github/workflows/ci.yml` runs on every push and pull request:

| Axis | Values |
|---|---|
| Operating system | Windows, Ubuntu, macOS (the `windows-latest`, `ubuntu-latest` and `macos-latest` runners) |
| Python | 3.11, 3.12, 3.13, 3.14 |

That is 12 cells, with `fail-fast` off, so one failing cell does not hide the others. Each cell
makes a virtual environment, installs `pip install -e ".[dev]"` (plus `libcairo2-dev pkg-config
python3-dev` on Linux) and runs `pytest` with the SDL dummy drivers. Goldens are compared only on
the Windows cells.

A change is done when the whole suite is green on the matrix
([PROCESS](../PROCESS.md), "Definitions"). Locally you can only run your own cell, so keep the
code free of anything system-specific.
