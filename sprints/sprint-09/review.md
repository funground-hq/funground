# Sprint 9 review — Phase 3c: path depth

**Dates:** 1 October 2026; closed by the maintainer 1 October 2026
**Goal:** DrawBot's path tools on funground's path builder: booleans, overlap removal, stroke
outlines, measuring and testing paths, moving them, and letters as paths.

## Outcome

All three stories are done; nothing is carried over.

**Checkpoint met.** No golden, snapshot or gallery image that existed before the sprint changed:

```
git diff -M --diff-filter=MD bd35897..HEAD -- tests/golden tests/snapshots docs/gallery/images docs/reference/images
```

That diff is empty.

**New dependency:** `skia-pathops` (D-037, ADR-005). It installs and passes on all 12 CI cells. One
module imports it, enforced by the boundary test.

**Public surface:**
- one new module function, `text_path` (145 → 146 names);
- the path builder gains 17 methods;
- no v0.5 API change.

| Story | Result | Built by |
|---|---|---|
| S-086 Shapes and booleans | builder helpers `rect`, `ellipse`, `circle`, `polygon`; `union`, `intersection`, `difference`, `xor`; operators `\|`, `&`, `-`, `^`, and DrawBot's `%` (added in review); `remove_overlap`; exact curves | Sonnet sub-agent |
| S-087 Outlines, queries, transforms | `expand_stroke` (caps, joins, miter, dashes), tight `bounds`, non-zero `contains`, `translate`, `scale`, `rotate`, `copy` | Sonnet sub-agent |
| S-088 Text as a path | `f.text_path()` uses the same layout code as `f.text`, so the two cannot drift | Sonnet sub-agent |

## Test results

```
1286 passed   (Sprint 8 close: 1166)
CI: 12/12 green on every story commit checked so far
```

## Findings

1. **Checking DrawBot's names against its source paid off.** Builders read DrawBot's
   `baseContext.py` and found DrawBot writes difference as `%`, not `-`. Review added `%`, so
   DrawBot path code ports unchanged.
2. **Skia's output needs care at the edges:**
   - Skia fills open sub-paths in booleans; we drop them first, as F11 says.
   - Round caps come back as conic curves, which we approximate closely.
   - Quadratic segments are raised to cubics.

   All of it is pinned in F11 and F12.
3. **One exactness trade-off was accepted (D-039).** A word drawn from `text_path` differs from
   `text` by a few anti-aliasing levels where letters touch, because it is one fill instead of one
   per letter. The shape is identical.
4. **A gap worth your decision, not taken:**
   - p5's `rect(x, y, w, h, r)` draws rounded corners; funground's `rect` cannot.
   - The text-path example had to build a rounded panel from rectangles and circles.
   - Adding the optional corner radius would change `rect`'s frozen v0.5 signature, which D-034
     keeps with you.
   - Listed under Decisions as a question for the next sprint.

## Decisions

| ID | Outcome | By |
|---|---|---|
| D-037 | skia-pathops in the base install (ADR-005) | maintainer |
| D-038 | Path API: DrawBot `BezierPath` names on `f.path()` | Claude, under D-034 |
| D-039 | Accept the touching-letters anti-aliasing difference in `text_path` | Claude, under D-034 |
| D-040 | Rounded corners for `rect`/`square`, as p5 (approved v0.5 signature change) | maintainer |

## Sign-off

**Closed 1 October 2026** by the maintainer ("go ahead"). D-038 and D-039 stand. Rounded corners approved as D-040, built in Sprint 10.

## Retrospective

- **Went well:**
  - Three stories went from contract to commit in one day.
  - Every DrawBot name was checked against DrawBot's source, not memory.
- **Went badly:** the first operator table claimed DrawBot used `-`. Our check caught it, but only
  because a builder looked.
- **Change for Sprint 10:** every story that cites another tool's API names cites where they were
  checked.

## AI-USAGE log entry

Added to `AI-USAGE.md` under Sprint 9.
