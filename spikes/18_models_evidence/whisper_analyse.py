"""Spike 18 part 2: word error rate with a 95 % bootstrap interval, speed and confusions.

    whisper_analyse.py OUT.json RESULTS.jsonl [RESULTS.jsonl ...]     (model name = file name before the first '_')

Normalised text: lower case; hyphens to spaces; punctuation removed (apostrophes inside words kept); whole numbers
0 to 9,999 and simple ordinals written as words; mr/mrs/dr expanded. WER = (S + D + I) / reference words, pooled over
utterances. 95 % interval: 2,000 bootstrap resamples of utterances (seed 18). Duplicate (id, cond) rows: the first is kept.
"""
import json, os, re, sys
from collections import Counter, defaultdict
import numpy as np, jiwer

ONES = "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen".split()
TENS = "_ _ twenty thirty forty fifty sixty seventy eighty ninety".split()
ORD = {"one": "first", "two": "second", "three": "third", "five": "fifth", "eight": "eighth", "nine": "ninth", "twelve": "twelfth"}
def words(n):
    if n < 20: return ONES[n]
    if n < 100: return TENS[n // 10] + ("" if n % 10 == 0 else " " + ONES[n % 10])
    if n < 1000: return ONES[n // 100] + " hundred" + ("" if n % 100 == 0 else " and " + words(n % 100))
    if 1100 <= n < 2000 and n % 100: return words(n // 100) + " " + words(n % 100)        # years: 1850 -> eighteen fifty
    return words(n // 1000) + " thousand" + ("" if n % 1000 == 0 else " " + words(n % 1000))
def ordinal(n):
    w = words(n).split(); last = w[-1]
    w[-1] = ORD.get(last, (last[:-1] + "ieth") if last.endswith("y") else last + "th"); return " ".join(w)
ABBR = {"mr": "mister", "mrs": "missus", "dr": "doctor", "st": "saint", "ok": "okay"}

def norm(t):
    t = t.lower().replace("-", " ").replace("—", " ")
    t = re.sub(r"(\d),(\d)", r"\1\2", t)
    t = re.sub(r"\b(\d{1,4})(st|nd|rd|th)\b", lambda m: ordinal(int(m.group(1))), t)
    t = re.sub(r"\b\d{1,4}\b", lambda m: words(int(m.group(0))), t)
    t = re.sub(r"[^a-z' ]", " ", t)
    t = re.sub(r"(^| )'|'( |$)", " ", t)
    return " ".join(ABBR.get(w, w) for w in t.split())

FUNC = set("a an the and of to in on at is was it he she i you we they his her for with as but or that this be by from had have".split())

def load(paths):
    rows = defaultdict(dict)
    for p in paths:
        model = os.path.basename(p).split("_")[0]
        for l in open(p):
            r = json.loads(l); k = (r["id"], r["cond"])
            if k not in rows[model]: rows[model][k] = r
    return rows

def wer_ci(errs, refs, rng):
    errs, refs = np.array(errs), np.array(refs)
    idx = rng.integers(0, len(errs), (2000, len(errs)))
    b = errs[idx].sum(1) / refs[idx].sum(1)
    return errs.sum() / refs.sum(), float(np.percentile(b, 2.5)), float(np.percentile(b, 97.5))

if __name__ == "__main__":
    rows = load(sys.argv[2:]); out = {"wer": [], "speed": {}, "confusions": {}, "examples": []}
    common = None
    for model, rs in rows.items():
        for r in rs.values():
            o = jiwer.process_words(norm(r["ref"]) or "empty", norm(r["hyp"]) or "")
            r["S"], r["D"], r["I"], r["N"] = o.substitutions, o.deletions, o.insertions, o.substitutions + o.deletions + o.hits
            r["_o"] = o
    # only (id, cond) pairs present for every model, so the models are compared on the same utterances
    keys = set.intersection(*(set(rs) for rs in rows.values()))
    for model, rs in rows.items():
        groups = defaultdict(list)
        for k in keys:
            r = rs[k]; groups[(r["group"], r["cond"])].append(r)
        for (g, c), lst in sorted(groups.items()):
            w, lo, hi = wer_ci([r["S"] + r["D"] + r["I"] for r in lst], [r["N"] for r in lst], np.random.default_rng(18))
            out["wer"].append({"model": model, "group": g, "cond": c, "utts": len(lst), "words": sum(r["N"] for r in lst),
                               "wer": round(w * 100, 1), "ci95": [round(lo * 100, 1), round(hi * 100, 1)],
                               "utt_exact": round(100 * np.mean([r["S"] + r["D"] + r["I"] == 0 for r in lst]), 1)})
        sp = [r for r in rs.values()]
        out["speed"][model] = {"threads": sorted({r["threads"] for r in sp}), "rows": len(sp),
                               "rtf_median": round(float(np.median([r["run_s"] / r["seconds"] for r in sp])), 3),
                               "s_per_utt_median": round(float(np.median([r["run_s"] for r in sp])), 3),
                               "note": "3 Whisper runs and 1 YAMNet run shared 4 CPUs, 1 thread each"}
        sub, dele, ins = Counter(), Counter(), Counter()
        for k in keys:
            r = rs[k]; o = r["_o"]; ref, hyp = o.references[0], o.hypotheses[0]
            for a in o.alignments[0]:
                if a.type == "substitute":
                    for i, j in zip(range(a.ref_start_idx, a.ref_end_idx), range(a.hyp_start_idx, a.hyp_end_idx)): sub[(ref[i], hyp[j])] += 1
                elif a.type == "delete":
                    for i in range(a.ref_start_idx, a.ref_end_idx): dele[ref[i]] += 1
                elif a.type == "insert":
                    for j in range(a.hyp_start_idx, a.hyp_end_idx): ins[hyp[j]] += 1
        allc = [("substitute", f"{a} -> {b}", n, "function word" if a in FUNC or b in FUNC else "content word") for (a, b), n in sub.items()]
        allc += [("delete", w, n, "function word" if w in FUNC else "content word") for w, n in dele.items()]
        allc += [("insert", w, n, "function word" if w in FUNC else "content word") for w, n in ins.items()]
        allc.sort(key=lambda x: -x[2])
        out["confusions"][model] = allc[:30]
    for k in sorted(keys)[:0]: pass
    # learner-facing examples: Indian English clean, both models wrong or differing
    ex = [k for k in sorted(keys) if k[1] == "clean" and rows["tiny"][k]["group"] == "indian" and rows["tiny"][k]["S"] + rows["tiny"][k]["D"] + rows["tiny"][k]["I"] > 0] if "tiny" in rows else []
    for k in ex[:15]:
        out["examples"].append({"id": k[0], "cond": k[1], "ref": rows["tiny"][k]["ref"], **{m: rows[m][k]["hyp"] for m in rows}})
    json.dump(out, open(sys.argv[1], "w"), indent=1)
    for r in out["wer"]: print(r)
    print(json.dumps(out["speed"]))
