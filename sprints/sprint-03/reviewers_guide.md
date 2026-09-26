# Sprint 3 — Reviewer's guide

For the maintainer reviewing Sprint 3 before closing it. Budget: about an hour. The sprint's
claim: **Cairo now draws everything; the only pixels that changed are the ones the contract said
would change; learner code asked for exactly the same things.**

Diff under review: `git diff 9d9bdab..HEAD -- playground tests`.

## 1. Verify the claim first (10 minutes)

```powershell
.venv\Scripts\python -m pytest                          # expect: 185 passed
git diff --stat db18b08..HEAD -- tests/snapshots         # expect: no output - IR snapshots unchanged since they were created
git log --oneline -- tests/golden                        # expect: exactly two commits touching goldens: 4dd11d6 (created) and ef97c53 (regenerated once)
git grep -n "pygame.draw\|pygame.font" -- playground     # expect: nothing
.venv\Scripts\python examples\session1\04_fill_stroke.py # real window: round line caps, crisp edges
```

Then open `sprints/sprint-03/before_after_04_fill_stroke.png` and `before_after_05_text.png`
(left v0.5, right Cairo) and confirm each difference is one listed in `review.md`.

## 2. Commits in reading order

| Commit | Story | Read | Why |
|---|---|---|---|
| `929a000` | S-029 | `playground/typography.py`, `tests/test_text.py` | Text as outlines. Leaf module (imports fontTools, uharfbuzz — not rendering backends). |
| `0200c65` | S-023 | `renderers/cairo2d.py`, `tests/test_cairo_renderer.py` | The renderer. Read `draw()` op by op against the contract rows. |
| `20356eb` | S-023.4 | `sketch.py` (renderer selection), the `text.py → typography.py` rename | The shadowing bug and its fix. |
| `ef97c53` | S-025 | `tests/test_semantics.py` (5 rewritten tests), `tests/golden/`, `Semantic_Contract.md` | The deliberate semantic change. |
| `984c957` | S-026 | deleted `legacy_pygame.py`, `tests/test_boundaries.py` | pygame is platform-only. |
| `7d82e4a` | S-024 | `platform/base.py`, `platform/pygame_platform.py`, `renderers/__init__.py`, `sketch.py`, `tests/test_hidpi.py` | Presentation moves to the platform; HiDPI. |
| `6ce1078` | S-034 | `platform/headless.py`, `export/__init__.py`, `api.py` (`save`), `tests/test_export.py`, `tests/test_headless.py` | Headless and export. |

## 3. What to scrutinise

### `renderers/cairo2d.py`
- `draw()` is the only place semantics live. Check each branch against the contract: `Clear` uses
  `OPERATOR_SOURCE` with the clip reset (a background must paint everything, even inside a clip
  from a previous op); `Circle` uses the diameter/2; `Ellipse` scales a unit circle (radius 0 →
  nothing); `_paint` fills then strokes (S5); `Point` is a filled dot of radius `stroke_width/2`.
- `draw()` tracks `Save`/`Restore` depth and unwinds at the end so a learner frame that forgets a
  restore (Phase 2 API) cannot leak transforms into the next frame. `Restore` without `Save` raises.
- `_text_ops` caches `TextRun`s per `(text, size)` per attach; the glyph-outline cache is inside
  `FontResource`. *Question:* the run cache is unbounded within a window session; is that acceptable? (A sketch printing `frame_count` creates one run per frame — ~1 KB each. I'd cap it in Phase 2 if it bothers you.)

### `typography.py`
- Anchor: `baseline = y + ascent * scale` — top-left of the em box, matching pygame's blit
  behaviour (contract T1). `test_text_anchors_at_top_left` passes under Cairo unchanged.
- Shaping features `kern` + `liga` on; nothing script-specific.

### `sketch.py`
- `_render()` now does render → present → flush saves → clear, and the loop no longer calls
  `present()` itself. Confirm `run_namespace` order: poll → input → `draw()` → capture ops →
  `_render()` → `frame_count += 1` → capture pixels → tick.
- `size()` opens the window at physical size and attaches the renderer with the platform's
  `backing_scale`. `_check_capabilities()` still runs first.
- `save()` validates the extension immediately (learner sees the error at the call site) and
  defers the write to frame end.

### `platform/pygame_platform.py`
- `detect_backing_scale()`: override env → dummy driver → Windows DPI → 1.0. The
  `SetProcessDpiAwareness(2)` call can only succeed once per process; failure is ignored.
- `input_state()` divides by the scale and rounds — mouse stays logical.
- `present()` is the only blit in the package.

### `platform/headless.py`
- `capture()` converts BGRA→RGB in pure Python (~50 ms at 640×400). Fine for tests; if headless
  export of long animations becomes a use case, this moves to the renderer.

### Tests
- The five rewritten semantic tests each say which contract row and decision they implement.
  `git diff db18b08..HEAD -- tests/test_semantics.py` should show only those five.
- `test_boundaries.py` now allows each backend only in its provider dir and asserts
  `pygame.draw`/`pygame.font` are gone.

## 4. Things I would flag

1. **D-012 (text size).** Text is ~1.4× larger than v0.5 at the same `text_size`. The goldens
   already embody option A (em-size). If you choose B, one more regeneration.
2. **macOS/Linux HiDPI is not done** — `detect_backing_scale()` returns 1.0 there. Windows was the
   teaching machine and the verified case; the others need `SDL_WINDOW_ALLOW_HIGHDPI` plumbing.
   Suggest a Phase 2 story.
3. **Base install is ~7 MB heavier** (pycairo, fontTools, uharfbuzz, DejaVu Sans). Within what
   ADR-001/002 accepted, but it is the first time the classroom install grew.
4. **`save()` is a new public name.** Additive, listed in `ADDED_FUNCTIONS`, but it is the first
   learner-facing vocabulary added since v0.5 beyond `random_seed`. Check you like the name and the
   "written at frame end" semantics.

## 5. Open decision

**D-012 — meaning of `text_size`.** Context, options, trade-offs and recommendation in
`Decision_Log.md` § Open.

## 6. Sign-off checklist

- [ ] 185 tests pass; IR snapshots unchanged; goldens touched by exactly two commits
- [ ] Every visual change in the composites is one listed in `review.md`
- [ ] No `pygame.draw`/`pygame.font` in the package; renderers import no pygame
- [ ] `run_namespace` order as stated; `save()` semantics acceptable
- [ ] Real-window run at your display scaling looks crisp
- [ ] D-012 decided, or explicitly deferred to Sprint 4
