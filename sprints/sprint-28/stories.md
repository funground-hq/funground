# Sprint 28 — The camera (E-33)

**Dates:** planned 16 October 2026. Work in funground (parts 1, 2, 5), `funground-web` (part 3), `funground-run.github.io`
and `funground-hq.github.io` (part 4), and the github.dev extension (part 5). Each part ships when it is checked
(D-089).

**Goal:** a learner can see themselves in a sketch: draw the camera's picture, read its pixels, take a photo and record
a short clip, on a Windows or Linux computer and in Play.

**Decisions:** D-089, accepted 16 October as recommended (Mac desktop: use the website; mirror on; clips at most 10 s;
ships as built). Design: `docs/design/Camera_Note.md`; contract rows I4 and I5 (Proposed until this review). New
public names: `f.camera`, `f.cameras` and the camera's and clip's methods. No new dependency: pygame-ce captures on
Windows (Media Foundation, checked: "Integrated Webcam" listed) and Linux (V4L2).

| Story | Value | Status |
|---|---|---|
| S-172 | Camera input, `f.camera()`, desktop and browser, still image and short clips | building: parts 1 and 2 done (funground, built by a Sonnet subagent, reviewed); the browser next |

## Tasks

**Part 1, funground on the desktop**
- [x] `funground/camera_input.py`: the only module that touches `pygame.camera` (boundary table); a replaceable device
  (as `microphone_input.use_host_input`); a fake device for tests; the headless camera (never ready)
- [x] `f.camera()`, `f.cameras()`; `Camera.start/stop/is_ready/picture/save/record`, `width`, `height`; `Clip`
- [x] the frame taken once before each `draw()`; recording one frame per drawn frame; cameras stopped at the end
- [x] `f.image(cam, ...)` draws the frame (P3, P5, P6); nothing before the first frame
- [x] the Mac message; errors as I4 and I5
- [x] tests: `tests/test_camera.py` with the fake device (drawn, mirrored, scaled, `picture`, `save`, `record`, clip
  GIF, the 10 s cap, headless, errors, the boundary)

**Part 2, documentation**
- [x] docstrings, `make_api_reference.py`, Quick Reference rows, a guide section (images chapter)
- [x] two gallery examples with a fallback picture when there is no camera: a mirror of dots (sampling `picture()`),
  a photo booth (a key records a 3 s GIF); goldens show the fallback (headless camera); originality check

**Part 3, the browser runner (`funground-web`)**
- [x] `Session.push_camera(pixels, width, height)` and the host camera device in `funground.web`
- [ ] the page opens `getUserMedia({video})` when the sketch calls `start()`, scales frames on an `OffscreenCanvas`,
  transfers at most one a display frame to the worker; stops the tracks on `stop()`, Stop and the end
- [ ] refusal: never ready and one line of output; test with Chrome's fake camera

**Part 4, Play**
- [ ] the preview iframe gets `allow="camera"`; the preview page passes frames; a check in `test_editor.mjs`

**Part 5, github.dev**
- [ ] the extension's panel cannot use the camera: one line saying to run the sketch on the website or the desktop

Acceptance (S-172): a fake camera's frames are drawn, saved and recorded on the desktop and in headless Chrome; refusal
leaves a black picture and one line of output; the maintainer tries it on the live site and on Windows.
