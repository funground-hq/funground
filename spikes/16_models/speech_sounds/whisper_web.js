// S-231 speech: Whisper tiny.en q8 on onnxruntime-web, our own log-mel and greedy decode loop. Same steps as whisper_desktop.py.
// Imported by worker.js (a module worker). Needs the ort module, a fetcher for the model files, and 16 kHz mono Float32 audio.
const SR = 16000, N_FFT = 400, HOP = 160, N_MELS = 80, CHUNK = 30 * SR, SOT = 50257, NO_TS = 50362, EOS = 50256;

function melFilters() {   // Slaney filterbank, (80 x 201), same as librosa and the desktop script
  const hz2mel = (f) => (f < 1000 ? f / (200 / 3) : 15 + Math.log(f / 1000) / (Math.log(6.4) / 27));
  const mel2hz = (m) => (m < 15 ? m * (200 / 3) : 1000 * Math.exp((Math.log(6.4) / 27) * (m - 15)));
  const nb = N_FFT / 2 + 1, pts = [];
  for (let i = 0; i < N_MELS + 2; i++) pts.push(mel2hz(hz2mel(0) + ((hz2mel(SR / 2) - hz2mel(0)) * i) / (N_MELS + 1)));
  const w = new Float32Array(N_MELS * nb);
  for (let m = 0; m < N_MELS; m++) for (let k = 0; k < nb; k++) {
    const f = (k * SR) / N_FFT, lo = (f - pts[m]) / (pts[m + 1] - pts[m]), hi = (pts[m + 2] - f) / (pts[m + 2] - pts[m + 1]);
    w[m * nb + k] = Math.max(0, Math.min(lo, hi)) * (2 / (pts[m + 2] - pts[m]));
  }
  return w;
}
const FILTERS = melFilters();

export function logMel(audio) {   // -> Float32Array (80 x 3000), row = mel bin
  const x = new Float32Array(CHUNK + N_FFT); // reflect padding by 200 each side, as numpy does
  const body = new Float32Array(CHUNK); body.set(audio.subarray(0, Math.min(audio.length, CHUNK)));
  const P = N_FFT / 2;
  x.set(body, P);
  for (let i = 1; i <= P; i++) { x[P - i] = body[i]; x[P + CHUNK - 1 + i] = body[CHUNK - 1 - i]; }
  const nb = N_FFT / 2 + 1, frames = CHUNK / HOP;
  const win = new Float32Array(N_FFT), cos = new Float32Array(nb * N_FFT), sin = new Float32Array(nb * N_FFT);
  for (let n = 0; n < N_FFT; n++) win[n] = 0.5 - 0.5 * Math.cos((2 * Math.PI * n) / N_FFT);
  for (let k = 0; k < nb; k++) for (let n = 0; n < N_FFT; n++) { const a = (2 * Math.PI * k * n) / N_FFT; cos[k * N_FFT + n] = Math.cos(a); sin[k * N_FFT + n] = Math.sin(a); }
  const lastData = Math.ceil((audio.length + P) / HOP) + 3;   // frames after this see only zeros: one calculation serves them all
  const power = new Float32Array(nb), mel = new Float32Array(N_MELS * frames), seg = new Float32Array(N_FFT);
  let silent = null;
  for (let t = 0; t < frames; t++) {
    let col;
    if (t > lastData && silent) col = silent;
    else {
      for (let n = 0; n < N_FFT; n++) seg[n] = x[t * HOP + n] * win[n];
      for (let k = 0; k < nb; k++) { let re = 0, im = 0; const o = k * N_FFT; for (let n = 0; n < N_FFT; n++) { re += seg[n] * cos[o + n]; im -= seg[n] * sin[o + n]; } power[k] = re * re + im * im; }
      col = new Float32Array(N_MELS);
      for (let m = 0; m < N_MELS; m++) { let s = 0; for (let k = 0; k < nb; k++) s += FILTERS[m * nb + k] * power[k]; col[m] = s; }
      if (t === lastData) silent = col;
    }
    for (let m = 0; m < N_MELS; m++) mel[m * frames + t] = col[m];
  }
  let max = -Infinity;
  for (let i = 0; i < mel.length; i++) { mel[i] = Math.log10(Math.max(mel[i], 1e-10)); if (mel[i] > max) max = mel[i]; }
  for (let i = 0; i < mel.length; i++) mel[i] = (Math.max(mel[i], max - 8) + 4) / 4;
  return mel;
}

function byteDecoder() {   // GPT-2's byte <-> printable character table
  const bs = [], cs = [];
  for (let b = 33; b <= 126; b++) bs.push(b); for (let b = 161; b <= 172; b++) bs.push(b); for (let b = 174; b <= 255; b++) bs.push(b);
  cs.push(...bs); let n = 0;
  for (let b = 0; b < 256; b++) if (!bs.includes(b)) { bs.push(b); cs.push(256 + n++); }
  return new Map(bs.map((b, i) => [String.fromCharCode(cs[i]), b]));
}

export class Whisper {
  static async create(ort, load, folder) {   // load(path) -> ArrayBuffer or parsed json (by extension)
    const w = new Whisper(); w.ort = ort;
    const opts = { executionProviders: ["wasm"], graphOptimizationLevel: "all" };
    w.enc = await ort.InferenceSession.create(await load(`${folder}/onnx/encoder_model_quantized.onnx`), opts);
    w.dec = await ort.InferenceSession.create(await load(`${folder}/onnx/decoder_model_merged_quantized.onnx`), opts);
    const tok = await load(`${folder}/tokenizer.json`), gen = await load(`${folder}/generation_config.json`);
    w.words = []; for (const [t, id] of Object.entries(tok.model.vocab)) w.words[id] = t;
    w.bytes = byteDecoder(); w.suppress = new Set(gen.suppress_tokens); w.beginSuppress = gen.begin_suppress_tokens;
    w.pastNames = w.dec.inputNames.filter((n) => n.startsWith("past_key_values"));
    return w;
  }
  text(ids) {
    const chars = ids.map((i) => this.words[i]).join(""), out = [];
    for (const c of chars) out.push(this.bytes.get(c) ?? 63);
    return new TextDecoder().decode(new Uint8Array(out)).trim();
  }
  async transcribe(audio, maxTokens = 200) {
    const { Tensor } = this.ort;
    const hidden = (await this.enc.run({ input_features: new Tensor("float32", logMel(audio), [1, N_MELS, CHUNK / HOP]) })).last_hidden_state;
    let past = Object.fromEntries(this.pastNames.map((n) => [n, new Tensor("float32", new Float32Array(0), [1, 6, 0, 64])]));
    const out = []; let feed = [SOT, NO_TS], first = true;
    for (let step = 0; step < maxTokens; step++) {
      const res = await this.dec.run({
        input_ids: new Tensor("int64", BigInt64Array.from(feed.map(BigInt)), [1, feed.length]), encoder_hidden_states: hidden,
        use_cache_branch: new Tensor("bool", [!first], [1]), ...past });
      const lg = res.logits, V = lg.dims[2], off = (lg.dims[1] - 1) * V;
      let best = -1, bv = -Infinity;
      for (let v = 0; v < V; v++) { if (this.suppress.has(v) || (!out.length && this.beginSuppress.includes(v))) continue; const s = lg.data[off + v]; if (s > bv) { bv = s; best = v; } }
      if (best === EOS) break;
      out.push(best);
      for (const name of this.dec.outputNames.slice(1)) { const key = name.replace("present", "past_key_values"); if (first || key.includes(".decoder.")) past[key] = res[name]; }
      feed = [best]; first = false;
    }
    return this.text(out);
  }
}
