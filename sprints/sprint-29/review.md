# Sprint 29 review — Creative exercises, closer to Play (E-35, E-34, E-22, E-33)

**Dates:** 16 to 17 October 2026. Work in funground (PRs #11 to #15), `funground-web` (PR #12) and
`funground-hq.github.io` (PRs #24 to #26). Every story shipped when it was checked. **Awaiting sign-off.**

## Outcome

Goal met, and more. Play suggests what funground's objects can do; the gallery says where the guide teaches each
example; Lessons 1, 3 and 5 open their experiments in Play with prompts and a way back; and the camera grew into a small
toolkit for video pieces, shaped by the maintainer's own tries: a photo booth that records takes with sound, a way to
load a take back, and a word cloud blown away by breath.

| Story | Result |
|---|---|
| S-214 Suggestions for objects | `completions.json` lists 24 classes' members and what calls return; Play suggests a path's (camera's, picture's...) methods after `f.path().`, a chain, or a variable; unknown variables get none |
| S-215 Gallery and guide | each example page says "In the guide: chapter › section" (86 of 105 examples); each area names the chapters that link it |
| S-216 The course in Play | 12 experiments of Lessons 1, 3, 5 (`examples/course/play.json`, the lessons' own words): Open in Play in the lessons; in Play a panel with Back to the lesson, Predict before the first Run, Compare after, Keep this (a My sketch with the learner's note) |
| S-173 Blow the words away | gallery projects-09: a fog of bold words around a spot you click, blown by breath; Record/Stop takes played back with the recorded breath and saved as `blow.gif` and `take.gif`; zoom |
| S-219 The photo booth records takes (from Sprint 30) | Record/Stop, Pause/Resume, Photo, zoom; red frame, blinking light and timer while recording, amber while paused, "Saving" before the slow save; `take.gif` and `take.wav` in step |
| S-220 Loading a take (from Sprint 30) | `f.load_clip()` (D-109) through pygame-ce's `load_animation`; `clip.pause()`, `clip.resume()`, `clip.is_paused()`, `clip.stop()`; gallery images-08, Play a take |

Also: gallery motion-02 (sparks that fade, a class and a list), path `square`/`triangle`/`quad`, PlotDevice and
`with`-statement questions answered.

**Tests:** funground's full suite 4361 passed, 1 skipped (17 Oct). Site editor checks 56 to 65 added (all pass, with
13 to 24, 42, 45, 55). `funground-web` `test_runner.py` with images-08 added: passes (2 corner pixels differ by 1 in the
browser, a scaling edge, like D-101). The booth and the words piece were driven by scripts with a pushed camera and
probed in headless Chrome with Chrome's fake camera and microphone.

## Measurements

| What | Result | How |
|---|---|---|
| Booth Stop (saving a 4 s take) | 1.0 s, now behind a "Saving" frame | headless Chrome, fake camera |
| Booth Pause (taking the sound) | 0.05 s | the same |
| Words piece frame rate | 17 fps at 480 x 360 (14.6 at 640 x 480 before) | headless Chrome |
| A 2 s booth take with a pause | `take.wav` 2.0 s, the frames 2.0 s | scripted run |

## Decisions

- Maintainer: D-104 (course: linked lesson and Play first), D-105 (words as fog), D-106 approach (background
  replacement; names pending), D-107 (takes as video and sound), D-108 (My files plus download and upload), D-109
  (`load_clip`, pause, resume), D-110 (pixels project, average as an option), D-111 (edge filter), D-112 (AI page
  declined for now).
- Decided by Claude, for review: `clip.stop()` and `clip.is_paused()` added beside the approved names (a stop button
  needs the first; a button label the second); a loaded clip's rate is the median frame time; course panel words taken
  from the lessons, not rewritten; areas credited only to chapters that link them.
- Pending: D-106 names, D-113 (course experiments and `f.variations`/`f.keep`/`f.mark`, `Course_Studio_Note.md`).

## Findings that change later work

1. **The maintainer's real use found every interaction problem** (no recording feedback, coordinating breath and a key,
   an unresponsive Stop); tests found none of them. A piece with a camera or a microphone needs a try by a person.
2. **Saving a GIF blocks the sketch** (1 s for 4 s of video in headless Chrome, more on busy real frames). A sketch should
   show "Saving" on one frame and save on the next; this belongs in the guide's camera section.
3. **Play keeps drafts and the browser keeps files for 10 minutes**, so a fixed example can look unchanged. Reset, or a
   reload after a few minutes, is the answer; the site might say so when an example changed since the draft.
4. **Memory and load still shape the work:** one full-suite half took 47 minutes while a browser test ran beside it,
   and a timing test failed; run heavy jobs one at a time.

## Built by subagents

S-214 (both repositories), S-215 (site) and S-216's site part by Sonnet builders, each reviewed (S-215's area rule
changed; S-214's `Picture` return types added; S-216 comments tidied). Everything else by the main session.

## Retrospective

Splitting the camera work into a recorder (the booth) and pieces that load a take, as the maintainer proposed, turned
three tangled examples into a model that other video pieces can follow.
