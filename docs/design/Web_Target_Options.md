# Design note: funground on the web — options for 0.2

**Status:** options study, 8 October 2026, on branch `release-0.2-web`. **Nothing here is decided.** It
updates [Browser_Mode_Note.md](Browser_Mode_Note.md) (25 September 2026, Spike 08), which was written
when funground had no pictures with history, layers, groups, marks, sound, microphone, controls, GIF/MP4,
real PDF text or live SVG text. D-014 put the browser after 1.0. A 0.2 web target would supersede that,
and the maintainer has to make that call (section 7). Spikes are proposed in section 6 and recorded as
candidate stories in `docs/backlog/stories.md` (E-31). All web facts were checked on 8 October 2026 and
are cited in section 8. Anything that could not be checked is marked **unverified**.

**Decided since (D-074, 8 October 2026):** W2 is the 0.2 target; the browser comes into 0.2 (supersedes D-014 for E-31); B or C are both acceptable (a tolerance is fine), with a lean to a web renderer (B) and C prototyped; Chrome only is acceptable for 0.2 (Edge, Firefox, Brave and Safari kept in view); editor H1; GitHub Pages. Still open: Q4, Q7, Q8, Q10.

## 0. Summary

- **The IR is the right seam, but it is not the only thing the browser has to replace.** Cairo is
  reached from four places: the renderer, pictures (`picture.py` imports `CairoRenderer`), pixel access
  and filters, and all file export. uharfbuzz is reached from the *sketch* layer, through `text_width`,
  wrapping and `text_box`, not only from the renderer. So every route that runs funground's Python in the
  browser needs a shaper in Python, whatever draws the pixels.
- **None of funground's three C extensions has a browser build.** pycairo, uharfbuzz and skia-pathops
  are not among Pyodide 314's packages and have no Emscripten wheels on PyPI. Everything else is either
  already in Pyodide (fontTools, Pillow, numpy, pygame-ce) or pure Python that micropip can install
  (svgelements, pypdf). PEP 783 (accepted April 2026) and cibuildwheel 4 now make it possible to publish
  `pyemscripten` wheels to PyPI. So building those three is ordinary packaging work, not a fork.
- **The blocking loop is solved most simply by inverting it** (`start/step/finish`, S-060), with Python
  in a module Web Worker that the page drives frame by frame. That works in every current browser with no
  special headers, so GitHub Pages can host it. A runaway sketch is stopped with `worker.terminate()`.
  Stack switching (JSPI) would keep the `while` loop, but on 8 October 2026 it is on by default only in
  Chrome 137+.
- **Recommendation (section 5):**
  - Put the gallery online as static pages now.
  - Run three cheap spikes that decide the renderer:
    - uharfbuzz in Pyodide;
    - Cairo in Pyodide (speed and golden identity);
    - the Canvas 2D renderer over today's full IR.
  - **Prefer "the desktop stack in wasm" (architecture C)** if Cairo-in-wasm keeps a typical gallery
    sketch under about 12 ms a frame at the browser's pixel density. It keeps the semantic contract,
    the goldens, PDF/SVG output and nearly all product code unchanged.
  - Fall back to the IR-on-Canvas-2D route (B) only if it does not.
  - Offer a static editor with URL sharing. Do not build accounts in 0.2.

## 1. Goals and non-goals

### What the web target could be for

These are different products with different costs. The first three need no server. The fourth needs one.

| # | Purpose | What it needs | Open question for the maintainer |
|---|---|---|---|
| W1 | **The gallery online.** Read every example, see its picture, read its code and explanation | Static pages generated from `examples/gallery` and the goldens. No Python in the browser | Is this enough for 0.2 on its own, or the first step? |
| W2 | **Run without installing.** A learner on a Chromebook, a school PC without admin rights, or a tablet opens a page and runs a sketch | Python in the browser, a canvas, input, sound | Which devices and browsers are the floor (section 7, Q5)? |
| W3 | **Share a sketch as a link.** Send a URL, the other person sees it run and can change it | W2, plus a way to carry the code: in the URL, or a GitHub/gist link | Is a link that holds the code enough, or are saved projects expected? |
| W4 | **A hosted editor with accounts** (editor.p5js.org style): saved sketches, collections, uploads | A backend, storage, moderation, privacy duties for minors | Is a backend with accounts ever in scope for a volunteer project? |
| W5 | **Classroom pages.** A lesson page with the sketch embedded next to the text | W2, plus an embeddable element (Pyxel's `<pyxel-run>` pattern) | Should the guide and gallery pages become runnable? |

### What must stay true

1. **One semantic contract.** A sketch means the same thing on the desktop and on the web. Where the web
   cannot honour a row, the difference is written down as its own contract row and gives a clear
   message. It never fails silently.
2. **Learner code does not change shape.** The same `setup()/draw()/f.run()` file and the same top-level
   script run on both. No `async def`, no `await` (pygbag's requirement is ruled out by this).
3. **The desktop stays the reference.** Cairo goldens remain the truth, and the web is measured against
   them.
4. **funground stays installable and offline.** The web is an extra way in, not a replacement.

### Non-goals (proposed)

- Not a general Python IDE, and not a notebook.
- Not real-time collaboration, comments or social features.
- Not a JavaScript version of funground for JavaScript learners.
- Not server-side execution of learner code.

## 2. Inventory: each feature against what the browser offers

The numbers come from `examples/gallery` (95 examples): 85 animated sketches and 8 scripts.

| Example count | Features used |
|---|---|
| 65 | text |
| 16 | save files |
| 15 | make sound |
| 13 | controls |
| 6 | the microphone |
| 6 | pictures |
| 6 | layers |
| 5 | marks |
| 3 | path booleans |
| 3 | GIF/MP4 |

| Feature | Desktop today (module, library) | What a browser offers | Gap and difficulty |
|---|---|---|---|
| **Drawing** | `renderers/cairo2d.py` replays 20 op types (`ir.OP_TYPES`) on pycairo | Canvas 2D covers paths, dashes, caps, joins, gradients (including conic), all 16 blend modes plus `destination-out` for erase, shadows, `Path2D` clips. No switch to turn off anti-aliasing for paths. `ctx.filter` is off by default in Safari. Or Cairo compiled to wasm (no maintained build exists) | **Medium.** Spike 08 drew early-IR frames on Canvas 2D within 2.3 % of pixels. Today's IR adds groups, erase, pixel blocks, pictures with history and layers |
| **Pictures, pixels, filters** | `picture.py` keeps a persistent Cairo surface per picture. `get/set/load_pixels`, `filter` read Cairo pixels (Pillow optional) | OffscreenCanvas (Safari 17+) with `getImageData`/`putImageData`. Round trips through premultiplied alpha can change values | **Medium–hard** on the Canvas route (a second picture implementation). **None** if Cairo runs in wasm |
| **Text shaping and fonts** | `typography.py`: uharfbuzz shapes, fontTools gives outlines, text becomes `FillPath` ops. Used by the sketch (`text_width`, wrap, `text_box`) *and* the renderer | Pyodide has fontTools 4.62.1. **No uharfbuzz.** harfbuzzjs 1.6.3 (441 KB wasm) shapes and returns glyph paths. `fillText` is not deterministic across browsers and canvas has no `fontVariationSettings` | **Required by every Python route.** Build uharfbuzz for Pyodide, or put a shim with the same small API over harfbuzzjs. Never `fillText` (it breaks T-rows) |
| **Fonts on disk** | 4.4 MB bundled (DejaVu ×4, Noto Emoji, Devanagari, Symbols 2); `system_font()` searches OS folders | Files must be fetched. No system font folder | Load DejaVu Sans (757 KB) up front and the rest on first use. `system_font()` gives a clear "not on the web" error |
| **Images** | `imaging.py` decodes with pygame-ce | Pillow 12.2.0 and pygame-ce 2.5.7 are both in Pyodide. Browser decoding is asynchronous | **Small.** A Pillow decoder (ADR-004 already allows Pillow), with the files preloaded into Pyodide's file system |
| **SVG import** | `svg.py` via svgelements (pure Python) | micropip from PyPI | **None** |
| **Path booleans** | `pathops.py` via skia-pathops (C++) | Not in Pyodide; no wasm wheel. CanvasKit has path ops but is 7–8 MB | Build the wheel, or make it desktop-only in 0.2 (3 examples) |
| **Window and events** | `platform/pygame_platform.py` (SDL): window, HiDPI, mouse, keys, wheel, cursor, full screen | DOM events, `devicePixelRatio`, Pointer Events (touch counts as mouse), Fullscreen API, CSS cursors | **Small.** A `BrowserPlatform` against the existing `Platform` protocol. Escape must not be the only way to stop |
| **Frame loop** | `Sketch.run_namespace` is a `while` loop. `platform.tick()` blocks | The page's event loop must get control back every frame. `requestAnimationFrame` follows the display rate (60–144 Hz) and pauses in background tabs | **The central constraint.** See "The frame loop" below |
| **Scripts and `f.show()`** | `show()` blocks until the window closes. Pages flip with Left/Right | Nothing may block the page | `show()` becomes "show this drawing now" and returns. A web contract row is needed (R15 differs) |
| **Sound playback** | `sound.py`: pure-Python synthesis and analysis, clock-driven state; `pygame.mixer` only plays | Web Audio: `AudioBuffer.copyToChannel` from float samples, `StereoPannerNode`. Needs a user gesture first (autoplay rules). No `AudioContext` in workers | **Small–medium.** The samples and the clock stay in Python and are posted to the page to play. Synthesis speed in wasm is unmeasured |
| **Loading sound files** | `pygame.mixer` decodes WAV/OGG/MP3 synchronously | `decodeAudioData` is asynchronous. Format support per browser is unverified (Safari added Ogg Vorbis in 18.4) | Decode while preloading, before the sketch starts. WAV can be decoded in Python |
| **Microphone** | `microphone_input.py`: `pygame._sdl2.audio` capture into a 10 s ring buffer | `getUserMedia` (HTTPS, a permission prompt, `allow="microphone"` in iframes), AudioWorklet. Labels in `enumerateDevices` only after permission | **Medium.** An AudioWorklet posts chunks to Python. `start()` returns at once and listening begins when the user allows it. Until then the contract's "not listening" values (0, zeros, `None`) apply |
| **Saving PNG** | Cairo pixels to a file | `canvas.toBlob` plus a download, or Pillow/Cairo in wasm | **Small.** A save becomes a download |
| **Saving PDF and SVG** | Cairo PDF/SVG surfaces plus pypdf post-processing (real text, OCG layers); `svg_text.py` with fontTools subsets | No PDF writer that does what funground's does: jsPDF, pdf-lib and PDFKit document no optional-content layers, and pdf-lib is unmaintained since 2021. pypdf and fontTools run in Pyodide | **None if Cairo runs in wasm** (the export code runs as is). **Large otherwise** (a new SVG writer from the IR; PDF deferred) |
| **GIF and MP4** | Pillow for GIF; ffmpeg subprocess for MP4 | Pillow is in Pyodide, so GIF works as on the desktop. No subprocess. WebCodecs (Safari full only from 26) plus Mediabunny (MPL-2.0) can mux MP4. MediaRecorder MP4 in Chrome 126+ | GIF: **small**. MP4: **medium**, or desktop-only in 0.2 |
| **`keep` and `save_frames`** | Write `studio/NNN.*` next to the sketch | No folder next to the sketch. OPFS is baseline. `showSaveFilePicker` is Chromium-only | Write into Pyodide's file system (persisted to IndexedDB or OPFS), with a "studio" panel listing kept files and a download-as-zip button |
| **Controls** | `controls.py` lays out the panel as IR ops; the platform shows it below the canvas | Same ops on any renderer; or HTML inputs | **Small.** Draw the same panel (identical look). HTML controls could come later, for accessibility |
| **The gallery app** | `gallery.py`, a funground app that runs each example with `subprocess.Popen` | No subprocesses | Replace it with the static gallery (W1). The "Run" button opens the example in the web runner |
| **Errors and output** | Terminal | A console panel | `print` and tracebacks go to an output panel (Pyodide's `setStdout`/`setStderr`) |
| **`input()`** | Terminal | Pyodide uses `prompt()` on the main thread. There is none in a worker | Desktop-only, with a clear error, unless SharedArrayBuffer is available |
| **Threads** | Only the microphone callback (SDL's thread) | Pyodide has no threads | No change: the microphone moves to an AudioWorklet |

### The frame loop: four ways to map `draw()` onto the browser

`run_namespace` is the only `while` loop in the core. The only blocking call is `platform.tick()`.
`show()` loops on `platform.poll()` until the window closes.

| Way | How it works | Keeps | Costs | Evidence |
|---|---|---|---|---|
| **L1 Invert the loop** (S-060) | `Sketch.start()` runs `setup()`. The host calls `step()` once a frame. `finish()` cleans up. On the desktop, `run()` becomes `while running: step(); tick()`. On the web, `f.run()` registers the sketch and returns, and the page calls `step()` | Learner code byte-identical. No special headers. Works in every browser | One refactor of `run_namespace` (desktop behaviour pinned by the existing tests). `show()` cannot wait. Synchronous loads need preloading | Spike 08: "the `Platform` protocol needed no change" |
| **L2 Stack switching (JSPI)** | Keep the `while` loop. `tick()` awaits a frame promise through `pyodide.ffi.run_sync`, so the browser runs between frames | Even the loop code is unchanged. `show()` could wait. Loads can await | `run_sync` is *experimental*. JSPI is default only in Chrome 137+. Firefox and Safari status is **unverified** (one secondary source) | Pyodide `ffi` docs, JSPI blog |
| **L3 Worker with a synchronous bridge** | Python runs in a worker and blocks in `tick()` on `Atomics.wait`. Input arrives through a SharedArrayBuffer | The loop is unchanged. `show()` can wait | Needs cross-origin isolation (COOP/COEP). GitHub Pages cannot set headers (a `coi-serviceworker` workaround reloads the page once). Safari has no `credentialless` COEP. PyScript calls its service-worker fallback "inevitably slower" | MDN, PyScript workers docs |
| **L4 Async learner code** (pygbag) | `async def main()` with `await asyncio.sleep(0)` | — | Breaks "learner code does not change shape" | pygbag docs |

**Proposed:** L1, with Python in a **module worker** (Pyodide 314 supports only module workers). The page's
`requestAnimationFrame` posts "step" with the input events gathered since the last frame. The worker steps,
renders, posts the frame back, and the page shows it. This keeps the page responsive when a sketch is slow,
and **Stop is `worker.terminate()`**, which needs no SharedArrayBuffer. L2 can be added later as an
enhancement (a blocking `show()` and `input()` in Chrome) without changing L1. L1 also helps the desktop:
tools, tests and a future live-reload editor can drive frames.

**Scripts under L1.**
- A script runs top to bottom in one go. Each `f.show()` puts the drawing so far in the output area and
  returns; drawing more and showing again adds another view.
- Pages are shown with page buttons and the arrow keys. `save()` downloads.
- That is a web-specific contract row (R15w). The meaning of the drawing does not change, only the waiting.

## 3. The architectures

Five coherent wholes. B, C and D share the same runtime pieces:

- Pyodide in a module worker;
- loop inversion (L1);
- a `BrowserPlatform`;
- the shaper in Python;
- Pillow image decoding;
- Web Audio for playback and an AudioWorklet microphone;
- a virtual file system preloaded with the sketch's folder;
- downloads.

They differ in **what turns the IR into pixels and files**.

```
                           learner sketch -> api -> Sketch -> IR (Frame)
                                                               |
     A  static site       (no Python: pictures and code generated at build time from the goldens)
     B  Pyodide worker  --IR as JSON or arrays-->  JS Canvas 2D renderer  (screen)
                                                    + new SVG writer from the IR; PDF later
     C  Pyodide worker  --> CairoRenderer in wasm --> pixels --> canvas      (screen)
                                                 --> existing export/      (PNG, PDF, SVG, GIF)
     D  B for the screen, C's Cairo loaded on first save, picture or pixel access
     E  JS reimplementation of the API; learner Python run by MicroPython/Brython/Skulpt
```

### A. The gallery online, static (no runtime)

- **How:** a build tool (beside `tools/make_gallery.py`) writes one HTML page per example:
  - the golden picture (or an animated GIF/MP4 made on the desktop);
  - the code, highlighted;
  - "What you see / How it works / Make it yours";
  - a "Copy" button and "Install funground" instructions.
  - Hosted on GitHub Pages (1 GB site, a soft limit of 100 GB a month).
- **Keeps:** everything, because nothing runs. **Loses:** interaction, sound and the microphone. It is not
  "no install".
- **Effort:** small (days). **Risk:** none. **Evidence:** the goldens and `docs/gallery/images` (3 MB,
  93 pictures) already exist.
- **Role:** step one under any choice. Later the pages get a "Run in the browser" button.

### B. Python core in Pyodide, IR replayed on Canvas 2D (the September recommendation)

- **How:**
  - The sketch runs in Pyodide and produces each frame's IR.
  - Text is already shaped into `FillPath` outlines in Python, so the JS side never shapes or uses
    `fillText`.
  - A JS renderer replays the IR on an OffscreenCanvas in the worker. `Frame.to_jsonable()` exists;
    typed arrays for path data would avoid JSON costs.
  - Pictures become OffscreenCanvases, and pixel access uses `getImageData`.
  - A new SVG writer from the IR replaces Cairo's SVG surface. PDF is deferred or desktop-only.
- **Keeps:**
  - learner code;
  - the IR and everything above it;
  - IR snapshots (byte-identical, since they are made before rendering);
  - GPU-composited drawing, which is fast at any pixel density;
  - a small download (no Cairo).
- **Loses:**
  - Pixel identity: browsers anti-alias differently (Skia, Direct2D, CoreGraphics), so goldens can only
    be met within a tolerance.
  - `no_smooth()` for paths (Canvas has no switch).
  - Exact pixel values after `get`/`set` round trips.
  - `filter()` blur on Safari (`ctx.filter` disabled), unless done in Python.
  - PDF output and its real text and layers, unless rewritten.
  - The SVG writer and picture-history replay become a second implementation of behaviour that today
    lives in one place.
- **Effort:**
  - renderer, medium (Spike 08's 130-line consumer covered the 2025 subset; today's IR has groups,
    erase, shadows, layers, pixel blocks and picture history);
  - pictures and pixels on canvas, medium;
  - SVG writer, medium;
  - PDF, large (deferred).
- **Risks:**
  - Two renderers to keep in step for every future op.
  - Subtle drift in compositing (groups, erase on pictures) that only appears in some browsers.
- **Evidence:** Spike 08 measured ≤ 2.3 % differing pixels on anti-aliased edges only, for 11 frames. That
  was early IR, Chromium only.

### C. The desktop stack in wasm (Cairo renders in the browser)

- **How:**
  - funground builds and publishes three `pyemscripten_2026_0` wheels with cibuildwheel 4 or
    `pyodide-build` (PEP 783 lets PyPI host them): pycairo (with cairo and pixman), uharfbuzz and
    skia-pathops.
  - `CairoRenderer`, `picture.py`, `export/` and `typography.py` then run **unchanged** in Pyodide.
  - The `BrowserPlatform.present()` posts the finished BGRA bytes. A frame is opaque, so this is a
    byte-order swap, no un-premultiplying. The page puts them on a canvas with `putImageData`, or with
    a WebGL texture that swaps the channels.
- **Keeps:**
  - The whole contract, including `no_smooth`, pixels, filters, erase and groups.
  - Goldens identical. Cairo and pixman's C fallback paths should give the same bytes as the desktop, but
    this is **unverified**, which is why Spike S-134 compares the bytes.
  - PNG/PDF/SVG/GIF files byte-for-byte as on the desktop, with real PDF text, OCG layers and live SVG
    text.
  - One implementation of every behaviour.
- **Loses:**
  - Speed, at large or high-density canvases. Cairo rasterises on the CPU, and wasm is slower than
    native: Pyodide says 3–5× for Python code, and C code is usually closer to native, but that is
    **unverified** for pixman.
  - Spike 05 measured native Cairo at 3.5 ms (640×400), 6.4 ms (1280×720) and 11.2 ms (1920×1080) for a
    heavy scene. A 640×400 canvas at `devicePixelRatio` 2 has the pixels of 1280×800.
  - A bigger first download: three more wasm modules. Sizes are **unverified**; pycairo's native wheel is
    0.9 MB.
- **Effort:**
  - Mostly build engineering: three wheels, rebuilt once a year when Pyodide moves to a new Python
    (the 314 numbering ties binary compatibility to the Python version).
  - Product code is the shared pieces only.
- **Risks:**
  - The builds may fight Emscripten. pixman's SIMD paths are off in wasm. cairo needs FreeType only for
    text, and funground draws text as paths, so cairo may build without it.
  - Frame time on low-end Chromebooks.
  - Nobody else maintains a Cairo-in-Pyodide build: none was found in Pyodide, pyodide-recipes or on
    PyPI, so funground would own it.
- **Evidence:**
  - Pyxel ships its Rust engine as an Emscripten wheel loaded into Pyodide.
  - matplotlib-pyodide's `wasm_backend` rasterised with Agg in wasm and copied the buffer to a canvas
    (now archived for a webagg backend).
  - Spike 08 ran funground's core in Pyodide unchanged.

### D. Hybrid: Canvas 2D on screen, Cairo for files and pixels

- **How:** B for each live frame. C's Cairo wheel is fetched the first time a sketch saves a PDF/SVG,
  makes a picture, reads pixels or applies a filter. Files then come from the unchanged `export/`.
- **Keeps:** B's speed on screen and C's files.
- **Loses:**
  - Screen and file differ slightly (anti-aliasing).
  - A PNG of an accumulating canvas (no `background()` each frame) must come from a Cairo surface kept in
    step with the screen, which means drawing twice.
  - Pictures drawn by Cairo but shown through Canvas need a copy each time they change.
- **Effort:** B's renderer plus C's builds. The most code of all.
- **Risks:** two renderers *at run time*, with mixed pixels on one screen. The hardest to reason about.
- **Role:** only if C is too slow and the contract's file output is still required on the web.

### E. A JavaScript funground, with a light Python

- **How:** reimplement the API in JavaScript. Run learner code in MicroPython-wasm (about 450 KB wasm,
  near-instant start), Brython 3.14 or Skulpt.
- **Keeps:** a fast first load.
- **Loses:**
  - The single implementation. Every contract row, the sound analysis, ragas and text layout would have
    to be written twice.
  - CPython semantics (MicroPython and Skulpt differ). Skulpt describes itself as Python 2 with a 3 mode.
  - None of them runs C extensions.
- **Effort:** very large. **Risk:** permanent divergence.
- **Evidence:** Trinket used Skulpt and shut down on 31 August 2026. pyp5js (Transcrypt or Pyodide) has
  been dormant since 2022.
- **Not recommended.** It is listed so the choice is explicit.

### The editor and hosting, in tiers (independent of B, C or D)

| Tier | What | Backend | Notes |
|---|---|---|---|
| H0 | `<funground-run src="sketch.py">` element and a launcher URL that loads a file from GitHub (Pyxel's `?run=user/repo/branch/path`) | None | Raw GitHub sends CORS. The REST API allows 60 unauthenticated requests an hour; raw-file limits were tightened in May 2025 (numbers unpublished) |
| H1 | A static editor page: CodeMirror (PyScript's `py-editor` is a precedent), Run/Stop, output, the studio panel, examples menu, drafts in local storage, **share as a link**: code compressed with `CompressionStream("deflate-raw")` in the URL **fragment** (never sent to a server) | None | marimo.app caps `?code=` at 14 KB and uses lz-string in the hash for more. The TypeScript playground uses `#code/` with lz-string. Chrome allows 2 MB URLs; Firefox and Safari about 65–80 K (secondary source); chat apps may cut long links. Data files (images, sounds) do not fit: those sketches share a GitHub link instead |
| H2 | Save to a gist / open a gist | A token exchange proxy (GitHub's OAuth token endpoint has no CORS), e.g. one Cloudflare Worker (100 000 requests a day free) | Anonymous gists were removed in 2018. It adds an OAuth app and a secret to look after |
| H3 | Accounts, saved projects, uploads, collections (editor.p5js.org) | A server, database and object storage (p5: Node/Express, MongoDB, S3, GKE) | Moderation is real: p5 removed Present view in 2021 "to prevent phishing" and still redirects embed links for that reason. Its terms carry DMCA and removal processes. Accounts for under-13s (COPPA, amended rule in force April 2026) and under-16s (GDPR Art. 8) bring duties. **Not recommended for 0.2** |

**Hosting.** GitHub Pages under `funground-hq` is enough for A, H0 and H1:

- The proposed L1 design needs no COOP/COEP headers, which Pages cannot set.
- Pyodide can be loaded from jsDelivr (`cdn.jsdelivr.net/pyodide/v314.0.7/full/`) or self-hosted. jsDelivr
  refuses GitHub files over 20 MB, which none of ours are.
- Cloudflare Pages (free: 20 000 files, 25 MiB a file, `_headers` allowed) is the alternative if headers
  are ever needed (L3).

**Security of running learner code.**
- Pyodide code can reach any browser API through the `js` module, so a shared link is "run this code on
  our domain".
- If the editor and the runner share an origin, a link could read drafts in local storage or show a
  phishing page under funground's name. CodePen moved its previews to a separate registrable domain for
  exactly this reason ("essentially one massive XSS vulnerability"). The p5 editor previews on
  `preview.p5js.org`.
- So for H1:
  - run the sketch in an iframe on a **separate origin** (a second Pages site or subdomain), sandboxed
    with `allow-scripts` and **without** `allow-same-origin` on the editor's side;
  - give the iframe `allow="microphone"` only when asked;
  - talk to it by `postMessage`.
- A worker alone is not a boundary: it shares the page's origin.

## 4. Comparison

Sizes are first-load downloads before compression. "Pyodide core" is about 13.5 MB (wasm 9.6 MB, stdlib
2.5 MB, JS 1.3 MB, version 314.0.7), plus fontTools and Pillow. It is cached after the first visit.

| | A static | B Canvas 2D | C Cairo in wasm | D hybrid | E JS port |
|---|---|---|---|---|---|
| W1 gallery online | ✅ | ✅ | ✅ | ✅ | ✅ |
| W2 no install / W3 share / W5 embed | ❌ | ✅ | ✅ | ✅ | ✅ |
| Semantic contract | n/a | most rows; AA, `no_smooth`, pixel values differ | **all rows** except the blocking `show()` | as B on screen, all in files | rewritten |
| Goldens | exact (they *are* the goldens) | tolerance (≤ ~2–3 % edge pixels in Spike 08) | **expected exact** (unverified) | screen: tolerance; files: exact | tolerance at best |
| PDF / SVG on the web | download desktop-made files | SVG new; PDF deferred | **as desktop** | as desktop | new |
| Sound, microphone | ❌ | ✅ (shared pieces) | ✅ | ✅ | rewritten |
| Speed at DPR 2 | n/a | fast (GPU-composited) | **the risk**: to be measured | fast | fast |
| Extra download beyond Pyodide | 0 | small (JS renderer, uharfbuzz or harfbuzzjs ~0.5–1 MB) | + pycairo, uharfbuzz, skia-pathops wasm (unverified, estimated 3–5 MB) | B + C's, lazily | tiny runtime |
| Product code to write | small | renderer, canvas pictures, SVG writer, (PDF) | shared pieces only | most | everything |
| Build engineering | none | uharfbuzz wheel or shim | three wheels, yearly | three wheels | none |
| Second implementation to keep in step | no | yes (renderer) | **no** | yes | yes (all) |
| Effort (rough, unverified) | days | 2–3 sprints | 1–2 sprints after the builds work | 3–4 sprints | many |

## 5. Recommendation

1. **Ship A in 0.2 regardless.** The gallery online is cheap, useful on its own, and the place where
   "Run in the browser" buttons will later live.
2. **Run spikes S-133 to S-135 before choosing a renderer** (section 6). They are cheap and they decide the
   rest.
3. **Prefer C, the desktop stack in wasm, if S-134 passes.** From first principles, funground's value is:
   - one contract;
   - vector files with real text;
   - the sound and microphone teaching;
   - p5-like friendliness.

   C keeps the first two *by construction*: the same renderer, export and picture code run, and the
   goldens can be checked byte for byte. The other two come from the shared pieces, which every route
   needs. C also writes the least product code and leaves no second renderer to drift. Its costs are
   build engineering (once, then yearly) and CPU speed, and S-134 measures exactly that.
4. **Fall back to B if Cairo-in-wasm is too slow or will not build.** Accept the tolerance, and make PDF
   desktop-only in 0.2. Consider D only if, after B, saving PDF/SVG on the web turns out to matter.
5. **Loop: L1 (inverted, Python in a module worker), for every route.** It needs no headers, works in all
   current browsers, and keeps learner code unchanged. Stop is `terminate()`. Keep L2 (JSPI) as a later
   enhancement.
6. **Editor: H0 then H1** (embeddable element, launcher URL, static editor with links that carry the code,
   on a separate preview origin). **No accounts (H3) in 0.2.** H2 (gists) only if the maintainer wants
   saving beyond links.
7. **Degrade, clearly, rather than block.** Proposed desktop-only in 0.2, each with a message that says so:
   - `system_font()`;
   - `input()`;
   - MP4 (GIF works);
   - choosing a microphone by name before permission;
   - `f.gallery`'s subprocess runner;
   - path booleans, if their wheel slips.

Why not the September recommendation (B) straight away? It was right for the 2025 IR. Since then the
contract has grown four things the Canvas route would have to reimplement: pictures with history, groups,
erase, and real PDF/SVG text with layers. Meanwhile PEP 783 made publishing wasm wheels ordinary. The
balance has moved towards C, but only a measurement can confirm it.

## 6. Feasibility spikes, in order

Each spike is time-boxed, lives in `spikes/NN_name/`, writes its numbers into `spikes/RESULTS.md`, and
changes no product code (prototypes stay on a spike branch). Spikes 1–3 decide the renderer. 4–8 de-risk
the shared pieces.

| # | Story | Question | Pass | Fail means |
|---|---|---|---|---|
| 1 | **S-133** uharfbuzz in Pyodide (2 days) | Can uharfbuzz be built as a `pyemscripten_2026_0` wheel, and does `typography.py` then give the same outlines as native? | The wheel builds with cibuildwheel 4 / `pyodide-build`. For every golden's text and the T-row test strings, the `FillPath` ops from Pyodide equal the native ones exactly | Write a shim with uharfbuzz's small used API (Face, Font, Buffer, shape, variations) over harfbuzzjs, and repeat the comparison |
| 2 | **S-134** Cairo in Pyodide (3–4 days) | Can pycairo (with cairo and pixman) be built for Pyodide 314, and is it fast enough? | (a) It builds. (b) The 14 Session-1 goldens rendered in Pyodide (Node) are **byte-identical** to `tests/golden`. (c) Gallery examples (the 10 heaviest by op count) average **≤ 12 ms a frame at 640×400 × DPR 2** in Chrome on the teaching machine, and ≤ 25 ms on a low-end Chromebook if one is available. (d) The three wheels add ≤ 6 MB | (a) or (c) fails: architecture B. (b) fails by AA only: C still works with a tolerance |
| 3 | **S-135** Canvas 2D over today's IR (3 days) | Does the IR replayed on Canvas 2D match the Cairo goldens within a tolerance, for every op type? | Spike 08's `ir_canvas.js` extended to all 20 op types (groups, erase, shadows, pixel blocks, images with tint and source rectangles). Against the 14 goldens and 20 gallery goldens: ≤ 3 % pixels differing and mean absolute difference ≤ 3, differences only on anti-aliased edges, in Chrome, Firefox and Safari. A list of ops that cannot match | Fails on structure (not just edges): B is costlier than estimated, which strengthens C |
| 4 | **S-136** The inverted loop in a worker (3 days) | Does a sketch run unchanged, driven by `requestAnimationFrame`, with Python in a module worker and no COOP/COEP, on GitHub Pages? | A prototype of `start/step/finish` (desktop tests still green on the spike branch). Session-1 sketches with mouse and keys at a steady 60 fps in Chrome, Firefox and Safari. Stop ends a `while True:` sketch within 1 s. Input-to-screen delay ≤ 2 frames | If input lags or messages cost too much: a SharedArrayBuffer for input (L3) on Cloudflare Pages |
| 5 | **S-137** Sound and microphone (2 days) | Do made sounds play and does the microphone feed `level()`/`pitch()` from a worker? | After one click: `f.tone`, `f.melody` and a raga drone play in three browsers. Synthesis of the longest gallery melody in wasm ≤ 1 s. Microphone level reaches Python ≤ 100 ms after the sound. A denied permission gives the "not listening" values and a clear message | Pre-compute in a second worker, or cap lengths on the web |
| 6 | **S-138** Files on the web (2 days, after S-134) | Do PNG, PDF (real text and layers), SVG (live text) and GIF from Pyodide equal the desktop files? | With C: the same bytes as desktop (pypdf and fontTools in Pyodide), or differences only in timestamps and IDs. GIF via Pillow in ≤ 2× desktop time. MP4: does WebCodecs + Mediabunny produce a playable file in Chrome and Safari 26? | Without C: only PNG and GIF, plus the SVG writer as a story |
| 7 | **S-139** First load and size (1 day) | How long until the first frame on a real page? | First visit ≤ 10 s on a 10 Mb/s link. Repeat visit ≤ 3 s. A budget per piece (Pyodide, fontTools, Pillow, funground, fonts, wheels) | Trim: lazy fonts, no Pillow until needed, a smaller funground web wheel without the gallery |
| 8 | **S-140** Sharing by link (½ day) | Do gallery examples fit in a link? | Code compressed with `deflate-raw` and base64url: 95 % of the 95 examples under 8 KB of URL. List those that need data files | Use GitHub links for those. Consider H2 |

Not spiked: pygame-ce in Pyodide as a sound and image provider. Pyodide calls its SDL support
experimental, PyScript says it must run on the main thread, and whether `pygame.mixer` and
`pygame._sdl2.audio` work there is **unverified**. Pillow and Web Audio are the simpler providers.

## 7. Decisions only the maintainer can make

| # | Decision | Options | Notes |
|---|---|---|---|
| Q1 | What the web target is for, in order | W1 gallery online · W2 run without installing · W3 share by link · W4 hosted editor with accounts · W5 runnable lesson pages | Drives everything else. The recommendation assumes W1 + W2 + W3 (+ W5), not W4 |
| Q2 | Does 0.2 bring the browser forward from "after 1.0" (D-014)? | yes, in 0.2 · partly (gallery only) · keep after 1.0 | A new decision row superseding D-014 |
| Q3 | Fidelity bar on the web | identical to desktop (pushes C) · "visually equivalent" within a tolerance (allows B) | A contract question: is the golden the web's truth? |
| Q4 | What may be desktop-only in 0.2 | the list in section 5 point 7 · fewer · more (e.g. microphone, PDF) | Each becomes a web contract row with its message |
| Q5 | Browser and device floor | Chrome/Edge only · plus Firefox · plus Safari (macOS, iPad) · phones | Safari is the hardest (no `ctx.filter`, WebCodecs only from 26, no `credentialless`) |
| Q6 | Editor scope | H0 embed and launcher · H1 static editor with links · H2 gists · H3 accounts | H3 brings moderation and children's-privacy duties |
| Q7 | Owning wasm builds | build and publish `pyemscripten` wheels of pycairo, uharfbuzz, skia-pathops (yearly) · ask upstream projects to publish them · avoid (B) | An ongoing maintenance commitment |
| Q8 | Loop inversion in the desktop code (S-060) | accept in 0.2 · keep the `while` loop and require JSPI (Chrome only) | The recommendation needs it. The desktop gains a steppable sketch |
| Q9 | Where it lives | GitHub Pages under `funground-hq` (with a second origin for previews) · Cloudflare Pages · a project domain | Domains cost money. A separate preview origin is a security requirement for H1 |
| Q10 | Version and packaging | one `funground` wheel for both · a slimmer web build (no gallery data, lazy fonts) | Affects S-139 |

## 8. Sources

All checked on 8 October 2026 unless noted. Repository evidence: `spikes/RESULTS.md` §2–§5 and §8,
`spikes/08_browser_pyodide/`, `docs/design/Browser_Mode_Note.md`, `funground/ir.py`,
`funground/sketch.py` (`run_namespace`, `show`), `funground/picture.py`, `funground/typography.py`,
`funground/export/`, `tests/test_boundaries.py`.

**Python runtimes**
- Pyodide 314.0.7 (14 September 2026), Python 3.14.2, Emscripten 5.0.3; version numbering; module workers
  only: https://pyodide.org/en/stable/project/changelog.html, https://blog.pyodide.org/posts/314-release/
- Packages in Pyodide (numpy 2.4.6, Pillow 12.2.0, fontTools 4.62.1, pygame-ce 2.5.7, imageio 2.37.3,
  matplotlib 3.10.8; no pycairo, uharfbuzz, skia-pathops): https://pyodide.org/en/stable/usage/packages-in-pyodide.html
- pyodide-recipes (no pycairo, uharfbuzz, skia-pathops recipes): https://github.com/pyodide/pyodide-recipes
- PEP 783, Emscripten packaging (accepted; `pyemscripten_2026_0`): https://peps.python.org/pep-0783/
- PyPI file lists (no Emscripten wheels): https://pypi.org/simple/pycairo/, https://pypi.org/simple/uharfbuzz/,
  https://pypi.org/simple/skia-pathops/; pure-Python: https://pypi.org/project/pypdf/, https://pypi.org/simple/svgelements/
- micropip and loading packages: https://pyodide.org/en/stable/usage/loading-packages.html
- File sizes of pyodide@314.0.7: https://data.jsdelivr.com/v1/packages/npm/pyodide@314.0.7
- Speed ("3x to 5x slower"; old start-up figure 4–5 s): https://pyodide.org/en/stable/project/roadmap.html
- No threads: https://pyodide.org/en/stable/usage/wasm-constraints.html; PEP 776: https://peps.python.org/pep-0776/
- WebLoop: https://pyodide.org/en/stable/usage/api/python-api/webloop.html; `time.sleep` and stdin:
  https://pyodide.org/en/stable/usage/streams.html
- `run_sync` and JSPI: https://pyodide.org/en/stable/usage/api/python-api/ffi.html, https://blog.pyodide.org/posts/jspi/,
  https://v8.dev/blog/jspi; Firefox/Safari JSPI status (secondary, unverified): https://blog.openreplay.com/jspi-javascript-wasm-bridge/
- SDL in Pyodide (experimental): https://pyodide.org/en/stable/usage/sdl.html
- Workers: https://pyodide.org/en/stable/usage/webworker.html; interrupts need SharedArrayBuffer:
  https://pyodide.org/en/stable/usage/keyboard-interrupts.html
- PyScript 2026.7.3, workers, sync bridge, pygame-ce, editor: https://github.com/pyscript/pyscript/releases,
  https://docs.pyscript.net/2026.7.3/user-guide/workers/, https://docs.pyscript.net/2026.7.3/faq/,
  https://docs.pyscript.net/2026.7.3/user-guide/pygame-ce/, https://docs.pyscript.net/2026.7.3/user-guide/editor/
- MicroPython webassembly: https://data.jsdelivr.com/v1/packages/npm/@micropython/micropython-webassembly-pyscript@1.29.0-6,
  https://github.com/micropython/micropython/blob/master/ports/webassembly/README.md
- Brython: https://github.com/brython-dev/brython/releases/, https://brython.info/static_doc/3.14/en/faq.html;
  Skulpt: https://registry.npmjs.org/skulpt/latest, https://github.com/skulpt/skulpt
- py2wasm (last release April 2024, Python 3.11, WASI target): https://pypi.org/pypi/py2wasm/json,
  https://wasmer.io/posts/py2wasm-a-python-to-wasm-compiler
- CPython support tiers (WASI tier 2, Emscripten tier 3): https://peps.python.org/pep-0011/

**Existing projects**
- Pyxel web: https://github.com/kitao/pyxel/blob/main/docs/web-usage.md, https://raw.githubusercontent.com/kitao/pyxel/main/wasm/pyxel.js,
  https://pypi.org/project/pyxel/
- pygbag 0.9.3 and its async loop: https://pypi.org/pypi/pygbag/json, https://github.com/pygame-web/pygbag, https://pygame-web.github.io/
- p5.js Web Editor (stack, preview, routes, releases, deployment): https://github.com/processing/p5.js-web-editor,
  https://raw.githubusercontent.com/processing/p5.js-web-editor/develop/.env.example,
  https://raw.githubusercontent.com/processing/p5.js-web-editor/develop/client/modules/Preview/EmbedFrame.jsx,
  https://raw.githubusercontent.com/processing/p5.js-web-editor/develop/server/routes/embed.routes.ts,
  https://github.com/processing/p5.js-web-editor/releases,
  https://github.com/processing/p5.js-web-editor/blob/develop/contributor_docs/deployment.md
- p5 editor present mode removed (phishing): https://discourse.processing.org/t/editor-p5js-org-present-mode-disappeared/33495;
  preview origin: https://discourse.processing.org/t/embedding-p5-js-web-editor-in-external-site/18400;
  asset limit: https://discourse.processing.org/t/you-cannot-upload-any-more-files-in-p5-js-web-editor/48976
- p5 terms and privacy: https://p5js.org/terms-of-use, https://p5js.org/privacy-policy/
- p5.js releases: https://github.com/processing/p5.js/releases
- pyp5js: https://pypi.org/pypi/pyp5js/json, https://berinhard.github.io/pyp5js/; p5 (p5py): https://p5.readthedocs.io/;
  py5 (JVM): https://py5coding.org/content/install.html
- Trinket shutdown (31 August 2026) and trinket-oss: https://trinket.io/announcement, https://github.com/trinketapp/trinket-oss
- Basthon and Capytale: https://basthon.fr/, https://framagit.org/basthon/basthon-kernel/-/raw/master/README.md,
  https://www.ac-paris.fr/capytale-un-service-web-pour-creer-et-partager-des-activites-pedagogiques-de-codage-127480
- Pyde (code in the URL hash): https://github.com/milesberry/pyde
- JupyterLite: https://jupyterlite.readthedocs.io/en/stable/, https://pypi.org/pypi/jupyterlite-pyodide-kernel/json
- marimo WASM and sharing: https://docs.marimo.io/guides/wasm/, https://docs.marimo.io/guides/publishing/playground/
- Thonny (desktop only): https://thonny.org/
- matplotlib-pyodide (Agg buffer to canvas; canvas renderer): https://github.com/pyodide/matplotlib-pyodide,
  https://blog.pyodide.org/posts/canvas-renderer-matplotlib-in-pyodide/
- ipycanvas batching: https://ipycanvas.readthedocs.io/en/latest/drawing_shapes.html

**Rendering, files, audio**
- Canvas 2D: https://developer.mozilla.org/en-US/docs/Web/API/CanvasRenderingContext2D/globalCompositeOperation,
  https://developer.mozilla.org/en-US/docs/Web/API/CanvasRenderingContext2D/createConicGradient,
  https://caniuse.com/mdn-api_canvasrenderingcontext2d_filter, https://developer.mozilla.org/en-US/docs/Web/API/CanvasRenderingContext2D/letterSpacing,
  https://caniuse.com/mdn-api_canvasrenderingcontext2d_fontkerning, https://developer.mozilla.org/en-US/docs/Web/API/CanvasRenderingContext2D/reset,
  https://caniuse.com/offscreencanvas, https://html.spec.whatwg.org/multipage/canvas.html,
  https://developer.mozilla.org/en/docs/Web/API/CanvasRenderingContext2D/imageSmoothingEnabled
- Firefox canvas back ends: https://firefox-source-docs.mozilla.org/gfx/Moz2D.html
- Text rendering differs across browsers (fingerprinting research): https://www.ieee-security.org/TC/W2SP/2012/papers/w2sp12-final4.pdf
- CanvasKit 0.42.0 (sizes, features, no PDF): https://registry.npmjs.org/canvaskit-wasm/latest,
  https://data.jsdelivr.com/v1/packages/npm/canvaskit-wasm@0.42.0?structure=flat,
  https://cdn.jsdelivr.net/npm/canvaskit-wasm@0.42.0/types/index.d.ts
- harfbuzzjs 1.6.3: https://github.com/harfbuzz/harfbuzzjs, https://data.jsdelivr.com/v1/packages/npm/harfbuzzjs@1.6.3?structure=flat
- PDF libraries: https://registry.npmjs.org/jspdf/latest, https://raw.githubusercontent.com/Hopding/pdf-lib/master/README.md,
  https://pdfkit.org/docs/getting_started.html
- toBlob: https://developer.mozilla.org/en-US/docs/Web/API/HTMLCanvasElement/toBlob; gifenc: https://github.com/mattdesl/gifenc
- Mediabunny (successor of mp4-muxer): https://mediabunny.dev/, https://github.com/Vanilagy/mp4-muxer; WebCodecs: https://caniuse.com/webcodecs
- Save picker (Chromium only): https://caniuse.com/native-filesystem-api; OPFS:
  https://developer.mozilla.org/en-US/docs/Web/API/File_System_API/Origin_private_file_system
- Web Audio: https://developer.mozilla.org/en-US/docs/Web/Media/Guides/Autoplay,
  https://developer.mozilla.org/en-US/docs/Web/API/AudioBuffer/copyToChannel, https://developer.mozilla.org/en-US/docs/Web/API/AudioWorklet,
  https://developer.mozilla.org/en-US/docs/Web/API/StereoPannerNode, https://developer.mozilla.org/en-US/docs/Web/API/BaseAudioContext/decodeAudioData
- Microphone: https://developer.mozilla.org/en-US/docs/Web/API/MediaDevices/getUserMedia
- requestAnimationFrame: https://developer.mozilla.org/en-US/docs/Web/API/Window/requestAnimationFrame
- FontFace: https://developer.mozilla.org/en-US/docs/Web/API/FontFace/FontFace

**Hosting, sharing, security**
- GitHub Pages limits and headers: https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits,
  https://github.com/orgs/community/discussions/13309; coi-serviceworker: https://github.com/gzuidhof/coi-serviceworker
- Cloudflare limits: https://developers.cloudflare.com/pages/platform/limits/, https://developers.cloudflare.com/workers/platform/limits/,
  https://developers.cloudflare.com/workers/static-assets/billing-and-limitations/
- Netlify credits: https://docs.netlify.com/manage/accounts-and-billing/billing/billing-for-credit-based-plans/credit-based-pricing-plans/
- jsDelivr limits: https://github.com/jsdelivr/jsdelivr; Pyodide deployment: https://pyodide.org/en/stable/usage/downloading-and-deploying.html
- URL lengths: https://chromium.googlesource.com/chromium/src/+/main/docs/security/url_display_guidelines/url_display_guidelines.md;
  Firefox/Safari figures (secondary): https://nuqs.dev/docs/limits
- CompressionStream: https://developer.mozilla.org/en-US/docs/Web/API/CompressionStream/CompressionStream
- TypeScript playground URLs: https://www.typescriptlang.org/_playground-handbook/url-structure.html
- Gists and OAuth: https://github.blog/2018-03-20-removing-anonymous-gist-creation, https://docs.github.com/en/rest/gists/gists,
  https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/authorizing-oauth-apps,
  https://docs.github.com/en/rest/using-the-rest-api/using-cors-and-jsonp-to-make-cross-origin-requests,
  https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api,
  https://github.blog/changelog/2025-05-08-updated-rate-limits-for-unauthenticated-requests/
- COPPA amended rule: https://www.federalregister.gov/documents/2025/04/22/2025-05904/childrens-online-privacy-protection-rule;
  GDPR Art. 8: https://gdpr-info.eu/art-8-gdpr/
- Cloudflare D1/KV/R2 free tiers: https://developers.cloudflare.com/d1/platform/pricing/, https://developers.cloudflare.com/kv/platform/pricing/,
  https://developers.cloudflare.com/r2/pricing/
- iframe sandbox: https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/iframe; CodePen's preview domain:
  https://blog.codepen.io/2019/10/03/changed-domains-for-iframe-previews/
- Cross-origin isolation: https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Cross-Origin-Embedder-Policy,
  https://caniuse.com/mdn-http_headers_cross-origin-embedder-policy_credentialless, https://web.dev/articles/coop-coep
- Storage quotas: https://developer.mozilla.org/en-US/docs/Web/API/Storage_API/Storage_quotas_and_eviction_criteria

### Could not verify

- Pyodide 314's cold-start time and compressed download size. The only official start-up figure (4–5 s)
  is old. Spike 08 measured 2.5–3 s locally on Pyodide 0.28.
- Pyodide's slowdown: the docs say 3–5×; Spike 08 measured 2–2.5× for funground frames. Neither is a
  figure for C code such as pixman.
- JSPI default status in Firefox and Safari (one secondary source only).
- That Cairo, pycairo, uharfbuzz and skia-pathops build cleanly with Emscripten 5.0.3, their wasm
  sizes, and whether Cairo in wasm gives byte-identical goldens. No public build was found.
- Whether pygame-ce's mixer and `pygame._sdl2.audio` work in Pyodide.
- `decodeAudioData` format support per browser (MP3, Ogg Vorbis on Safari).
- Current per-browser anti-aliasing of paths and clips (sources found were 2009–2010).
- Firefox and Safari URL length limits from primary sources. Unauthenticated raw.githubusercontent.com
  limits since May 2025.
- Whether pyscript.com is still operated, and its limits.
- p5 editor costs and moderation workload (none published).
- Effort figures in section 4 are estimates by analogy with funground's own sprints, not measurements.
