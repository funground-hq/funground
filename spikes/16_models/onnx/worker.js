// S-231 step 3 module worker: loads onnxruntime-web from the CDN (exact version), runs one task 100 times on one 640 x 480 frame.
// postMessage({ok, result}) with timings and the last points. Message in: {task, ep, threads, version, base, frames}
import * as G from "./glue_web.js";
const CDN = (v) => `https://cdn.jsdelivr.net/npm/onnxruntime-web@${v}/dist/`;
const MODELS = {   // task -> [model files, frame, labels json]
  pose: [["zoo_persondet.onnx", "zoo_pose.onnx"], "pose.png"], hand: [["zoo_palm.onnx", "zoo_hand.onnx"], "thumb_up.png"],
  selfie: [["selfie.onnx"], "pose.png"], humanseg: [["zoo_humanseg.onnx"], "pose.png"], yunet: [["zoo_yunet.onnx"], "portrait.png"],
  movenet: [["movenet.onnx"], "pose.png"], classify: [["mnv4.onnx"], "cats.png", "mnv4_config.json"],
  objects: [["dfine.onnx"], "city-streets.png", "dfine_config.json"], embed: [["mnv4.onnx"], "cats.png"], embed_dino: [["dino_q8.onnx"], "cats.png"],
};
const q = (a, f) => a[Math.min(a.length - 1, Math.floor(f * a.length))];

async function job({ task, ep, threads, version, base, frames = 100 }) {
  const baseTask = task.replace("_tracked", ""), [files, pic, labelFile] = MODELS[baseTask];
  const out = { task, ep, threads, version, where: "worker", isolated: self.crossOriginIsolated };
  const t0 = performance.now();
  const ort = await import(`${CDN(version)}${ep === "webgpu" ? "ort.webgpu.mjs" : "ort.wasm.mjs"}`);
  ort.env.wasm.wasmPaths = CDN(version); ort.env.wasm.numThreads = threads; ort.env.logLevel = "error";
  out.import_ms = performance.now() - t0;
  if (ep === "webgpu") { const a = await navigator.gpu?.requestAdapter(); out.gpu = a ? { vendor: a.info.vendor, architecture: a.info.architecture, device: a.info.device, description: a.info.description, fallback: a.isFallbackAdapter } : "no adapter"; }   // software adapter?
  let modelBytes = 0;
  const sessions = [];
  for (const f of files) {
    const buf = await (await fetch(`${base}/models/${f}`)).arrayBuffer(); modelBytes += buf.byteLength;
    sessions.push(await ort.InferenceSession.create(buf, { executionProviders: [ep], graphOptimizationLevel: "all" }));
  }
  out.model_bytes = modelBytes; out.created_ms = performance.now() - t0;
  const bmp = await createImageBitmap(await (await fetch(`${base}/frames/${pic}`)).blob());
  const frame = new OffscreenCanvas(640, 480); frame.getContext("2d").drawImage(bmp, 0, 0);
  const labels = labelFile ? await (await fetch(`${base}/models/${labelFile}`)).json().then((j) => j.id2label) : null;

  let step;
  if (baseTask === "pose" || baseTask === "hand") {
    const m = new (baseTask === "pose" ? G.Pose : G.Hand)(sessions[0], sessions[1], ort);
    const have = () => (baseTask === "pose" ? m.region : m.box);
    step = async () => { if (!task.endsWith("_tracked") || !have()) await m.find(frame); return m.points(frame); };
  } else {
    const fn = { selfie: G.selfie, humanseg: G.humanseg, yunet: G.yunet, movenet: G.movenet, classify: G.classify, objects: G.objects, embed: G.embed, embed_dino: G.embed }[baseTask];
    step = () => fn(sessions[0], ort, frame, labels);
  }
  let last = await step();
  out.first_result_ms = performance.now() - t0;
  const ms = [];
  const begin = performance.now();
  for (let i = 0; i < frames; i++) { const s = performance.now(); last = await step(); ms.push(performance.now() - s); }
  const total = performance.now() - begin, sorted = [...ms].sort((a, b) => a - b);
  Object.assign(out, { frames, fps: frames / (total / 1000), median_ms: q(sorted, 0.5), p90_ms: q(sorted, 0.9) });
  if (last && last.mask) last = { count: last.count };
  out.last = baseTask.startsWith("embed") ? { dim: last.length, vector: last } : last;
  out.found = Array.isArray(last) ? last.length : last ? (last.count ?? 1) : 0;
  out.resources = performance.getEntriesByType("resource").map((e) => ({ url: e.name, encoded: e.encodedBodySize, transfer: e.transferSize }));
  for (const s of sessions) await s.release();
  return out;
}
self.onmessage = async (e) => {
  try { self.postMessage({ ok: true, result: await job(e.data) }); }
  catch (err) { self.postMessage({ ok: false, error: String(err?.stack ?? err) }); }
};
