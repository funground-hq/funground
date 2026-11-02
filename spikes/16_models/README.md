# Spike S-231: which models, from which provider, on the web and on the desktop

**Status:** measurements done, 2 Nov 2026. D-124 was accepted (d, 29 Oct) and D-125 (the first API, 2 Nov). The Pyodide
route and the same pose sketch on both platforms became product code in S-232 (gallery `models-01_stick_figure`: the
desktop and Play agree within 0.03 px). Speech, sounds and a model the learner teaches are measured in
`speech_sounds/results.md`; the closing recommendation is at the end of this file.

| Step | File | What it found |
|---|---|---|
| Desk research | `research.md` | MediaPipe Tasks is the only provider with the same tasks and the same named points (33 pose, 21 hand, 478 face) on the web and in Python. Pyodide has no model runtime, so in Play the model runs in JavaScript and Python reads its latest result each frame, as camera frames already arrive |
| Web, measured | `web/results.md` | MediaPipe Tasks Vision 1.2.0 in headless Chrome: every task runs in a module worker, beside Pyodide. CPU: pose lite 11/s, hands 16/s, face 21/s, outline 40/s. GPU: pose lite about 40/s. Network: only the CDN and the model storage |
| Desktop, MediaPipe | `desktop/results.md` | `mediapipe` 1.2.0 works on Python 3.14, at 358 MB with its dependencies. It is 4 to 7 times faster than the web: pose lite 74/s, hands 85/s, face 88/s. **Its native library logs usage to Google** (`play.googleapis.com/log`, Clearcut). The name was looked up once a task was created, and no switch to turn it off was found |
| Desktop, OpenCV | `opencv/results.md` | `opencv-python` 4.14 runs the OpenCV Zoo's MediaPipe-derived models, at about 180 MB with numpy. Pose and hand keep MediaPipe's 33 and 21 points in the same order. With the detector's box reused, pose runs at 21/s and hands at 39/s; the outline runs at 34/s. No network use was found. The weights are Apache-2.0 (YuNet is MIT). The Zoo has no face mesh (YuNet gives a box and 5 points). funground would own about 450 lines of glue, plus the detectors' anchor tables. OpenCV 5.0 breaks the Zoo's person detector |
| MediaPipe in detail | `mediapipe_detail/results.md` | **Logging:** Google will not add a switch (issue #6291: "We are not adding an official API to disable this data collection"; build from source or block the host) and says telemetry is rolling out to all platforms. The logger is only in Google's prebuilt library; it connects about 0.15 s after `task.close()`. It sends timings, counts and versions, no pictures or points. A proxy is ignored, and blanking its settings does not stop it. **Unbundling:** it works with mediapipe, numpy and certifi alone (about 124 MB, not 358 MB), but only with empty stand-ins for cv2 and matplotlib, which a drawing helper imports (a hack) |
| Hugging Face, desk | `huggingface/research.md` | Without torch, the route is `onnxruntime` with ONNX files. It is strong for naming a picture, objects, embeddings and speech, and has nothing first-class for pose, hands or the face mesh |
| ONNX on both platforms | `onnx/results.md` | **The same .onnx files run in `onnxruntime` on the desktop and `onnxruntime-web` in Play's worker.** Desktop, with the box reused: pose 52/s, hand 162/s, selfie outline 88/s, 2.5 to 3.5 times faster than cv2.dnn. Play: pose 13 to 15/s on wasm (MediaPipe web 11/s on CPU) and 20/s on WebGPU. The points agree within 5 px between platforms (mean 1.6 px for pose). funground's own glue is 141 lines of Python and 151 of JavaScript for all twelve models, with the anchor tables generated. Telemetry: the Windows 1.31.1 wheel has no network code (ETW only, which stays on the computer); 0 connections in 7 runs. Microsoft's privacy page documents 1DS over HTTPS with `ORT_DISABLE_TELEMETRY=1` as the switch; Linux and macOS are not measured. Install about 109 MB with numpy. The int8 files are slower and one gave wrong answers here: use fp32 |
| onnxruntime on Linux and macOS | `ci_telemetry/results.md` | onnxruntime 1.31.1, with and without `ORT_DISABLE_TELEMETRY=1`: no connections on Linux (strace, every thread) or macOS (lsof). Linux's module links no networking library; macOS's links Apple's networking frameworks and has a telemetry log manager, so funground-ml sets the switch before import everywhere and rechecks when the pinned version changes |
| Speech, sounds, a model you teach | `speech_sounds/results.md` | All on the same engine, both platforms (web: onnxruntime-web 1.30.0 wasm, 1 thread). **Whisper tiny.en q8** (40.8 MB): real-time factor 0.11 to 0.17 on the desktop (rerun by the main session: 0.13 and 0.17), 0.37 to 0.54 on the web; a synthesized clip 0 % word error, a LibriVox clip 13 % ("LibraVox"), the same words on both platforms; own decode loop, 86 lines of Python, 94 of JavaScript. **YAMNet** (16.1 MB, community ONNX, raw 16 kHz in): 1.4 ms per 0.96 s window on the desktop, 13 to 28 ms on the web, scores agree within 1e-5, sensible top 3 for dog, whistle and speech, clapping only partly ("Hands"). Uploader unvetted; matches a second independent conversion to 5 decimals. **kNN on picture vectors** (3 taught per class, cat, dog, bird, 200 splits): DINOv2-small q8 91 %, 79 ms; MobileNetV4's pre-classifier vector 90 % at k=1, 3.9 ms, but needs a derived file we would host |

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

## Closing recommendation (2 Nov 2026)

Every task the spike set out to compare now has a measured route on one engine, `onnxruntime` and `onnxruntime-web`,
with the same files on both platforms and answers that agree by test:

| Task | Recommended model | Story | Notes |
|---|---|---|---|
| Body, hands, the person's outline | OpenCV Zoo MediaPipe-derived, selfie segmentation | S-232, S-233 (done) | shipped in funground-ml |
| Words you say | Whisper tiny.en q8, own decode loop | S-234 | English only; base.en (77 MB) if tiny proves too weak on learners' voices. Needs the microphone's samples to reach the model in Play as the camera's frames do |
| Sounds | YAMNet (16 MB) | new candidate | the only ONNX copy is a community conversion: host a copy we have checked against Google's TensorFlow model before shipping; the 521 AudioSet names are CC BY 4.0 and need credit |
| A model you teach | k=1 cosine on picture vectors, the margin as "how sure" | S-235 | start with MobileNetV4's vector (live speed), offer DINOv2 for subtle classes; three examples a class gives 80 to 100 % between tries, so the guide should say "add more examples" |
| Face points | none yet | none | no open 478-point model that sends nothing; MediaPipe web stays the only good source |
| Objects, naming a picture | D-FINE nano, MobileNetV4 | later | measured in `onnx/results.md`; not yet asked for |

Each new task's names (for example `ml.words(mic)`, `ml.sounds(mic)`, `ml.teach(...)` and `ml.guess(...)`) are public
API and go to the maintainer as a decision before S-234 or S-235 starts. Not measured: Linux and macOS speed, learners'
own voices and rooms, more or harder taught classes.
