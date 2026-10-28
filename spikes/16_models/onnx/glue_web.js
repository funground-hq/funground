// S-231 spike: the JavaScript twin of ort_glue.py (same steps, same constants), for onnxruntime-web in a module worker.
// Frames are 640 x 480 OffscreenCanvas objects. `ort` is passed in (the module is loaded by the worker from the CDN).
// Points come back in frame pixels, as in the Python glue. Lines are counted (non-blank, non-comment) for results.md.

const sigmoid = (x) => 1 / (1 + Math.exp(-Math.max(-50, Math.min(50, x))));

// Cut a square `side` px wide, centred on (cx, cy), turned by `angle`, resample to out x out (black outside).
// Returns RGBA pixels and toFrame(): crop pixels -> frame pixels. The canvas transform is the inverse of toFrame.
export function warp(frame, cx, cy, side, angle, out) {
  const c = Math.cos(angle), s = Math.sin(angle), k = side / out;
  const a = k * c, b = -k * s, e0 = cx - 0.5 * side * (c - s), d = k * s, e = k * c, f = cy - 0.5 * side * (s + c);
  const det = a * e - b * d;
  const canvas = new OffscreenCanvas(out, out), g = canvas.getContext("2d", { willReadFrequently: true });
  g.fillStyle = "#000"; g.fillRect(0, 0, out, out);
  g.imageSmoothingQuality = "high";
  g.setTransform(e / det, -d / det, -b / det, a / det, (b * f - e * e0) / det, (d * e0 - a * f) / det);   // frame -> crop
  g.drawImage(frame, 0, 0);
  const toFrame = (p) => p.map(([u, v]) => [a * u + b * v + e0, d * u + e * v + f]);
  return { rgba: g.getImageData(0, 0, out, out).data, toFrame, scale: k };
}

// RGBA bytes -> Float32Array, NHWC or NCHW, with (value / 255 - mean) / std per channel
function tensor(rgba, n, { nchw = false, mean = [0, 0, 0], std = [1, 1, 1], div = 255, bgr = false } = {}) {
  const out = new Float32Array(n * n * 3);
  for (let i = 0; i < n * n; i++) for (let ch = 0; ch < 3; ch++) {
    const v = (rgba[i * 4 + (bgr ? 2 - ch : ch)] / div - mean[ch]) / std[ch];
    out[nchw ? ch * n * n + i : i * 3 + ch] = v;
  }
  return out;
}

// SSD anchor centres, 2 per cell, layers of equal stride merged (as in MediaPipe's detector configs)
export function anchors(size, strides) {
  const out = [];
  for (let i = 0; i < strides.length;) {
    let j = i; while (j < strides.length && strides[j] === strides[i]) j++;
    const g = Math.ceil(size / strides[i]);
    for (let y = 0; y < g; y++) for (let x = 0; x < g; x++) for (let r = 0; r < 2 * (j - i); r++) out.push([(x + .5) / g, (y + .5) / g]);
    i = j;
  }
  return out;
}

// Region of interest from a detection: turn so key point k0 -> k1 points up, grow the box, shift along its up axis.
function roi(frame, [cx, cy, w, h], [x0, y0], [x1, y1], scale, shiftY, out) {
  let ang = Math.PI / 2 - Math.atan2(-(y1 - y0), x1 - x0);
  ang -= 2 * Math.PI * Math.floor((ang + Math.PI) / (2 * Math.PI));
  return warp(frame, cx - shiftY * h * Math.sin(ang), cy + shiftY * h * Math.cos(ang), Math.max(w, h) * scale, ang, out);
}
const letterbox = (frame, out) => warp(frame, frame.width / 2, frame.height / 2, Math.max(frame.width, frame.height), 0, out);
const run = async (sess, ort, data, dims, type = "float32") => sess.run({ [sess.inputNames[0]]: new ort.Tensor(type, data, dims) });

// SSD detector shared by the person and the palm models: best box and key points in frame pixels, or null
async function detect(sess, ort, frame, anc, size, nKp, centre) {
  const { rgba, toFrame, scale } = letterbox(frame, size);
  const first = sess.inputNames[0];
  const isNchw = first.includes(":0");                       // the person detector takes NCHW, the palm detector NHWC
  const x = tensor(rgba, size, { nchw: isNchw, mean: centre ? [.5, .5, .5] : [0, 0, 0], std: centre ? [.5, .5, .5] : [1, 1, 1] });
  const out = await run(sess, ort, x, isNchw ? [1, 3, size, size] : [1, size, size, 3]);
  const o = sess.outputNames.map((n) => out[n]);
  const [reg, sc] = o[0].dims[2] > 1 ? [o[0].data, o[1].data] : [o[1].data, o[0].data];
  const nPer = (2 + nKp) * 2;
  let best = 0; for (let i = 1; i < anc.length; i++) if (sc[i] > sc[best]) best = i;
  if (sigmoid(sc[best]) < 0.5) return null;
  const d = Array.from({ length: 2 + nKp }, (_, j) => [reg[best * nPer + 2 * j], reg[best * nPer + 2 * j + 1]]);
  const [cxy] = toFrame([[(d[0][0] / size + anc[best][0]) * size, (d[0][1] / size + anc[best][1]) * size]]);
  const kps = toFrame(d.slice(2).map(([u, v]) => [(u / size + anc[best][0]) * size, (v / size + anc[best][1]) * size]));
  return { box: [cxy[0], cxy[1], Math.abs(d[1][0]) * scale, Math.abs(d[1][1]) * scale], kps };
}

export class Pose {
  constructor(det, lm, ort) { Object.assign(this, { det, lm, ort, anc: anchors(224, [8, 16, 32, 32, 32]), region: null }); }
  async find(frame) {
    const r = await detect(this.det, this.ort, frame, this.anc, 224, 4, true);
    this.region = r && r.kps.slice(0, 2); return this.region;
  }
  async points(frame) {
    if (!this.region) return null;
    const [[x0, y0], [x1, y1]] = this.region, dist = Math.hypot(x1 - x0, y1 - y0);
    const { rgba, toFrame } = roi(frame, [x0, y0, 2 * dist, 2 * dist], [x0, y0], [x1, y1], 1.25, 0, 256);
    const out = await run(this.lm, this.ort, tensor(rgba, 256), [1, 256, 256, 3]);
    const names = this.lm.outputNames, raw = out[names[0]].data;
    if (out[names[1]].data[0] < 0.5) return null;
    const px = Array.from({ length: 33 }, (_, i) => [raw[i * 5], raw[i * 5 + 1]]);
    return toFrame(px).map(([x, y], i) => [x, y, raw[i * 5 + 2] * 2 * dist * 1.25 / 256, sigmoid(raw[i * 5 + 3])]);
  }
}

export class Hand {
  constructor(det, lm, ort) { Object.assign(this, { det, lm, ort, anc: anchors(192, [8, 16, 16, 16]), box: null }); }
  async find(frame) {
    const r = await detect(this.det, this.ort, frame, this.anc, 192, 7, false);
    this.box = r && [r.box, r.kps[0], r.kps[2]]; return this.box;
  }
  async points(frame) {
    if (!this.box) return null;
    const { rgba, toFrame } = roi(frame, ...this.box, 2.6, -0.5, 224);
    const out = await run(this.lm, this.ort, tensor(rgba, 224), [1, 224, 224, 3]);
    const raw = out[this.lm.outputNames[0]].data;
    if (out[this.lm.outputNames[1]].data[0] < 0.8) return null;
    const px = Array.from({ length: 21 }, (_, i) => [raw[i * 3], raw[i * 3 + 1]]);
    return toFrame(px).map(([x, y], i) => [x, y, raw[i * 3 + 2]]);
  }
}

// MoveNet single pose: 17 points (x, y, score); square input, int32 0..255
export async function movenet(sess, ort, frame) {
  const { rgba, toFrame } = letterbox(frame, 192);
  const x = Int32Array.from(tensor(rgba, 192, { div: 1 }));   // MoveNet takes integers 0..255
  const o = (await run(sess, ort, x, [1, 192, 192, 3], "int32"))[sess.outputNames[0]].data;
  return toFrame(Array.from({ length: 17 }, (_, i) => [o[i * 3 + 1] * 192, o[i * 3] * 192])).map(([x, y], i) => [x, y, o[i * 3 + 2]]);
}

// Resize the whole frame to n x n (stretch) and read the pixels
function stretch(frame, n) {
  const g = new OffscreenCanvas(n, n).getContext("2d", { willReadFrequently: true });
  g.imageSmoothingQuality = "high"; g.drawImage(frame, 0, 0, n, n);
  return g.getImageData(0, 0, n, n).data;
}

// MediaPipe selfie model as ONNX: 256 x 256, 0..1, returns the number of person pixels at 256 x 256 (mask > 0.5) and the mask
export async function selfie(sess, ort, frame) {
  const o = (await run(sess, ort, tensor(stretch(frame, 256), 256, { nchw: true }), [1, 3, 256, 256]))[sess.outputNames[0]].data;
  return { mask: o, count: o.reduce((n, v) => n + (v > 0.5), 0) };
}

// PP-HumanSeg (OpenCV Zoo): 192 x 192, mean/std 0.5; person where class 1 beats class 0
export async function humanseg(sess, ort, frame) {
  const o = (await run(sess, ort, tensor(stretch(frame, 192), 192, { nchw: true, mean: [.5, .5, .5], std: [.5, .5, .5] }), [1, 3, 192, 192]))[sess.outputNames[0]].data;
  let n = 0; for (let i = 0; i < 192 * 192; i++) n += o[192 * 192 + i] > o[i];
  return { count: n };
}

// YuNet: 640 x 640 canvas with the frame top-left, BGR 0..255; best face (x, y, w, h, score, 5 points)
export async function yunet(sess, ort, frame) {
  const g = new OffscreenCanvas(640, 640).getContext("2d", { willReadFrequently: true });
  g.fillStyle = "#000"; g.fillRect(0, 0, 640, 640); g.drawImage(frame, 0, 0);
  const o = await run(sess, ort, tensor(g.getImageData(0, 0, 640, 640).data, 640, { nchw: true, bgr: true, div: 1 }), [1, 3, 640, 640]);
  const out = sess.outputNames.map((n) => o[n].data);
  let best = null;
  [8, 16, 32].forEach((s, n) => {
    const cls = out[n], obj = out[3 + n], bb = out[6 + n], kp = out[9 + n], gcols = 640 / s;
    for (let i = 0; i < cls.length; i++) {
      const sc = Math.sqrt(Math.min(Math.max(cls[i], 0), 1) * Math.min(Math.max(obj[i], 0), 1));
      if (sc > 0.6 && (!best || sc > best.score)) {
        const r = Math.floor(i / gcols), c = i % gcols, w = Math.exp(bb[i * 4 + 2]) * s, h = Math.exp(bb[i * 4 + 3]) * s;
        best = { score: sc, box: [(c + bb[i * 4]) * s - w / 2, (r + bb[i * 4 + 1]) * s - h / 2, w, h],
                 points: Array.from({ length: 5 }, (_, j) => [(kp[i * 10 + 2 * j] + c) * s, (kp[i * 10 + 2 * j + 1] + r) * s]) };
      }
    }
  });
  return best;
}

// ImageNet preprocessing for MobileNetV4: shortest edge 256, centre crop 224, mean/std. Returns the tensor data.
function imagenetInput(frame) {
  const k = 256 / Math.min(frame.width, frame.height), w = Math.round(frame.width * k), h = Math.round(frame.height * k);
  const g = new OffscreenCanvas(224, 224).getContext("2d", { willReadFrequently: true });
  g.imageSmoothingQuality = "high"; g.drawImage(frame, -(w - 224) / 2 | 0, -(h - 224) / 2 | 0, w, h);
  return tensor(g.getImageData(0, 0, 224, 224).data, 224, { nchw: true, mean: [0.485, 0.456, 0.406], std: [0.229, 0.224, 0.225] });
}
export async function classify(sess, ort, frame, labels) {
  const lg = (await run(sess, ort, imagenetInput(frame), [1, 3, 224, 224]))[sess.outputNames[0]].data;
  const m = Math.max(...lg), e = Array.from(lg, (v) => Math.exp(v - m)), t = e.reduce((a, b) => a + b);
  return e.map((v, i) => [i, v / t]).sort((a, b) => b[1] - a[1]).slice(0, 5).map(([i, p]) => [labels[i], p]);
}
export async function embed(sess, ort, frame) {
  const o = (await run(sess, ort, imagenetInput(frame), [1, 3, 224, 224]))[sess.outputNames[0]];
  const v = o.dims.length === 3 ? o.data.slice(0, o.dims[2]) : o.data;          // DINOv2: the first token (CLS)
  const n = Math.hypot(...v); return Array.from(v, (x) => x / n);
}

// D-FINE nano: 640 x 640 stretched, 0..1; boxes are (cx, cy, w, h) as fractions
export async function objects(sess, ort, frame, labels, threshold = 0.4) {
  const o = await run(sess, ort, tensor(stretch(frame, 640), 640, { nchw: true }), [1, 3, 640, 640]);
  const logits = o[sess.outputNames[0]].data, boxes = o[sess.outputNames[1]].data, found = [];
  for (let q = 0; q < 300; q++) {
    let c = 0, s = -1e9; for (let j = 0; j < 80; j++) if (logits[q * 80 + j] > s) { s = logits[q * 80 + j]; c = j; }
    if (sigmoid(s) > threshold) { const [cx, cy, w, h] = [...boxes.slice(q * 4, q * 4 + 4)]; found.push([labels[c], sigmoid(s), (cx - w / 2) * frame.width, (cy - h / 2) * frame.height, w * frame.width, h * frame.height]); }
  }
  return found;
}
