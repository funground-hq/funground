# Sprint 28 review — The camera (E-33)

**Dates:** 16 October 2026. Work in funground (PR #10), `funground-web` (PR #11) and `funground-hq.github.io` (PR #23).
All three merged and live the same day. **Awaiting sign-off.**

## Outcome

Goal met. A learner can see themselves in a sketch: draw the camera's picture, read its pixels, take a photo and record
a short clip, on a Windows or Linux computer and in Play. The maintainer recorded a clip with a real camera on the live
site (16 Oct): "recording worked".

| Story | Result |
|---|---|
| S-172 Camera | done. `f.camera()`, `f.cameras()`; `start`, `stop`, `is_ready`, `picture`, `save`, `record`; clips saved as GIF (MP4 with the `video` extra on a computer). One frame per `draw()`, scaled to the asked size, mirrored by default. Headless: never ready; Mac desktop: a message to use the website (D-089). In the browser the page opens the camera (`runner/camera.js`) and sends a frame before each step; a refusal, or VS Code's panel, gives one line. Play's preview may use the camera. Contract rows I4, I5; guide section; Quick Reference; gallery images-06 (mirror of dots) and images-07 (photo booth), each with a fallback photo |

**Tests:** funground's full suite 4332 passed, 1 skipped (45 camera tests with a fake device; the real camera is never
opened by a test). `funground-web` `tools/test_camera.py`: Chrome's fake camera reaches the sketch, a 0.5 s clip of 30
frames saves as a GIF, the camera closes after Stop; a refusal and a host refusal each give one line. `test_sound.py`
and `test_runner.py` still pass (images-01 differs as recorded in D-101). Site `test_editor.mjs` check 55: the fake
camera shows in Play's preview after 3.4 s.

## Measurements

| What | Result | How |
|---|---|---|
| First camera frame in Play | 3.4 s after Run (fake camera, local) | check 55 |
| A 3 s clip at 400 x 300, 15 fps | about 22 MB in memory | 45 frames x 480 KB |

## Decisions

- Maintainer: D-089 as recommended (16 Oct).
- Decided by Claude, for review (pinned in I4/I5): frames are always the asked size; the frame is taken once before each
  `draw()`; `clip.done` is also `True` once `stop()` ends a recording, so a sketch waiting on it saves; `record()`
  before `start()` is an error; `.jpg` photos need Pillow; one camera per sketch in the browser; `cam.stop()` closes
  the browser's camera too, so its light goes off.

## Findings that change later work

1. **Lists of files are a trap.** The site and the VS Code extension each copy a fixed list of runner files, and
   neither had `camera.js`; check 55 caught it. A new runner file needs both lists.
2. **Merge order across repositories matters.** The runner passes funground a new argument, and the site's build
   checks the runner's files: funground, then `funground-web`, then the site. The site's first build failed only
   because it ran before the runner merge.
3. **The machine's memory stopped a CI watcher again.** One quick status check is enough; long watchers are avoided.

## Built by subagents

Part 1 and 2 (funground: `camera_input.py`, the browser hook, tests, docs, the two examples) by a Sonnet builder; the
main session reviewed it, changed `clip.done` and `record()` before `start()`, fixed the guide's photo example (it saved
every frame after a key) and added the Mac sentence. Parts 3 to 5 by the main session.

## Retrospective

A fake device on every layer (pygame's module in Python tests, Chrome's fake camera in the browser) let the whole story
be tested without opening a camera, and the maintainer's single try with a real one confirmed it.
