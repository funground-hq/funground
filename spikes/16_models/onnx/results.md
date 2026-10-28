# S-231 step 5: ONNX models with `onnxruntime` (desktop) and `onnxruntime-web` (Play), the same .onnx files (measured)

28 Oct 2026. Windows 11, the same slow 8-thread machine. Python 3.14.7, a throwaway venv in the scratchpad (never funground's).
Desktop `onnxruntime` 1.31.1 (CPU provider). Browser: Chrome 156.0.8078.48, `--headless=new`, Playwright temporary profile, a fresh context
per job, `onnxruntime-web` 1.31.1 (the same version) from cdn.jsdelivr.net, models and frames from a 127.0.0.1 server. Frames: the
sample pictures of the earlier steps, resized once to 640 x 480 PNG files (the same file is read on both platforms, so the input
is identical: only the resampling inside the model's own preprocessing differs). 100 timed frames, the same frame each time, one run
per cell (the machine is noisy: differences under about 20 percent are not meaningful). Numbers: `results.json` (everything),
the per-run files `web_*.json`, `tjs_*.json`, `compare_*.json`, `embed_check.json`.
Scripts (small, commented): `ort_telemetry.py` (+ `_child`), `tcp_watch.py`, `ort_glue.py` and `glue_web.js` (our pre- and
post-processing), `ort_desktop.py`, `measure.mjs` + `worker.js` + `page.html`, `measure_tjs.mjs` + `tjs_worker.js`,
`compare.py`, `embed_check.py`, `count_lines.py`, `build_results.py`. Models and frames stay in the scratchpad.

## 1. Does `onnxruntime` send anything? (Windows wheel 1.31.1, cp314)

**Install** (venv without pip and Pillow): `onnxruntime` 1.31.1 48 MB on disk (`onnxruntime.dll` 19.3 MB, `onnxruntime_pybind11_state.pyd` 20.0 MB),
numpy 2.5.4 55 MB (34 + 21 for `numpy.libs`), flatbuffers 25.12.19 1 MB, protobuf 7.36.2 3 MB, packaging 26.3 2 MB: **about 109 MB installed**
(download about 29 MB, from `../huggingface/research.md`). The whole venv with pip and Pillow 13.0.0 (used only to read pictures) is 137 MB.

**Observed** (`ort_telemetry.py`; `tcp_watch.py` polls the real interpreter's TCP table every 2 ms from a parent process, so interpreter exit is covered;
`watch_selftest.py` shows it sees a deliberate connection to pypi.org):
- 7 runs of a small model (MoveNet): import, session creation, 100 runs, deleting the session, 2 s idle, interpreter exit. **3 runs without the
  variable, 3 with `ORT_DISABLE_TELEMETRY=1`, and 1 without it that idled 60 s: 0 TCP connections in every run.**
  (An earlier set of runs watched the wrong pid, the venv launcher's, and was discarded.) The DNS cache (`ipconfig /displaydns`, read only)
  held no Microsoft, events or telemetry name afterwards. UDP and ETW were not captured (ETW sessions need admin).
- **Static check of the wheel's binaries** (`wide_strings.py`, ASCII and UTF-16): `onnxruntime.dll` and the `.pyd` import only `advapi32` (not
  `winhttp`, `wininet` or `ws2_32`) and contain none of those names. `onnxruntime.dll` has `EventRegister`, `EventSetInformation` and `EventWrite`
  imports, the string `Microsoft.ML.ONNXRuntime` (an ETW provider name), `ONNXRuntimeTraceLoggingProvider`, and the classes `Telemetry` and
  `WindowsTelemetry`. There is **no `ORT_DISABLE_TELEMETRY` string at all** (so this binary never reads the variable), no 1DS strings, and no
  collector URL: the 92 `https://` strings are documentation links (arXiv, Wikipedia, pytorch.org, Microsoft certificate lists). The `.pyd` has
  `enable_telemetry_events` / `disable_telemetry_events`. The process had `ws2_32.dll` loaded, but a bare Python (`baseline_mods.py`) does too;
  `crypt32.dll` is loaded only when ORT is imported (why: unverified; nothing calls the network).
- Reading: **the Windows wheel is the TraceLogging (ETW) build. It is a local event provider with no network code in the binary, and it made no
  connection.** Whether Windows itself uploads ETW events marked `TraceLoggingOptionMicrosoftTelemetry` depends on the machine's diagnostic-data
  setting and is not something this process does (documented, not measured).

**Documented** (all at tag `v1.31.1`, the release of 26 Oct 2026):
- `docs/Privacy.md` lines 8-12 ("Official Builds"): ORT collects trace events; Windows apps use the platform's ETW telemetry, "other Windows builds
  including our official releases", Linux, macOS, Android and iOS use the **1DS SDK built into ORT** (over HTTPS); on by default. WebAssembly has none.
  Lines 32-34: the two providers. Lines 38-44 ("Disabling Telemetry"): `ORT_DISABLE_TELEMETRY=1` before ORT initialises disables the uploader, events
  and persistent device id **for 1DS builds**; "the legacy Windows TraceLogging backend does not use this environment variable"; the API
  (`onnxruntime.disable_telemetry_events()`) suppresses non-essential events only. Page: <https://github.com/microsoft/onnxruntime/blob/v1.31.1/docs/Privacy.md>
  (privacy statement it links: <https://go.microsoft.com/fwlink/?LinkID=824704>).
- `onnxruntime/core/platform/telemetry_environment.h:276-280`: `IsTelemetryDisabledByEnvironment()` reads `ORT_DISABLE_TELEMETRY` (1/true/yes/on/y); its
  comment (lines 277-278): the POSIX 1DS provider latches it; **"Windows ETW retains its separate API/trace-session control model and does not consult this
  environment variable."**
- `onnxruntime/core/platform/windows/telemetry.cc:61-64` (`TRACELOGGING_DEFINE_PROVIDER(... "Microsoft.ML.ONNXRuntime" ... TraceLoggingOptionMicrosoftTelemetry())`)
  and `:280` (`TraceLoggingRegisterEx`): the ETW provider the wheel contains. `windows/telemetry_1ds.cc` exists in the same tag: the 1DS code for Windows is in
  the source, and the privacy page says official Windows releases use it.
- **Observed against documented:** the page says official Windows releases use 1DS over HTTPS. The 1.31.1 cp314 wheel on PyPI contains the ETW build and
  no network code, and the variable is not read. On Windows with this wheel nothing was sent by the process. This does **not** cover Linux or macOS wheels
  (documented as 1DS, with libcurl built in): not measured, no machine for it. A later wheel could switch Windows to 1DS (the source already supports it), so
  the safe design is still `os.environ.setdefault("ORT_DISABLE_TELEMETRY", "1")` before the first `import onnxruntime`, plus a test that fails if the
  variable is not set (a decision for the maintainer).
- `onnxruntime-web`: no telemetry in the package. The browser runs made requests only to our own server and cdn.jsdelivr.net (section 3); the wasm file and
  loader contain no "telemetry" and no URL except documentation links; the JS loader mentions only `web.dev`.

## 2. The same models on desktop ORT, `cv2.dnn` and MediaPipe (640 x 480, 100 frames, CPU)

The ORT column uses 8 threads (the default). "Box reused": the detector ran once, then only the landmark model is timed (the cost of a tracked
frame, the same definition as in `../opencv/results.md`). cv2.dnn numbers are copied from there (OpenCV 4.14), MediaPipe from `../desktop/results.md`. Median / p90 ms (results per second).

| Task (model) | **ORT** 1.31.1, 8 threads | ORT, 1 thread | cv2.dnn 4.14 (same Zoo files) | MediaPipe desktop | First result (ORT, import excluded) |
|---|---|---|---|---|---|
| Pose, detector + landmarks every frame (Zoo person det + pose, 33 points) | 32.4 / 44.9 (28.2) | 39.1 / 62.7 (23.3) | 104.4 / 118.1 (10.3) | lite 12.9 / 15.8 (74.1) | 0.32 s |
| Pose, box reused | 17.9 / 26.1 (51.7) | 21.9 / 24.2 (45.2) | 44.8 / 54.8 (21.3) | same row | 0.21 s |
| Hand, palm + landmarks every frame (21 points) | 16.0 / 17.1 (62.4) | not run | 74.9 / 90.9 (13.0) | 10.3 / 16.0 (84.6) | 0.12 s |
| Hand, box reused | 6.4 / 6.9 (161.9) | 6.7 / 7.6 (145.5) | 25.3 / 28.3 (39.4) | same row | 0.10 s |
| Face: YuNet 2023mar (box + 5 points) | 17.7 / 20.2 (56.3) | not run | 41.3 / 73.0 (20.6) | FaceLandmarker 478 points 11.2 / 13.4 (87.7) | 0.09 s |
| Person mask: PP-HumanSeg | 15.7 / 17.3 (64.2) | not run | 29.2 / 33.2 (33.5) | selfie segmenter 6.3 / 7.0 (156.0) | 0.10 s |
| Person mask: `mediapipe_selfie_segmentation` (Hub, fp32, 0.46 MB) | 11.5 / 13.5 (87.7) | 10.6 / 11.6 (93.6) | n/a | same model as MediaPipe's, 6.3 / 7.0 (156.0) | 0.16 s |
| MoveNet lightning fp32 (17 points, 9.4 MB) | 8.0 / 9.4 (126.2) | 11.4 / 12.0 (87.6) | n/a | n/a | 0.11 s |
| MoveNet lightning int8 (2.8 MB) | 116.6 / 153.0 (8.4) | not run | n/a | n/a | 0.25 s |
| MobileNetV4-small fp32 (names a picture, 15.1 MB) | 11.6 / 13.4 (85.7) | 9.9 / 11.1 (98.0) | n/a | EfficientNet-Lite0 not measured on desktop | 0.13 s |
| MobileNetV4-small int8 (3.9 MB) | 90.9 / 134.2 (10.2) | not run | n/a | n/a | 0.25 s |
| D-FINE nano fp32 (objects, 15.3 MB) | 160.4 / 191.7 (6.1) | not run | n/a | n/a | 0.66 s |
| D-FINE nano int8 (4.5 MB) | 933.9 / 1366.4 (1.0) | not run | n/a | n/a | 1.49 s |
| Picture to vector: MobileNetV4 output (1000 numbers) | 8.6 / 10.3 (117.1) | not run | n/a | n/a | 0.14 s |
| Picture to vector: DINOv2-small q8 (384 numbers, 24.4 MB) | 110.0 / 144.8 (8.9) | not run | n/a | n/a | 0.29 s |

- **ORT is 2.5 to 3.5 times faster than cv2.dnn** on the very same Zoo files (pose 28 against 10 per second, tracked 52 against 21; hand 62 against 13, tracked 162
  against 39; YuNet 56 against 21; PP-HumanSeg 64 against 34), for a venv of about 109 MB against 180 MB. It is 1.4 to 2.6 times slower than MediaPipe on pose and
  hand (28 against 74, 62 against 85); the same selfie model is about 1.8 times slower (88 against 156, MediaPipe's is the TFLite/XNNPACK build). One thread is nearly as fast as
  eight for these small nets (so the browser's single wasm thread is a fair comparison with desktop 1 thread).
- **The int8 files are a trap.** All three `int8`/`q8` files were 8 to 20 times slower than fp32 on this CPU (MoveNet 117 against 8 ms, MobileNetV4 91 against 12 ms, D-FINE 934
  against 160 ms), and **the MobileNetV4 int8 file gives a wrong answer** (a picture of cats is "knee pad", 0.80; fp32 says "tabby cat", 0.77): reproduced in two runtimes (this
  desktop run, and Transformers.js's default `q8` in the browser, section 4). Use fp32 (or fp16 on a GPU). Do not take the small file on trust.
- Points found: pose 33 (our glue returns the 33 of the 39 rows; the 6 helper points are skipped), hand 21, MoveNet 17, YuNet box + 5, D-FINE 14 boxes above 0.4 on a street picture
  (no non-maximum suppression in our glue, so some boxes are near-duplicates; Transformers.js gave the same boxes, section 4). Sanity: skeleton and hand overlays were looked at by eye
  and are right (`overlay.py`); selfie and PP-HumanSeg give 21 907 and 21 666 person pixels on pose.jpg (cv2.dnn: 22 206 for PP-HumanSeg).
- Glue we wrote is limited: **one person and one hand (the best detection, no NMS), no handedness, no world (3D) points, no mask from the pose model, no
  tracking from the last frame's landmarks** (the "box reused" row is the stand-in). MediaPipe and the Zoo wrappers do more.

## 3. `onnxruntime-web` in a module Web Worker, the same .onnx files

Headless Chrome 156, `new Worker("worker.js", {type: "module"})`, OffscreenCanvas frames, CDN `onnxruntime-web@1.31.1` (`ort.wasm.mjs` for CPU, `ort.webgpu.mjs` for WebGPU),
`env.wasm.numThreads` as stated. **No cross-origin isolation is the normal case** for a page like Play (it needs `COOP`/`COEP` headers, which a plain static host may not send),
so 1 thread is the headline; "4 threads" ran with the headers set on our server. Median / p90 ms (results per second); first result = from the start of loading the library to the first
result, including the wasm and model download from localhost.

| Task | wasm, 1 thread | wasm, 4 threads (isolated) | WebGPU | First result (wasm / WebGPU) | MediaPipe web, worker (`../web/results.md`) |
|---|---|---|---|---|---|
| Pose, detector + landmarks every frame | 184.1 / 217.0 (5.3) | 119.2 / 171.6 (7.5) | 94.7 / 107.2 (10.3) | 2.7 s / 7.4 s | pose lite 89.0 / 113.0 (11.1) CPU, 23.6 / 26.1 (42.4) GPU (it tracks) |
| Pose, box reused | 78.9 / 97.3 (12.6); rerun 71.6 / 86.4 (14.6) | 67.7 / 80.5 (14.9) | 49.7 / 56.6 (19.8) | 2.7 s / 6.3 s | same row |
| Hand every frame | 121.6 / 161.8 (7.9) | 103.9 / 134.7 (9.5) | not run | 2.0 s | 70.0 / 107.7 (13.5) |
| Hand, box reused | 68.2 / 97.8 (14.6) | 35.5 / 51.0 (27.5) | not run | 1.6 s | same row |
| Selfie mask (0.46 MB) | 27.7 / 49.1 (32.3) | 27.4 / 36.5 (39.2) | 33.7 / 52.8 (27.1) | 1.6 s / 4.3 s | 25.6 / 37.8 (38.2) |
| PP-HumanSeg | 110.7 / 148.4 (8.7) | not run | not run | 1.9 s | n/a |
| YuNet (box + 5 points) | 140.7 / 181.9 (6.8) | not run | not run | 2.4 s | FaceLandmarker 37.5 / 53.2 (25.1) |
| MoveNet lightning fp32 | 71.8 / 83.6 (14.4); reruns 69.6 (14.2), 61.0 (16.7) | 47.6 / 64.9 (19.8) (this run had a bug in the web glue, since fixed; speed unaffected) | 41.3 / 50.0 (23.1) | 1.8 s / 5.1 s | n/a |
| MobileNetV4-small fp32 | 38.6 / 56.2 (25.3) | not run | not run | 1.6 s | EfficientNet-Lite0 76.9 / 95.6 (13.0) |
| D-FINE nano fp32 | 615.1 / 686.3 (1.6) | not run | not run | 3.1 s | EfficientDet-Lite0 gave a suspect result there |
| Picture to vector: MobileNetV4 output | 35.1 / 54.2 (26.4); rerun 41.0 (24.4) | not run | not run | 1.7 s | n/a |
| Picture to vector: DINOv2-small q8 | 495.4 / 554.5 (2.0) | not run | not run | 2.2 s | n/a |

- **The key question: yes.** The same `zoo_persondet.onnx` + `zoo_pose.onnx` run in the module worker. Tracked-frame pose (box reused) is 12.6 to 14.6 per second on one wasm
  thread and 19.8 on WebGPU, against MediaPipe's 11.1 (CPU) and 42.4 (GPU). That is 10 per second or better for tracked frames, but **not for "detector on every frame"** (5.3 per second on wasm,
  10.3 on WebGPU). So a shared-file design needs tracking (reuse last frame's landmarks to place the next region, as MediaPipe does) to be usable on the web, and the glue here does not yet do that.
  Hand: 14.6 per second tracked, 7.9 every frame. MoveNet (17 points, one stage) 14 to 17 per second on wasm and 23 on WebGPU, with no tracking needed.
- **Compared with MediaPipe on the web:** pose and hand on CPU are at par when tracked (12.6 against 11.1; 14.6 against 13.5). On the GPU MediaPipe is twice as fast (42 against 20). The selfie model is the
  same speed. Desktop to browser: ORT native one thread (45 per second, pose tracked) is 3.5 times faster than ORT-web one thread (12.6), the usual wasm gap.
- Threads: 4 threads with cross-origin isolation gained about 15 to 90 percent (hand tracked 14.6 to 27.5, pose 12.6 to 14.9). Only worth it if Play can be isolated.
- WebGPU worked in a module worker in headless Chrome without extra flags. The adapter reported by the worker: vendor `intel`, architecture `gen-12lp` (an integrated GPU, not a named
  software renderer; this Chrome did not report `isFallbackAdapter`, so a fallback is not strictly ruled out). The first result takes 5 to 13 s (shader compile, cold). It loads a larger wasm (see below).
- **Same-file point agreement (desktop ORT against ORT-web, same .onnx and same 640 x 480 PNG)**, `compare.py`, `compare_wasm.json`:

  | Model | Points | Largest difference | Mean |
  |---|---|---|---|
  | Pose 33 points | 33 | **4.65 px** (point 25, left knee) | 1.59 px |
  | Hand 21 points | 21 | **2.17 px** (point 5) | 1.07 px |
  | MoveNet 17 points | 17 | **5.26 px** (point 9, left wrist) | 1.80 px |
  | YuNet box points | 5 | 0.00 px (no resampling; input is identical) | 0.00 |
  | Selfie mask | person pixels | 4642 at 256 x 256 (web) against 21 907 at 640 x 480 (desktop): 4642 x 4.6875 = 21 759, 0.7 percent apart | |
  | MobileNetV4 fp32 | top 5 | same top name ("tabby, tabby cat"), probability 0.766 against 0.796; the order of the last two differs | max 0.030 |
  | D-FINE nano | boxes | 14 against 14; the big boxes agree within about 1 px; borderline scores (0.4 to 0.5) differ so a few boxes appear on one side only | |

  WebGPU and 4-thread runs gave the same pose differences (4.64 px). The difference is the resampling (Pillow's bilinear warp against Chrome's `drawImage`), not the model.
  Expect the same few pixels between platforms for any shared-file design; a golden test needs a tolerance of about 5 px at 640 x 480 (under 1 percent of the width).
- **Download sizes (wire, brotli):** CPU runtime `ort.wasm.mjs` 149 KB + loader 10 KB + `ort-wasm-simd-threaded.wasm` 3.20 MB = **3.36 MB** (14.8 MB unpacked). The WebGPU build:
  `ort.webgpu.mjs` 171 KB + loader 20 KB + `ort-wasm-simd-threaded.asyncify.wasm` 5.99 MB = **6.2 MB** (28.7 MB unpacked; the `.jsep.wasm` is 29.5 MB). MediaPipe's CPU runtime was 3.25 MB.
  Models: Zoo person 12.0 + pose 5.6 = 17.5 MB; palm 3.9 + hand 4.1 = 8.0 MB; selfie 0.46 MB; MoveNet 9.4 MB.
- **Hosts, every request of every job:** `127.0.0.1` (ours) and `cdn.jsdelivr.net` only (the wasm loader, the wasm and the library). In the 4-thread runs there are also `blob:` URLs (ORT's own worker
  threads). Nothing else, and no failed request.

## 4. Transformers.js 4.3.2 pipelines in a module worker

Library `https://cdn.jsdelivr.net/npm/@huggingface/transformers@4.3.2/dist/transformers.min.js` (588 KB, 142 KB on the wire). **Use `transformers.min.js`**: `transformers.web.min.js` (the
file the package's `exports` suggests for browsers) fails in a worker with `Failed to resolve module specifier "onnxruntime-web/webgpu"` because it leaves ORT out for a bundler
(import maps do not work in workers). 30 runs per pipeline, wasm, 1 thread, an already decoded `RawImage` of 640 x 480 each call (so decode is excluded; resizing is included).

| Pipeline | Model (download) | Median / p90 ms (per second) | First result | Result |
|---|---|---|---|---|
| `image-classification` | MobileNetV4-small **fp32** (15.1 MB) | 44 / 60 (21.6) | 3.7 s | tabby cat 0.77, Egyptian cat 0.13, tiger cat 0.06 (right; same as desktop) |
| `image-classification` | MobileNetV4-small **q8** (3.9 MB, the library's default for wasm) | 67 / 80 (15.0) | 7.5 s (from the Hub) | "knee pad" 0.45: **wrong** |
| `object-detection` | D-FINE nano fp32 (15.3 MB) | 694 / 777 (1.5) | 5.0 s | 14 boxes at threshold 0.4: car (451,284,...), person, traffic lights, bicycle: the same boxes as our own glue |
| `object-detection` | D-FINE nano q8 (4.5 MB) | 2641 / 2774 (0.4) | 6.0 s | similar boxes, 4 times slower than fp32 |
| `background-removal` | `Xenova/modnet` q8 (6.6 MB; fp32 is 25.9 MB) | 2298 / 2415 (0.4) | 5.8 s | an RGBA 640 x 480 image |
| `image-segmentation` | no small fitting model found (the SegFormer b0 files are 15 MB fp32 / 4.4 MB q8, one is ADE20K scenes, one is clothes with no licence field); MODNet is the person outline here | | | |

- **Speed:** classification at 15 to 22 per second is fine. Detection (1.5 per second) and MODNet (0.4 per second) are for pictures, not live video, on this CPU; the selfie model in section 3
  is the live outline.
- **Hosts, defaults ("remote" mode: library and wasm from the CDN, model from the Hub):** `cdn.jsdelivr.net` (library; `onnxruntime-web@1.31.0-dev.20260914-8d85527a0/dist/ort-wasm-simd-threaded.asyncify.{mjs,wasm}`,
  5.55 MB on the wire), **`huggingface.co`** (8 requests: `config.json`, `preprocessor_config.json` (twice), a 404 for `tokenizer_config.json`, and `resolve/main/onnx/model_quantized.onnx` which redirects with 302)
  and **`us.aws.cdn.hf.co`** (the model file itself, 3.9 MB), plus a `blob:` worker. The Hub requests were 307/302 redirects to `huggingface.co/api/resolve-cache/...` and to the xet CDN. No other host, no analytics call.
- **With `env.allowRemoteModels = false` and `env.localModelPath = <our origin>/hf/` ("cdn" mode): only `127.0.0.1` and `cdn.jsdelivr.net`** (library and wasm), no contact with huggingface.co at all.
  With the library and wasm also served from our origin (`env.backends.onnx.wasm.wasmPaths = <our origin>/tjs/`, the files `ort-wasm-simd-threaded.asyncify.mjs/.wasm` from the same npm version; "local" mode): **every
  request went to 127.0.0.1 (9 of 9, 2 jobs)**. The library bundle holds only these URLs as strings: huggingface.co (3), cdn.jsdelivr.net, github.com, gist.github.com, developer.mozilla.org, web.dev (comments/messages).
  So Transformers.js can run fully self-hosted. The wasm it picks in this setup is the **asyncify** build (26.9 MB unpacked, 5.55 MB on the wire), not the plain 14.3 MB one.
- **A problem to know about:** with models served locally, `pipeline()` alone failed with `TypeError: this.processor is not a function` (cause not found; the preprocessor file was not even requested).
  Calling `AutoProcessor.from_pretrained(model)` first made it work, so `tjs_worker.js` does that outside "remote" mode.
- Transformers.js did not add a pose, hand or face-point pipeline (`../huggingface/research.md`); we use `onnxruntime-web` directly for those (section 3).

## 5. Picture embeddings (for a learner's kNN)

| Model | Per embedding, desktop ORT | Per embedding, ORT-web (worker, 1 thread) | Vector size | Desktop against web, same picture |
|---|---|---|---|---|
| MobileNetV4-small fp32, its 1000 class scores used as the vector | 8.6 ms | 35.1 ms | 1000 | cosine **0.99998** |
| DINOv2-small q8 (CLS token of the last hidden state, 24.4 MB) | 110.0 ms | 495.4 ms | 384 | cosine **0.988** |

- Quality check (desktop, `embed_check.py`, cosine to the cats picture): **DINOv2 q8 works as an embedding**: the cats picture flipped 0.961, darker 0.989, a street 0.049, a yoga picture -0.020, a portrait 0.092.
  **MobileNetV4's class scores do not**: everything is 0.997 to 1.000 (the 1000 scores share a large common part; it has no pooled-feature output in this ONNX file), so it needs centring at least, and would be a weak
  embedding. For a kNN, DINOv2-small is the one to use; it costs 4 times more per picture (about 110 ms on the desktop, 0.5 s in the browser here), fine for "add an example" and "classify now", slow for live video.
- Desktop and web vectors are near-identical (0.988 to 0.99998), so a classifier trained on one platform's vectors would work on the other's, but the difference is real: resampling again. One picture only.
- q8 caution (section 2): DINOv2's q8 looked healthy in this test; it was not checked against the fp32 file (88.5 MB) or on more pictures.

## 6. Glue code we own

Lines of code without blanks, comments and docstrings (`count_lines.py`):

| Piece | Python (`ort_glue.py`) | JavaScript (`glue_web.js`) |
|---|---|---|
| Affine crop/rotate/resize, region of interest, anchors, sigmoid (shared) | 30 | 38 (warp 12, tensor 8, anchors 10, roi 5, letterbox, run, sigmoid) |
| SSD detector (person and palm share it) | 13 | 16 |
| Pose (person detector + 33 landmarks) | 21 | 17 |
| Hand (palm detector + 21 landmarks) | 18 | 16 |
| **Pose + hand total** | **82** | **87** |
| MoveNet, selfie, PP-HumanSeg, YuNet, MobileNetV4, D-FINE, embedding | 56 | 64 |
| **All twelve models** | **141** (plus 3 header) | **151** |

Against the OpenCV step: the Zoo wrappers for pose and hand are about 440 lines plus about 4 260 lines of anchor tables (`../opencv/results.md`). Ours is 82 lines in Python and 87 in JavaScript, **because the anchors are generated by a
10-line rule (the generated tables equal the Zoo's: 2254 and 2016 anchors, largest difference 0 and 3e-8) and one affine call does crop, rotation and resize**. Honest limits: one person and one hand, no NMS, no handedness, no
world points, no mask, no tracking; adding tracking and several people would add perhaps 30 to 60 lines on each side (estimate, unmeasured). The two languages need **a golden test** (section 3: expect about 5 px).
Point names (33 BlazePose, 21 hand, 17 COCO) are data we would supply once.

## Licences (cards as read on 28 Oct 2026; upstream terms not re-read)

`onnx-community/mediapipe_selfie_segmentation` Apache-2.0 (card); `Xenova/movenet-singlepose-lightning` Apache-2.0 (card; `STMicroelectronics/movenet` says "other", so the origin of the weights is unverified);
`onnx-community/mobilenetv4_conv_small.e2400_r224_in1k`, `onnx-community/dfine_n_coco-ONNX`, `onnx-community/dinov2-small`: no licence field on the Hub repo, upstream Apache-2.0 per `../huggingface/research.md`;
`Xenova/modnet` Apache-2.0 (card); Zoo files: see `../opencv/results.md`. ORT: MIT (PyPI metadata, from `../huggingface/research.md`). The OpenCV Zoo wrapper sources were read in the scratchpad for the tensor layouts only; none was copied.

## What was not done

- No Linux or macOS check of `onnxruntime` telemetry (documented as 1DS there). No packet capture and no ETW session (admin needed). One machine, one run per cell, one picture per task.
- Detection quality was not measured (no labelled data); correctness was checked by overlay and against Transformers.js's own output.
- RTMPose and Whisper (plan items 5 and 6 of `../huggingface/research.md`) were not started. Nothing over 100 MB was downloaded (the biggest file was D-FINE and MobileNetV4 fp32 at 15 MB, DINOv2 q8 24 MB).
- Memory next to Pyodide was not measured.
- YuNet's decode and PP-HumanSeg's colour order are from memory of the Zoo/OpenCV code and are only checked by result (a face with plausible points; 21 666 person pixels).
