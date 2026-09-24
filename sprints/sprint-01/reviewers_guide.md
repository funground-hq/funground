# Sprint 1 — Reviewer's guide

For the maintainer reviewing Sprint 1 before closing it. Budget: about an hour. The sprint's
claim is narrow and checkable: **the package was restructured and no learner-visible behaviour
changed.** Everything below is organised to let you confirm or refute that claim.

Diff under review: `git diff 34bc581..a80d07f` — 18 code/test files, +1674 / −395 lines
(the 675-line generated colour table accounts for most of the additions).

## 1. Verify the claim first (10 minutes)

```powershell
.venv\Scripts\python -m pytest            # expect: 115 passed
git status --short                        # expect: empty (goldens untouched)
git diff --stat 18a5d21..HEAD -- tests/golden   # expect: no output - not one golden changed since Sprint 0
```

Then run one learner sketch for real, in a window, exactly as a student would:

```powershell
.venv\Scripts\python examples\session1\06_animation.py     # Escape closes it
```

If those four things hold, the rest of the review is about *how* the code is shaped, not
whether it works.

## 2. Read the commits in order (they are the story list)

| Commit | Story | Read | Why in this order |
|---|---|---|---|
| `27927fe` | S-016 | `playground/color.py`, `tests/test_color.py` | Leaf module, no dependencies. Warm-up. |
| `b0b4832` | S-015 | `playground/state.py`, `tests/test_state.py` | Leaf module. 46 lines. |
| `fa5c66e` | S-014 | `platform/base.py` → `platform/pygame_platform.py` → `renderers/__init__.py` → `renderers/pygame2d.py` | The two provider boundaries. Read the protocol before its implementation. |
| `503264f` | S-013 | `sketch.py` → `api.py` → `__init__.py` → `tests/conftest.py` | The centre of the sprint; `_core.py` deleted here. Diff `sketch.py` against `src_v0.5/playground/_core.py` side by side. |
| `5a5ca04` | S-017 | `tests/test_boundaries.py` | The rule that keeps S-014 honest. |
| `0f750fe` | S-031 | `spikes/06_text_outlines/spike.py`, the PNGs, `spikes/RESULTS.md` §6 | Not production code; evidence for D-009. |

`git show <commit>` on each; `git diff 34bc581..HEAD -- playground` for the whole picture.

## 3. Map of the package after the sprint

```
playground/
  __init__.py      84   public names, __all__, __getattr__ for live values     ← no backend import
  api.py          141   one public function per v0.5 name → active Sketch      ← no backend import
  sketch.py       232   Sketch: lifecycle, live values, state, RNG, helpers   ← no backend import
  state.py         46   GraphicsState (frozen dataclass), StateStack
  color.py         87   Color (frozen), Color.parse()
  _colornames.py  675   generated: 665 names from pygame-ce colordict
  platform/
    base.py        50   Platform protocol, InputState, KEY_NAMES
    pygame_platform.py 92   the only pygame window/event/input/clock code
  renderers/
    __init__.py    25   Renderer protocol (per-primitive; replaced by render(ops) in Sprint 2)
    pygame2d.py    69   the only pygame.draw code — v0.5's calls, verbatim
```

Call path for a learner line: `p.circle(x, y, d)` → `api.circle` → `api.active_sketch().circle`
→ `Sketch._require_window()` → `PygameRenderer.circle(x, y, d, sketch.style)`.

Live value: `p.width` → `playground.__getattr__("width")` → `api.live_value` → `active_sketch().width`.

## 4. What to scrutinise, file by file

### `sketch.py` (the important one)
- **`run_namespace`** vs v0.5 `_core.run` (`src_v0.5/playground/_core.py:196–244`). The loop order
  must be identical: poll → sample mouse → `draw()` → present → `frame_count += 1` → max_frames
  capture → `delta_time = tick()`. Then `finally`: running=False, platform close, window forgotten.
  *Question to ask:* is there any path where v0.5 called pygame and this doesn't, or vice versa?
- **`text()`** colour fallback: explicit → fill → stroke → white. v0.5 line 166.
- **`key_down()`** now validates names in Playground before the platform maps them. v0.5 raised the
  same `ValueError` message from `_key_code`. Check `tests/test_semantics.py::test_unknown_key_name_is_an_error`.
- **Defaults** on `__init__`: 640×480, 60 fps, title `"playground"`, style white/black/1/20.
- `constrain`/`distance` are `@staticmethod` — deliberate: they need no sketch.
- The lazy imports of `PygamePlatform`/`PygameRenderer` inside `__init__` keep `sketch.py` free of
  backend imports (the lint checks the module top level and all `import` statements — including
  these lazy ones — so note they import from `.platform`/`.renderers`, not from `pygame`).

### `api.py`
- Every signature must equal the v0.5 one — `tests/test_api_contract.py` enforces the strings, but
  read them anyway: docstrings were carried over from `_core.py`.
- `run()` still discovers `setup`/`draw` by inspecting the caller's frame (`f_back.f_globals`). Same
  mechanism as v0.5; if you dislike frame inspection, that is a pre-existing design, not this sprint's.
- `use_sketch()` / `active_sketch()` are maintainer-facing (tests, future multi-sketch). They are not
  in `__all__`.

### `renderers/pygame2d.py`
- This is v0.5's drawing code moved, not rewritten. Compare each method with `_core.py:89–168`.
  The only additions: `Color.rgba` instead of the raw learner value, and a font cache keyed by size
  (`_fonts`) instead of `pygame.font.Font(None, size)` per call. *Question:* is caching a `Font`
  object across frames safe? (It is — fonts are immutable — but confirm you're happy with it.)

### `platform/pygame_platform.py`
- `open_window` calls `pygame.display.init()` and `pygame.font.init()` itself so `p.size()` works
  before `p.run()` (v0.5 relied on the test/caller having called `pygame.init()`).
- `close()` sets `_screen = None` — this is the Sprint 0 second-run fix, now living where it belongs.
- `key_code()` is v0.5's `_key_code`, unchanged.

### `color.py`
- `parse()` accepts: `Color`, str (name, `#RRGGBB[AA]`, `0xRRGGBB[AA]`), 3/4-tuple or list of ints
  (floats only if integral). Rejects bools, out-of-range, wrong length — with a message containing the
  word "colour". *Question:* v0.5 accepted anything pygame accepts, including `pygame.Color` objects
  and ints. Contract S1 documents only the forms above. Is dropping the undocumented forms acceptable?
  (My view: yes — none appear in the Quick Reference or the sample suite.)
- `_colornames.py` is generated; `tests/test_color.py::test_named_table_matches_pygame_ce` proves it
  equals pygame-ce's table today. When pygame-ce changes its table, that test tells us.

### `state.py`
- `GraphicsState` is frozen; every style call replaces it (`StateStack.update`). This is what makes
  `save()`/`restore()` and, later, `with p.state():` trivial. Check `restore()` without `save()` raises.

### Tests
- `conftest.py`: the autouse fixture gives every test a fresh `Sketch` via `api.use_sketch`, seeds
  the RNG, and quits pygame afterwards. `run_sketch` executes learner files **unchanged** by swapping
  `playground.run` for a wrapper that forwards the sketch's own globals. Read this once; it is the
  mechanism the whole golden layer rests on.
- `test_semantics.py` changed only in how it reaches internals (`sketch` fixture instead of
  `_core._style`); the assertions are identical. `git diff 34bc581..HEAD -- tests/test_semantics.py`
  should show no changed `assert` lines except the defaults test.
- `test_boundaries.py`: an AST walk. Allowed dirs are `platform/` and `renderers/`. Note it checks
  *imports*, not string mentions — the `__init__.py` docstring says "pygame-ce" and that is fine.

## 5. Things I would flag if I were reviewing this

1. **`Renderer` protocol is temporary.** Per-primitive methods exist only so Sprint 1 could land
   without the IR. Sprint 2 replaces it with `render(ops)`. Don't invest in its shape.
2. **`Sketch` still has a 1:1 relationship with a window** via `PygamePlatform`; two sketches can
   hold state independently (tested) but cannot both open windows. Off-screen canvases are Sprint 3.
3. **Frame inspection in `api.run()`** is inherited from v0.5. It is the reason `conftest.run_sketch`
   needs its wrapper trick. A future `p.run(setup, draw)` overload would remove it; not in scope.
4. **`Color.parse` on every style call** is a tiny cost per call (dict lookup / small parse). Not
   measurable at teaching scale; noted so nobody "optimises" it into a cache prematurely.
5. **`__version__` is `0.6.0.dev0`** while the Quick Reference says `0.5.0`. Intentional; the QR is
   updated in S-030.

## 6. The retrospective item to weigh

The sprint review records a commit-staging mistake: a `git rm` of `_core.py` was staged before the
first story commit and got swallowed into S-016's commit. I noticed it via `git show --stat`, reset
the five unshared local commits, and redid them with per-group `git add -A -- <paths>`. Nothing had
been pushed (there is no remote). The proposed rule is in `review.md` § Retrospective. You may want
to decide whether history rewrites of *local, unshared* commits are acceptable practice for this
repo, and record that in `PROCESS.md`.

## 7. Open decision you will be asked about

**D-009 — which font to bundle** (DejaVu Sans recommended). Full context/options/trade-offs in
`docs/design/Decision_Log.md` § Open. It blocks only S-029 in Sprint 4.

## 8. Sign-off checklist

- [ ] 115 tests pass locally; goldens unchanged since `18a5d21`
- [ ] One sketch run in a real window behaves as before
- [ ] `sketch.py::run_namespace` loop order matches v0.5 `_core.run`
- [ ] No backend import outside `platform/` and `renderers/` (lint passes; spot-check `sketch.py`, `api.py`)
- [ ] Public signatures unchanged (`test_api_contract.py` passes; `api.py` read)
- [ ] Dropping undocumented colour forms (§4, `color.py`) is acceptable
- [ ] Retrospective rule on local history rewrites decided
- [ ] D-009 decided, or explicitly deferred to Sprint 4
