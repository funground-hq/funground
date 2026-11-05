"""Embed Imagenette-160 (train split) with DINOv2-small q8, 150 per class x 10 classes, 4 processes x 1 thread.
Usage: embed_in.py <imagenette2-160 dir> <model.onnx> <out_prefix>. Reuses ../embed.py's prepare and worker."""
import os, sys, glob
os.environ["ORT_DISABLE_TELEMETRY"] = "1"
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np
from multiprocessing import Pool
import embed
if __name__ == "__main__":
    root, model, out = sys.argv[1:4]; rng = np.random.default_rng(0); files, labels = [], []
    for c in sorted(d for d in os.listdir(f"{root}/train") if d.startswith("n")):
        fs = sorted(glob.glob(f"{root}/train/{c}/*.JPEG")); fs = [fs[i] for i in sorted(rng.choice(len(fs), 150, replace=False))]
        files += fs; labels += [c] * len(fs)
    with Pool(4, embed.init, (model,)) as p: X = np.array(p.map(embed.emb, files, chunksize=8), np.float32)
    np.save(out + "_X.npy", X); np.save(out + "_y.npy", np.array(labels)); print(X.shape)
