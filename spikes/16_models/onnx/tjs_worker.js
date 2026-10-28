// S-231 step 4 module worker: one Transformers.js 4.3.2 pipeline, timed. Message in: {task, mode, dtype, runs, base}
//   mode "remote": library and wasm from jsDelivr, models from huggingface.co (the library's defaults)
//   mode "cdn":    library and wasm from jsDelivr, models only from our 127.0.0.1 server (allowRemoteModels = false)
//   mode "local":  library, wasm and models all from our 127.0.0.1 server
const CDN_LIB = "https://cdn.jsdelivr.net/npm/@huggingface/transformers@4.3.2/dist/transformers.min.js";
const TASKS = {   // task -> [pipeline, model id, picture, options]
  classify: ["image-classification", "onnx-community/mobilenetv4_conv_small.e2400_r224_in1k", "cats.png", { top_k: 5 }],
  objects: ["object-detection", "onnx-community/dfine_n_coco-ONNX", "city-streets.png", { threshold: 0.4 }],
  segment: ["background-removal", "Xenova/modnet", "pose.png", {}],
};
const q = (a, f) => a[Math.min(a.length - 1, Math.floor(f * a.length))];

async function job({ task, mode, dtype, runs, base, device }) {
  const [pipe, model, pic, opts] = TASKS[task];
  const out = { task, mode, dtype, model, pipeline: pipe, device, isolated: self.crossOriginIsolated };
  const t0 = performance.now();
  const T = await import(mode === "local" ? `${base}/tjs/transformers.min.js` : CDN_LIB);
  out.import_ms = performance.now() - t0;
  if (mode !== "remote") { T.env.allowRemoteModels = false; T.env.allowLocalModels = true; T.env.localModelPath = `${base}/hf/`; }
  if (mode === "local") T.env.backends.onnx.wasm.wasmPaths = `${base}/tjs/`;
  // With models served from our own folder, pipeline() alone failed with "this.processor is not a function" (cause not found);
  // loading the processor first makes it work, so the worker does that outside "remote" mode.
  if (mode !== "remote") await T.AutoProcessor.from_pretrained(model);
  const p = await T.pipeline(pipe, model, { dtype, device });
  out.created_ms = performance.now() - t0;
  const img = await T.RawImage.read(`${base}/frames/${pic}`);
  const call = () => p(img, opts);
  let r = await call();
  out.first_result_ms = performance.now() - t0;
  const ms = [];
  const begin = performance.now();
  for (let i = 0; i < runs; i++) { const s = performance.now(); r = await call(); ms.push(performance.now() - s); }
  const total = performance.now() - begin, sorted = [...ms].sort((a, b) => a - b);
  Object.assign(out, { runs, fps: runs / (total / 1000), median_ms: q(sorted, 0.5), p90_ms: q(sorted, 0.9) });
  if (task === "classify") out.found = r.slice(0, 3).map((x) => [x.label, +x.score.toFixed(3)]);
  else if (task === "objects") out.found = r.map((x) => [x.label, +x.score.toFixed(2), ...Object.values(x.box).map(Math.round)]).slice(0, 12), out.n = r.length;
  else out.found = { type: r.constructor?.name, width: r.width, height: r.height, channels: r.channels };
  out.resources = performance.getEntriesByType("resource").map((e) => ({ url: e.name, encoded: e.encodedBodySize }));
  return out;
}
self.onmessage = async (e) => {
  try { self.postMessage({ ok: true, result: await job(e.data) }); }
  catch (err) { self.postMessage({ ok: false, error: String(err?.stack ?? err) }); }
};
