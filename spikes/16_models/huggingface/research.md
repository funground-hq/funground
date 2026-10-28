# S-231 desk research: Hugging Face as the model provider

Desk research only, 28 October 2026. Nothing was installed. No model over 20 MB was downloaded. No browser was started.
What I did fetch: PyPI and npm JSON, the Hugging Face model API (file sizes and licence fields), model cards as text, the
`@huggingface/transformers` 4.3.2 npm tarball (2.2 MB, read as source in the scratchpad), and a few `HEAD` requests.
"Unverified" means I could not confirm it. "Estimate" means my own guess, not a measurement.

Read first: `../README.md`, `../research.md`, `../web/results.md`, `../desktop/results.md`, `../opencv/results.md`.

## Headline findings

1. **The smallest Python route is plain `onnxruntime`, and it is small: about 29 MB to download on Windows** (ORT wheel
   15.3 MB for Python 3.14, numpy about 12.7 MB, three tiny packages). `torch` is 127 MB (Windows) to 539 MB (Linux, plus
   CUDA wheels). `optimum` needs torch. So torch is never needed to *run* an ONNX file.
2. **But official `onnxruntime` wheels send telemetry by default.** Since 1.30 the ORT privacy page says official builds on
   Windows, Linux and macOS send trace events to Microsoft over HTTPS (the "1DS" SDK). It can be switched off with the
   environment variable `ORT_DISABLE_TELEMETRY=1`, set before ORT starts. Transformers.js does this itself in Node. The
   browser build (WebAssembly) has no telemetry. Whether the 1.31.1 wheel really does this is **not yet measured**. It is
   the first measurement in the plan. This is the same kind of finding as MediaPipe's logger, but ORT has a documented off
   switch.
3. **Transformers.js 4.3.2 has no pose, hand or face-point pipeline.** It has image classification, feature extraction,
   object detection, segmentation, background removal, speech to words and audio classification. For pose and hands the web
   side would use `onnxruntime-web` directly and funground would own the pre- and post-processing.
4. **A shared ONNX file is realistic for these:** selfie outline (0.2 to 0.5 MB), MoveNet (2.8 MB), the OpenCV Zoo
   MediaPipe pose, hand and palm models, objects (D-FINE nano, 4.5 MB), naming a picture (MobileNetV4, 3.9 MB), Whisper. The
   price is a second copy of the glue code, in JavaScript, for every two-stage pipeline.
5. **Hugging Face has nothing first-class for hands, face mesh or 33-point pose.** Only community conversions of Google's and
   OpenCV's models (provenance unverified). MediaPipe (web) and the OpenCV Zoo (desktop) still win those. Hugging Face wins
   speech, objects, naming and embeddings, because MediaPipe is weak or absent there.
6. **Plain HTTPS from funground is enough.** `huggingface_hub` is not needed to fetch a model. Telemetry is a separate thing
   that `huggingface_hub` does, and it can be switched off. Better still, mirror the pinned files on our own host.

## 1. Desktop without torch: three routes, sizes, Python 3.11 to 3.14

Sizes are wheel sizes from the PyPI JSON files (download size, not installed size; installed size not measured).
Files fetched 28 Oct 2026.

### Route A: `onnxruntime` and ONNX files fetched by funground

| Package | Version | Python | Windows x64 | macOS arm64 | Linux x86-64 | Notes |
|---|---|---|---|---|---|---|
| onnxruntime | 1.31.1 (MIT) | >=3.11 | 14.9 MB (cp311-313), 15.3 MB (cp314) | 20.9 MB | 23.8 MB | Also Windows ARM64 14.7/15.2 MB, Linux aarch64 21.4 MB. cp314 wheels exist on all of them (and cp313t/cp314t free-threaded on Linux). **No Intel Mac wheel** in 1.31.1. The last release with an Intel Mac wheel I saw is 1.23.2 (cp313; cp314 not checked). |
| numpy | 2.5.4 | | about 12.7 MB (from `../opencv/results.md`) | not checked | not checked | |
| flatbuffers, packaging, protobuf | | | under 1 MB each | | | `onnxruntime` 1.31.1 requires exactly: flatbuffers, numpy>=1.21.6, packaging, protobuf>=4.25.8. `sympy` is only for an extra, so it is not pulled in. |

Total on Windows: about 29 MB to download. This is smaller than OpenCV (44 MB wheel, 180 MB venv in the OpenCV step) and
far smaller than MediaPipe (358 MB). Installed size: not measured (plan item 1).
Sources: [onnxruntime on PyPI](https://pypi.org/pypi/onnxruntime/json), [sympy/protobuf/flatbuffers JSON](https://pypi.org/pypi/protobuf/json).

### Route B: `optimum[onnxruntime]`

`optimum` 2.3.0 lists `torch>=1.11` and `transformers>=4.29` as hard requirements ([PyPI](https://pypi.org/pypi/optimum/json)).
`optimum-onnx` 0.1.0 adds `onnx`, pins `optimum~=2.1.0` and `transformers<4.58` ([PyPI](https://pypi.org/pypi/optimum-onnx/json)).
So this route is Route C plus ONNX Runtime plus `onnx`. It is an export tool, not a light runtime. **Do not use it to run
models.** Only useful on a developer machine, if funground ever exports its own ONNX files.

### Route C: `transformers` and torch

| Package | Version | Windows | macOS arm64 | Linux x86-64 | Notes |
|---|---|---|---|---|---|
| transformers | 5.21.0 (Apache-2.0) | 13.0 MB (py3-none) | same | same | Python >=3.11 |
| huggingface_hub | 2.3.0 | 0.9 MB | same | same | needs `httpx2`, `hf-xet`, `fsspec`, `tqdm`, `pyyaml`, `click` |
| tokenizers | 0.23.3 | 2.9 MB (abi3, cp310+) | 3.1 MB | 3.4 MB | |
| safetensors | 0.8.0 | 0.4 MB (abi3) | 0.5 MB | 0.5 MB | |
| hf-xet | 1.7.1 | 3.8 MB | 3.6 MB | 4.2 MB | abi3 and cp314t wheels |
| torch | 2.15.0 | 126.7 MB | 138.6 MB | 539.2 MB | cp311 to cp315 wheels, so 3.14 works. Linux also requires `cuda-toolkit`, `nvidia-cudnn-cu13`, `triton`, NCCL and more (several GB; sizes unverified). Linux aarch64 483.7 MB. No Intel Mac wheel. |

Windows download is roughly 165 MB (estimate: torch 127 + transformers 13 + the rest). Linux is over 540 MB and about
several GB with CUDA. Sources: [transformers](https://pypi.org/pypi/transformers/json), [torch](https://pypi.org/pypi/torch/json),
[tokenizers](https://pypi.org/pypi/tokenizers/json), [hf-xet](https://pypi.org/pypi/hf-xet/json), [safetensors](https://pypi.org/pypi/safetensors/json).

### Verdict

Route A. Wheels exist for Python 3.14 on Windows, macOS arm64 and Linux. Gaps: Intel Macs (no wheel for 1.31.1, none for
torch either), and the telemetry default (section 4). The OpenCV route stays as the fallback because it is already measured
and sends nothing, but it costs about 150 MB more.

## 2. Web: Transformers.js

Current version `@huggingface/transformers` **4.3.2**, Apache-2.0, 10 MB package ([npm](https://registry.npmjs.org/@huggingface/transformers/4.3.2)).

- **Runtime.** It depends on `onnxruntime-web` pinned to the development build `1.31.0-dev.20260914-8d85527a0` (same npm
  record). Its wasm files, from the [jsDelivr file list](https://data.jsdelivr.com/v1/packages/npm/onnxruntime-web@1.31.0-dev.20260914-8d85527a0):
  plain CPU `ort-wasm-simd-threaded.wasm` **14.3 MB**; JSPI 16.8 MB; asyncify 26.9 MB; WebGPU "jsep" **28.4 MB**.
  Each has a small `.mjs` loader (0.02 to 0.05 MB). The library itself is 0.46 MB minified (`transformers.web.min.js`, 456 KB).
  Compressed size on the wire: not measured (MediaPipe's 14.5 MB wasm was 3.25 MB brotli on the wire, so expect a similar ratio).
  Which wasm file is chosen for a given device: unverified.
- **Where the wasm comes from.** By default Transformers.js points ORT at `https://cdn.jsdelivr.net/npm/onnxruntime-web@<version>/dist/`
  (read in `src/backends/onnx.js` of the tarball). It can be overridden with `env.backends.onnx.wasm.wasmPaths`, and it
  can cache the wasm for offline use (`env.useWasmCache`, default true when a cache exists)
  ([env docs](https://huggingface.co/docs/transformers.js/api/env)).
- **Module Web Worker.** Yes, by the project's own tutorial, which runs the pipeline in a module `Worker`
  ([React tutorial](https://huggingface.co/docs/transformers.js/tutorials/react)). I did not run it. The MediaPipe step
  showed the *worker side* is the fiddly part (the module build of the loader), so measure it (plan item 4).
- **WebGPU.** Yes: pass `device: "webgpu"` ([guide](https://huggingface.co/docs/transformers.js/guides/webgpu)). Chrome, Edge
  and recent Safari and Firefox on some platforms (browser matrix: unverified here; `../research.md` quoted about 85% in March 2026).
  It needs the 28.4 MB wasm. WebGPU in a worker: unverified.
- **Pipelines in 4.3.2** (file names in `src/pipelines/` of the tarball): audio-classification, automatic-speech-recognition,
  background-removal, depth-estimation, document-question-answering, feature-extraction, fill-mask, image-classification,
  image-feature-extraction, image-segmentation, image-to-image, image-to-text, object-detection, question-answering,
  summarization, text-classification, text-generation, text-to-audio, text2text-generation, token-classification,
  translation, and the zero-shot variants. **No pose, hand or face-point pipeline.** ViTPose exists only as a model class
  (`src/models/vitpose/`), without a pipeline.

## 3. Per task: best Hub model that runs through ONNX on both platforms

Sizes are the real file sizes from the Hub API (`?blobs=true`), 28 Oct 2026. "q8" is the `model_quantized`/`int8` file.
Licence: "card" = the model card or API licence field; "upstream" = the card of the original model; many `onnx-community`
repos have **no licence field**, so the upstream one counts, and I mark it. Library code is Transformers.js (Apache-2.0)
or onnxruntime (MIT) in every case. The Zoo is Apache-2.0 ([LICENSE](https://raw.githubusercontent.com/opencv/opencv_zoo/main/LICENSE)).

| Task | Best Hub-or-Zoo choice | Size (fp32 / q8) | Weights licence | Transformers.js pipeline? | Verdict against MediaPipe or OpenCV |
|---|---|---|---|---|---|
| **Person outline** | [`onnx-community/mediapipe_selfie_segmentation`](https://huggingface.co/onnx-community/mediapipe_selfie_segmentation) (Google's own model as ONNX). Also `Xenova/modnet` for finer edges | 0.5 MB / 0.2 MB. MODNet 25.9 / 6.6 MB | Apache-2.0 (card). MODNet Apache-2.0 (card; its training-data terms unverified) | The card uses `AutoModel` + `AutoProcessor`, not `pipeline()`. A `background-removal` pipeline exists and suits MODNet (unverified together) | **Hub wins or ties.** Same model as MediaPipe, 0.2 MB, trivial glue. Best first test of the shared-file idea |
| **Body pose** | Single stage: [`Xenova/movenet-singlepose-lightning`](https://huggingface.co/Xenova/movenet-singlepose-lightning), 17 COCO points. Two stage, 33 points: OpenCV Zoo MediaPipe pose 5.6 MB / 1.7 MB ([HF mirror](https://huggingface.co/opencv/pose_estimation_mediapipe)) with person detector 12.0 / 3.5 MB. Community port of Google's full model: [`fernandotonon/QtMeshEditor-poselandmarks-onnx`](https://huggingface.co/fernandotonon/QtMeshEditor-poselandmarks-onnx) 12.8 MB + detector 11.9 MB | MoveNet 9.4 / 2.8 MB (fp16 4.8) | MoveNet Apache-2.0 (card). Zoo Apache-2.0. QtMeshEditor port: Apache-2.0 (card, says "direct conversion of Google's model"; the converter is not ours to trust yet) | **None** | **MediaPipe (web) and the Zoo (desktop) still win** for 33 named points. MoveNet is the cheap single-stage option with 17 points. See section 5 |
| | RTMPose (OpenMMLab, ONNX in zips on `download.openmmlab.com`, not on the Hub): body7 tiny 12.5 MB, small 20.5 MB, medium 50.8 MB zips; YOLOX-tiny person box 18.9 MB zip; whole-body RTMW-m 58.1 MB zip (133 points) | see left | MMPose code Apache-2.0 ([LICENSE](https://raw.githubusercontent.com/open-mmlab/mmpose/main/LICENSE)). Weights: the Hub copies say Apache-2.0 (card); training-data terms (Body7, Cocktail14) unverified | None | Top-down: needs a person box first, then a very simple decode. 17 body points (133 for RTMW). RTMW hand AP is low in its own table (0.49 for m; [card](https://huggingface.co/akore/rtmw-l-256x192)). Hub ONNX copies of RTMW (`bukuroo/RTMW-ONNX`, 62 MB for m) are an individual's upload with no card: provenance unverified |
| | ViTPose small ONNX: [`onnx-community/vitpose-plus-small-ONNX`](https://huggingface.co/onnx-community/vitpose-plus-small-ONNX) | 132.9 / 42.1 MB | upstream `usyd-community/vitpose-plus-small` Apache-2.0 (card); the ONNX repo has no licence field | Model class only | **Too big and needs a person box.** Not a candidate |
| | YOLO-pose (`Xenova/yolov8n-pose`, `onnx-community/yolo26n-pose-ONNX` 12.1 / 3.5 MB) | | **AGPL-3.0** (Ultralytics; `Xenova/yolov8*-pose` tagged agpl-3.0; the YOLO26 ONNX repo has no licence field, and a YOLO26-pose repo from another uploader is tagged agpl-3.0) | | **Excluded.** AGPL is not usable with an LGPL library for learners |
| **Hands** | OpenCV Zoo palm 3.9 MB + hand 4.1 MB ([HF mirrors](https://huggingface.co/opencv/handpose_estimation_mediapipe)); RTMPose-m hand5 51 MB zip | 3.9 + 4.1 / 1.2 + 1.2 MB (int8) | Zoo Apache-2.0 | None | **Hugging Face has nothing native.** I found no `onnx-community` or `Xenova` hand-landmark model. MediaPipe wins on web, Zoo on desktop. A shared file means using the Zoo files in `onnxruntime-web` too |
| **Face points** | Community ports of MediaPipe's face mesh: `fernandotonon/QtMeshEditor-facemesh-onnx` 4.9 MB (Apache-2.0 card), `astaileyyoung/FaceMeshONNX` 5.1 MB (MIT card, provenance unverified). Needs a face detector first (YuNet 0.2 MB, MIT) | 4.9-5.1 MB | Google's face-mesh weights licence: unverified (cards not read in `../research.md` either) | None | **Hugging Face has nothing first-class.** MediaPipe web (478 points) remains the only good source; the desktop has no safe 478-point model that sends nothing yet. Community ports are the only route to test |
| **Objects** | [`onnx-community/dfine_n_coco-ONNX`](https://huggingface.co/onnx-community/dfine_n_coco-ONNX) (D-FINE nano, COCO 80 classes, no NMS step). Alternatives: `Xenova/yolos-tiny` (26.2 / 9.7 MB), `onnx-community/rtdetr_r18vd` (82.6 / 21.7 MB), Zoo NanoDet/YOLOX | D-FINE n: 15.3 / **4.5 MB** | Upstream `ustc-community/dfine-nano-coco` Apache-2.0 (API); the ONNX repo has no licence field. YOLOS-tiny Apache-2.0 (upstream card) | **Yes, `object-detection`** (the repos are tagged for it; D-FINE specifically: unverified) | **Hub wins or ties.** MediaPipe's EfficientDet-Lite0 gave a suspect result in the web step. Speed unknown |
| **Naming a picture** | [`onnx-community/mobilenetv4_conv_small.e2400_r224_in1k`](https://huggingface.co/onnx-community/mobilenetv4_conv_small.e2400_r224_in1k) (ImageNet 1000) | 15.1 / **3.9 MB** | Apache-2.0 (upstream `timm/` card) | **Yes, `image-classification`** | **Hub wins on size** (MediaPipe's EfficientNet-Lite0 is 18.6 MB). Accuracy not compared |
| **Image embeddings (learner kNN)** | [`onnx-community/dinov2-small`](https://huggingface.co/onnx-community/dinov2-small) (384 numbers per picture); or MobileNetV4's output used as a vector | 88.5 / 24.4 MB | Apache-2.0 (upstream `facebook/dinov2-small` card) | **Yes, `image-feature-extraction`** | **Hub fine.** DINOv2-S is much slower than MobileNet (estimate: about 20 times the arithmetic; unmeasured). The kNN is funground's own few lines |
| **Speech to words** | `onnx-community/whisper-tiny.en` / `Xenova/whisper-tiny.en`; base: `onnx-community/whisper-base.en` | tiny.en: encoder 32.9 + merged decoder 118.6 = 151 MB fp32; **q8 10.1 + 30.7 = 40.8 MB**. base.en q8 23.2 + 53.7 = **76.9 MB** | Apache-2.0 (card of `openai/whisper-tiny.en`); the OpenAI repo says MIT (read in `../research.md`) | **Yes, `automatic-speech-recognition`** | **Hub wins** (MediaPipe has no speech to text). Desktop needs a decoding loop on ORT, or `faster-whisper` (not ORT; see `../research.md`) |
| **Sounds** | Hub: `Xenova/ast-finetuned-audioset-10-10-0.4593` / `onnx-community/...-ONNX` (527 classes). Community YAMNet ONNX: `zeropointnine/yamnet-onnx`, `audiomagic/yamnet-onnx` 16.1 MB | AST 346.8 / **90.6 MB**; YAMNet 16.1 MB | AST BSD-3-Clause (upstream card). YAMNet repos Apache-2.0 (card), uploaders unknown, input form (raw audio or mel patches) unknown | AST: **yes, `audio-classification`** | **MediaPipe's AudioClassifier (YAMNet, 4.1 MB, both platforms) wins** on size. AST is 22 times larger. Desktop telemetry caveat applies to MediaPipe's Python package |

Other licence flags found while searching: `STMicroelectronics/movenet` ("other"), `litert-community/PANNs-CNN14-AudioSet-LiteRT` (CC BY 4.0, a data licence),
`hugocornellier/*-face-landmarks` (CC BY-NC 4.0, animals), Bria RMBG (non-commercial, from `../research.md`). Sources for the numbers above:
Hub API (`https://huggingface.co/api/models/<repo>?blobs=true`) for each repo named, and the model cards linked.

Where Hugging Face has nothing good, plainly:
- **Hands and face mesh:** no first-party or well-used ONNX. Only conversions of Google or OpenCV models by individuals.
- **33-point pose:** same.
- **Small sound models:** the ONNX audio models on the Hub are large (AST) or unvetted (YAMNet).
- **Real-time pose with a ready pipeline in the browser:** none. MediaPipe Tasks (web) is easier and was measured at 11 to 42 results per second.

## 4. Telemetry and network

### `huggingface_hub` and `transformers` (Python)

- **What is sent.** `send_telemetry()` queues a background thread that makes a `HEAD` request to
  `{ENDPOINT}/api/telemetry/{topic}` (default `https://huggingface.co`). The topic, library name and version, and a user-agent
  string go with it ([source `_telemetry.py`](https://raw.githubusercontent.com/huggingface/huggingface_hub/main/src/huggingface_hub/utils/_telemetry.py)).
  Libraries choose the topic (for example, `transformers`' example scripts).
- **User-agent on every Hub request.** With telemetry on, the string is `library/version; hf_hub/<ver>; python/<ver>`, plus
  the **torch version** and, when detected, the name of an AI coding agent (`agent/...`) ([`_headers.py`](https://raw.githubusercontent.com/huggingface/huggingface_hub/main/src/huggingface_hub/utils/_headers.py)).
  `transformers` adds a per-process `session_id` ([`hub.py`](https://raw.githubusercontent.com/huggingface/transformers/main/src/transformers/utils/hub.py)).
  With telemetry off, `transformers` adds `telemetry/off` and the torch/agent parts are dropped. The library name and versions of
  `hf_hub` and Python stay in the user-agent either way (read in `_http_user_agent`). And of course any download tells
  `huggingface.co` the IP address and the file.
- **Switches.** `HF_HUB_DISABLE_TELEMETRY=1`, or `DO_NOT_TRACK=1`, disables telemetry for the whole Hugging Face Python
  ecosystem; `HF_HUB_OFFLINE=1` also disables it and blocks all calls ([environment variables](https://huggingface.co/docs/huggingface_hub/package_reference/environment_variables),
  [utilities, Telemetry](https://huggingface.co/docs/huggingface_hub/main/en/package_reference/utilities)).
  Variables are read when `huggingface_hub` is imported, so set them first. `HF_HUB_DISABLE_UPDATE_CHECK=1` stops the `hf` command line
  tool asking PyPI for updates (that only concerns the CLI).
- **Not measured:** the real traffic of a `hf_hub_download` call with and without the switch. It is in the plan.

### `onnxruntime` alone, with models fetched by funground

- `onnxruntime` itself makes no model download. **But official builds carry telemetry.** The ORT privacy page (on `main`, and
  on the `v1.31.1` and `v1.30.0` tags; the `v1.24.0` and `v1.22.0` pages describe only Windows telemetry) says: official
  builds for Windows, Linux, macOS, Android and iOS use the cross-platform 1DS SDK to send trace events to Microsoft over
  HTTPS; telemetry is **on by default**; WebAssembly builds contain none ([Privacy.md](https://raw.githubusercontent.com/microsoft/onnxruntime/main/docs/Privacy.md)).
- **Switches.** `ORT_DISABLE_TELEMETRY=1` set before ORT initialises prevents the uploader, the events and the persistent
  device identifier. Python also has `onnxruntime.disable_telemetry_events()` (non-essential events only: "ORT may already have emitted a
  minimal initialization event before the API can be called"). So **the environment variable is the right switch and must be set
  before `import onnxruntime`**. Legacy Windows TraceLogging (Windows apps) does not use the variable ([same page](https://raw.githubusercontent.com/microsoft/onnxruntime/main/docs/Privacy.md)).
- What is in the 1.31.1 wheel from PyPI is **unverified**. The doc speaks about official builds in general. The MediaPipe step showed
  how to check: look for strings in the native library, then watch DNS and TCP with and without the switch.
- Transformers.js sets this variable itself for its Node build (`process.env.ORT_DISABLE_TELEMETRY = '1'` in `src/backends/onnx-node.js` of the 4.3.2 tarball). That is a sign that the ORT people and the Hugging Face people both know about it.
- A clean funground design: `os.environ.setdefault("ORT_DISABLE_TELEMETRY", "1")` as the first line of `funground-ml` before
  any ORT import, plus a test that fails if the variable is not set at import. (A decision for the maintainer, and it
  makes the library's promise "sends nothing" depend on an upstream switch. The OpenCV route has no such dependency.)
- A pinned older ORT (1.22 to 1.24) has Windows-only telemetry in the docs, but I did not check 1.25 to 1.29, and old versions lack Python 3.14 wheels (unverified). Not recommended.

### Transformers.js in the browser

- Read the 4.3.2 source and the web bundle for telemetry, analytics and beacons: none found in `src/` or in
  `dist/transformers.web.js`. The one match is the Node-only line above. All network use goes through `env.fetch` (`src/utils/hub.js`,
  `get_file_metadata.js`, `cacheWasm.js`, `text-to-audio.js`). The `User-Agent` header is set only in Node.
- Hosts it contacts in the browser by default: `huggingface.co` for model files (a 302 redirect to `*.cdn.hf.co`; I checked a
  `HEAD` on `onnx-community/mediapipe_selfie_segmentation`: the redirect target allows any origin), and `cdn.jsdelivr.net` for the
  ORT wasm. It also reads `config.json` and processor files from the model repo. An experimental cache (`experimental_useCrossOriginStorage`, off by default) can fetch a raw URL.
  **Not captured on the wire yet** (plan item 4).
- Own host: yes. Set `env.allowRemoteModels = false` and `env.localModelPath`, or set `env.remoteHost` and `env.remotePathTemplate`;
  set `env.backends.onnx.wasm.wasmPaths` for the wasm ([env docs](https://huggingface.co/docs/transformers.js/api/env)).
- `onnxruntime-web` has no telemetry per the ORT privacy page.

### Mirror the files

For children, copy each pinned file to a host funground controls (or a GitHub release asset), and check its SHA-256 on download.
The Hub gives the SHA-256 for large files in the `X-Linked-ETag` header (seen in a `HEAD`; the value `9bc3d56b...` for the 0.2 MB selfie
`int8` file). All the licences above that are Apache-2.0, MIT or BSD allow this with a licence and notice file. Doing so means
**no contact with huggingface.co at all**, and `huggingface_hub` is not needed.

## 5. The same points on both platforms: can one ONNX file serve both?

**Yes for the file, partly for the code.** ONNX Runtime (Python) and `onnxruntime-web` run the same ONNX graphs. The risk is
operators that the wasm build lacks or runs slowly; this is only known by running (plan items 2 and 3).

What funground would own, per model family (Python line counts of the Zoo's own wrappers were counted on 28 Oct 2026; my estimates are
marked):

| Pipeline | Where the work is | Lines, Python | Lines, JavaScript | Notes |
|---|---|---|---|---|
| Selfie outline (single stage) | resize to 256x256, scale to 0..1, read a mask, resize back | about 20 (estimate) | about 25 (estimate) | |
| MoveNet (single stage) | resize to 192x192, read `[1,1,17,3]`, scale to the picture | about 30 (estimate) | about 30 (estimate) | 17 points, with names from COCO |
| Objects (D-FINE) | resize, normalise, take top boxes from logits | about 40 (estimate) | **0 on the web with Transformers.js** (`object-detection` pipeline) | |
| Naming, embeddings | resize, normalise, softmax | about 30 (estimate) | **0 with Transformers.js** | |
| Speech (Whisper) | log-mel, encoder, decoder loop with a cache, tokenizer | 150 to 250 (estimate) | **0 with Transformers.js** | Desktop alternative is `faster-whisper` |
| MediaPipe-style pose/hand (two stage) | detector, anchors, non-max suppression, crop and rotate, landmarks, undo the crop | Zoo wrappers: `mp_pose.py` 179, `mp_handpose.py` 200, plus the detectors (`mp_palmdet.py` 2121 and `mp_persondet.py` 2366 lines, mostly inlined anchor tables). The earlier estimate for funground was about 450 lines plus anchors ([../opencv/results.md](../opencv/results.md)) | a second port of about the same size (estimate 400 to 500) | Generate the anchors from a rule (an SSD anchor generator is about 25 lines, estimate) instead of tables |
| RTMPose (top-down, 17 points) | person box from a detector, crop to 192x256, decode two 1-D score vectors per point | about 60 plus a detector (estimate) | about 60 plus a detector (estimate) | The decode is an arg-max per axis |

Reading the table:
- **Single-stage models are cheap to share**: tens of lines each side. The sketch API and the point names (`nose`, `left_wrist`...)
  live in `funground-ml` once, as data.
- **MediaPipe-style two-stage pose and hands are the cost.** Writing it once in Python for the desktop is the plan (b) in D-124. A shared file would
  mean a JavaScript twin of 400 to 500 lines that must produce the same points, kept in step by a golden test (same picture, same
  ONNX file, points within a tolerance on both sides).
- **Why not do the glue once, in Python, and run it in Pyodide?** Pyodide has numpy but no ORT; every model call would cross
  to JavaScript and back with a promise. The sketch must not wait, so each stage becomes a state machine over frames
  (route A in `../research.md`, section 2). It is a worse design than two small ports with a golden test.
- **Does it beat today's plan (MediaPipe web + Zoo desktop)?** The points are the same in both. The shared file gives one set
  of weights, identical bugs, and a web side that does not depend on `storage.googleapis.com` for models or on Google's wasm.
  It loses the working, measured MediaPipe Tasks code on the web, and its speed advantage (11 to 42 results/s on the
  web CPU/GPU) is unknown against ORT-web. I would only take it for the web if ORT-web matches that speed (plan item 3).
- **A cheaper first win for the "one file" idea is the single-stage group:** selfie outline, MoveNet, objects, naming, embeddings, Whisper. These need no
  second port, or only a very short one, and they cover the parts where Hugging Face is strongest.

## 6. Measurement plan (for the main session), by value

Do each in its own throwaway venv or folder (not the project's `.venv`). Items 1 to 3 need little: every model named there is
under 20 MB.

| # | Measure | Install / fetch | Size | Why it matters |
|---|---|---|---|---|
| 1 | **Does the `onnxruntime` 1.31.1 wheel send anything, with and without `ORT_DISABLE_TELEMETRY=1`?** Strings scan of the native library (look for telemetry and endpoint names), DNS-cache probe (as in `../desktop/telemetry_probe.py`) and a TCP poll (as `../opencv/netwatch.ps1`) while a small model runs | venv: `onnxruntime==1.31.1` + `numpy` | about 29 MB download (installed: record it) | Decides the whole desktop route. Cheapest, most valuable |
| 2 | **ORT against `cv2.dnn` on this machine** for the models already on disk from the OpenCV step (Zoo pose, hand, palm, person, PP-HumanSeg), plus: MoveNet lightning int8 (2.8 MB) and fp32 (9.4 MB), `mediapipe_selfie_segmentation` fp32/int8 (0.5/0.2 MB), D-FINE nano int8 (4.5 MB), MobileNetV4 small int8 (3.9 MB), YAMNet (16.1 MB). Record speed, install size, first-result time, same 640x480 frames as before | same venv | models total under 50 MB | Tells if ORT can replace OpenCV on the desktop (29 MB against 180 MB) |
| 3 | **ORT-web in headless Chrome, in a module worker beside nothing else first**, the *same files* as item 2: selfie, MoveNet, Zoo pose (then hand). CPU wasm and WebGPU. Compare with the MediaPipe web numbers (pose lite 11/s CPU, 40/s GPU). Compare outputs with item 2's (same picture, points within a tolerance) | no install: load `onnxruntime-web` from the CDN as the web step did, or a local copy of the npm package | wasm 14.3 MB (CPU) or 28.4 MB (WebGPU), pin the version Transformers.js 4.3.2 uses | The "big prize": proves one file on both sides, and shows whether the speed is acceptable |
| 4 | **Transformers.js 4.3.2 pipelines in a module worker**: `object-detection` (D-FINE nano), `image-classification` (MobileNetV4), `image-feature-extraction` (DINOv2-small q8, 24.4 MB), `background-removal` (MODNet q8). Log **every request by host** (expect `huggingface.co`, `*.cdn.hf.co`, `cdn.jsdelivr.net`). Repeat with `allowRemoteModels=false` and our own wasm path | CDN or npm tarball (2.2 MB) | wasm 14.3 MB + models 4 to 24 MB | Confirms the network claims in section 4 and the self-hosting settings |
| 5 | **Whisper tiny.en q8 (40.8 MB) on the web** (Transformers.js) **and on the desktop** (ORT decode loop, then `faster-whisper` for comparison). Real-time factor on this slow machine, word accuracy on one or two clips, and the Python glue size | `tokenizers` (2.9 MB) in the venv of item 1; clip: a short public-domain sample | 41 MB; do base.en (76.9 MB) only if tiny is too poor | Speech is where Hugging Face is the only good source |
| 6 | **RTMPose-s body (20.5 MB zip) + YOLOX-tiny (18.9 MB zip)** and **RTMW-m (58.1 MB zip, 133 points including hands)** in ORT (desktop) and ORT-web. Check the hand quality | direct download from `download.openmmlab.com` | 97 MB in total: **ask the maintainer first** (just under the 100 MB mark; only the small ones are needed for a first look) | Tests a Hub-era alternative to the MediaPipe family with a very short decode |
| 7 | **Teachable kNN**: DINOv2-small q8 against MobileNetV4's output as the vector, on a few classes of simple photos | models from items 2 and 4 | | Picks the embedding model |
| 8 | **`huggingface_hub` 2.3.0 traffic** with and without `HF_HUB_DISABLE_TELEMETRY=1` for one `hf_hub_download` of a small file | venv: `huggingface_hub` (0.9 MB) + `hf-xet` (3.8 MB) + `httpx2` | small | Verifies section 4 only if funground ever uses the hub library (it need not) |

Do **not** measure without the maintainer's say: `transformers` + `torch` (127 MB wheel on Windows, installed size larger; 539 MB and CUDA on Linux),
AST fp32 (347 MB), `vitpose-plus-small` fp32 (133 MB), `Xenova/clip-vit-base-patch32` fp32 (606 MB, from `../research.md`). The torch route is documented here by size only.

## Open questions for the main session

1. If item 1 shows ORT sends data even with the variable set, the desktop route is OpenCV (already measured) or nothing.
2. If item 3 shows ORT-web is much slower than MediaPipe Tasks, keep MediaPipe on the web and use ORT on the desktop with the
   same points (that is D-124 option b with ORT in place of OpenCV, which would save about 150 MB).
3. Licences still to read: the Zoo repos have no licence field on the Hub (they follow the Zoo's Apache-2.0, each model's own
   `LICENSE` in the Zoo folder should be read), Google's face-mesh and hand weights, and the training-data terms of the RTMPose models.
