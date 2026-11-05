"""Spike 18 part 1: compare YAMNet ONNX files with Google's TensorFlow YAMNet (TF Hub google/yamnet/1), window by window.

    venv_y/bin/python -I yamnet_compare.py GOOGLE_SAVED_MODEL ESC50_DIR OUT.jsonl NAME=ONNX [NAME=ONNX ...]

Every clip is read, resampled 44.1 kHz -> 16 kHz once (scipy resample_poly 160/441, the same samples go to every model),
and run through Google's model (TF, 1 thread) and each ONNX file (onnxruntime, 1 thread). Edge cases are added first.
One json line per clip and file: window counts, largest absolute score difference, per-window top-1/top-3 agreement,
clip (mean over windows) top-1/top-3 agreement, and the top 3 names of both. Partial results survive a stop.
"""
import csv, json, os, sys
os.environ["ORT_DISABLE_TELEMETRY"] = "1"; os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"; os.environ["CUDA_VISIBLE_DEVICES"] = ""
import numpy as np, soundfile as sf
from scipy.signal import resample_poly
import tensorflow as tf
tf.config.threading.set_intra_op_parallelism_threads(1); tf.config.threading.set_inter_op_parallelism_threads(1)
import onnxruntime as ort


def top(v, n): return list(np.argsort(v)[::-1][:n])


def compare(g, o):
    """g, o: (windows, 521) scores. Returns agreement numbers (windows compared up to the shorter one)."""
    n = min(len(g), len(o))
    gw, ow = g[:n], o[:n]
    w1 = [top(a, 1)[0] == top(b, 1)[0] for a, b in zip(gw, ow)]
    w3 = [set(top(a, 3)) == set(top(b, 3)) for a, b in zip(gw, ow)]
    gm, om = g.mean(0), o.mean(0)
    return {"win_g": len(g), "win_o": len(o), "max_abs_diff": float(np.abs(gw - ow).max()) if n else None,
            "mean_abs_diff": float(np.abs(gw - ow).mean()) if n else None,
            "win_top1_agree": float(np.mean(w1)) if n else None, "win_top3_set_agree": float(np.mean(w3)) if n else None,
            "clip_max_abs_diff": float(np.abs(gm - om).max()), "clip_top1_agree": top(gm, 1) == top(om, 1),
            "clip_top3_set_agree": set(top(gm, 3)) == set(top(om, 3)), "clip_top3_order_agree": top(gm, 3) == top(om, 3)}


if __name__ == "__main__":
    gdir, esc, out = sys.argv[1:4]
    names = [r["display_name"] for r in csv.DictReader(open(f"{gdir}/assets/yamnet_class_map.csv", encoding="utf-8"))]
    google = tf.saved_model.load(gdir)
    so = ort.SessionOptions(); so.intra_op_num_threads = 1; so.inter_op_num_threads = 1
    onnx = {}
    for spec in sys.argv[4:]:
        k, p = spec.split("=", 1); s = ort.InferenceSession(p, so, providers=["CPUExecutionProvider"]); onnx[k] = s
    meta = list(csv.DictReader(open(f"{esc}/meta/esc50.csv")))
    rng = np.random.default_rng(18)
    def esc_audio(fn):
        x, sr = sf.read(f"{esc}/audio/{fn}", dtype="float32"); assert sr == 44100
        return resample_poly(x, 160, 441).astype(np.float32)
    first = esc_audio(meta[0]["filename"])
    edge = [("edge_silence_1s", np.zeros(16000, np.float32)), ("edge_silence_5s", np.zeros(80000, np.float32)),
            ("edge_short_0.5s", first[:8000]), ("edge_short_0.1s", first[:1600]), ("edge_exact_0.96s", first[:15360]),
            ("edge_empty_0s", np.zeros(0, np.float32)),
            ("edge_clipped_x20", np.clip(first * 20, -1, 1)), ("edge_quiet_x0.001", first * 0.001),
            ("edge_white_noise", (rng.standard_normal(80000) * 0.1).astype(np.float32))]
    done = set()
    if os.path.exists(out):
        for l in open(out): done.add(json.loads(l)["clip"])
    with open(out, "a") as fo:
        items = [(n, a, None) for n, a in edge] + [(m["filename"], None, m) for m in meta]
        for clip, audio, m in items:
            if clip in done: continue
            if audio is None: audio = esc_audio(clip)
            rec = {"clip": clip, "category": m["category"] if m else None, "fold": int(m["fold"]) if m else None, "seconds": len(audio) / 16000}
            try:
                g = google(tf.constant(audio))[0].numpy()
            except Exception as e:
                g = None; rec["google_error"] = repr(e)[:200]
            if g is not None:
                gm = g.mean(0); rec["google_top3"] = [names[i] for i in top(gm, 3)]; rec["google_top3_scores"] = [round(float(gm[i]), 4) for i in top(gm, 3)]
            for k, s in onnx.items():
                try:
                    o = s.run(None, {s.get_inputs()[0].name: audio})[0]
                    rec[k] = {"top3": [names[i] for i in top(o.mean(0), 3)]}
                    if g is not None: rec[k].update(compare(g, o))
                except Exception as e:
                    rec[k] = {"error": repr(e)[:200]}
            fo.write(json.dumps(rec) + "\n"); fo.flush()
