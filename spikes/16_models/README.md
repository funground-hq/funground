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
| MediaPipe in detail | `mediapipe_detail/results.md` | **Logging:** Google will not add a switch (issue #6291: "We are not adding an official API to disable this data collection"; build from source or block the host) and says telemetry is rolling out to all platforms. The logger is only in Google's prebuilt library; it connects about 0.15 s after `task.close()`. It sends timings, counts and versions, no pictures or points. A proxy is ignored, and blanking its settings does not stop it. **Unbundling:** it works with mediapipe, numpy and certifi alone (about 124 MB, not 358 MB), but only with empty stand-ins for cv2 and matplotlib, which a drawing helper imports (a hack) |
| Hugging Face, desk | `huggingface/research.md` | Without torch, the route is `onnxruntime` with ONNX files. It is strong for naming a picture, objects, embeddings and speech, and has nothing first-class for pose, hands or the face mesh |
| ONNX on both platforms | `onnx/results.md` | **The same .onnx files run in `onnxruntime` on the desktop and `onnxruntime-web` in Play's worker.** Desktop, with the box reused: pose 52/s, hand 162/s, selfie outline 88/s, 2.5 to 3.5 times faster than cv2.dnn. Play: pose 13 to 15/s on wasm (MediaPipe web 11/s on CPU) and 20/s on WebGPU. The points agree within 5 px between platforms (mean 1.6 px for pose). funground's own glue is 141 lines of Python and 151 of JavaScript for all twelve models, with the anchor tables generated. Telemetry: the Windows 1.31.1 wheel has no network code (ETW only, which stays on the computer); 0 connections in 7 runs. Microsoft's privacy page documents 1DS over HTTPS with `ORT_DISABLE_TELEMETRY=1` as the switch; Linux and macOS are not measured. Install about 109 MB with numpy. The int8 files are slower and one gave wrong answers here: use fp32 |

## D-124: the route for models (accepted 29 Oct: d, with the models from the Hugging Face Hub)

**Context:** E-37's first stories (pose and hands, S-232; the person's outline, S-233) need a model provider on each
platform. The sketch must be the same file on both (D-120, ADR-007), and the library is for learners, children
included. MediaPipe's prebuilt packages log usage to Google with no switch, and Google says this is coming to every
platform.

**Options:**
- **Keep current behaviour:** no models.
- **a. MediaPipe everywhere:** the fastest, with one call per task, but it sends data to Google on the desktop now, and on
  the web later, with no switch.
- **b. MediaPipe in Play, OpenCV on the desktop:** nothing is sent on the desktop. It is slower, with different engines
  on each side, and Play inherits MediaPipe's coming telemetry.
- **c. Play only at first:** it breaks "the same file on both".
- **d. ONNX everywhere:** `onnxruntime` on the desktop and `onnxruntime-web` in Play, running the **same .onnx files**:
  the OpenCV Zoo's MediaPipe-derived pose and hand models (Apache-2.0), Google's selfie outline and YuNet for the face
  box. funground owns the pre- and post-processing in Python and in JavaScript, kept in step by a test that the points
  agree within 5 px. `ORT_DISABLE_TELEMETRY=1` is set before importing it.

**Trade-offs:**

| | a | b | d |
|---|---|---|---|
| Sends data | desktop now, web later, no switch | Play later | nothing observed; a documented switch is set anyway |
| Pose, desktop | 74/s | 21/s | 52/s (box reused) |
| Pose, Play (CPU / GPU) | 11 / 42 per second | 11 / 42 per second | 13 to 15 / 20 per second |
| Same engine and files on both | yes | no | yes |
| Face | 478 points | box and 5 points | box and 5 points |
| Desktop install for `funground-ml` | 358 MB | about 180 MB | about 109 MB |
| Code funground owns | one call per task | about 450 lines of Python plus 4,000 lines of anchor tables | about 150 lines of Python and 150 of JavaScript |

**Recommendation: d.** Start with pose, hands and the outline (S-232, S-233). Add tracking from the last frame's points
for speed in Play, and the face mesh when an open model exists.

**Why:** it is the only option that sends nothing we know of, runs one set of files on both platforms, and keeps the
same points on both platforms by test. It is also the smallest install. Play's CPU speed is level with MediaPipe's. The
GPU path is half MediaPipe's, and the planned tracking closes most of that gap.

**What would change it:** `onnxruntime` on Linux or macOS sending data despite the switch (to measure in CI before
building), or Play needing MediaPipe's GPU speed for a piece. The rest of the spike (speech, sounds, a model the
learner teaches with DINOv2 embeddings, which agree at cosine 0.988 across platforms) uses the same engine.
