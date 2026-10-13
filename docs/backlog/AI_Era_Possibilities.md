# Future possibilities: funground in the AI era

Parked on 13 October 2026 at the maintainer's request: suggestions from an AI agent on making funground more useful
alongside AI tools. Nothing here is planned or decided. Each idea is set against what funground already has, so a
later sprint can pick one up as a story with a clear starting point.

The agent's theme: funground is deterministic, structured drawing, which is what text-to-image models are not. It
could be the place where human intent, AI-written code and exact output meet: code an assistant can write
reliably, a canvas an assistant can look at, and data an assistant can produce instead of code.

| # | Idea | What funground has today | What would be new | First step, if picked up |
|---|---|---|---|---|
| 1 | An API that assistants write without mistakes, and one reference file to give them | Plain snake_case functions on one module (`f.circle`, no class hierarchy to learn); the shorter style (`from funground import *`); **`llms.txt` and `llms-full.txt`** (S-129), generated from the docstrings, tested, shipped in the package | A measurement: how often an assistant's sketch runs, with and without the files. The agent's "zero-error rate" is a hope until it is measured | An evaluation story: a fixed set of prompts, sketches from two or three assistants, run headless, counted; repeated when the API or the files change |
| 2 | Vision hooks: camera to model to drawing | Nothing yet for the camera: **S-172 camera input**, waiting for decision **D-089** (`docs/design/Camera_Note.md`); the microphone already feeds sketches (`f.microphone`, pitch, level) | Model wrappers (object detection, poses). These are large, fast-moving dependencies, so they would not be core: an optional extra or a separate package, after the camera exists | After S-172: one gallery project that draws on what a model sees, written with a plain library call in the sketch, to learn what a wrapper would save |
| 3 | Let an AI see the canvas: render, look, correct | `f.save("x.png")`, headless runs (`FUNGROUND_HEADLESS=1`), `f.load_pixels()`, `f.keep()` and `f.variations()` for comparing versions | The frame as PNG bytes in memory (for example `f.png_bytes()`), so an agent loop needs no files; a documented recipe for the loop: write, render, look, edit | A small story: the in-memory PNG, its contract row and a guide recipe; the loop itself stays in the user's code, so funground calls no AI service |
| 4 | Drawing from data (JSON) instead of code | Every frame is already recorded as a list of drawing operations (the IR) and saved as JSON in the tests; areas, grids and marks place things by structure | A public, documented format a person or an assistant writes as data (layers, text, shapes, placements) that funground draws and saves, including multi-page PDFs | A design note first: what the data describes (a page of areas and marks, not raw operations), how it maps to the existing vocabulary, and what stays code |
| 5 | Layout and colour with guard-rails | Pages in real units, margins, `f.grid`, `f.area`, marks, `f.fit_text_size`, text boxes that flow and justify, colour modes and CMYK | Colour checks and helpers: a contrast ratio between two colours, a palette builder (analogous, complementary), a warning when text is too faint for its background | A story for `f.contrast(a, b)` and a palette helper, taught in the course's colour lesson |

What would stay out, whatever is picked up: funground does not call AI services itself (no keys, no network in a
sketch unless the learner writes it), and learner code keeps one shape on every platform.

**Where it came from:** an AI agent's proposal, pasted by the maintainer on 13 October 2026. Recorded in
`docs/Roadmap.md` under "Directional".
