# Design note: camera input (`f.camera`)

**Status:** accepted, 16 October 2026 (D-089, all four as recommended). Story S-172 (epic E-33), built in
Sprint 28. Written 11 October 2026.

## Why

Learners want their own face, hands and room in a sketch: a mirror that turns them into letters or dots,
a photo booth, a "blow the letters away" piece (S-173), a stop-motion clip. funground can play and hear
sound and can listen to the microphone, but it cannot see. The camera is the missing input.

## What a learner writes

```python
import funground as f

cam = f.camera()                 # the default camera; f.cameras() lists them (desktop)


def setup():
    f.size(640, 480)
    cam.start()                  # asks permission the first time (browser, macOS)


def draw():
    f.image(cam, 0, 0)           # the camera is used like a picture: always its latest frame
    if f.key == "s":
        cam.save("me.png")       # a still photo, at the camera's resolution


f.run()
```

| Call | Does |
|---|---|
| `f.camera(name=None)` | The default camera, or (desktop) the one whose name contains `name`. Nothing opens yet |
| `f.cameras()` | The cameras' names (desktop); `[]` in the browser, where the browser chooses |
| `cam.start(width=640, height=480, mirror=True)` | Opens the camera at (about) that size; `mirror` flips it like a mirror, as people expect of a selfie view |
| `cam.stop()` | Lets it go (the light goes off). Also done when the sketch ends |
| `cam.is_ready()` | `True` once frames arrive (after permission is given) |
| `f.image(cam, x, y, ...)` | Draws the latest frame, with everything `image()` already does: scaling, `tint`, `image_mode` |
| `cam.picture()` | A still copy of the latest frame as an ordinary picture: `get`/`set`, pixels, filters, `copy`, `mask`, drawing on it |
| `cam.save(path)` | A still photo (`.png`, `.jpg`) |
| `clip = cam.record(seconds)` | Records the next `seconds` of frames into a clip (in memory). `clip.done`, `len(clip)`, `clip.frame(i)` (a picture), `clip.fps` |
| `clip.save(path)` | The clip as `.gif` (both platforms) or `.mp4` (desktop with the `video` extra, as `save_movie`) |

Pixels from the camera work with the existing picture vocabulary, so "turn me into dots" is
`cam.picture().get(x, y)` in a loop, with nothing new to learn. Until permission is given, `f.image(cam, ...)`
draws nothing and `cam.picture()` is a black picture of the asked size, so a sketch never crashes while
waiting (the same rule as the microphone's silence).

**Short video** means a clip the learner records and saves (a few seconds: at 640 x 480, about 1.2 MB a
frame in memory, so the length is capped, e.g. 10 seconds, with a clear error above it). Playing a video
*file* as a source (`f.load_movie`) is a separate, later story.

## How it works

The camera follows the microphone's pattern (`microphone_input.py`, `Web_Runner_Note.md`, "Sound and
microphone"): one module, `camera_input.py`, opens a device and keeps **the latest frame**; a host can replace
the device.

**Desktop.** pygame-ce, already a dependency, captures from cameras: Media Foundation on Windows and V4L2 on
Linux with no extra install (checked: pygame-ce 2.5.8 lists `_camera (MSMF)` on this machine). Its frames
arrive as surfaces and become funground pictures (the same conversion `load_image` uses). **macOS** has no
native backend in pygame-ce: it needs OpenCV (`opencv-python`, a large wheel), which would be an optional extra
(decision 1).

**Browser.** The page opens the camera with `getUserMedia({video})` (the browser asks permission and shows its
camera indicator), draws frames into an `OffscreenCanvas` at the asked size, and transfers each frame's pixels
to the worker (as the microphone transfers its chunks); the worker gives them to
`Session.push_camera(pixels, width, height)`, which keeps the latest. One frame a display frame at most;
frames the sketch has not used are dropped, never queued. On the Play page the preview iframe needs
`allow="camera"`. **VS Code's panel cannot use the camera** (its frame allows neither camera nor microphone),
so in github.dev a sketch using the camera gets one line saying to run it on the website or the desktop.

**Clips** keep their frames as pictures; `clip.save(".gif")` uses the GIF writer `save_gif` uses;
`.mp4` uses the `video` extra's ffmpeg on the desktop. In the browser, `.gif` only (recording with the page's
`MediaRecorder` to WebM is possible later).

## Privacy and safety

- The camera opens only when the sketch calls `cam.start()`, and the operating system or browser asks first.
- Frames stay on the learner's machine: funground never sends them anywhere. A saved photo is a file the
  learner chose to write. In the browser, the preview's origin (D-078) holds the camera, never the website.
- The camera is released when the sketch ends or stops (Stop on the Play page ends it at once).
- Teaching material says plainly when the camera is used, and examples work without one (a fallback picture).

## Testing

- Desktop: a fake device (as the microphone tests use) feeding known frames: `f.image(cam)` draws them,
  `picture()` copies, `save()` writes, `record()` holds the right number, mirroring flips.
- Browser: headless Chrome's fake camera (`--use-fake-device-for-media-stream` feeds a moving test pattern):
  frames reach the worker and are drawn, permission refusal leaves a black picture and one line of output.
- No goldens of live camera pictures (they change); goldens of the fake frames only.

## Performance

640 x 480 at 30 frames a second is about 37 MB/s of pixels: fine to transfer and to hand to Cairo once per
frame; turning every pixel into a funground colour in Python is not (a sketch that samples a grid of points
is). The guide shows sampling, not looping over every pixel; `picture()` copies only when asked.

## Decisions (D-089, accepted 16 October 2026 as recommended)

1. **macOS:** a `camera` extra with OpenCV (large), or "desktop camera on Windows and Linux; on a Mac use the
   website" for 0.2. Recommendation: the latter for 0.2, the extra later if asked for.
2. **Mirror by default:** `mirror=True` (what a selfie view looks like) or `False` (what the camera sees).
   Recommendation: `True`.
3. **Clip length cap:** 10 seconds at 640 x 480 by default. Recommendation: yes, with the size in the error.
4. **Release:** with 0.2 (the browser work is fresh) or after. Recommendation: after Sprint 21, in 0.2 if the
   sprint after has room; it is a sizeable story (desktop, browser host, Play page, extension message, docs).
