# Sprint 29 — Creative exercises, closer to Play (E-35, E-34, E-22)

**Dates:** planned 16 October 2026. Work in funground (S-173, course text for S-216) and `funground-hq.github.io`
(S-214, S-215, S-216). Each story ships when it is checked.

**Goal:** Play becomes the place to experiment: it suggests what a path (and every other funground object) can do, the
course's first lessons open their experiments in it, the gallery says where the guide teaches each example, and a new
piece invites the learner to blow words away with their breath.

**Decisions:** D-104 (course: linked lesson and Play first, Lessons 1, 3 and 5; runnable blocks later), D-105 (S-173:
a spot the learner places, words as fog). No new public funground name is planned; S-173 is an example.

| Story | Value | Status |
|---|---|---|
| S-214 | Play suggests the methods of what funground gives back (`f.path().`, a camera, a picture...) | planned |
| S-215 | Each gallery example says where the guide teaches it | planned |
| S-216 | Lessons 1, 3 and 5 open their experiments in Play, with prompts and a way back | planned |
| S-173 | Blow the words away: a fog of words around your mouth, scattered by your breath | planned |

## Tasks

**S-214 Suggestions for objects** (site, `tools/codemirror/completion.js`; funground `completions.json` if it lacks the
classes' members)
- [ ] `completions.json` lists each class's methods with signature and summary (PathBuilder, Camera, Clip, Picture,
  Sound, Microphone, Vector, Grid...) and which functions return which class
- [ ] after `f.path().`, `f.path().rect(...).` (a chain) and a variable assigned from such a call, suggest that class's
  methods; hints and hover as for `f.` names
- [ ] checks in `test_editor.mjs`

**S-215 Gallery and guide** (site, `tools/assemble.py`)
- [ ] from the guide's links and pictures, the guide sections that use each example
- [ ] "In the guide: ..." on each example page; the chapter on each area of the gallery index
- [ ] `check_links.py`, strict build

**S-216 The course in Play, first step** (funground `docs/course`, `examples/course`; site)
- [ ] for each experiment of Lessons 1, 3 and 5: its prediction prompt and named comparison, written in the course's
  voice (Look, Predict, Make, Compare, Choose, Extend), kept with the example
- [ ] "Open in Play" in the lesson, with the code and files; Play shows the prompt and comparison, "Keep this" (My
  sketches, with a sentence about the choice) and "Back to Lesson N, section"
- [ ] checks in `test_editor.mjs`; the lesson pages still work without Play (download stays)

**S-173 Blow the words away** (funground, `examples/gallery/`)
- [ ] an original example: the camera picture, a cloud of words drifting and fading like fog around a spot the learner
  places with a click; breath (`mic.level()`) blows the nearest words away, they fade and drift back; save a GIF
- [ ] works without a camera or a microphone (a photo, and the mouse as breath); golden; originality check; the GIF
  that inspired it credited

Order: S-214 and S-215 first (independent, site), S-173 alongside (funground), then S-216 (it touches the course text
and Play). One builder at a time on this machine.
