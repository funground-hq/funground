# Spike S-231: which models, from which provider, on the web and on the desktop

**Status:** in progress, 28 Oct 2026. The vision measurements on both platforms are done, and the route is proposed as
D-124 (pending). Still to do: speech and sounds, a model the learner teaches, the Pyodide route as working code, and
the same 30-line pose sketch on the desktop and in Play.

| Step | File | What it found |
|---|---|---|
| Desk research | `research.md` | MediaPipe Tasks is the only provider with the same tasks and the same named points (33 pose, 21 hand, 478 face) on the web and in Python. Pyodide has no model runtime, so in Play the model runs in JavaScript and Python reads its latest result each frame, as camera frames already arrive |
| Web, measured | `web/results.md` | MediaPipe Tasks Vision 1.2.0 in headless Chrome: every task runs in a module worker, beside Pyodide. CPU: pose lite 11/s, hands 16/s, face 21/s, outline 40/s. GPU: pose lite about 40/s. Network: only the CDN and the model storage |
| Desktop, MediaPipe | `desktop/results.md` | `mediapipe` 1.2.0 works on Python 3.14, at 358 MB with its dependencies. It is 4 to 7 times faster than the web: pose lite 74/s, hands 85/s, face 88/s. **Its native library logs usage to Google** (`play.googleapis.com/log`, Clearcut). The name was looked up once a task was created, and no switch to turn it off was found |
| Desktop, OpenCV | `opencv/results.md` | `opencv-python` 4.14 runs the OpenCV Zoo's MediaPipe-derived models, at about 180 MB with numpy. Pose and hand keep MediaPipe's 33 and 21 points in the same order. With the detector's box reused, pose runs at 21/s and hands at 39/s; the outline runs at 34/s. No network use was found. The weights are Apache-2.0 (YuNet is MIT). The Zoo has no face mesh (YuNet gives a box and 5 points). funground would own about 450 lines of glue, plus the detectors' anchor tables. OpenCV 5.0 breaks the Zoo's person detector |

## D-124: the route for models (pending)

**Context:** E-37's first stories (pose and hands, S-232; the person's outline, S-233) need a model provider on each
platform. The sketch must be the same file on both (D-120, ADR-007), and the library is for learners, children
included.

**Options:**
- **Keep current behaviour:** no models.
- **a. MediaPipe everywhere:** MediaPipe Tasks in Play, `mediapipe` on the desktop. It is the fastest, needs one call
  per task and gives the same points everywhere, the 478 face points included. But the desktop package sends usage
  data to Google, with no switch to turn it off.
- **b. MediaPipe in Play, OpenCV with the Zoo's models on the desktop:** nothing is sent anywhere. The same 33 pose and
  21 hand points, with names funground supplies. The desktop is still at least as fast as Play. funground owns the
  pipeline code, and the face starts as a box and 5 points on both platforms, not the 478.
- **c. Play only at first:** the desktop says plainly that models run in Play for now. It is the least work, but it
  breaks "the same file runs on both" until the desktop follows.

**Trade-offs:**

| | a | b | c |
|---|---|---|---|
| Sends data to a third party | the desktop, to Google | no | no |
| Pose on the desktop | 74/s | 21/s (box reused) | not offered |
| Same points on both platforms | pose, hands, face (478) | pose, hands; face as box and 5 points | not applicable |
| Desktop install for `funground-ml` | about 358 MB | about 180 MB | none |
| Code funground owns | small (one call per task) | about 450 lines of pipeline, kept working on OpenCV 4 and 5 | small |
| Work, estimated, not measured | least | most: the pipeline, the point names and the tests | least, then a or b later |

**Recommendation: b**, starting with pose, hands and the outline. The face mesh waits until there is a desktop model
for it that sends nothing.

**Why:** a children's library should not send data it cannot switch off. b is the only option that keeps the same
sketch on both platforms without it. Its desktop speed (21/s and up) is at least the web's. The pipeline code is a cost,
but it is designed once, inside `funground-ml`, and tested against MediaPipe's points.

**What would change it:** Google documenting an off switch for the Python package's logging, which would make a the
simplest choice; or the pipeline proving much larger than measured, which would make c the first step.
