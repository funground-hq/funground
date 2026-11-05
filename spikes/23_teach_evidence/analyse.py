"""S-235 numbers from saved embeddings. Usage: analyse.py <prefix> <out.json> [splits=2000]
kNN on cosine; k=3 is a majority vote, ties go to the nearest; "how sure" (margin) = best class's top similarity minus
the runner-up class's (as in spikes/16_models/speech_sounds/knn_teach.py). Seeded: numpy default_rng(235)."""
import sys, json, itertools
import numpy as np
X = np.load(sys.argv[1] + "_X.npy"); y = np.load(sys.argv[1] + "_y.npy"); OUT = sys.argv[2]
N = int(sys.argv[3]) if len(sys.argv) > 3 else 2000
CL = sorted(set(y)); idx = {c: np.where(y == c)[0] for c in CL}; TEST_PER = 60
rng = np.random.default_rng(235)

def predict(T, tl, Q, k, nc):
    s = Q @ T.T                                                     # (q, t)
    top = np.full((len(Q), nc), -9.0)
    for c in range(nc):
        if (tl == c).any(): top[:, c] = s[:, tl == c].max(1)
    srt = np.sort(top, 1); margin = srt[:, -1] - srt[:, -2]; topsim = srt[:, -1]
    if k == 1: return top.argmax(1), margin, topsim
    o = np.argsort(-s, 1)[:, :k]; lab = tl[o]
    votes = np.stack([(lab == c).sum(1) for c in range(nc)], 1); best = votes.max(1, keepdims=True)
    win = votes == best; g = np.empty(len(Q), int)
    for i in range(len(Q)): g[i] = next(l for l in lab[i] if win[i, l])   # the nearest of the tied classes
    return g, margin, topsim

def split(classes, n_per, test_per=TEST_PER, counts=None):
    T, tl, Q, ql = [], [], [], []
    for j, c in enumerate(classes):
        n = counts[j] if counts else n_per; p = rng.permutation(idx[c])
        T.append(p[:n]); tl += [j] * n; q = p[n:n + test_per]; Q.append(q); ql += [j] * len(q)
    return np.concatenate(T), np.array(tl), np.concatenate(Q), np.array(ql)

def ci(acc):  # mean of per-split accuracy, 95% percentile interval of the splits and 95% interval of the mean
    a = np.array(acc); m = a.mean(); se = a.std(ddof=1) / np.sqrt(len(a))
    return {"mean": round(m, 4), "mean_95": [round(m - 1.96 * se, 4), round(m + 1.96 * se, 4)],
            "split_2.5_97.5": [round(float(np.percentile(a, 2.5)), 3), round(float(np.percentile(a, 97.5)), 3)]}

out = {"pictures": {c: int(len(idx[c])) for c in CL}, "splits": N, "test_per_class": TEST_PER, "seed": 235}
# 2. accuracy
acc = {}; pool = {1: [], 3: []}   # (setting-id, margin, right) for calibration
for nc in [2, 3]:
    for n in [1, 2, 3, 5, 10, 20]:
        r = {1: [], 3: []}
        for s in range(N):
            cls = list(rng.choice(CL, nc, replace=False)); T, tl, Q, ql = split(cls, n)
            for k in (1, 3):
                g, m, _ = predict(X[T], tl, X[Q], k, nc); ok = g == ql; r[k].append(ok.mean())
                pool[k].append(np.stack([np.full(len(m), s % 2), m, ok, np.full(len(m), n), np.full(len(m), nc)], 1))
        for k in (1, 3): acc[f"classes{nc}_n{n}_k{k}"] = ci(r[k])
        print(nc, n, acc[f"classes{nc}_n{n}_k1"]["mean"], acc[f"classes{nc}_n{n}_k3"]["mean"], flush=True)
out["accuracy"] = acc
# 3. calibration: fit on even splits, test on odd splits
EDGES = [0, .01, .02, .05, .1, .15, .2, .3, .4, 1.01]
def bins(m, ok, f=None):
    rows = []
    for lo, hi in zip(EDGES[:-1], EDGES[1:]):
        b = (m >= lo) & (m < hi)
        if b.sum(): rows.append({"margin": f"{lo}-{min(hi, 1)}", "n": int(b.sum()), "right": round(float(ok[b].mean()), 4),
                                 **({"score_mean": round(float(f(m[b]).mean()), 4)} if f else {})})
    return rows
def ece(p, ok):
    e = 0; edges = np.linspace(0, 1, 11)
    for lo, hi in zip(edges[:-1], edges[1:]):
        b = (p >= lo) & (p < hi) if hi < 1 else (p >= lo)
        if b.sum(): e += b.mean() * abs(p[b].mean() - ok[b].mean())
    return round(float(e), 4)
cal = {}
for k in (1, 3):
    P = np.concatenate(pool[k]); fit, test = P[P[:, 0] == 0], P[P[:, 0] == 1]
    # proposal A: score = 1/2 + 1/2 * min(1, margin / M): margin 0 = a coin flip between the top two; fit M by grid
    grid = np.arange(0.02, 0.5, 0.005)
    def fA(M): return lambda m: 0.5 + 0.5 * np.minimum(1, m / M)
    MA = min(grid, key=lambda M: ((fA(M)(fit[:, 1]) - fit[:, 2]) ** 2).mean())
    # proposal B: logistic 1/(1+exp(-(a + b*margin))), Newton steps
    a = b = 0.0
    for _ in range(50):
        z = a + b * fit[:, 1]; p = 1 / (1 + np.exp(-z)); w = p * (1 - p) + 1e-9; Xd = np.stack([np.ones(len(z)), fit[:, 1]], 1)
        H = Xd.T @ (Xd * w[:, None]); g = Xd.T @ (fit[:, 2] - p); a, b = np.array([a, b]) + np.linalg.solve(H, g)
    fB = lambda m: 1 / (1 + np.exp(-(a + b * m)))
    by_setting = {}
    for n in [1, 3, 5, 20]:
        for nc in [2, 3]:
            t = test[(test[:, 3] == n) & (test[:, 4] == nc)]
            by_setting[f"classes{nc}_n{n}"] = {"ece_A": ece(fA(MA)(t[:, 1]), t[:, 2]), "ece_B": ece(fB(t[:, 1]), t[:, 2]),
                                               "mean_right": round(float(t[:, 2].mean()), 4)}
    cal[f"k{k}"] = {"bins_test": bins(test[:, 1], test[:, 2], fA(MA)), "A_M": round(float(MA), 3),
                    "A_ece_test": ece(fA(MA)(test[:, 1]), test[:, 2]), "B_ab": [round(a, 3), round(b, 3)],
                    "B_ece_test": ece(fB(test[:, 1]), test[:, 2]), "raw_margin_ece_test": ece(np.clip(test[:, 1], 0, 1), test[:, 2]),
                    "by_setting_test": by_setting}
    print("cal", k, cal[f"k{k}"]["A_M"], cal[f"k{k}"]["A_ece_test"], cal[f"k{k}"]["B_ece_test"], flush=True)
out["calibration"] = cal
# 4. never taught: teach 2 classes (n each), show pictures of the third
unk = {}
for n in [3, 5, 10]:
    known_top, known_m, known_ok, unk_top, unk_m = [], [], [], [], []
    for s in range(N):
        out_c = CL[s % 3]; cls = [c for c in CL if c != out_c]; T, tl, Q, ql = split(cls, n)
        g, m, ts = predict(X[T], tl, X[Q], 1, 2); known_top.append(ts); known_m.append(m); known_ok.append(g == ql)
        U = rng.choice(idx[out_c], TEST_PER, replace=False); _, mu, tu = predict(X[T], tl, X[U], 1, 2); unk_top.append(tu); unk_m.append(mu)
    kt, km, ko, ut, um = map(np.concatenate, (known_top, known_m, known_ok, unk_top, unk_m))
    rows = []
    for th in [0.3, 0.4, 0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8]:
        rows.append({"top_similarity_below": th, "unknown_caught": round(float((ut < th).mean()), 4),
                     "known_right_lost": round(float(((kt < th) & ko).mean()), 4), "known_wrong_caught": round(float(((kt < th) & ~ko).mean()), 4)})
    unk[f"n{n}"] = {"known_accuracy": round(float(ko.mean()), 4),
                    "unknown_margin_pct": {p: round(float(np.percentile(um, p)), 3) for p in (10, 50, 90)},
                    "known_margin_pct": {p: round(float(np.percentile(km, p)), 3) for p in (10, 50, 90)},
                    "unknown_topsim_pct": {p: round(float(np.percentile(ut, p)), 3) for p in (10, 50, 90)},
                    "known_topsim_pct": {p: round(float(np.percentile(kt, p)), 3) for p in (10, 50, 90)},
                    "unknown_with_margin_over_0.1": round(float((um > 0.1).mean()), 4), "thresholds": rows}
    print("unk", n, unk[f"n{n}"]["unknown_topsim_pct"], unk[f"n{n}"]["known_topsim_pct"], flush=True)
out["never_taught"] = unk
# 5. bad teaching
bad = {}
r = {1: [], 3: []}; rc = {1: [], 3: []}
for s in range(N):
    T, tl, Q, ql = split(CL, 5); tl2 = tl.copy()
    for c in range(3):  # one of each class's 5 gets another class's label
        i = np.where(tl == c)[0][0]; tl2[i] = (c + 1 + rng.integers(2)) % 3
    for k in (1, 3):
        r[k].append((predict(X[T], tl2, X[Q], k, 3)[0] == ql).mean()); rc[k].append((predict(X[T], tl, X[Q], k, 3)[0] == ql).mean())
bad["one_in_five_wrong_3classes"] = {f"k{k}": {"wrong_labels": ci(r[k]), "clean_same_splits": ci(rc[k])} for k in (1, 3)}
for k in (1, 3): pass
im = {1: {"big": [], "small": []}, 3: {"big": [], "small": []}}
for s in range(N):
    cls = list(rng.choice(CL, 2, replace=False)); T, tl, Q, ql = split(cls, None, counts=[20, 3])
    for k in (1, 3):
        g = predict(X[T], tl, X[Q], k, 2)[0]; im[k]["big"].append((g == ql)[ql == 0].mean()); im[k]["small"].append((g == ql)[ql == 1].mean())
bad["twenty_against_three"] = {f"k{k}": {"class_with_20": ci(im[k]["big"]), "class_with_3": ci(im[k]["small"])} for k in (1, 3)}
print("bad", json.dumps(bad)[:600], flush=True)
out["bad_teaching"] = bad
json.dump(out, open(OUT, "w"), indent=1)
