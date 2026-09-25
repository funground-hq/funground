# Sprint 4 — Reviewer's guide

For the maintainer reviewing Sprint 4 before closing it. Budget: about an hour. The sprint's
claim: **sixteen new learner-facing names sit on top of the IR the previous sprints built; nothing
that existed before changed — not one pre-existing golden or snapshot byte — and every new
semantic is a pinned contract row with its own tests, sample sketch and reference page.**

Diff under review: `git diff 0d97587..HEAD -- playground tests` (21 files, +2 809 / −18).
Documents: `git diff 0d97587..HEAD -- docs sprints`.

## 1. Verify the claim first (10 minutes)

```powershell
.venv\Scripts\python -m pytest                                          # expect: 275 passed
.venv\Scripts\python -m pytest --co -q | Select-Object -Last 1          # expect: 275 tests collected (the -q addopts hides the summary line)
git diff --stat 3e4eccd..HEAD -- tests/golden tests/snapshots            # expect: ONLY 13_transforms.* and 14_paths.* (4 new files); no existing file listed
git log --oneline 0d97587..HEAD                                          # expect: 7 commits: 2 spike, 5 stories (578dba7 42dc6fb d885fb7 bd79d45 3dcc718)
git grep -n "import cairo\|import pygame" -- playground | findstr /v "platform/ renderers/"   # expect: only playground/export/__init__.py (pre-existing, D-011)
.venv\Scripts\python examples\session1\13_transforms.py                  # real window: spinning square, nested state blocks, nothing leaks frame to frame
.venv\Scripts\python examples\session1\14_paths.py                       # real window: star filled through its centre (non-zero), open polyline stroked only, clipped pattern
.venv\Scripts\python tools\make_reference_images.py                      # expect: 11 images rewritten in docs/reference/images, then `git status` shows them unchanged
```

Then open `docs/reference/Playground_Quick_Reference_v0.6.md` and spot-check three pages against
the sketches in `examples/reference/` — the test asserts the sketch text is embedded verbatim and
the image exists; only you can judge whether a beginner can read it.

## 2. Commits in reading order

| Commit | Story | Read | Why |
|---|---|---|---|
| `578dba7` | S-027 | `playground/api.py` (`translate`…`degrees`), `sketch.py` (`push/pop/state/_end_draw`, transforms), `state.py` (`StateStack.unwind`), `capabilities.py` (`PlaygroundWarning`), `renderers/cairo2d.py` (`_draw_ops` save/restore), `tests/test_transforms.py`, `Semantic_Contract.md` F2 | The state stack and the one renderer change that could have leaked. Read `_end_draw()` first. |
| `42dc6fb` | S-028 | `playground/paths.py`, `geometry.py` (`Path.is_closed`), `sketch.py` (`begin_shape`…`clip`), `ir.py`, `renderers/cairo2d.py` (`FILL_RULE_WINDING`), `tests/test_paths.py`, contract F3/F4 | Paths as a thin layer over `FillPath`/`StrokePath`/`ClipPath`. Check open-shape and error behaviour against F3. |
| `d885fb7` | S-037 | `renderers/cairo2d.py` (`_text_runs` OrderedDict, `TEXT_RUN_CACHE_SIZE`), `typography.py` (`text_width`), `sketch.py`, `tests/test_text.py`, contract T6 | Closes the "unbounded cache" question from the Sprint 3 guide. |
| `bd79d45` | S-038 | `platform/pygame_platform.py` (`detect_backing_scale`, `open_window`, `present`), `tests/test_hidpi.py` | The unverified code path. Read with the pygame-ce/SDL notes in `stories.md` beside you. |
| `3dcc718` | S-030 | `docs/reference/Playground_Quick_Reference_v0.6.md`, `examples/reference/*.py`, `tools/make_reference_images.py`, `tests/test_reference.py` | The learner-facing document; the only place D-012/D-004/D-003 are restated in learner terms. |
| `2eb318d`, `6cfadc2` | S-059 (spike) | `spikes/RESULTS.md` §8, `spikes/08_browser_pyodide/README.md`, `docs/design/Browser_Mode_Note.md` | Research only; nothing in `playground/` changed. Skim for the S-060/S-062/S-063 implications. |

## 3. What changed — the map

- **Public API** (`api.py`, `__init__.py`, `ADDED_FUNCTIONS` in `tests/test_api_contract.py`):
  16 names. Transforms 8, paths 7, text 1. `saved_state()` returns `AbstractContextManager[None]`;
  `path()` returns a `PathBuilder`; `draw_path`/`clip` accept a `PathBuilder` (or a raw
  `geometry.Path` at the `Sketch` level).
- **Sketch** (`sketch.py`): `push/pop` use the existing `StateStack`; `_end_draw()` runs after
  `draw()` in the loop and at the top of `_render()`; shape-building state (`_shape`) lives on the
  sketch and is dropped with a warning at frame end.
- **Renderer** (`cairo2d.py`): two defensive changes with zero pixel effect (per-frame
  `save/restore`; explicit winding fill rule) and the LRU cache.
- **Platform** (`pygame_platform.py`): new darwin/linux route via `pygame.Window`; Windows, dummy
  driver and `PLAYGROUND_BACKING_SCALE` untouched.
- **Contract:** F2 pinned, F3 new and pinned, old F3 renumbered F4 (still Proposed), T6 pinned.
- **Docs:** Quick Reference v0.6 (markdown), 11 reference sketches + images, Decision Log D-013,
  backlog statuses, `RESULTS.md` §8.

## 4. What to scrutinise

### `sketch.py`
- `_end_draw()`: an open shape is dropped (warning), then `StateStack.unwind()` returns the count
  of open pushes and that many `ir.Restore` ops are appended before the frame renders. Confirm
  it is called on every path a frame can take (the run loop **and** `_render()`), so a headless
  or `max_frames` run gets the same safety as a windowed one.
- `pop()` with nothing pushed: warns and is ignored, never raises. `scale(0)`: `ValueError` at
  the call site. Decide whether you want those two asymmetric (one soft, one hard); the argument
  is that `scale(0)` is a maths error a learner needs to see, a stray `pop()` is a typo.
- Rotation direction: `rotate(90)` maps +x to +y — clockwise on a y-down screen, as p5.
  `test_transforms.py` pins it; the contract F1/F2 wording should agree with what you expect
  learners to be told.
- `end_shape(close=False)` and `draw_path`: `FillPath` is emitted **only when the path is
  closed** and a fill is set; `StrokePath` uses the current stroke. `clip()` emits `ClipPath` and
  is lifted only by `pop()` — a `clip()` outside any `push()` therefore lasts until frame end. Is
  that the semantic you want, or should `clip()` require an enclosing `push`?
- `text_width()` goes to `typography.text_width` → `FontResource.shape(...).advance`, which is
  the same sum of x-advances `TextRun.outline_ops` uses for pen movement, so T6's "exactly the
  distance `text()` moves its pen" is by construction, not by coincidence.

### `renderers/cairo2d.py`
- `draw()` → `ctx.save()` / `_draw_ops()` / `ctx.restore()`: the reason is that the window
  context persists across frames, so a top-level `Concat` would otherwise accumulate. Check
  `_draw_ops` still tracks `Save`/`Restore` depth as before (Sprint 3 guide) — two layers of
  defence, one learner-side, one renderer-side.
- `_text_runs`: `OrderedDict`; hit → `move_to_end`; miss → insert then `popitem(last=False)`
  while over 256. `attach()` clears it, so the bound is per window. A title drawn every frame
  survives a changing counter (LRU, not FIFO) — `test_text.py` has the ordering test.
- `set_fill_rule(FILL_RULE_WINDING)` in `context_for`: Cairo's default, now stated. The eleven
  old goldens prove it changed nothing.

### `playground/paths.py`
- `PathBuilder` is a chainable wrapper over the immutable `geometry.Path`; every method returns
  `self`; `quad_to` is stored as a cubic (F3 says so). `.geometry` exposes the `Path`. Ask whether
  learners should ever see `.geometry` or whether it should be underscored.

### `platform/pygame_platform.py`
- The darwin/linux branch: `pygame.Window(title, (w, h), allow_high_dpi=True)` at **logical**
  size; `get_surface()` is drawable-sized (SDL ≥ 2.26); scale = drawable ÷ window size. With no
  window yet, a hidden 64×64 probe window is opened and destroyed. Mouse coordinates are **not**
  divided on this route (SDL reports screen units there) — the opposite of the Windows route.
  This is the one claim in the sprint that no test can confirm; the six tests fake
  `pygame.Window` and patch `sys.platform`. Read it as "plausible, sourced from pygame-ce 2.5.8
  and SDL 2.32 source", not "works".
- Probe failure → 1.0 (runs, not crisp). Confirm nothing on that path can raise into a learner's
  first sketch on a Mac.

### `docs/reference/Playground_Quick_Reference_v0.6.md` and `examples/reference/`
- The reference sketches call `p.run()` like real learner code; `tools/make_reference_images.py`
  runs them headless with `max_frames=30` and captures `p.save()` of the last frame. Check the
  transforms and paths pages say what the contract says (F2 reset rule, F3 fill rule, open shapes
  stroked only).
- Colour appendix is the v0.5 PDF pages 8–19 by reference, not copied.

### Tests
- `test_transforms.py` (19): rotation direction, order of operations, nesting, unwind warning,
  stray pop, `scale(0)`, `background` ignores transform, sample golden/snapshot.
- `test_paths.py` (23): pentagram centre filled (non-zero), open polyline not filled, `quad_to`
  as cubic, clip lifted by pop, errors outside `begin_shape`, headless PDF export of the sample.
- `test_text.py` (+6): 1 000-frame cache run, LRU order, size scaling, kerning, transform
  independence, centred-text pixel check.
- `test_hidpi.py` (+11 cases across 6 tests): all simulated.
- `test_reference.py` (25): `__all__` coverage, verbatim embedding, headless render, image size.
- `test_api_contract.py`: `ADDED_FUNCTIONS` carries a signature string per name; `__all__` must
  equal v0.5 ∪ added ∪ live values exactly.

## 5. Things I would flag

1. **D-013 — decided: `with p.saved_state():`** (renamed from `state()`). Previously: your call; either
   alternative is a one-line alias plus the F2 row and one reference page. Decide before the
   reference is handed to a class, because the name will be on the page.
2. **Contract F2 overstates the reset rule** (verifier finding). It says "a transform or style set
   inside `draw()` never carries into the next frame"; a probe shows an unpushed `p.fill('blue')`
   inside `draw()` persists (white, blue, blue) — as p5 does and as S3 says. Only open pushes and
   the transform reset. Suggested wording: "the stack and the transform reset at the start of every
   `draw()`; a style set without a `push()` persists wherever it is made (S3)". Not fixed in this
   sprint's commits; fix it in the same change that records D-013.
3. **Contract "Test coverage" paragraph is stale**: says every Pinned row is tested in
   `test_semantics.py` or `test_api_contract.py`; F2/F3/T6 live in `test_transforms.py`,
   `test_paths.py`, `test_text.py`. One-paragraph doc fix.
4. **S-037's acceptance line says 10 000 frames through the run loop; the test does 1 000 frames
   against the renderer directly.** Verified independently to 10 000 with the real headless loop
   (peak exactly 256, title survives), so behaviour is right; either lift the test or soften the
   acceptance line so the two agree.
5. **S-038 is unverified on the hardware it targets.** Nothing in the repo claims otherwise, but
   it is new code in the platform layer that has only ever run under fakes. Needs a Retina Mac or a
   Wayland desktop: run `examples/session1/01_first_sketch.py`, expect a 640×400-point window,
   `backing_scale == 2.0`, crisp shapes, `08_mouse.py` tracking the cursor. Linux X11 → 1.0 is
   expected, not a bug.
6. **S-039 is blocked, so CI has never run.** Every count here is Windows 11 / Python 3.14.7.
   Snapshots must pass on Linux/macOS; goldens are Windows-only by policy. Nothing can confirm
   that until there is a remote — the one thing only you can provide.
7. **`clip()` outside a `push()` lasts to frame end** (see §4 `sketch.py`). Legal per F3 as
   written; ask yourself whether the reference should tell learners to always wrap it.
8. **`text_width` shapes on every call** and does not share the renderer's LRU. Cheap (uharfbuzz)
   and correct; a follow-up if a learner calls it many times per frame.
9. **Sixteen names in one sprint.** `path` vs `draw_path`, `state` vs `push`, `vertex` vs
   `curve_vertex` are the pairs a beginner is most likely to confuse. The Quick Reference is where
   that is either solved or not.
10. **No PDF of the reference.** Backlog said "PDF/MD"; markdown delivered, images generated. If a
    printable handout is needed for the class, that is a small tooling story.

## 6. Open decisions

**D-013 — name of the state-stack context manager.** Context, options (A `state()` implemented,
B `push()` returning a context manager, C both), trade-offs, recommendation (A) and reasoning in
`sprints/sprint-04/stories.md` § D-013; `pending` row in `docs/design/Decision_Log.md` § Open.
**Decided 25 Sept 2026: `with p.saved_state():`.** When decided, set the outcome and date in the log in the
same change that applies it (alias in `api.py` if B/C; F2 row; reference page).

No other decision was raised. D-014 (`rect_mode`-style switches) was anticipated and not needed:
row F4 stays Proposed as "not offered".

## 7. Sign-off checklist

- [ ] 275 tests pass; `git diff --stat 3e4eccd..HEAD -- tests/golden tests/snapshots` lists only the four new `13_transforms.*` / `14_paths.*` files
- [ ] `13_transforms.py` and `14_paths.py` look right in a real window (nothing leaks frame to frame; star filled through the centre; open shape stroked only)
- [ ] `tools/make_reference_images.py` reproduces `docs/reference/images/*` unchanged; three reference pages read well to you
- [ ] `_end_draw()` runs on every frame path; the warn-vs-raise split (stray `pop()` soft, `scale(0)` hard) is acceptable
- [ ] `clip()` outside `push()` semantics acceptable, or a follow-up story raised
- [ ] Contract F2 wording corrected and the "Test coverage" paragraph updated (or a follow-up story raised)
- [ ] S-037 test lifted to 10 000 frames through the loop, or the acceptance line softened
- [ ] S-038 accepted as "code path only, unverified" with a named owner for hardware verification
- [ ] S-039 carried over to the backlog as blocked; a remote created or the block acknowledged
- [ ] D-013 decided (A / B / C), or explicitly deferred to Sprint 5
