"""Spike 18 part 1: summarise compare.jsonl.  yamnet_analyse.py COMPARE.jsonl CLASS_MAP.csv OUT.json

Agreement numbers per ONNX file against Google's TF model, and the learner check: for ESC-50 classes that map cleanly
to an AudioSet name, the share of clips whose Google / ONNX clip score has the right name in the top 1 and top 3.
"tie-aware top-3": a top-3 set difference only counts when a differing label scores >= 0.001 (silence gives exact ties at 0).
"""
import csv, json, sys
import numpy as np

sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__)))
from yamnet_analyse_clean import CLEAN

rows = [json.loads(l) for l in open(sys.argv[1])]
names = [r["display_name"] for r in csv.DictReader(open(sys.argv[2], encoding="utf-8"))]
for k, v in CLEAN.items():
    for n in v: assert n in names, n
keys = [k for k in rows[0] if isinstance(rows[0][k], dict)]
out = {"clips": len(rows), "esc50_clips": sum(r["category"] is not None for r in rows), "files": {}}
for k in keys:
    rs = [r[k] for r in rows if "max_abs_diff" in r[k]]
    nwin = sum(min(r["win_g"], r["win_o"]) for r in rs)
    out["files"][k] = {
        "clips_compared": len(rs), "errors": sum("error" in r[k] for r in rows),
        "window_count_mismatch": sum(r["win_g"] != r["win_o"] for r in rs), "windows": nwin,
        "max_abs_diff_any_window": max(r["max_abs_diff"] for r in rs),
        "max_abs_diff_clip_mean": max(r["clip_max_abs_diff"] for r in rs),
        "window_top1_agree": sum(r["win_top1_agree"] * min(r["win_g"], r["win_o"]) for r in rs) / nwin,
        "window_top3_set_agree_raw": sum(r["win_top3_set_agree"] * min(r["win_g"], r["win_o"]) for r in rs) / nwin,
        "window_top3_set_agree_tieaware": (sum(r["win_top3_set_agree_tieaware"] * min(r["win_g"], r["win_o"]) for r in rs) / nwin) if "win_top3_set_agree_tieaware" in rs[0] else None,
        "clip_top1_agree": float(np.mean([r["clip_top1_agree"] for r in rs])),
        "clip_top3_set_agree_raw": float(np.mean([r["clip_top3_set_agree"] for r in rs])),
        "clip_top3_order_agree_raw": float(np.mean([r["clip_top3_order_agree"] for r in rs])),
        "clip_top1_disagreements": [[r["clip"], rr["top3"], r["google_top3"]] for r, rr in ((r, r[k]) for r in rows if "max_abs_diff" in r[k]) if not rr["clip_top1_agree"]][:10],
    }
    # tie-aware clip top-3: count a disagreement only if Google's 3rd score >= 0.001
    real = [r for r in rows if "max_abs_diff" in r[k] and not r[k]["clip_top3_set_agree"] and r["google_top3_scores"][2] >= 0.001]
    out["files"][k]["clip_top3_set_disagree_nontie"] = len(real)
    out["files"][k]["clip_top3_nontie_examples"] = [[r["clip"], r[k]["top3"], r["google_top3"], r["google_top3_scores"]] for r in real[:5]]
learner = {}
for src in ["google"] + keys:
    per = {}
    for c, ok in CLEAN.items():
        cs = [r for r in rows if r["category"] == c]
        if not cs: continue
        t3 = [(r["google_top3"] if src == "google" else r[src]["top3"]) for r in cs]
        from collections import Counter
        per[c] = {"common_top1": Counter(t[0] for t in t3).most_common(3), "n": len(cs), "top1": sum(t[0] in ok for t in t3) / len(cs), "top3": sum(any(x in ok for x in t) for t in t3) / len(cs)}
    n = sum(p["n"] for p in per.values())
    learner[src] = {"classes": len(per), "clips": n, "top1": sum(p["top1"] * p["n"] for p in per.values()) / n,
                    "top3": sum(p["top3"] * p["n"] for p in per.values()) / n, "per_class": per}
out["learner"] = learner
edge = {r["clip"]: {"google": r.get("google_top3"), **{k: r[k].get("top3") for k in keys}, "windows": r[keys[0]].get("win_g")} for r in rows if r["clip"].startswith("edge_")}
out["edge"] = edge
json.dump(out, open(sys.argv[3], "w"), indent=1)
for k, v in out["files"].items(): print(k, {a: b for a, b in v.items() if "examples" not in a and "disagreements" not in a})
for k, v in learner.items(): print("learner", k, v["classes"], v["clips"], round(v["top1"], 3), round(v["top3"], 3))
