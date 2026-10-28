# S-231 step 1: MediaPipe Tasks Vision in headless Chrome (measured)

Date 28 Oct 2026. Chrome 156.0.8078.48 (headless=new, Playwright temporary profile). `@mediapipe/tasks-vision` 1.2.0 from
cdn.jsdelivr.net. Models from storage.googleapis.com/mediapipe-models (float16 `latest`, except EfficientDet-Lite0 int8 and
EfficientNet-Lite0 float32). Windows 11, slow low-memory machine. One job at a time, a fresh browser context (empty cache) per job.
Frames: one 640 x 480 picture (MediaPipe's sample images; pose.jpg for pose, segmenter, objects, classifier; thumb_up.jpg for the
hand; portrait.jpg for the face), the same canvas given 100 times with increasing timestamps, VIDEO mode, CPU delegate.
Numbers: `results.json` (CPU), `gpu.json` (GPU). Scripts: `measure.mjs`, `page.html`, `bench.js`, `worker.js`, `summarise.mjs`.
One run per cell: the machine is noisy, so differences under about 20 percent between main and worker are not meaningful.

"Wire" = response body bytes over the network (Playwright), after compression. Model sizes match the files' own sizes
(none is compressed). First result = from the start of loading the library to the first result, including the wasm download.

| Task | Model (wire) | Where | First result | Results/s | Median ms | p90 ms | Found |
|---|---|---|---|---|---|---|---|
| PoseLandmarker lite | 5.78 MB | main | 14.4 s | 10.8 | 91.8 | 110.7 | 33 points |
| | | worker | 5.0 s | 11.1 | 89.0 | 113.0 | 33 |
| PoseLandmarker full | 9.40 MB | main | 8.3 s | 7.9 | 128.1 | 156.8 | 33 |
| | | worker | 6.6 s | 8.1 | 123.8 | 151.2 | 33 |
| HandLandmarker | 7.82 MB | main | 5.4 s | 16.1 | 58.9 | 84.6 | 21 |
| | | worker | 6.6 s | 13.5 | 70.0 | 107.7 | 21 |
| FaceLandmarker | 3.76 MB | main | 3.1 s | 21.3 | 46.6 | 62.6 | 478 |
| | | worker | 4.3 s | 25.1 | 37.5 | 53.2 | 478 |
| ImageSegmenter (selfie) | 0.25 MB | main | 1.9 s | 39.8 | 20.6 | 39.4 | mask 307200 px |
| | | worker | 2.3 s | 38.2 | 25.6 | 37.8 | same |
| ObjectDetector EfficientDet-Lite0 (int8) | 4.61 MB | main | 4.0 s | 1.1 | 848.8 | 1310.1 | 2553 "detections" (suspect) |
| | | worker | 5.5 s | 1.1 | 886.6 | 1166.8 | 2553 |
| ImageClassifier EfficientNet-Lite0 | 18.59 MB | main | 8.8 s | 13.3 | 72.2 | 97.6 | top label "sandbar" |
| | | worker | 11.0 s | 13.0 | 76.9 | 95.6 | same |

Notes
- Wasm runtime on the wire: 3.25 MB (main, `vision_wasm_internal.wasm` plus loader, brotli) and 3.7 MB (worker, the `module` build).
  The files are 14.5 MB unpacked. The first-load times above include it; a warm cache would be faster. The 14.4 s for the first
  job is a cold start (first CDN fetches, Chrome warming up) and is not repeatable: later jobs with the same download took 5 to 8 s.
- Segmenter: `found` is the pixel count of the confidence mask returned (307200 = 640 x 480, the mask comes back at the input size).
- Object detector looks wrong: 2553 detections and 850 ms per frame. I did not investigate (likely the int8 model on this CPU
  and the default score threshold). Treat the object detector numbers as "does not give a usable result as configured"; try the
  float32 / float16 variant and a `scoreThreshold` before relying on it.
- Audio classifier and embedder: not measured (no time spent).

## Does it run in a module Web Worker?

Yes, all 7 configurations ran in `new Worker("worker.js", {type: "module"})` with OffscreenCanvas frames, with the same results
(same point counts) and about the same speed as the main page. One thing is needed: `FilesetResolver.forVisionTasks()` returns the
classic loader, which fails in a module worker with `Error: ModuleFactory not set`. Pass the module build instead:
`{wasmLoaderPath: ".../wasm/vision_wasm_module_internal.js", wasmBinaryPath: ".../wasm/vision_wasm_module_internal.wasm"}`
(see `bench.js`). So it can sit in Play's worker. Memory next to Pyodide was not measured (step 7 of the plan).

## GPU delegate (pose lite)

Works in headless Chrome, in the main page and in the module worker. Probably a software WebGL renderer (SwiftShader) in headless:
I did not read the renderer string. Even so it was about 3.5 times faster than CPU here.

| Where | First result | Results/s | Median ms | p90 ms | Found |
|---|---|---|---|---|---|
| main GPU | 16.8 s | 38.8 | 25.6 | 29.9 | 33 |
| worker GPU | 13.5 s | 42.4 | 23.6 | 26.1 | 33 |

First load on GPU is slower (shader compile).

## Network: what MediaPipe requests besides the wasm and the model

Every request of all 16 jobs, by host: only `cdn.jsdelivr.net` (`/npm/@mediapipe/tasks-vision@1.2.0/...`: bundle, wasm loader, wasm),
`storage.googleapis.com` (`/mediapipe-models/...`, the model) and our own 127.0.0.1 server. No analytics, metrics or other host,
and no failed request. This is for Tasks Vision 1.2.0 in the browser in this setup; the Python package's telemetry sentence
(desk research) is a separate question.
