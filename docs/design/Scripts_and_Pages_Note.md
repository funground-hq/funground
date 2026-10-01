# Design note: scripts, pages and documents

**Status:** decided (D-029, 30 Sept 2026 and D-036, 1 Oct 2026, both under D-034 for the page names).
Built in Sprint 7 (S-076), Sprint 8 (S-084, S-085). Contract rows R13 to R17 and D1 in
[Semantic_Contract.md](Semantic_Contract.md). Code: `Sketch.size`, `_begin_script`, `_start_page`,
`new_page`, `show`, `_save_script`, `_save_pages` in `funground/sketch.py`; `funground/pages.py`;
`save_document` in `funground/export/__init__.py`; `exit_hint` in `funground/api.py`.

## The problem

Until Sprint 7 every funground file was an animated sketch: `draw()` and `f.run()`. A learner who
wants one picture, or a multi-page PDF as in DrawBot, had to fake it. A top-level `size()` opened a
window, and a top-level `save()` wrote nothing and said nothing.

## The route: two styles, no third

D-029 chose option D. A file is **either** an animated sketch **or** a script.

```
animated sketch                         script
  setup()  (optional)                     f.size(w, h)        no window
  draw()                                  f.circle(...)       ops kept
  f.run()                                 f.save("a.png")     written now
                                          f.new_page("A4")    next page
                                          f.show()            window, waits
```

- `Sketch.size()` looks at `self.running`. Inside `run_namespace` it opens a window. Outside it
  calls `_begin_script`.
- A script keeps every op in `self.frame`. `_script_flush` draws only the new ones onto the
  renderer's persistent surface (`_script_drawn`, `_script_depth`, `draw_batch`).
- `_has_window` is True for a script, so `create_graphics`, `get`, `pixels`, fonts and `image`
  work unchanged. Animation-only calls go through `_only_in_animated` and raise a `RuntimeError`
  that names the animated style.
- `run_namespace` on a script with a non-empty frame raises the "mixes the two styles" error. A
  script with only `f.size()` is turned back into a plain size setting, so a draw-only sketch may
  call `f.size()` first (R13).
- `_sketch_functions` gives `setup()` with no `draw()` an error that offers both styles.
- `exit_hint` is registered with `atexit`. It prints one line to stderr when `__main__` has a
  callable `draw` and `f.run()` never started. It stays quiet in interactive sessions
  (`sys.ps1`, `sys.flags.interactive`), for scripts, and after a crash (`_note_crash` is the
  `sys.excepthook`).

## Saving and showing

- `save()` in a script is immediate. PNG: `_script_flush`, then `save_pixels` of the surface at
  `_script_scale` (1, or `FUNGROUND_BACKING_SCALE`). PDF and SVG: `save_frame` replays the whole
  frame as vectors.
- In an animated sketch `save()` queues in `_pending_saves`. `_render` writes it once the frame
  is complete.
- `show()` makes a fresh renderer at the window's backing scale and replays `self.frame` onto it.
  So a script drawn at scale 1 is still sharp on a HiDPI window. Headless it returns at once.
- Why replay rather than present the surface: the surface was drawn at the script's own scale.

## Pages (D-036)

DrawBot's names, because DrawBot is the model for documents and its names port directly:
`new_page`, `page_count`, `page_size`. `size()` keeps its frozen v0.5 signature.

```
self._pages  = [ (w, h, ops, bgra pixels), ... ]    finished pages
self.frame / self._renderer                          the current page, live
```

- `new_page` calls `_sync_canvas`, stores the finished page with a copy of its pixels, then
  `_start_page`. That builds a new surface, empties the frame, unwinds `push`es and resets the
  pixel state. Style settings carry over; transform and clip do not (R16).
- Before any `size()`, `new_page` simply starts the first page by calling `size()`.
- `size()` again clears `_pages`: a new document.
- `page_size` (`pages.py`) is a small table in points (1/72 inch, the PDF unit, and one logical
  pixel). A name ending in `Landscape` swaps the sides. A name given to `new_page` stands alone.
- `save("x.pdf")` calls `save_document`: one `PDFSurface`, `set_size` for each page, the page's
  ops replayed through `CairoRenderer.draw`, then `show_page`. Each page has its own size.
- `save("x.png")` or `.svg` with several pages writes `x_1.png`, `x_2.png` and so on.
  Earlier PNG pages come from the stored pixels. SVG pages replay their ops.
- `show()` with pages (`_show_pages`) opens the current page, then re-attaches the renderer and
  replays when the arrow keys change page. The window title says "page n of N".

## Full screen in a script (S-085)

`full_screen()` in a script sets `width` and `height` from `platform.display_size()` (headless:
1920 by 1080) and `_page_full`. No window opens. `show()` then calls `open_full_screen`. The flag
is kept per page in `_pages_full`.

## Alternatives rejected

- **Setup-only sketches (D-029 A)** and **A plus scripts (B)**: option D has no setup-only form.
  A file with `setup()` and no `draw()` gets an error that offers both styles.
- **Keep `draw()` required and make a top-level `save()` an error (C)**: it fixes the silent
  `save()` but leaves DrawBot-style use out.
- **Auto-start the sketch.** Python cannot run code after a file ends in IDLE or Thonny, so a
  missing `f.run()` would fail silently there. Hence a hint at exit, in terminals only.
- **A document object (D-036 alternative)**: the log prefers DrawBot's names, which port
  directly, and notes that scripts already hold every op.

## Invariants and edge cases

- One page behaves exactly like R14. `page_count()` is 0 before a canvas and 1 in an animated
  sketch.
- `new_page("A4", 10)` is a `ValueError`. `new_page` in an animated sketch is a `RuntimeError`.
- A page keeps its own `_page_full` flag, so full-screen and sized pages can mix.

## Memory per kept shape

A script keeps every op until it ends. Each op holds a reference to an immutable `GraphicsState`
(shared until the style changes), so an op costs about 100 bytes. Measured in Sprint 8: 1 000
circles are about 90 KB, 10 000 about 950 KB. A million shapes is about 100 MB. The contract's
first guess (1 KB per hundred) was ten times too low and was corrected (R14). Each finished page
also keeps a full copy of its pixels.

## Limits and follow-ups

- `Frame.ops` builds a new tuple on every call. `_script_flush`, `_document_pages` and
  `new_page` each copy the whole op list, so a script that calls `get()` in a loop slows as it
  grows. Not measured; a counter in `Frame` would remove the copy.
- Ops are never dropped, even under a full-canvas `background`. Saving in parts is the advice.
- Real-desktop `show()` and `full_screen()` are not tested in CI (headless only). The Roadmap lists
  a manual run as a release prerequisite.
- Open question: `_start_page` calls `unwind()`, so a style set *inside* an open `push()` is
  lost on a new page. R16 says style carries over and does not mention this case.

## Tests

`tests/test_script_mode.py` (R13 to R15, exit hint), `tests/test_pages.py` (R16, R17, D1, page
reading with `/MediaBox` checks), `tests/test_script_mode.py` (full screen and the memory measurement, S-085), `tests/test_window.py` (R12). Sprint 8 review:
[sprint-08/review.md](../../sprints/sprint-08/review.md).
