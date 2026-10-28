# S-231 desk research: models for pose, hands, faces, outlines, objects, words and sounds

Desk research only, 28 October 2026. Nothing was installed. Sizes of files were read with HTTP HEAD requests or from
package indexes; model cards were read as text. "Published, not measured" means a figure from a vendor page. "Unverified"
means I could not confirm it. This is input for the main session. Names such as `f.pose()` are the maintainer's to
decide.

Context read: S-231 row in `docs/backlog/stories.md`; `docs/design/ADR-007-core-and-libraries.md` (ML is the separate
package `funground-ml`, `from funground import ml`); `spikes/14_cutout/README.md`; the camera route in
`funground/camera_input.py`, `funground-web/runner/camera.js`, `runner.js`, `worker.js`.

## Headline findings

1. MediaPipe is the only provider that has the same task, with the same named points, on the web (JS/WASM) and on the
   desktop (Python). Its pose model gives 33 landmarks, hands 21, face 478 (plus 52 blendshapes).
2. `mediapipe` on PyPI changed this month. Version 1.2.0 (27 Oct 2026) ships `py3-none` wheels (no per-Python tags) for
   Windows x86-64 and ARM64, macOS arm64 only, Linux x86-64 and aarch64. There is no Intel Mac wheel. It depends on
   `opencv-contrib-python`, `matplotlib`, `numpy` and `sounddevice`, so the install is far bigger than the 24 MB wheel.
3. The web side can run in a module worker only since MediaPipe 0.10.35 (April 2026). Funground's `worker.js` is a module
   worker, so this matters.
4. Pyodide has no `mediapipe`, `onnxruntime` or `torch` (it does have `opencv-python` 4.11 and `scikit-learn`). In Play
   the model must run in JavaScript, outside the Python interpreter. The camera route shows how.
5. Weights licences: the MediaPipe pose and selfie-segmentation model cards say Apache-2.0. Excluded: YOLO via
   Ultralytics (AGPL-3.0), Bria RMBG (non-commercial), SegFormer (NVIDIA, "other"), MobileViT (Apple, "other").
6. ml5.js 1.x has a custom licence (ml5.js License 1.0) with a Code of Conduct condition, though npm says MIT. Flag it.

## 1. Evidence table

### 1a. Library facts (version, licence, size, platforms)

| Provider | Version, date | Library licence | Runtime download | Platform and Python coverage | Source |
|---|---|---|---|---|---|
| MediaPipe Tasks, web (`@mediapipe/tasks-vision`) | 1.2.0, Oct 2026 | Apache-2.0 | `vision_wasm_internal.wasm` 14.5 MB + `.js` 0.33 MB + bundle 0.16 MB (a no-SIMD wasm of 12.9 MB is a fallback). Package unpacked 44 MB | Browser. A module-worker wasm variant `vision_wasm_module_internal.*` exists | [npm](https://registry.npmjs.org/@mediapipe/tasks-vision/latest), [file list](https://data.jsdelivr.com/v1/packages/npm/@mediapipe/tasks-vision@1.2.0) |
| MediaPipe Python | 1.2.0, 27 Oct 2026 (0.10.35 on 27 Apr 2026) | Apache-2.0 | Wheel: win_amd64 24.5 MB, win_arm64 21.4 MB, macOS arm64 39.0 MB, Linux x86-64 42.7 MB, Linux aarch64 40.1 MB. Needs `numpy`, `opencv-contrib-python` (win x86-64 about 54 MB, Linux 79-82 MB, macOS Intel 43 MB), `matplotlib`, `sounddevice`, `absl-py`, `flatbuffers`, `certifi` | Wheels are `py3-none`. PyPI classifiers list 3.9-3.14, Windows, macOS, Linux. No macOS Intel wheel in 1.2.0 or 0.10.35. Whether `py3-none` really loads on 3.14 is unverified | [PyPI 1.2.0 files](https://pypi.org/pypi/mediapipe/1.2.0/json), [0.10.35](https://pypi.org/pypi/mediapipe/0.10.35/json), [project page](https://pypi.org/project/mediapipe/), [opencv-contrib](https://pypi.org/pypi/opencv-contrib-python/json) |
| ml5.js | 1.4.0 | npm says MIT; the repo's LICENSE.md is "ml5.js License v1.0": use must comply with the ml5 Code of Conduct, the licence ends 30 days after an unfixed breach, contributions revert to Blue Oak 1.0.0 after 3 years. Pre-May-2021 code is MIT. LGPL compatibility is not addressed | npm package 77.7 MB unpacked; depends on `@tensorflow/tfjs` ^4.22, legacy `@mediapipe/pose`, `hands`, `face_mesh`, `selfie_segmentation`, tfjs `pose-detection`, `body-segmentation`, `hand-pose-detection`, `face-landmarks-detection`, `coco-ssd`, `mobilenet`, `speech-commands`. Loaded size of one task: not measured | Browser only (no Python) | [npm](https://registry.npmjs.org/ml5/latest), [LICENSE.md](https://raw.githubusercontent.com/ml5js/ml5-next-gen/main/LICENSE.md), [repo](https://github.com/ml5js/ml5-next-gen) |
| Transformers.js (`@huggingface/transformers`) | 4.3.2 | Apache-2.0 | 10 MB package. Runs on `onnxruntime-web` (MIT, 1.31.x): wasm 14.8 MB (plain), 17.9 MB (JSPI), 28.7-29.5 MB (asyncify / WebGPU "jsep") | Browser (WASM by default, `device: "webgpu"` optional; WebGPU about 85% of browsers in March 2026). Its official React tutorial runs the pipeline in a module `Worker` | [npm](https://registry.npmjs.org/@huggingface/transformers/latest), [ORT npm](https://registry.npmjs.org/onnxruntime-web/latest), [ORT files](https://data.jsdelivr.com/v1/packages/npm/onnxruntime-web@1.31.1), [WebGPU guide](https://huggingface.co/docs/transformers.js/guides/webgpu), [React tutorial](https://huggingface.co/docs/transformers.js/tutorials/react) |
| Hugging Face `transformers` (Python) | 5.21.0 | Apache-2.0 | Pure Python (`tokenizers`, `safetensors`, `huggingface-hub`...) but needs a backend. `torch` 2.15.0: Windows x86-64 126.7 MB, macOS arm64 138.6 MB, Linux x86-64 539 MB (plus NVIDIA CUDA wheels it depends on, several GB; sizes unverified), Linux aarch64 484 MB | Python >=3.11; torch cp311-cp315; torch has no macOS Intel wheel | [transformers](https://pypi.org/pypi/transformers/json), [torch](https://pypi.org/pypi/torch/json) |
| OpenCV `cv2.dnn` (`opencv-python-headless`) | 5.0.0.93 | Apache-2.0 | Windows x86-64 43.8 MB, macOS arm64 48.3 MB, macOS Intel 34.8 MB, Linux x86-64 56.6-61.2 MB | abi3 (`cp37`) wheels: any CPython 3.7+, so 3.11-3.14 | [PyPI](https://pypi.org/pypi/opencv-python-headless/json) |
| ONNX Runtime, Python (`onnxruntime`) | 1.31.1 | MIT | Windows 14.9-15.3 MB, macOS arm64 20.9 MB, Linux x86-64 23.8 MB | cp311-cp314 on Windows, macOS arm64, Linux; no macOS Intel in the list | [PyPI](https://pypi.org/pypi/onnxruntime/json) |
| LiteRT (`ai-edge-litert`, TFLite's successor) | 2.3.0 | not stated on PyPI | Windows 20.7-21.4 MB, Linux x86-64 21.8 MB, macOS arm64 12.8 MB | cp310-cp314; no macOS Intel | [PyPI](https://pypi.org/pypi/ai-edge-litert/json) |
| Pyodide (for reference) | 314.0.7 | n/a | n/a | Has `opencv-python` 4.11.0.86, `scikit-learn` 1.8.0, `numpy` 2.4.6. Lacks `onnxruntime`, `mediapipe`, `tflite`, `torch` | [package list](https://pyodide.org/en/stable/usage/packages-in-pyodide.html) |

Privacy note: the PyPI page for `mediapipe` says MediaPipe Tasks "sends performance and usage metrics to Google"
([source](https://pypi.org/project/mediapipe/), as summarised by a tool; confirm by reading the page). A teaching library
for children should check this before adopting it.

### 1b. Provider by task

"Weights licence" is the licence of the model files, not of the library. Sizes are real file sizes (HTTP HEAD, or the Hugging Face API).
Model files: [MediaPipe bucket](https://storage.googleapis.com/mediapipe-models/), [OpenCV Zoo on Hugging Face](https://huggingface.co/opencv), [Xenova / onnx-community repos](https://huggingface.co/Xenova).

| Task | MediaPipe Tasks (web and Python) | ml5.js (web) | Transformers.js (web) | HF `transformers` (Python) | OpenCV `cv2.dnn` (Python) |
|---|---|---|---|---|---|
| **Body pose** | Yes. PoseLandmarker lite 5.8 MB, full 9.4 MB, heavy 30.7 MB (`.task`). 33 landmarks, 2D and 3D ([guide](https://developers.google.com/edge/mediapipe/solutions/vision/pose_landmarker)). Weights: Apache-2.0 ([BlazePose GHUM 3D card](https://storage.googleapis.com/mediapipe-assets/Model%20Card%20BlazePose%20GHUM%203D.pdf), read). | Yes (`bodyPose`, on tfjs pose-detection; model names and point counts unverified). Weights licences: unverified. | Weak. ViTPose exists (`onnx-community/ViTPose-base-simple`, 344 MB fp32, 87.5 MB int8, Apache-2.0 upstream) but needs a person box first; no ready pipeline seen. | ViTPose in `transformers` (`usyd-community/vitpose-plus-small`, 133 MB, Apache-2.0). Heavy. | Yes. OpenCV Zoo `pose_estimation_mediapipe` 5.6 MB (1.7 MB int8), Apache-2.0; same 33 points as MediaPipe, but needs a person-detection step (`MP-PersonDet`). |
| **Hands** | Yes. HandLandmarker 7.8 MB, 21 landmarks. Published, not measured: 17.1 ms CPU, 12.3 ms GPU (Pixel 6) ([guide](https://developers.google.com/edge/mediapipe/solutions/vision/hand_landmarker)). Weights licence: card not read (the links I tried returned HTML); unverified. | Yes (`handPose`). | No ready model seen (unverified). | No. | Yes. Zoo `handpose_estimation_mediapipe` 4.1 MB (1.2 MB int8), Apache-2.0; plus a palm detector. |
| **Face points** | Yes. FaceLandmarker 3.8 MB, 478 landmarks, 52 blendshapes; BlazeFace detector 0.23 MB ([guide](https://developers.google.com/edge/mediapipe/solutions/vision/face_landmarker)). Weights licence: three cards listed, not read; unverified. | Yes (`faceMesh`). | No ready model seen (unverified). | No. | Face detection only: YuNet 0.2 MB, MIT. No landmark mesh in the Zoo list ([Zoo](https://github.com/opencv/opencv_zoo)). |
| **Person outline (segmentation)** | Yes. SelfieSegmenter `selfie_segmenter.tflite` 0.25 MB (256 x 256; also a 144 x 256 landscape version), SelfieMulticlass 16.4 MB, DeepLab-V3 2.8 MB. Published, not measured: selfie 33.5 ms CPU / 35.2 ms GPU (Pixel 6) ([guide](https://developers.google.com/edge/mediapipe/solutions/vision/image_segmenter)). Weights: Apache-2.0 for selfie and multiclass (cards read: [selfie](https://storage.googleapis.com/mediapipe-assets/Model%20Card%20MediaPipe%20Selfie%20Segmentation.pdf), [multiclass](https://storage.googleapis.com/mediapipe-assets/Model%20Card%20Multiclass%20Segmentation.pdf)). | Yes (`bodySegmentation`; underlying model unverified). | Yes. `Xenova/modnet` (portrait matting) 25.9 MB, 6.6 MB q8, Apache-2.0 ([card](https://huggingface.co/Xenova/modnet)). Avoid: `briaai/RMBG-1.4` and `2.0` (Bria licence; 2.0 is CC BY-NC and 1 GB), `segformer` (NVIDIA, "other"), `mobilevit` (Apple, "other"). | Possible with the same models; heavy. | Yes. Zoo `human_segmentation_pphumanseg` 6.2 MB (1.6 MB int8), Apache-2.0. |
| **Objects in a picture** | Yes. ObjectDetector EfficientDet-Lite0 7.3 MB, Lite2 12.1 MB, COCO 80 classes. Published, not measured: Lite0 float16 54 ms CPU / 28 ms GPU (Pixel 6) ([guide](https://developers.google.com/edge/mediapipe/solutions/vision/object_detector)). Weights licence: the page does not state one; unverified. | Yes (`objectDetector`; COCO-SSD / YOLO, unverified). | Yes. `Xenova/yolos-tiny` 26 MB (9.7 MB q8), Apache-2.0 upstream (`hustvl/yolos-tiny`); `Xenova/detr-resnet-50` 167 MB (43 MB q8), Apache-2.0 upstream. | Same models, via torch. | Yes. Zoo YOLOX 35.9 MB (9.1 MB int8), NanoDet 3.8 MB (1.0 MB int8), both Apache-2.0. Excluded: `onnx-community/yolov10n` and Ultralytics (AGPL-3.0). |
| **Naming a picture** | Yes. ImageClassifier EfficientNet-Lite0 18.6 MB, Lite2 24.3 MB (ImageNet). Weights licence not stated; unverified. | Yes (`imageClassifier`, MobileNet). | Yes. `onnx-community/mobilenetv4_conv_small...` 15.1 MB (3.9 MB q8); the timm card says Apache-2.0. Larger: `vit-base-patch16-224` 346 MB (Apache-2.0 upstream). | Same, via torch. | Yes. Zoo MobileNet v1 16.9 MB (4.3 MB int8), v2 14.0 MB, Apache-2.0. |
| **Speech to words** | No. Tasks has audio classification and embedding, not speech recognition. | No (`soundClassifier` uses speech-commands: a few words, not free speech). | Yes. Whisper `onnx-community/whisper-tiny.en`: encoder 10.1 MB + merged decoder q8 30.7 MB, about 41 MB. Weights: MIT per the [OpenAI repo](https://github.com/openai/whisper); the Hugging Face card of `openai/whisper-tiny.en` says Apache-2.0. | Yes, `openai/whisper-tiny.en` 151 MB; needs torch. | No. |
| **Speech, desktop alternative** | -- | -- | -- | `faster-whisper` 1.2.1 (MIT) with CTranslate2 4.8.4 (MIT; wheels cp310-cp315: Windows 20.4 MB, Linux x86-64 42.4 MB, macOS arm64 1.5 MB, Intel 12.2 MB; [PyPI](https://pypi.org/pypi/ctranslate2/json)); model `Systran/faster-whisper-tiny.en` 75.5 MB (MIT), `base.en` 145 MB. It also needs `onnxruntime`, `av`, `tokenizers`. Or `vosk` 0.3.45 (`py3-none`, 14 MB on Windows; licence and models unverified). | -- |
| **Sounds** | Yes. AudioClassifier YAMNet 4.1 MB (AudioSet). Web and Python. Published, not measured: 12.3 ms CPU (Pixel 6) ([guide](https://developers.google.com/edge/mediapipe/solutions/audio/audio_classifier)). Weights licence not stated; unverified. | Yes (`soundClassifier`, speech-commands). | Yes. `Xenova/ast-finetuned-audioset-10-10-0.4593` 347 MB (90.8 MB q8), BSD-3-Clause upstream. Heavy. | Same, via torch. | No. |
| **A model the learner trains (Teachable Machine style)** | Partial. ImageEmbedder (`mobilenet_v3_small` 4.1 MB) and AudioEmbedder (Python, added in 1.1.0; [releases](https://github.com/google-ai-edge/mediapipe/releases)) give vectors. The kNN or small head over those vectors is funground's own code (a few lines of plain Python). Embedder weights licence: unverified. | Yes. `neuralNetwork` trains in the browser on tfjs (web only). | Yes. The `image-feature-extraction` pipeline gives embeddings ([docs](https://huggingface.co/docs/transformers.js/index)); the kNN is ours. A small CLIP is 154 MB q8 / 606 MB fp32: too big. MobileNetV4 (3.9 MB q8) is the right size. | Possible, heavy. | Embeddings from a Zoo MobileNet, then kNN (our code). |

ONNX Runtime is the carrier under Transformers.js (web) and can run the OpenCV Zoo `.onnx` files in Python; I did not find
a reason to add it as a third engine beside OpenCV.

Speed. The only published figures are the Pixel 6 numbers above (marked "published, not measured") and the BlazePose model
card, which quotes about 40 and 49 FPS via TFLite GPU on a Pixel phone (which variant is which is unclear). I found no
published frames per second for Transformers.js, ml5.js or OpenCV `dnn` on a laptop CPU. Phone figures say little about
this machine or headless Chrome.

Does it run in a worker (web)?
- MediaPipe Tasks: yes, in a module worker since 0.10.35 (April 2026). Before that the bundle called `importScripts()`,
  which module workers forbid. The maintainer closed three issues as fixed and pointed to worker samples in
  `mediapipe-samples-web` ([#5257](https://github.com/google-ai-edge/mediapipe/issues/5257),
  [#5479](https://github.com/google-ai-edge/mediapipe/issues/5479),
  [#5527](https://github.com/google-ai-edge/mediapipe/issues/5527)). I read these through a summarising tool, not the
  full threads. Whether the GPU delegate works in a worker (needs OffscreenCanvas WebGL) is unverified; plan on CPU
  first.
- Transformers.js: yes, its own tutorial runs the pipeline in a module `Worker`. WebGPU inside a worker: unverified.
- ml5.js: built for the main page (p5-style); worker use unverified.

## 2. The Pyodide route

### How camera frames reach a sketch today

- The sketch calls `cam.start()`. Python calls a host callback; the worker posts `camera {command:"start", fields:{width,height}}`
  to the page (`worker.js:400-403`, `postCameraRequest`; protocol at `worker.js:30-31`).
- The page owns the device because a worker cannot open the camera (`camera.js:3`). `command()` records the wanted size
  and opens it (`camera.js:28-36`). `open()` calls `getUserMedia` and plays a hidden `<video>` (`camera.js:38-55`).
  `requestVideoFrameCallback` sets a `fresh` flag (`camera.js:58-66`).
- Before each step, `runner.js:215-221` (`tick`) calls `camera.sendFrame()` then posts `step`. One step is in flight at
  most, so "a slow sketch drops display frames, never queues them".
- `sendFrame()` draws the newest video frame into an OffscreenCanvas, reads the RGBA pixels and posts them, transferring
  the buffer (`camera.js:69-81`; the `postMessage` is `runner.js:61-65`). A frame is sent only when there is a new one.
- In the worker, the `camera` message handler calls `push_camera` (`worker.js:284-286`, `220-222`), which hands the bytes
  to `Session.push_camera` (`funground/web.py:199`). Python keeps only the latest frame.
- The Python side never waits. `camera_input.py:15-17`: "A Camera never waits for a device. Before each `draw()` the
  sketch calls `take_frames()`" (defined at `camera_input.py:119`), which reads each started camera once; the frame stays
  until the next draw. The web device is plugged in with `use_host_camera` (`camera_input.py:48-52`).
- So the whole route is: command out (asynchronous, to the page), data in (asynchronous message, latest wins), Python
  reads a plain attribute each frame. No `async` in the sketch. The microphone works the same way
  (`worker.js:53-54, 280-282`).

### Options for a model result

| Route | How it works | Costs and risks |
|---|---|---|
| **A. Model in the page or a second worker; results posted; Python reads the latest (recommended starting point)** | Add a "model" message pair like the camera's: Python asks `model {command:"start", task:"pose"}`; the page starts a model worker (MediaPipe or Transformers.js); the page already has frames (or could send the `<video>` as an `ImageBitmap`, unverified) and posts the result `{task, time, points}` to the Pyodide worker; Python's `ml` library keeps the latest result and `f.pose()` returns it, as `cam.picture()` does. | The result is 1-3 frames old (say so in the docs). Inference never blocks `draw()`, so a slow machine slows the model, not the sketch. Works for async-only Transformers.js. Needs a new message type in `worker.js` and `runner.js` and a `models.js` beside `camera.js`. On the desktop the same call runs in a thread or inline; the sketch is identical. |
| **B. MediaPipe in the same worker as Pyodide** | Possible since 0.10.35 (module worker). MediaPipe has IMAGE, VIDEO and LIVE_STREAM modes; LIVE_STREAM uses a callback ([options](https://developers.google.com/edge/mediapipe/solutions/vision/image_segmenter)). I did not confirm that the IMAGE and VIDEO calls are synchronous in JS: unverified. Python could call it through Pyodide's JS bridge inside `draw()`. | A 15 MB wasm and the model share the worker's memory with Pyodide and Cairo (a risk on a low-memory machine). Each inference blocks the frame (tens of ms on a phone CPU; unknown here). Not usable for Transformers.js (promises only). Frame pixels must still reach the worker (the existing route does that). |
| **C. `SharedArrayBuffer` and `Atomics`** | The page writes frames and results into shared memory; the worker reads without copying, and may block with `Atomics.wait`. | Needs cross-origin isolation (COOP/COEP headers) ([MDN](https://developer.mozilla.org/en-US/docs/Web/API/SharedArrayBuffer), not fetched in this session). I found no such headers in the `funground-web` runner (searched; only `vscode-extension/serve.py` matched "Cross-Origin"). That changes how Play can be embedded. Not needed for latest-result semantics. Not recommended now. |
| **D. Block on a promise with `pyodide.ffi.run_sync` / JSPI** | Library code (not learner code) blocks until a JS promise resolves, so the sketch stays synchronous. | Browser support beyond Chromium: unverified. Blocks the frame like B. Learner code is unchanged, but the browser matrix is a risk. |
| **E. Synchronous XHR to a service worker that runs the model** | `worker.js` already uses synchronous `XMLHttpRequest` for fonts and URLs (`worker.js:100-123`). | A hack for inference; blocks the frame; hard to test. Rejected on clean-code grounds. |

Answers to the specific questions:
- Can MediaPipe run in the same worker as Pyodide? Yes in principle (module worker since 0.10.35), at a memory and
  frame-time cost (route B).
- Can Transformers.js? It can run in a module worker, but its calls return promises, so synchronous Python cannot call
  it without route D. Use route A.
- Model packages inside Pyodide: not available (`mediapipe`, `onnxruntime`, `torch` are missing). So there is one model
  engine per platform: the JS one in Play, the Python one on the desktop. The sketch and the names stay the same.
- Frame cost: `getImageData` copies the pixels once per frame (`camera.js:80`) and `to_bytes()` copies again
  (`worker.js:222`). A model worker fed from the page avoids the second copy.
- A model download is a new first-load cost: a 15 MB wasm plus 4-30 MB per MediaPipe model. Play already fetches fonts
  "on open" (`worker.js:21`) and loads packages only when a sketch needs them (`ON_DEMAND`, `worker.js:69-70`), so the
  pattern exists.

## 3. Shortlist

Judged on: licence fit with an LGPL library's teaching examples (Apache-2.0, MIT, BSD are fine; AGPL, non-commercial
and custom "other" are excluded), size, platform coverage, and the same named points on both platforms.

| Task | Web | Desktop | Why, and what to watch |
|---|---|---|---|
| Body pose | MediaPipe Tasks PoseLandmarker lite (5.8 MB) | MediaPipe Python PoseLandmarker lite; fallback OpenCV Zoo MP-Pose 5.6 MB | 33 landmarks on both: one API. Apache-2.0 weights confirmed. Desktop risk: the install pulls `opencv-contrib-python` and `matplotlib`, and there is no Intel Mac wheel. The OpenCV fallback uses the same 33 points and a smaller install, but needs a person detector first. |
| Hands | MediaPipe HandLandmarker (7.8 MB) | MediaPipe Python; fallback OpenCV Zoo MP-HandPose | 21 points on both. Weights licence unverified: read the hand card first. |
| Face points | MediaPipe FaceLandmarker (3.8 MB) | MediaPipe Python | 478 points and 52 blendshapes on both. Weights licence unverified. OpenCV has no face mesh. |
| Person outline | MediaPipe SelfieSegmenter (0.25 MB) | MediaPipe Python SelfieSegmenter | Tiny, Apache-2.0, the same model both sides. Alternatives: PP-HumanSeg (OpenCV, 6.2 MB), MODNet (Transformers.js, 6.6 MB q8, Apache-2.0). |
| Objects | MediaPipe EfficientDet-Lite0 (7.3 MB) | MediaPipe Python | Same model, 80 COCO names on both. Weights licence not stated: check. Not YOLO via Ultralytics or `yolov10n` (AGPL). Fallback: YOLOX / NanoDet (OpenCV Zoo, Apache-2.0) or `yolos-tiny` (Transformers.js). |
| Naming a picture | MediaPipe ImageClassifier EfficientNet-Lite0 (18.6 MB) | MediaPipe Python | Same model, same labels on both. |
| Speech to words | Transformers.js Whisper tiny.en (about 41 MB q8) | `faster-whisper` tiny.en (75 MB model, MIT) | The only task with different engines, but the same Whisper weights (MIT per OpenAI, Apache-2.0 per the Hugging Face card). Web needs about 55-70 MB in total including the wasm. Desktop avoids torch. Speed on this machine is the question. |
| Sounds | MediaPipe AudioClassifier YAMNet (4.1 MB) | MediaPipe Python | Same model both sides. Weights licence not stated. |
| Learner-trained classifier | MediaPipe ImageEmbedder (4.1 MB) plus funground's own kNN | the same | Teachable Machine's recipe. The kNN is about 20 lines of plain Python, identical on both platforms. Avoids ml5's licence and tfjs size. Embedder weights licence unverified. |

If this holds, one provider (MediaPipe) covers 7 of the 9 tasks with matching names on both platforms (speech differs by
engine, and the learner-trained classifier is MediaPipe embeddings plus our own kNN). ml5.js is not on the shortlist: web
only, a heavy dependency list that includes the legacy `@mediapipe/*` solutions, and a custom licence with a Code of
Conduct condition.

## 4. What to measure next on this machine (Windows, low memory, slow)

One at a time, each in its own throwaway folder or venv (not the project's `.venv`). Sizes are download sizes from the
indexes above; transitive installs I could not size are marked.

| # | Measurement | Install and download | Size note |
|---|---|---|---|
| 1 | Web MediaPipe pose, hands, face, selfie segmentation, object detection: frames per second at 640 x 480 in headless Chrome, first-load time, in a module worker. | Nothing to install: load `@mediapipe/tasks-vision@1.2.0` and the `.task` files from the CDN, as `worker.js` loads Pyodide (`worker.js:56`). | 15 MB runtime + 5.8 / 7.8 / 3.8 / 0.25 / 7.3 MB models; about 40 MB total |
| 2 | Python MediaPipe 1.2.0: the same tasks, fps, install on Python 3.14 (and 3.11 if available), memory. | `mediapipe==1.2.0` 24.5 MB + `opencv-contrib-python` 54 MB + `matplotlib` (about 8 MB plus Pillow, kiwisolver, contourpy, fonttools, cycler, pyparsing; unverified) + `numpy` + `sounddevice` | roughly 100-150 MB (estimate) |
| 3 | OpenCV `cv2.dnn` with Zoo ONNX: pose (plus person detector), hands, PP-HumanSeg, YOLOX / NanoDet, MobileNet. | `opencv-python-headless` 43.8 MB + models 1-36 MB each | under 150 MB |
| 4 | Web Whisper tiny.en via Transformers.js, then MODNet and `yolos-tiny`. | CDN or npm `@huggingface/transformers` 10 MB; ORT wasm 14.8-29.5 MB; Whisper about 41 MB; MODNet 6.6 MB; yolos-tiny 9.7 MB | under 120 MB |
| 5 | Desktop `faster-whisper` tiny.en and base.en: real-time factor on this CPU. | `faster-whisper` + `ctranslate2` 20.4 MB + `onnxruntime` 15 MB + `av` (unsized) + model 75.5 / 145 MB | under 300 MB |
| 6 | The result route (section 2, route A) in a 30-line pose sketch on the desktop and in Play. | no new installs | |
| 7 | Whether MediaPipe in the same worker as Pyodide (route B) fits in memory, and what it does to the frame time. | no new installs | |
| 8 | Teachable-Machine style kNN over ImageEmbedder vectors. | model 4.1 MB | |

Over about 500 MB, do not measure without the maintainer's say-so:
- `torch` on Linux: 539 MB wheel plus NVIDIA CUDA wheels (several GB). `transformers` and `openai-whisper` pull it in.
  Windows torch is 127 MB but the installed size is larger (unverified).
- `onnx-community/ViTPose-base-simple` fp32 344 MB (under 500 MB, but heavy); `Xenova/clip-vit-base-patch32` fp32 606 MB;
  `briaai/RMBG-2.0` 1 GB (and non-commercial); `ast-finetuned-audioset` fp32 347 MB.
- Excluded for licence: `ultralytics` (AGPL-3.0), `yolov10n` (AGPL-3.0), Bria RMBG, SegFormer, MobileViT.

Checks that need no install and should come first:
- Read the hand, face and ImageEmbedder model cards. The `mediapipe.page.link` card links I tried returned HTML, not the
  cards, so use the links on the Tasks pages.
- Confirm the telemetry sentence on the MediaPipe PyPI page, and whether it can be turned off.
- Confirm that the `mediapipe` 1.2.0 `py3-none` wheels import on Python 3.14.
- Confirm that MediaPipe's VIDEO mode is synchronous in JS.

## 5. Would a person-outline model beat `remove_background`?

Context (`spikes/14_cutout/README.md`): the colour-based cut-out leaves specks (room bits that look like you) and holes
(you bits that look like the room), and has trouble with clothes near the wall's colour. The spike's tidy step ("keep the
biggest part, fill the gaps") can pick the wrong part.

Likely yes for the failures that colour cannot fix, likely no for edge sharpness. This is a hypothesis to measure.
- A learned person model does not care about wall-coloured clothes, stripes or a change of light, because it finds people
  by shape and texture, not by colour distance. That removes specks and holes at the source.
- Its mask is coarse: SelfieSegmenter works at 256 x 256 (or 144 x 256) with a soft edge
  ([model list](https://developers.google.com/edge/mediapipe/solutions/vision/image_segmenter)). Upscaled to 640 x 480,
  the edge will be blurrier than a clean colour key against a known background. MODNet (matting, 25.9 MB fp32) gives a
  finer alpha at more cost.
- It can fail the other way: a person partly out of frame, several people, a held object that gets dropped.
- The best use may be as a guide to the existing method, for example to choose the part to keep (`at=`) or to tidy the
  colour mask. That is a design choice for the main session.
- To measure: run the three synthetic scenes plus a few real photos through SelfieSegmenter and compare the overlap with
  the truth masks, as `measure.py` does. The spike's scenes are drawn figures, not real people (its README says so), so a
  model trained on photos needs real photos too.
