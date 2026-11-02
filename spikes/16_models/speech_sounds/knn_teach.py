"""S-231 "a model the learner teaches": nearest-neighbour on picture embeddings, DINOv2-small q8 against MobileNetV4-small.

    knn_teach.py PHOTO_DIR DINO_ONNX MNV4_POOLED_ONNX [--splits 200]

PHOTO_DIR holds <class>_<n>.jpg. Per split, 3 pictures per class are "taught" (their embeddings stored with the class name) and
the rest are test pictures: each gets the class of its nearest taught picture (k=1) or the majority of its 3 nearest (k=3),
by cosine similarity. "How sure" = best class's top similarity minus the runner-up class's top similarity.
Prints one json document. MNV4_POOLED_ONNX is MobileNetV4 with its flattened pre-classifier vector (1280) as an extra output
(made by make_pooled.py), the first output being the 1000 class scores which we ignore.
"""
import glob, json, os, sys, time
os.environ["ORT_DISABLE_TELEMETRY"] = "1"
import numpy as np
import onnxruntime as ort
from PIL import Image

MEAN, STD = np.array([0.485, 0.456, 0.406]), np.array([0.229, 0.224, 0.225])


def prepare(path):
    """Shortest edge 256 (bicubic), centre crop 224, mean/std: the same for both models."""
    im = Image.open(path).convert("RGB"); w, h = im.size; k = 256 / min(w, h)
    im = im.resize((round(w * k), round(h * k)), Image.BICUBIC); l, t = (im.width - 224) // 2, (im.height - 224) // 2
    x = (np.asarray(im.crop((l, t, l + 224, t + 224)), np.float32) / 255 - MEAN) / STD
    return x.transpose(2, 0, 1)[None].astype(np.float32)


def embedder(onnx_path, pick):
    s = ort.InferenceSession(onnx_path, providers=["CPUExecutionProvider"]); name = s.get_inputs()[0].name
    def embed(x):
        v = pick(s.run(None, {name: x})); return v / np.linalg.norm(v)
    return embed


def knn(taught, labels, v, k):
    sims = taught @ v; order = np.argsort(-sims)
    votes = {}
    for i in order[:k]: votes[labels[i]] = votes.get(labels[i], 0) + 1
    best = max(votes.values()); winners = [c for c in votes if votes[c] == best]
    guess = next(labels[i] for i in order if labels[i] in winners)           # ties: the nearest of the tied classes
    top = {c: max(sims[j] for j in range(len(labels)) if labels[j] == c) for c in set(labels)}
    ranked = sorted(top.values(), reverse=True)
    return guess, float(ranked[0] - ranked[1])


def main(photo_dir, dino, mnv4, splits):
    files = sorted(glob.glob(f"{photo_dir}/*.jpg")); classes = [os.path.basename(f).rsplit("_", 1)[0] for f in files]
    xs = [prepare(f) for f in files]
    models = {"dinov2_small_q8": embedder(dino, lambda o: o[0][0, 0]), "mobilenetv4_small_pooled": embedder(mnv4, lambda o: o[1][0])}
    out = {"pictures": len(files), "per_class": {c: classes.count(c) for c in sorted(set(classes))}, "splits": splits}
    for mname, embed in models.items():
        embed(xs[0])                                                          # warm up
        ms, vecs = [], []
        for x in xs:
            t = time.perf_counter(); vecs.append(embed(x)); ms.append((time.perf_counter() - t) * 1000)
        V = np.array(vecs); rec = {"dim": int(V.shape[1]), "ms_per_picture_median": round(float(np.median(ms)), 1)}
        rng = np.random.default_rng(1234)
        for k in (1, 3):
            acc, margins_ok, margins_bad, per_class = [], [], [], {c: [] for c in set(classes)}
            for _ in range(splits):
                taught = []
                for c in sorted(set(classes)):
                    idx = [i for i, cc in enumerate(classes) if cc == c]; taught += list(rng.choice(idx, 3, replace=False))
                test = [i for i in range(len(files)) if i not in taught]
                T, L = V[taught], [classes[i] for i in taught]
                right = 0
                for i in test:
                    g, margin = knn(T, L, V[i], k); ok = g == classes[i]; right += ok; per_class[classes[i]].append(ok)
                    (margins_ok if ok else margins_bad).append(margin)
                acc.append(right / len(test))
            rec[f"k{k}"] = {"accuracy_mean": round(float(np.mean(acc)), 3), "accuracy_min": round(float(np.min(acc)), 3), "accuracy_max": round(float(np.max(acc)), 3),
                            "per_class": {c: round(float(np.mean(v)), 3) for c, v in sorted(per_class.items())},
                            "margin_when_right_median": round(float(np.median(margins_ok)), 3), "margin_when_wrong_median": round(float(np.median(margins_bad)), 3) if margins_bad else None,
                            "wrong_answers": len(margins_bad), "test_answers": len(margins_ok) + len(margins_bad)}
        out[mname] = rec
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    a = [x for x in sys.argv[1:]]; n = 200
    if "--splits" in a: i = a.index("--splits"); n = int(a[i + 1]); del a[i:i + 2]
    main(a[0], a[1], a[2], n)
