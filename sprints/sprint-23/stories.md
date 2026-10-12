# Sprint 23 — release 0.1

**Dates:** planned 12 October 2026. **Goal:** publish funground 0.1.0 on PyPI with everything built so far
(D-091): the desktop library, sound, studios and Play from `main`; the web runner and editor, print posters,
CMYK and the shorter style from `release-0.2-web`; and the documentation for AI assistants.

**Decisions:** D-091 = b (0.1 contains the 0.2 scope and S-129; today's `main` is pre-0.1; untested points are
named in the release notes). Process for the release itself: `docs/developer/Releasing.md`.

| Story | Value | Status |
|---|---|---|
| S-177 | One line of work again: `release-0.2-web` merged into `main` by pull request (maintainer's OK); `Releasing.md`, the website's runtime path (`runtime/0.2-dev/`) and the extension's runtime URL renamed for 0.1 where a version is meant | planned |
| S-178 | CI green on all 12 cells: find why `main`'s runs hang until the 6-hour limit, and why Windows on GitHub draws some gallery and example goldens differently from the golden machine; fix both properly | planned |
| S-129 | Documentation for AI assistants and agents (carried from Sprint 16; now in 0.1): `llms.txt`, `llms-full.txt` (generated), both in the repository and the package, `AGENTS.md`; covering both styles (`f.` and `from funground import *`) and the web runner | planned |
| S-179 | Every option word explained in the API reference (D-092): word -> meaning tables printed under each function; a test that none is unexplained | done: 12 option sets (blend modes, caps, joins, alignment, styles, filters, cursors, keys, waves, anchors); DrawBot names in `blend_mode` and chapter 15 |
| S-180 | A script that never shows its drawing says so: the Play page and VS Code show it anyway; the desktop prints a one-line hint | planned |
| S-181 | Leading-based line fitting in `text_box()` (D-093), as DrawBot and InDesign | planned |
| S-073 | Release 0.1 (carried): version `0.1.0` in `pyproject.toml` and `funground.__version__`; changelog "Unreleased" becomes `0.1.0 — <date>` with the 0.2-branch work folded in; release notes with a "Not yet tested" section; README install line and absolute image links; Quick Reference checked against the code; TestPyPI dry run on a fresh dev version; tag `v0.1.0` after the maintainer's go-ahead | planned |

**The maintainer:** the PyPI pending publisher and the `pypi` GitHub environment (TestPyPI is done); the checks
they can do from `sprints/sprint-11/release_checklist.md`; sign-offs of the open sprints (10, 11, 16, 17, 19,
20, 21, 22; reviews of 20, 21 and 22 to be written); the go-ahead; Approve on the `pypi` environment.

Acceptance for the sprint: 0.1.0 installs with `pip install funground` on Windows, macOS and Linux (the release
workflow's smoke test), the release notes list what was not tested by hand, and `main` is the only release line.
