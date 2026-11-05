"""Embed Rock Paper Scissors pictures with DINOv2-small q8 (CLS token), 4 processes x 1 thread.
Usage: embed.py <rps_dir> <model.onnx> <out_prefix> [per_class=500]"""
import os, sys, glob
os.environ["ORT_DISABLE_TELEMETRY"] = "1"
import numpy as np
from multiprocessing import Pool
from PIL import Image
MEAN, STD = np.array([0.485, 0.456, 0.406]), np.array([0.229, 0.224, 0.225])

def prepare(path):  # the same as spikes/16_models/speech_sounds/knn_teach.py
    im = Image.open(path).convert("RGB"); w, h = im.size; k = 256 / min(w, h)
    im = im.resize((round(w * k), round(h * k)), Image.BICUBIC); l, t = (im.width - 224) // 2, (im.height - 224) // 2
    x = (np.asarray(im.crop((l, t, l + 224, t + 224)), np.float32) / 255 - MEAN) / STD
    return x.transpose(2, 0, 1)[None].astype(np.float32)

S = None
def init(model):
    global S
    import onnxruntime as ort
    o = ort.SessionOptions(); o.intra_op_num_threads = 1; o.inter_op_num_threads = 1
    S = ort.InferenceSession(model, o, providers=["CPUExecutionProvider"])

def emb(p):
    v = S.run(None, {S.get_inputs()[0].name: prepare(p)})[0][0, 0]; return v / np.linalg.norm(v)

if __name__ == "__main__":
    root, model, out = sys.argv[1:4]; n = int(sys.argv[4]) if len(sys.argv) > 4 else 500
    rng = np.random.default_rng(0); files, labels = [], []
    for c in ["paper", "rock", "scissors"]:
        fs = sorted(glob.glob(f"{root}/**/{c}/*.png", recursive=True)); fs = [fs[i] for i in sorted(rng.choice(len(fs), min(n, len(fs)), replace=False))]
        files += fs; labels += [c] * len(fs)
    with Pool(4, init, (model,)) as p: X = np.array(p.map(emb, files, chunksize=8), np.float32)
    np.save(out + "_X.npy", X); np.save(out + "_y.npy", np.array(labels))
    print(X.shape, {c: labels.count(c) for c in set(labels)})
