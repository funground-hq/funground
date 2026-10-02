"""(1) Load cost of each candidate font (so fallback fonts must be loaded lazily).
   (2) Golden-test determinism: the same Hindi / CJK / emoji line under three chains: bundled, system-first, nothing."""
import hashlib, os, time
from fb import *
def timed(f):
    t = time.perf_counter(); r = f(); return r, (time.perf_counter() - t) * 1000
print("load cost (TTFont + HarfBuzz face), ms, first load in this process:")
for n in ("NotoSansDevanagari-Regular.ttf", "NotoSansArabic-Regular.ttf", "NotoSansSymbols2-Regular.ttf", "NotoEmoji-VF.ttf", "NotoSansJP-Subset.otf", "NotoSansCJK-Regular.ttc"):
    _, ms = timed(lambda: Face(os.path.join(FONTS, n))); print(f"  {n:34}{ms:8.1f} ms")
_, ms = timed(lambda: Face(DEJAVU)); print(f"  {'DejaVuSans.ttf (today)':34}{ms:8.1f} ms")

def sig(chain, text):
    runs = shape_itemised(text, chain)
    blob = repr([(a, b, chain[i].name, [(g, adv) for g, adv, _ in gl]) for a, b, i, gl in runs]).encode()
    return hashlib.sha256(blob).hexdigest()[:12], [(text[a:b], chain[i].name[:16]) for a, b, i, _ in runs]
bundled = chain_default()
sysfont = [Face(DEJAVU)] + [Face(p) for p in (r"C:\Windows\Fonts\Nirmala.ttc", r"C:\Windows\Fonts\msgothic.ttc", r"C:\Windows\Fonts\seguiemj.ttf") if os.path.exists(p)]
nothing = [Face(DEJAVU)]
for text in ("नमस्ते दुनिया", "日本語のテキスト", "go \U0001F680 now"):
    print(f"\n{text!r}")
    for label, ch in (("bundled Noto subsets", bundled), ("system fonts (this PC)", sysfont), ("no fallback (today)", nothing)):
        h, runs = sig(ch, text); print(f"   {label:24}{h}  {runs}")
