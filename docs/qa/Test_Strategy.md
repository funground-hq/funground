# Test strategy

Implements §10 of the architecture document; first written after Sprint 0, brought up to date in the
Sprint 10 review and again in Sprint 15. Run with `.venv/Scripts/python -m pytest -o addopts="" -q`
(about 2 500 tests, about 2 to 3 minutes). Everything is headless. The practical how-to is [Testing.md](../developer/Testing.md).

## Layers

| Layer | Purpose | Where | Status |
|---|---|---|---|
| Public API contract | Names and signatures of the v0.5 surface never drift by accident | `tests/test_api_contract.py` | live |
| Semantic tests | One pixel-level test per pinned row of `docs/design/Semantic_Contract.md` | `tests/test_semantics.py` | live |
| Sample-suite smoke | Every `examples/session1/*.py` runs unchanged for 30 frames headless | `tests/test_examples_golden.py::test_sketch_runs_unchanged_headless` | live |
| Golden images | The sample suite renders exactly what it did before | `tests/test_examples_golden.py::test_sketch_matches_golden`, `tests/golden/*.png` | live |
| **IR snapshots** (primary cross-backend contract) | Learner code → expected draw-op list of the final frame, JSON, platform-independent | `tests/test_ops_snapshot.py`, `tests/snapshots/*.json` | live (Sprint 2) |
| Capability / error contract | Unsupported features fail at `f.size()`/`run()` with a learner-readable message | `tests/test_capabilities.py` | live (Sprint 2) |
| Examples Gallery | Every gallery example runs headless, matches its golden and IR snapshot; together the examples use every public name | `tests/test_gallery.py`, `tests/golden/gallery/`, `tests/snapshots/gallery/`, `tools/make_gallery.py` | live (Sprint 5) |
| Provider boundaries | Each backend library is imported only by its provider module | `tests/test_boundaries.py` | live |
| Cross-renderer conformance | Same ops → same semantics on two renderers | — | dropped: one renderer (Cairo, ADR-001/002); the IR snapshot is the guard |
| Export checks | PDF/SVG structure; PDF text extracted with pypdf and pdfium and rendered against the outline version | `tests/test_export.py`, `tests/test_pages.py`, `tests/test_pdf_text.py` | live |
| Guide | Every code block in the guide runs; links resolve | `tests/test_guide.py` | live |
| Quick Reference | Every public name appears; each reference sketch is embedded word for word | `tests/test_reference.py` | live |
| **Example explanations** | Every gallery example's docstring has "What you see", 3 to 6 "How it works" bullets and 3 to 5 "Make it yours" bullets, and every function it names exists (S-120, D-065) | `tests/test_example_docs.py` | live (Sprint 15) |
| Sound, no device | A sound's state, position and analysis behave the same with or without an audio device (A2) | `tests/test_sound.py`, `tests/test_making_sound.py`, `tests/test_rhythm_harmony.py`, `tests/test_ragas.py`, `tests/test_drawing_sound.py` | live |
| Microphone, fake device | Listing, ring buffer, analysis and errors, with `microphone_input.py`'s three device functions patched | `tests/test_microphone.py` | live |
| **Quiet microphone** | The voice game and the tuner work on a laptop microphone: room near RMS 0.0005, speech near 0.01 (levels in dB above the room) | `tests/test_quiet_microphone.py` | live (Sprint 14) |
| Controls | Sliders, checkboxes, buttons and the panel rules; the panel never reaches the canvas, saves or snapshots (U1) | `tests/test_controls.py` | live |
| Motion export | GIF with Pillow and with ffmpeg; MP4 through a fake ffmpeg on the PATH; one real-ffmpeg test when available | `tests/test_motion.py`, `tests/test_save_frames.py` | live |
| **PDF and SVG text** | Text in a PDF is extracted with pypdf and drawn with pdfium against the outline version (T15). Text in an SVG is a real `<text>` element, and the file draws as it should (T19) | `tests/test_pdf_text.py`, `tests/test_svg_text.py` | live |
| **Layers in files** | Layers are optional content groups in a PDF and Inkscape groups in an SVG; hidden layers are switched off; read back with pypdf and drawn with pdfium (F16) | `tests/test_layer_files.py`, `tests/test_layers.py` | live (Sprint 12) |
| Fonts | Font collections, fallback fonts and font information, using fonts the tests make (`tests/fontmaker.py`) | `tests/test_font_collections.py`, `tests/test_fonts.py`, `tests/test_fallback.py`, `tests/test_font_info.py` | live |
| Gallery in the package | The wheel holds the examples, data, pictures and CC0 licence; the locator works from a checkout and an installed layout | `tests/test_gallery_package.py` (builds a wheel), `tests/test_gallery_browser.py` | live |
| Packaging CI | Windows/macOS/Linux × Python 3.11–3.14; Linux installs the Cairo library first | `.github/workflows/ci.yml` | live, GitHub Actions (12 cells) |
| **Release smoke test** | The package built for release installs from TestPyPI on Windows, macOS and Linux; it draws, saves PDF/SVG/PNG, reads the PDF's text, makes a sargam melody and lists the gallery | `.github/workflows/release.yml` (job `smoke-test`) | live; runs only on a release or by hand ([Releasing.md](../developer/Releasing.md)) |

## Headless execution

`tests/conftest.py` sets `SDL_VIDEODRIVER=dummy` and `SDL_AUDIODRIVER=dummy` before pygame is
imported. Under the dummy driver the mouse is at (0, 0) and no keys are pressed, which makes the
input-driven sketches deterministic.

`run_sketch(path, frames)` executes a learner file **unchanged**: it swaps `funground.run` for a
wrapper that forwards the sketch's own globals to `Sketch.run_namespace(..., max_frames=frames)`,
then returns the final frame's RGB bytes captured by the `max_frames` hook. Learner files never
contain test hooks.

## Test hierarchy (PROCESS)

1. Public API semantics (`test_api_contract`, `test_semantics`)
2. **IR snapshots** — what the learner's code asked for. Two correct renderers may differ in pixels;
   they may not differ in ops. Regenerate with `FUNGROUND_UPDATE_SNAPSHOTS=1`; a change here is
   a change in *behaviour requested*, never in rendering.
3. Per-backend semantic tests (pixel rows in `test_semantics`)
4. Per-backend golden images (below)

## Golden-image policy

- Goldens are produced on the Windows teaching machine (`GOLDEN_PLATFORM = "Windows"`); other
  platforms run every sketch but skip the pixel comparison, because font rasterisation differs.
- Comparison is **exact** (Cairo on Windows). The op-list snapshot is the primary regression guard
  and runs on every system, compared with a small float tolerance.
- Regenerate only as a deliberate act tied to a contract change:
  `FUNGROUND_UPDATE_GOLDENS=1 pytest tests/test_examples_golden.py`. The diff of `tests/golden/`
  is reviewed like code.
- A failing comparison writes the actual frame to `tests/golden/_actual/` (git-ignored) for inspection.
- `11_delta_time.py` is time-dependent and smoke-tested only. Gallery examples marked
  `# gallery: time-dependent` are treated the same way.
- A gallery script that uses layers is pictured with its layers composited, as `f.show()` and a save show it.
- A new golden or snapshot is written only for a new example. No existing one is edited, deleted or
  regenerated to make a test pass. The sprint review checks this with a `git diff --diff-filter=MD` over
  `tests/golden`, `tests/snapshots` and the image folders. The few allowed cases are in
  [Testing.md](../developer/Testing.md), "How to regenerate a golden legitimately".

## Determinism

- `f.random_seed(0)` is applied by the autouse fixture before every test.
- Sketches run at `fps=1000` so 30 frames take ~30 ms of wall time; `delta_time` is not asserted
  beyond range checks.

## Adding a sketch to the suite

1. Write plain learner code in `examples/session1/NN_name.py` — it must call `f.run()` itself.
2. Run the suite once: the golden is written and the test skips with "golden written".
3. Run again: it compares. Commit the PNG with the sketch.

## Definition of green

All layers pass on the local machine and on every cell of the CI matrix. A skipped golden
comparison on macOS/Linux is expected; a skipped one on Windows is a bug.
