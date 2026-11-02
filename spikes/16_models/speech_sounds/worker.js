// S-231 speech and sounds: module worker. Loads onnxruntime-web (exact version, CDN), runs one task, posts {ok, result}.
// Message in: {task: "whisper" | "yamnet", threads, version, base}. Files come from our own server under /m/ (models) and /a/ (audio).
import { Whisper } from "./whisper_web.js";
import { Yamnet } from "./yamnet_web.js";
const CDN = (v) => `https://cdn.jsdelivr.net/npm/onnxruntime-web@${v}/dist/`;

function wavSamples(buf) {   // 16-bit PCM mono 16 kHz wav -> Float32Array
  const v = new DataView(buf); let p = 12;
  while (p < buf.byteLength) {
    const id = String.fromCharCode(v.getUint8(p), v.getUint8(p + 1), v.getUint8(p + 2), v.getUint8(p + 3)), size = v.getUint32(p + 4, true);
    if (id === "data") { const n = size / 2, out = new Float32Array(n); for (let i = 0; i < n; i++) out[i] = v.getInt16(p + 8 + 2 * i, true) / 32768; return out; }
    p += 8 + size;
  }
  throw new Error("no data chunk");
}
const median = (a) => [...a].sort((x, y) => x - y)[Math.floor(a.length / 2)];

async function job({ task, threads, version, base }) {
  const out = { task, threads, version, where: "worker", isolated: self.crossOriginIsolated };
  const t0 = performance.now();
  const ort = await import(`${CDN(version)}ort.wasm.mjs`);
  ort.env.wasm.wasmPaths = CDN(version); ort.env.wasm.numThreads = threads; ort.env.logLevel = "error";
  out.import_ms = performance.now() - t0;
  let bytes = 0;
  const load = async (path) => { const r = await fetch(`${base}/m/${path}`); if (path.endsWith(".json")) return r.json(); const b = await r.arrayBuffer(); bytes += b.byteLength; return b; };
  const names = task === "whisper" ? ["tts", "gettysburg"] : ["dog", "clap", "whistle", "speech"];
  const clips = {};
  for (const name of names) clips[name] = wavSamples(await (await fetch(`${base}/a/${name}.wav`)).arrayBuffer());
  out.clips = {};
  if (task === "whisper") {
    const m = await Whisper.create(ort, load, "whisper_tiny_en");
    out.model_bytes = bytes; out.ready_ms = performance.now() - t0;   // download from localhost + session creation
    for (const [name, audio] of Object.entries(clips)) {
      const runs = []; let text;
      for (let i = 0; i < 3; i++) { const s = performance.now(); text = await m.transcribe(audio); runs.push((performance.now() - s) / 1000); }
      out.clips[name] = { seconds: audio.length / 16000, run_s: runs, rtf: Math.min(...runs) / (audio.length / 16000), rtf_first: runs[0] / (audio.length / 16000), text };
    }
  } else {
    const m = await Yamnet.create(ort, load);
    out.model_bytes = bytes; out.ready_ms = performance.now() - t0;
    for (const [name, audio] of Object.entries(clips)) {
      const ms = []; let res;
      for (let i = 0; i < 5; i++) { const s = performance.now(); res = await m.classify(audio); ms.push(performance.now() - s); }
      const one = []; for (let i = 0; i < 20; i++) { const s = performance.now(); await m.classify(audio.subarray(0, 15360)); one.push(performance.now() - s); }
      out.clips[name] = { seconds: audio.length / 16000, windows: res.windows, ms_single_window_call: median(one), ms_per_clip: median(ms), ms_per_window: median(ms) / res.windows, scores: res.mean, top: res.top };
    }
  }
  out.resources = performance.getEntriesByType("resource").map((e) => ({ url: e.name, encoded: e.encodedBodySize }));
  return out;
}
self.onmessage = async (e) => {
  try { self.postMessage({ ok: true, result: await job(e.data) }); }
  catch (err) { self.postMessage({ ok: false, error: String(err?.stack ?? err) }); }
};
