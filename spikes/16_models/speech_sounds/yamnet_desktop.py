"""S-231 sounds: YAMNet ONNX (audiomagic/yamnet-onnx) on onnxruntime, desktop.

    yamnet_desktop.py MODEL_DIR WAV16K [WAV16K ...]  [--other OTHER_DIR]   -> one json line per clip

MODEL_DIR holds yamnet.onnx and yamnet_class_map.csv. The graph takes the raw 16 kHz waveform (mel front end inside),
and returns one row per 0.96 s window (hop 0.48 s). The clip's score is the mean of the rows, as in Google's demo.
--other: a second conversion (zeropointnine/yamnet-onnx); its scores for the same clip are compared with the first.
"""
import csv, json, os, sys, time
os.environ["ORT_DISABLE_TELEMETRY"] = "1"
import numpy as np
import onnxruntime as ort
import soundfile as sf


def load(folder):
    names = [r["display_name"] for r in csv.DictReader(open(f"{folder}/yamnet_class_map.csv", encoding="utf-8"))]
    return ort.InferenceSession(f"{folder}/yamnet.onnx", providers=["CPUExecutionProvider"]), names


def classify(session, audio):
    scores = session.run(None, {session.get_inputs()[0].name: audio})[0]
    return scores, scores.mean(axis=0)


def top(mean, names, n=3):
    return [[names[i], round(float(mean[i]), 4)] for i in np.argsort(mean)[::-1][:n]]


if __name__ == "__main__":
    args = [a for a in sys.argv[1:]]
    other = None
    if "--other" in args:
        i = args.index("--other"); other = load(args[i + 1]); del args[i:i + 2]
    t0 = time.perf_counter(); sess, names = load(args[0]); load_s = time.perf_counter() - t0
    for path in args[1:]:
        audio, sr = sf.read(path, dtype="float32"); assert sr == 16000
        times = []
        for _ in range(10):
            t = time.perf_counter(); scores, mean = classify(sess, audio); times.append((time.perf_counter() - t) * 1000)
        one = []
        for _ in range(20):
            t = time.perf_counter(); classify(sess, audio[:15360]); one.append((time.perf_counter() - t) * 1000)
        rec = {"clip": os.path.basename(path), "seconds": round(len(audio) / 16000, 2), "windows": len(scores), "load_s": round(load_s, 2),
               "ms_per_clip": round(float(np.median(times)), 1), "ms_per_window_in_clip": round(float(np.median(times)) / len(scores), 1),
               "ms_single_window_call": round(float(np.median(one)), 1), "top3": top(mean, names), "mean": [round(float(v), 5) for v in mean]}
        if other:
            _, m2 = classify(other[0], audio); rec["max_abs_diff_vs_other"] = round(float(np.abs(m2 - mean).max()), 5); rec["top3_other"] = top(m2, names)
        print(json.dumps(rec))
