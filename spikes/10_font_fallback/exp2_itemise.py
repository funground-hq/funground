"""Itemisation: cluster-based runs vs HarfBuzz-style notdef re-shaping, correctness on tricky strings + cost."""
import time, unicodedata
from fb import *
chain = chain_default()
names = [f.name[:14] for f in chain]
TESTS = {
 "latin only": "The quick brown fox, café, naïve — 100%",
 "emoji mid-sentence": "Hello \U0001F680 world \U0001F600!",
 "emoji ZWJ family": "family: \U0001F468‍\U0001F469‍\U0001F467 end",
 "skin tone": "ok \U0001F44D\U0001F3FD fine",
 "flag": "india \U0001F1EE\U0001F1F3 flag",
 "keycap": "press 1️⃣ now",
 "heart VS16": "love ❤️ and ❤",
 "rainbow flag ZWJ": "pride \U0001F3F3️‍\U0001F308 end",
 "devanagari conjunct": "Hindi: क्षत्रिय and क्षमा",
 "devanagari sentence": "नमस्ते दुनिया, hello",
 "arabic in latin": "say مرحبا now",
 "hebrew": "shalom שלום ok",
 "CJK": "日本語 and 中文 or 한국어",
 "latin + combining": "é ä q̣́ ok",
 "symbols": "★ ✓ → ∑ ♠ ⭐ \U0001F3B2 ⮩",
 "unsupported": "ancient \U00010380 \U0001F9D0 ꯍ",
}
def show(runs):
    return " | ".join(f"{names[i]}:{len(g)}g" for a, b, i, g in runs)
for k, s in TESTS.items():
    A = shape_itemised(s, chain)
    B = shape_notdef(s, chain)
    sig = lambda R: [(a, b, i, [x[0] for x in g]) for a, b, i, g in R]
    same = "same" if sig(A) == sig(B) else "DIFF"
    notdef = sum(1 for r in A for gid, _, _ in r[3] if gid == 0)
    print(f"\n[{k}] {s!r}\n  A cluster-first: {[ (s[a:b], names[i]) for a,b,i,g in A]}\n  B notdef-retry : {[ (s[a:b], names[i]) for a,b,i,g in B]}\n  A vs B: {same}; tofu glyphs in A: {notdef}")

# ---- cost -----------------------------------------------------------------------------
import statistics
def bench(fn, n=300):
    t = []
    for _ in range(n):
        t0 = time.perf_counter(); fn(); t.append(time.perf_counter() - t0)
    return statistics.median(t) * 1e6
LINES = {
 "latin 60 chars": "The quick brown fox jumps over the lazy dog; pack my box with five",
 "latin 60 + 1 emoji": "The quick brown fox jumps over the lazy \U0001F436; pack my box wi",
 "mixed latin/emoji/hindi/CJK": "Score: 10 ★ \U0001F600 नमस्ते 日本語 go",
 "CJK 30 chars": "日本語のテキストを表示します。これはテストです。漢字とかな",
}
D = chain[0]
print(f"\n{'case':34}{'today: 1 shape':>16}{'fast path check':>17}{'A itemise+shape':>17}{'B notdef-retry':>16}  (microseconds, median)")
for k, s in LINES.items():
    base = bench(lambda: D.shape(s))
    chk = bench(lambda: D.has_all(s))
    a = bench(lambda: shape_itemised(s, chain))
    b = bench(lambda: shape_notdef(s, chain))
    print(f"{k:34}{base:16.1f}{chk:17.1f}{a:17.1f}{b:16.1f}")
# itemise only
s = LINES["mixed latin/emoji/hindi/CJK"]
print("itemise() alone on the mixed line:", round(bench(lambda: itemise(s, chain)), 1), "us;  regex-X alone:", round(bench(lambda: [m.group() for m in GRAPHEME.finditer(s)]), 1), "us;  clusters() alone:", round(bench(lambda: clusters(s)), 1), "us")

# ---- stdlib cluster splitter versus the `regex` module's \X (reference) ---------------------
bad = 0
for k, s in TESTS.items():
    ref = [(m.start(), m.end()) for m in GRAPHEME.finditer(s)]
    if ref != clusters(s):
        bad += 1; print("cluster mismatch in", k, [s[a:b] for a, b in ref], [s[a:b] for a, b in clusters(s)])
print(f"clusters() vs regex-X on {len(TESTS)} test strings: {bad} mismatches")
