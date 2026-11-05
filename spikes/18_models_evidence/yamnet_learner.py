"""Spike 18 part 1: how a learner-facing helper could pick a better name from YAMNet's window scores.

    venv_y/bin/python -I yamnet_learner.py YAMNET.onnx CLASS_MAP.csv ESC50_DIR OUT.json

ONNX only (yamnet_compare.py shows the file equals Google's model to 7e-5). For the clean ESC-50 classes in
yamnet_analyse.CLEAN, the share with the right name in the top 1 / top 3 under four ways of making the clip score:
mean over windows (Google's demo), max over windows, and each with 'Silence' and broad parent names left out.
The parent list was written AFTER seeing which top-1 names were common (yamnet_summary.json), so the gain it shows is optimistic: a held-out check is still needed.
"""
import csv, json, os, sys
os.environ["ORT_DISABLE_TELEMETRY"] = "1"
import numpy as np, soundfile as sf, onnxruntime as ort
from scipy.signal import resample_poly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from yamnet_analyse_clean import CLEAN

GENERIC = ["Silence", "Animal", "Domestic animals, pets", "Livestock, farm animals, working animals", "Wild animals", "Vehicle",
           "Motor vehicle (road)", "Rail transport", "Aircraft", "Water", "Liquid", "Inside, small room", "Outside, rural or natural",
           "Outside, urban or manmade", "Speech", "Music", "Sound effect", "Mechanisms", "Bell", "Crying, sobbing", "Wood", "Bird",
           "Insect", "Engine", "Clock", "Tools", "Fowl"]
if __name__ == "__main__":
    onnx_path, cmap, esc, outp = sys.argv[1:5]
    names = [r["display_name"] for r in csv.DictReader(open(cmap, encoding="utf-8"))]
    so = ort.SessionOptions(); so.intra_op_num_threads = 1
    s = ort.InferenceSession(onnx_path, so, providers=["CPUExecutionProvider"])
    drop = np.array([names.index(g) for g in GENERIC])
    meta = [m for m in csv.DictReader(open(f"{esc}/meta/esc50.csv")) if m["category"] in CLEAN]
    tally = {k: [0, 0] for k in ["mean", "max", "mean_no_generic", "max_no_generic"]}
    per = {}
    for m in meta:
        x, sr = sf.read(f"{esc}/audio/{m['filename']}", dtype="float32")
        sc = s.run(None, {"waveform": resample_poly(x, 160, 441).astype(np.float32)})[0]
        ok = {names.index(n) for n in CLEAN[m["category"]]}
        for k in tally:
            v = (sc.mean(0) if k.startswith("mean") else sc.max(0)).copy()
            if "no_generic" in k: v[drop] = -1
            # a name that is itself a "right" answer is never dropped
            if "no_generic" in k:
                for i in ok: v[i] = (sc.mean(0) if k.startswith("mean") else sc.max(0))[i]
            t3 = list(np.argsort(v)[::-1][:3])
            tally[k][0] += t3[0] in ok; tally[k][1] += any(i in ok for i in t3)
            per.setdefault(m["category"], {}).setdefault(k, [0, 0, 0])
            p = per[m["category"]][k]; p[0] += t3[0] in ok; p[1] += any(i in ok for i in t3); p[2] += 1
    n = len(meta)
    res = {"clips": n, "classes": len(per), "generic_left_out": GENERIC,
           "share": {k: {"top1": round(a / n, 3), "top3": round(b / n, 3)} for k, (a, b) in tally.items()},
           "per_class": {c: {k: [round(a / t, 2), round(b / t, 2)] for k, (a, b, t) in v.items()} for c, v in per.items()}}
    json.dump(res, open(outp, "w"), indent=1); print(json.dumps(res["share"]))
