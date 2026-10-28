// Shared by page.html (main thread) and worker.js (module worker): loads one MediaPipe task and times it.
// The library version is fixed here so it is recorded in one place.
export const VERSION = "1.2.0";
const LIB = `https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@${VERSION}`;
const MODELS = "https://storage.googleapis.com/mediapipe-models";

// task -> [library class, model url, picture]
const TASKS = {
  pose_lite: ["PoseLandmarker", `${MODELS}/pose_landmarker/pose_landmarker_lite/float16/latest/pose_landmarker_lite.task`, "pose.jpg"],
  pose_full: ["PoseLandmarker", `${MODELS}/pose_landmarker/pose_landmarker_full/float16/latest/pose_landmarker_full.task`, "pose.jpg"],
  hand: ["HandLandmarker", `${MODELS}/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task`, "thumb_up.jpg"],
  face: ["FaceLandmarker", `${MODELS}/face_landmarker/face_landmarker/float16/latest/face_landmarker.task`, "portrait.jpg"],
  segment: ["ImageSegmenter", `${MODELS}/image_segmenter/selfie_segmenter/float16/latest/selfie_segmenter.tflite`, "pose.jpg"],
  objects: ["ObjectDetector", `${MODELS}/object_detector/efficientdet_lite0/int8/latest/efficientdet_lite0.tflite`, "pose.jpg"],
  classify: ["ImageClassifier", `${MODELS}/image_classifier/efficientnet_lite0/float32/latest/efficientnet_lite0.tflite`, "pose.jpg"],
};

// Runs one frame and returns what was found (a count, or a label), freeing the result.
function runFrame(task, landmarker, frame, ts) {
  switch (task) {
    case "pose_lite": case "pose_full": {
      const r = landmarker.detectForVideo(frame, ts); const n = r.landmarks[0]?.length ?? 0; r.close?.(); return n; }
    case "hand": { const r = landmarker.detectForVideo(frame, ts); return r.landmarks.reduce((a, l) => a + l.length, 0); }
    case "face": { const r = landmarker.detectForVideo(frame, ts); return r.faceLandmarks[0]?.length ?? 0; }
    case "segment": {
      const r = landmarker.segmentForVideo(frame, ts);
      const mask = r.confidenceMasks?.[0]; const n = mask ? mask.width * mask.height : 0; r.close(); return n; }
    case "objects": { const r = landmarker.detectForVideo(frame, ts); return r.detections.length; }
    case "classify": { const r = landmarker.classifyForVideo(frame, ts); return r.classifications[0]?.categories[0]?.categoryName ?? ""; }
  }
}

const quantile = (sorted, q) => sorted[Math.min(sorted.length - 1, Math.floor(q * sorted.length))];

export async function bench({ task, delegate = "CPU", frames = 100, base }) {
  const [cls, modelUrl, picture] = TASKS[task];
  const out = { task, delegate, where: typeof document === "undefined" ? "worker" : "main" };
  const t0 = performance.now();
  const lib = await import(`${LIB}/vision_bundle.mjs`);
  out.import_ms = performance.now() - t0;
  let fileset = await lib.FilesetResolver.forVisionTasks(`${LIB}/wasm`);
  // A module worker cannot importScripts(): it needs the "module" build of the wasm loader (since 0.10.35).
  if (out.where === "worker") fileset = { wasmLoaderPath: `${LIB}/wasm/vision_wasm_module_internal.js`, wasmBinaryPath: `${LIB}/wasm/vision_wasm_module_internal.wasm` };
  out.fileset_ms = performance.now() - t0;
  const options = { baseOptions: { modelAssetPath: modelUrl, delegate }, runningMode: "VIDEO" };
  if (task === "segment") { options.outputConfidenceMasks = true; options.outputCategoryMask = false; }
  const landmarker = await lib[cls].createFromOptions(fileset, options);
  out.created_ms = performance.now() - t0;

  // One 640 x 480 picture, drawn once, handed over again and again (the same canvas each time).
  const blob = await (await fetch(`${base}/img/${picture}`)).blob();
  const bitmap = await createImageBitmap(blob);
  const canvas = typeof document === "undefined" ? new OffscreenCanvas(640, 480) : Object.assign(document.createElement("canvas"), { width: 640, height: 480 });
  const g = canvas.getContext("2d");
  const scale = Math.max(640 / bitmap.width, 480 / bitmap.height);      // cover, centred
  g.drawImage(bitmap, (640 - bitmap.width * scale) / 2, (480 - bitmap.height * scale) / 2, bitmap.width * scale, bitmap.height * scale);

  let ts = 1000;
  const first = runFrame(task, landmarker, canvas, ts += 33);
  out.first_result_ms = performance.now() - t0;          // start of loading to the first result
  out.found = first;

  const per = [];
  const begin = performance.now();
  for (let i = 0; i < frames; i++) {
    const s = performance.now();
    runFrame(task, landmarker, canvas, ts += 33);
    per.push(performance.now() - s);
  }
  const total = performance.now() - begin;
  const sorted = [...per].sort((a, b) => a - b);
  Object.assign(out, { frames, fps: frames / (total / 1000), median_ms: quantile(sorted, 0.5), p90_ms: quantile(sorted, 0.9), min_ms: sorted[0], max_ms: sorted.at(-1) });
  landmarker.close();
  return out;
}
