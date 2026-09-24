# Sprint 4 — Phase 2a: the public vocabulary on the vector model

**Dates:** to be set by the maintainer (opens after Sprint 3 sign-off — done 25 Sept 2026)
**Goal:** expose what the IR already carries: transforms, a state stack, paths and clipping — as
learner-facing functions with pinned semantics — and bring the Quick Reference up to v0.6.
**Checkpoint:** existing Session-1 goldens and IR snapshots unchanged (everything is additive);
new sample sketches for each new verb with their own goldens and snapshots; contract rows F2/F3
pinned; `docs/reference` Quick Reference v0.6 published.
**Decisions open at start:** none. **Likely to raise:** D-013 naming of the state context manager
(`with p.state():` vs `with p.push():`), D-014 `rect_mode`-style switches (recommendation: keep
postponed, per the other agent's note).

## Story set

### S-027 Transforms and the state stack — E-10
- [x] S-027.1 `p.translate(dx, dy)`, `p.rotate(degrees)`, `p.scale(s)` / `p.scale(sx, sy)` emit `ir.Concat`; `p.radians()`, `p.degrees()` helpers (D-002)
- [x] S-027.2 `p.push()` / `p.pop()` emit `ir.Save` / `ir.Restore` **and** save/restore the `GraphicsState` (fill, stroke, width, text size) — one stack for both, so "restore restores everything" (other agent's contract row)
- [x] S-027.3 `with p.state():` context manager = push on enter, pop on exit, exception-safe
- [x] S-027.4 End-of-frame safety: unbalanced pushes are unwound at frame end with a `PlaygroundWarning` naming the count (never a crash mid-lesson)
- [x] S-027.5 Contract F2 pinned: transforms are cumulative; apply to all later geometry, text and images; the stack resets at the start of every `draw()`
- [x] S-027.6 Semantic tests (rotation direction, order of operations, nesting) + sample sketch `13_transforms.py` with golden + snapshot
*Acceptance:* `p.translate(100, 50); p.rotate(30); p.rect(0, 0, 80, 40)` draws exactly what Spike 05/07 drew for the same ops.
*Status:* done — `tests/test_transforms.py` (19 tests), sample `13_transforms.py` with golden + snapshot; contract F2 pinned; D-013 raised below.

#### D-013 (pending) — name of the state-stack context manager

1. **Context.** S-027.3 needs a `with`-block form of push/pop so a learner's block cannot leak style or transform even when it raises. The name is a public one and so is the maintainer's call; the sprint plan recommended `state()`. Without a decision the implemented name stays.
2. **Options.** **A** `with p.state():` (implemented) — a noun for the thing being saved. **B** `with p.push():` — `push()` returns a context manager, so `p.push()` on its own line still works as a plain call (p5's `push()`/`pop()` names, one fewer word to learn). **C** both, one as an alias.
3. **Trade-offs.** A: clear that a block is being scoped; one more name in the reference (now 8 new names in S-027). B: fewest names, matches p5, but a returned context manager that is usually ignored is an unusual shape and `with p.push():` reads as "with push" rather than "with saved state". C: no learner has to guess, but two names for one thing is what the Quick Reference tries to avoid.
4. **Recommendation.** A.
5. **Why.** Beginners meet `with open(...)` first; `with p.state():` follows the same "with *a thing*" pattern. Would change if the maintainer wants strict p5 vocabulary (then B). Either way the change is a one-line alias in `api.py` plus the contract row.

### S-028 Paths and clipping — E-11
- [x] S-028.1 `p.begin_shape()` / `p.vertex(x, y)` / `p.curve_vertex(...)` / `p.end_shape(close=False)` — the p5-shaped, beginner-first API; emits `FillPath`/`StrokePath` with the current style
- [x] S-028.2 `path = p.path()` builder object (`move_to`, `line_to`, `curve_to`, `close`) for reuse; `p.draw_path(path)`; `p.clip(path)` emits `ClipPath` (inside a `push`/`pop`)
- [x] S-028.3 Contract F3 pinned: fill rule non-zero; open shapes are stroked not filled unless closed
- [x] S-028.4 Tests + sample sketch `14_paths.py` with golden + snapshot
*Acceptance:* a star, a Bézier curve and a clipped pattern render through Cairo and export to PDF.
*Status:* done — `playground/paths.py` (`PathBuilder`, also `quad_to`), `tests/test_paths.py` (23 tests incl. a headless PDF export of the sample), sample `14_paths.py` with golden + snapshot; contract F3 pinned (the former mode-switch row is now F4, still proposed). No new decision raised: every public name came from this plan.

### S-037 Text rendering polish — E-15 *(small, from Sprint 3 findings)*
- [x] S-037.1 Cap the per-window `TextRun` cache (LRU, 256 entries) — `p.text(p.frame_count, …)` must not grow without bound
- [x] S-037.2 `p.text_width(message)` helper (advance in logical pixels) so learners can centre text
*Acceptance:* a 10 000-frame headless run with changing text keeps the cache ≤ 256.
*Status:* done — `CairoRenderer._text_runs` is an `OrderedDict` LRU capped at `TEXT_RUN_CACHE_SIZE = 256` (evicts least recently *used*, so a title drawn every frame survives a changing counter); `p.text_width(message)` via `playground.typography.text_width` (kerned advance, `str()` applied, transform-independent); contract T6 pinned; six tests in `tests/test_text.py` (1000-frame cache run, LRU order, size scaling, kerning, transforms, centred-text pixel check). No sample sketch, no new decision: name and semantic came from this plan.

### S-038 macOS / Linux HiDPI — E-13 *(follow-up from S-024)*
- [x] S-038.1 `detect_backing_scale()` on macOS/Linux via SDL's high-DPI window flag and drawable-size vs window-size ratio
- [x] S-038.2 Cannot be verified on the teaching machine; CI on macOS runs the forced-scale tests only; real verification deferred to a maintainer with the hardware
*Acceptance:* code path exists and is unit-tested with a forced scale; documented as unverified on real hardware.
*Status:* done as a code path — **NOT verified on real macOS / Linux hardware; do not claim it works there.** Research (pygame-ce 2.5.8 `src_c/display.c` / `window.c`, SDL 2.32 `SDL_video.c`): `display.set_mode()` never sets `SDL_WINDOW_ALLOW_HIGHDPI` and `SCALED` is the wrong tool (a logical surface upscaled by a renderer), but `pygame.Window(..., allow_high_dpi=True)` sets the flag and, since SDL 2.26, `Window.get_surface()` is sized with `SDL_GetWindowSizeInPixels` (drawable) while `Window.size` uses `SDL_GetWindowSize` (screen points) — their ratio is the backing scale. Implementation in `playground/platform/pygame_platform.py`: on `darwin` / `linux*` with a real driver and no override, `open_window` creates that window at the *logical* size, takes its surface as the physical target, measures the scale from the real window (`detect_backing_scale(window)`; with no window a hidden probe window is opened and destroyed), presents with `Window.flip()`, and does **not** divide mouse coordinates (SDL reports them in screen units on this route). Windows (`set_mode`, per-monitor DPI), the dummy driver (1.0) and `PLAYGROUND_BACKING_SCALE` are untouched, so the forced-scale tests run identically on every CI OS. Six simulated tests in `tests/test_hidpi.py` (fake `pygame.Window` at 2× and 1×, `sys.platform` patched to darwin and linux: probe ratio, physical window size, logical mouse, flip/destroy, probe failure → 1.0, override bypass, win32 guard). **Pending for a maintainer with a Retina Mac or a Wayland desktop:** run `examples/session1/01_first_sketch.py`, confirm the window is 640×400 points, `s._platform.backing_scale == 2.0`, shapes are crisp and the mouse-follow example tracks the cursor; if the surface comes back at window size (ratio 1.0) the sketch still runs, just not crisp — that is the designed fallback. Linux X11 has no SDL2 HiDPI, so 1.0 there is expected. No new decision raised.

### S-030 Quick Reference v0.6 — E-22
- [ ] S-030.1 `docs/reference/Playground_Quick_Reference_v0.6.md`: every v0.5 page updated for the pinned semantics (text size, centred strokes, alpha), plus new pages for `save`, transforms, `state()`, shapes/paths, `random_seed`, `text_width`
- [ ] S-030.2 Screenshots regenerated from the sample sketches via `p.save()` (headless) so the reference is produced by the code it documents
- [ ] S-030.3 Colour appendix kept; note on DejaVu Sans
*Acceptance:* every function in `__all__` appears in the reference with one runnable example.

### S-039 CI first run — E-02 *(needs a remote)*
- [ ] S-039.1 Push to a remote and get the 12-cell matrix green; fix what only CI finds (Linux/macOS font rasterisation is irrelevant — goldens are Windows-only by policy; snapshots must pass everywhere)
*Acceptance:* green badge; blocked until the maintainer provides a remote.

## Out of scope
Images, sound, SVG import, gradients as public API (Phase 3); searchable-PDF text (S-032); Blend2D (S-036).
