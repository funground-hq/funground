# Sprint 22 review — less verbose sketches (E-23)

**Dates:** 12 October 2026, on `release-0.2-web` (merged to `main` with S-177; released in 0.1.0a1).
**Not yet signed off.**

## Outcome

Goal met: a learner may leave out `f.`; `from funground import *` is safe, live values stay current, and a
forgotten `run()` no longer leaves a blank run.

| Story | Result | Commit |
|---|---|---|
| S-176 The global style and `run()` as a safety net (D-088) | the star import gives every public name except `set`, `filter`, `exit` and `random`, which are `set_pixel`, `apply_filter`, `random_number` and `stop` there (R19); live values refreshed in the sketch's globals (`funground/global_style.py`); a variable that hides a funground function gets a sentence in the error; a file with `draw()` and no `run()` starts when it ends (R13: terminal, VS Code, web Session; not IDLE, Thonny, notebooks or `python -m`); guide chapter 2 "Writing without `f.`", errors page, chapter 14, example `basics-04_without_f` | `fee27d1` |

**Tests:** the full suite was green before the commit; the count was not written down. Every existing
`import funground as f` sketch unchanged (the gallery goldens did not move).

## Decisions

- **D-088 accepted** (12 Oct): proposal 1 as a second style, proposal 3 as a safety net, proposal 2 dropped
  (`docs/design/Sketch_Style_Note.md`).
- **D-090** (constants instead of quoted option words) accepted; built as S-174, not in this sprint.

## Findings that change later work

1. **New public names reach the browser runner's on-demand list too.** `apply_filter` was new here, and the web
   runner did not know it needed pygame-ce: the first user-reported bug (14 Oct, `basics-04_without_f` in Play).
   Fixed in funground-web PR #7. A new public name that wraps a sketch method under another name needs the
   checker run.
2. `__all__` is now the star list, not the public list; tools must read `funground._PUBLIC_NAMES`.

## Built by

The main session (not recorded at the time).

## Retrospective

- A one-story sprint was the right size for a change to how every sketch can look; the spike before it
  (S-175) made the decision quick.
- The new example used a function whose browser needs were not checked against the runner. A gallery example
  should be run in Play before its story is done.
