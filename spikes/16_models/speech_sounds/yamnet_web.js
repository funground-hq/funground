// S-231 sounds: YAMNet ONNX on onnxruntime-web. Same steps as yamnet_desktop.py: raw 16 kHz waveform in, mean of the window rows out.
// Imported by worker.js. `load(path)` returns an ArrayBuffer (json files are parsed by the loader, csv comes as bytes).
function parseNames(buf) {   // yamnet_class_map.csv: index,mid,"display name"
  const lines = new TextDecoder().decode(buf).trim().split(/\r?\n/).slice(1);
  return lines.map((l) => { const m = l.match(/^\d+,[^,]+,(.*)$/); return m[1].replace(/^"|"$/g, ""); });
}

export class Yamnet {
  static async create(ort, load) {
    const y = new Yamnet(); y.ort = ort;
    y.session = await ort.InferenceSession.create(await load("yam_a/yamnet.onnx"), { executionProviders: ["wasm"], graphOptimizationLevel: "all" });
    y.names = parseNames(await load("yam_a/yamnet_class_map.csv"));
    return y;
  }
  async classify(audio) {
    const out = await this.session.run({ [this.session.inputNames[0]]: new this.ort.Tensor("float32", audio, [audio.length]) });
    const s = out[this.session.outputNames[0]], rows = s.dims[0], n = s.dims[1], mean = new Float32Array(n);
    for (let r = 0; r < rows; r++) for (let c = 0; c < n; c++) mean[c] += s.data[r * n + c] / rows;
    const top = [...mean.keys()].sort((a, b) => mean[b] - mean[a]).slice(0, 3).map((i) => [this.names[i], +mean[i].toFixed(4)]);
    return { windows: rows, mean: Array.from(mean, (v) => +v.toFixed(5)), top };
  }
}
