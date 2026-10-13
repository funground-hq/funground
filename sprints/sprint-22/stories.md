# Sprint 22 — less verbose sketches

**Dates:** started 12 October 2026, on `release-0.2-web` (ships with 0.2). Epic **E-23**.

**Goal:** a learner may leave out `f.` (D-088): `from funground import *` is safe, the values that change stay
current, and a forgotten `run()` no longer leaves a blank run from a terminal, VS Code or the website.

**Decisions:** D-088 accepted 12 October 2026 (proposal 1 as a second style, proposal 3 as a safety net,
proposal 2 dropped; `Sketch_Style_Note.md`). D-090 (constants) is S-174, planned next.

| Story | Value | Status |
|---|---|---|
| S-176 | The global style and `run()` as a safety net (D-088) | done: `__all__` less four names, which are `set_pixel`, `apply_filter`, `random_number` and `stop` there (R19), live values refreshed (`funground/global_style.py`), the hiding-variable note, auto-start at exit and in `Session.start` (R13), guide chapter 2 "Writing without `f.`", errors page, chapter 14 |

Acceptance for the sprint: the full suite green; contract rows R13 and R19 pinned; every existing
`import funground as f` sketch unchanged.
