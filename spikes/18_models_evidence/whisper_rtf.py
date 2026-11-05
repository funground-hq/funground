"""Spike 18 part 2: real-time factor on an otherwise idle machine, 1 and 4 threads.

    venv_w/bin/python -I whisper_rtf.py MODEL_DIR MANIFEST.jsonl N OUT.json

First N clips of the manifest, clean audio. One warm-up call, then best of 2 per clip. RTF = seconds of compute / seconds of
audio (under 1 = faster than real time). Whisper always encodes a 30 s window, so short clips have higher RTF.
"""
import json, os, sys, time
os.environ["ORT_DISABLE_TELEMETRY"] = "1"
import numpy as np, soundfile as sf
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from whisper_eval import W
folder, man, n, outp = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4]
items = [json.loads(l) for l in open(man)][:n]
res = {"model": folder.rstrip("/").split("/")[-1], "clips": n}
for th in (1, 4):
    w = W(folder, th); clips = [sf.read(it["wav"], dtype="float32")[0] for it in items]
    w.transcribe(clips[0])
    rt, secs = [], []
    for a in clips:
        best = min((lambda: (lambda t: (w.transcribe(a), time.perf_counter() - t)[1])(time.perf_counter()))() for _ in range(2))
        rt.append(best / (len(a) / 16000)); secs.append(best)
    res[f"threads_{th}"] = {"rtf_median": round(float(np.median(rt)), 3), "rtf_max": round(float(np.max(rt)), 3),
                            "s_per_utt_median": round(float(np.median(secs)), 3), "audio_s_median": round(float(np.median([len(a) / 16000 for a in clips])), 2)}
json.dump(res, open(outp, "w"), indent=1); print(json.dumps(res))
