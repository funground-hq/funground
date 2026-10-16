# Sprint 27 review — Play: fast and yours (E-35)

**Dates:** 15 to 16 October 2026. Work in `funground-hq.github.io` (site PRs #17 to #22), `funground-run.github.io`
(preview PRs #5 to #9), `funground-web` (PRs #9, #10) and funground (PRs #8, #9). Each story shipped when it was
checked. **Awaiting sign-off.**

## Outcome

Goal partly met. A learner now sees the example's picture while Python loads, gets a download line for every file
`f.save()` writes, can save the current picture, and keeps a list of their own sketches in the browser. The two
speed stories did not land: keeping the runtime on the device (S-210) was rolled back, and fonts on demand (S-211)
works but has no effect on GitHub Pages. Both go back to the backlog.

| Story | Result |
|---|---|
| S-209 The picture first | done (site PR #17, live): the example's gallery picture with the loading status over it, only while the code is the example's own |
| S-210 Runtime on the device | **carried over.** Built and tested locally (preview PR #6, site PR #22): a repeat visit took 5 to 6 s against about 14 s. On GitHub Pages the worker first never installed (`Cache.addAll` failed with "Entry already exists"); once fixed (preview PR #7) a first visit hung while Python loaded, which did not happen locally, even with compression like GitHub Pages'. Reverted (#8), then a pass-through worker (#9) that caches nothing and deletes the caches of the earlier one. The editor half (the forget button, the "new funground is ready" line) is live and harmless |
| S-211 Fonts on demand | **carried over.** Built (funground-web PRs #9, #10): fonts are lazy files with a fail-safe. GitHub Pages compresses fonts in transit, so the size check fails and Play loads them at start-up as before. Nothing is broken. Option B (a private funground hook that fetches a font when it is first opened) awaits the maintainer |
| S-212 Saving from Play | done (funground-web PR #9, preview PR #5, site PR #19, live): "Saved poster.png - Download" lines, replaced when saved again, no automatic downloads; Save picture downloads the frame; Pillow loads on demand for GIF saves |
| S-213 My sketches | done (site PR #20, live): New, Open .py, Rename, Duplicate, Download .py, Delete with Undo, Keep as my sketch; one localStorage key; a line if storage fails |

Also done in the sprint, from the maintainer's use of Play:

- A path's missing method says what to write instead (funground PR #8), then `square`, `triangle` and `quad` on a
  path, as on the canvas (PR #9; contract F11).
- Gallery motion-02, *Sparks that fade*: a class and a list of objects, new ones each frame, old ones fading (PR #9).
- Play's Alt key no longer moves focus to the browser's menu (the maintainer confirmed it locally).

**Tests:** funground's full suite 4257 passed, 1 skipped (16 Oct). `test_editor.mjs` gained checks for S-209, S-212,
S-213 and the S-210 editor half; its test server now compresses like GitHub Pages (uncommitted, kept for the S-210
fix). The live site was checked after each deploy with plain requests; the last first visit in a browser after the
pass-through worker was not checked (the machine ran short of memory).

## Measurements

| What | Result | How |
|---|---|---|
| Repeat visit with the runtime cached (S-210) | 5 to 6 s, against about 14 s without; the 3 s budget is not met, Python's start dominates | local build, headless Chrome |
| Fonts on demand on GitHub Pages (S-211) | no effect: fonts arrive compressed, the size check fails, eager loading | `curl -I` on the live files |

## Decisions

- Maintainer: Play work ships as built, not held for a release (15 Oct); path shapes `square`, `triangle`, `quad`
  (15 Oct); D-089 camera, all four as recommended (16 Oct).
- Decided by Claude, for review: roll S-210 back rather than debug it live (a hung first visit is worse than a slow
  one); keep S-211 as built, with its fail-safe, instead of reverting it.

## Findings that change later work

1. **A service worker cannot be judged on the local server alone.** GitHub Pages differs in compression, caching
   headers and timing; the local server now compresses, and the next attempt needs logging from the live preview
   before it is switched on for everyone.
2. **GitHub Pages compresses fonts and wheels** (as `application/octet-stream`), so anything that relies on a file's
   size from a HEAD request is wrong there. Recorded in the S-211 row.
3. **The maintainer's own use of Play finds the next work**: the path error, the path shapes and the sparks example all
   came from it. Play usability is now the priority (maintainer, 15 Oct).
4. **Memory on this machine limits browser checks.** With about 240 MB free, a headless Chrome running Pyodide is
   killed. Browser checks run one at a time, when memory allows.

## Built by subagents

None this sprint; the main session built and committed everything.

## Retrospective

Shipping each story when checked worked for the editor stories. It did not suit S-210, whose risk was only visible on
the live host: it should have gone out behind a switch, first for a test page only.
