# Sprint 1 review — Phase 1a: Sketch, platform, state

**Date:** 24 September 2026 (single session)
**Goal:** explicit `Sketch`, every pygame call behind `PygamePlatform`, `GraphicsState` and `Color` —
with zero learner-visible change.

## Outcome

All seven stories done. **Checkpoint 1 of Phase 1 (D-007) met: all 11 goldens byte-identical.**
One decision raised and left open for the maintainer (D-009, font file).

| Story | Result | Commit |
|---|---|---|
| S-012 Decide DECISION rows | All accepted as recommended before sprint start (D-001…D-008) | 34bc581 |
| S-016 `Color` + bundled name table | 665 names from pygame-ce colordict; every Quick Reference colour form parses | 27927fe |
| S-015 `GraphicsState` + `StateStack` | Immutable state, save/restore | b0b4832 |
| S-014 `Platform`/`Renderer` protocols + pygame implementations | `PygamePlatform`, `PygameRenderer` (pixel-identical `pygame.draw`) | fa5c66e |
| S-013 `Sketch` replaces `_core` globals | `api.py` facade over the active sketch; live values via `__getattr__`; two sketches per process; `_core.py` deleted | 503264f |
| S-017 Provider-boundary lint | AST test: backend imports only under `platform/`, `renderers/` | 5a5ca04 |
| S-031 Spike 06 deterministic text | Outlines route validated on 4 fonts; D-009 raised | this commit |

## Test results

```
115 passed in 19.7 s
  test_api_contract 7 · test_semantics 42 · test_examples_golden 24 (11 goldens, exact)
  test_color 27 · test_state 4 · test_sketch 5 · test_boundaries 2
```

Windows 11, Python 3.14.7, pygame-ce 2.5.8. Goldens unchanged since Sprint 0.

## Package layout after Sprint 1

```
playground/
  __init__.py     public names + __getattr__ live values      (no backend imports)
  api.py          learner-facing functions → active Sketch    (no backend imports)
  sketch.py       lifecycle, live values, state, RNG, helpers (no backend imports)
  state.py        GraphicsState, StateStack
  color.py        Color, Color.parse; _colornames.py (generated)
  platform/       base.py (Platform protocol, InputState, KEY_NAMES), pygame_platform.py
  renderers/      __init__.py (Renderer protocol, per-primitive), pygame2d.py
```

## Findings

1. **The refactor was mechanical and safe.** Every v0.5 behaviour, including rounding, inside
   strokes, alpha dropping and the text-colour fallback, moved into `PygameRenderer` unchanged,
   which is why the goldens did not move. Sprint 2 replaces the per-primitive `Renderer` protocol
   with `render(ops)`; nothing else has to change.
2. **Key names are now Playground's.** `Sketch.key_down` validates names/characters before the
   platform maps them; pygame key ints still pass through (contract I2, unchanged).
3. **Text as outlines works** (Spike 06): 0.44–0.48 ms per line with the glyph cache, byte-identical
   across runs, HarfBuzz gives kerning, ligatures and Devanagari conjuncts for free. fontTools +
   uharfbuzz + one font ≈ 5 MB. Full numbers in `spikes/RESULTS.md` §6.
4. **A commit mistake, corrected:** a staged deletion was swallowed by the first story commit; the
   five local commits were redone with correct staging before anything was shared. Process note
   added below.

## Decisions

- Taken before the sprint: D-001…D-008 (see `Decision_Log.md`).
- **Pending: D-009 — which font to bundle.** Presented in the decision log with context, options,
  trade-offs and recommendation (DejaVu Sans). Blocks only S-029 (Sprint 4).

## Retrospective

- *Went well:* stories were planned before the work; each landed as one commit with a byte-identical
  golden run in between.
- *Went badly:* commit staging error (finding 4). Rule: after `git rm`, stage and commit that
  group immediately or use `git add -A -- <paths>` per group; check `git show --stat` before moving on.
- *Carry-over:* none. Sprint 2 (IR + `LegacyPygameRenderer`) can start; its story set is in the backlog.
