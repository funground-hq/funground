"""Spike 18: fetch Indian English test utterances from EdAcc (edinburghcstr/edacc, CC BY-SA 4.0) by HTTP range reads.

    venv_w/bin/python -I fetch_edacc.py REVISION OUT_DIR MAX_UTTS    (seed 18)

Reads only the 'accent' column of each test parquet, then only the row groups holding 'Indian English' rows.
Writes 16 kHz wavs and OUT_DIR/edacc_indian.jsonl (a manifest for whisper_eval.py). Audio stays out of the repo.
"""
import io, json, os, random, sys
import numpy as np, pyarrow.parquet as pq, soundfile as sf
from huggingface_hub import HfFileSystem
from scipy.signal import resample_poly
rev, out, cap = sys.argv[1], sys.argv[2], int(sys.argv[3])
fs = HfFileSystem()
files = sorted(f for f in fs.ls(f"datasets/edinburghcstr/edacc@{rev}/data", detail=False) if "/test-" in f)
cands = []
for f in files:
    pf = pq.ParquetFile(fs.open(f, "rb", block_size=1 << 20))
    for g in range(pf.num_row_groups):
        acc = pf.read_row_group(g, columns=["accent"]).column(0).to_pylist()
        cands += [(f, g, i) for i, a in enumerate(acc) if a == "Indian English"]
    print(f, len(cands), flush=True)
rng = random.Random(18); rng.shuffle(cands); pick = sorted(cands[:cap])
rows = []
by = {}
for f, g, i in pick: by.setdefault((f, g), []).append(i)
for (f, g), idx in by.items():
    pf = pq.ParquetFile(fs.open(f, "rb", block_size=1 << 20))
    t = pf.read_row_group(g, columns=["speaker", "text", "accent", "gender", "l1", "audio"]).to_pylist()
    for i in idx:
        r = t[i]; a, sr = sf.read(io.BytesIO(r["audio"]["bytes"]), dtype="float32")
        if a.ndim > 1: a = a.mean(1)
        if sr != 16000: a = resample_poly(a, 16000, sr).astype(np.float32)
        if len(a) > 30 * 16000 or not r["text"].strip(): continue
        uid = f"edacc_{r['speaker']}_{os.path.basename(f)[:10]}_{g}_{i}"
        p = f"{out}/{uid}.wav"; sf.write(p, a, 16000, subtype="PCM_16")
        rows.append({"id": uid, "group": "indian_edacc", "speaker": r["speaker"], "wav": p, "ref": r["text"], "l1": r["l1"]})
with open(f"{out}/edacc_indian.jsonl", "w") as fo:
    for r in rows: fo.write(json.dumps(r) + "\n")
print(len(rows), "utterances,", len({r["speaker"] for r in rows}), "speakers")
