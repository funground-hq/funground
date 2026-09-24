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
- [ ] S-028.1 `p.begin_shape()` / `p.vertex(x, y)` / `p.curve_vertex(...)` / `p.end_shape(close=False)` — the p5-shaped, beginner-first API; emits `FillPath`/`StrokePath` with the current style
- [ ] S-028.2 `path = p.path()` builder object (`move_to`, `line_to`, `curve_to`, `close`) for reuse; `p.draw_path(path)`; `p.clip(path)` emits `ClipPath` (inside a `push`/`pop`)
- [ ] S-028.3 Contract F3 pinned: fill rule non-zero; open shapes are stroked not filled unless closed
- [ ] S-028.4 Tests + sample sketch `14_paths.py` with golden + snapshot
*Acceptance:* a star, a Bézier curve and a clipped pattern render through Cairo and export to PDF.

### S-037 Text rendering polish — E-15 *(small, from Sprint 3 findings)*
- [ ] S-037.1 Cap the per-window `TextRun` cache (LRU, 256 entries) — `p.text(p.frame_count, …)` must not grow without bound
- [ ] S-037.2 `p.text_width(message)` helper (advance in logical pixels) so learners can centre text
*Acceptance:* a 10 000-frame headless run with changing text keeps the cache ≤ 256.

### S-038 macOS / Linux HiDPI — E-13 *(follow-up from S-024)*
- [ ] S-038.1 `detect_backing_scale()` on macOS/Linux via SDL's high-DPI window flag and drawable-size vs window-size ratio
- [ ] S-038.2 Cannot be verified on the teaching machine; CI on macOS runs the forced-scale tests only; real verification deferred to a maintainer with the hardware
*Acceptance:* code path exists and is unit-tested with a forced scale; documented as unverified on real hardware.

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
