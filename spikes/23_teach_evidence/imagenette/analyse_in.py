"""Imagenette: k=1 kNN accuracy and the .score floor. Usage: analyse_in.py <prefix> <out.json> [splits=2000]. Seed 235.
Score = f + (1-f) * min(1, margin / M), floor f = 0.5 (fixed) or 1/n (n = classes taught). M fitted (grid, squared error)
on even splits, tested (ECE, 10 bins) on odd splits."""
import sys, json
import numpy as np
X = np.load(sys.argv[1] + "_X.npy"); y = np.load(sys.argv[1] + "_y.npy"); N = int(sys.argv[3]) if len(sys.argv) > 3 else 2000
CL = sorted(set(y)); idx = {c: np.where(y == c)[0] for c in CL}; rng = np.random.default_rng(235); TP = 40
def ece(p, ok):
    e = 0; ed = np.linspace(0, 1, 11)
    for lo, hi in zip(ed[:-1], ed[1:]):
        b = (p >= lo) & ((p < hi) if hi < 1 else (p <= 1))
        if b.sum(): e += b.mean() * abs(p[b].mean() - ok[b].mean())
    return round(float(e), 4)
out = {"pictures": len(y), "classes": len(CL), "splits": N, "test_per_class": TP, "seed": 235, "accuracy": {}}
rows = []
for nc in [2, 3, 4, 5]:
    for n in [3, 5, 10]:
        acc = []
        for s in range(N):
            cls = rng.choice(CL, nc, replace=False); T, tl, Q, ql = [], [], [], []
            for j, c in enumerate(cls):
                p = rng.permutation(idx[c]); T.append(p[:n]); tl += [j] * n; Q.append(p[n:n + TP]); ql += [j] * TP
            T, Q, tl, ql = np.concatenate(T), np.concatenate(Q), np.array(tl), np.array(ql)
            sm = X[Q] @ X[T].T; top = np.stack([sm[:, tl == j].max(1) for j in range(nc)], 1); srt = np.sort(top, 1)
            ok = top.argmax(1) == ql; acc.append(ok.mean())
            rows.append(np.stack([np.full(len(ok), s % 2), srt[:, -1] - srt[:, -2], ok, np.full(len(ok), nc), np.full(len(ok), n)], 1))
        a = np.array(acc); m = a.mean(); se = a.std(ddof=1) / np.sqrt(N)
        out["accuracy"][f"classes{nc}_n{n}"] = {"mean": round(m, 4), "mean_95": [round(m - 1.96 * se, 4), round(m + 1.96 * se, 4)],
            "split_2.5_97.5": [round(float(np.percentile(a, 2.5)), 3), round(float(np.percentile(a, 97.5)), 3)]}
        print(nc, n, round(m, 4), flush=True)
P = np.concatenate(rows); fit, test = P[P[:, 0] == 0], P[P[:, 0] == 1]; grid = np.arange(0.01, 0.6, 0.0025)
sc = lambda m, f, M: f + (1 - f) * np.minimum(1, m / M)
cal = {}
for name, fl in {"floor_0.5": lambda nc: 0.5, "floor_1/n": lambda nc: 1 / nc}.items():
    F = fl(fit[:, 3]); M = min(grid, key=lambda M: ((sc(fit[:, 1], F, M) - fit[:, 2]) ** 2).mean())
    Ft = fl(test[:, 3]); r = {"M": round(float(M), 4), "ece_all": ece(sc(test[:, 1], Ft, M), test[:, 2])}
    for nc in [2, 3, 4, 5]:
        t = test[test[:, 3] == nc]; r[f"ece_classes{nc}"] = ece(sc(t[:, 1], fl(t[:, 3]), M), t[:, 2])
        r[f"margin0_right_classes{nc}"] = round(float(t[t[:, 1] < 0.01, 2].mean()), 4)
    for n in [3, 5, 10]:
        t = test[test[:, 4] == n]; r[f"ece_n{n}"] = ece(sc(t[:, 1], fl(t[:, 3]), M), t[:, 2])
    r["fixed_M_0.075_ece_all"] = ece(sc(test[:, 1], Ft, 0.075), test[:, 2]); cal[name] = r; print(name, r, flush=True)
bins = []
for lo, hi in zip([0, .01, .02, .05, .1, .15, .2, .3], [.01, .02, .05, .1, .15, .2, .3, 1.01]):
    b = (test[:, 1] >= lo) & (test[:, 1] < hi); bins.append({"margin": f"{lo}-{min(hi,1)}", "n": int(b.sum()), "right": round(float(test[b, 2].mean()), 4)})
out["calibration"] = cal; out["bins_test"] = bins; print(bins)
json.dump(out, open(sys.argv[2], "w"), indent=1)
