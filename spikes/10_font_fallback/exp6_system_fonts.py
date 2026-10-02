"""Option (b): what fonts does THIS machine have, what do they cover, can they be embedded (fsType), how long does the scan take?
Read-only: files are opened with fontTools only (never started, installed or copied)."""
import glob, os, sys, time, platform
from fontTools.ttLib import TTFont, TTCollection
import logging; logging.disable(logging.WARNING)

DIRS = {"Windows": [r"C:\Windows\Fonts", os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Windows\Fonts")],
        "Darwin": ["/System/Library/Fonts", "/System/Library/Fonts/Supplemental", "/Library/Fonts", os.path.expanduser("~/Library/Fonts")],
        "Linux": ["/usr/share/fonts", "/usr/local/share/fonts", os.path.expanduser("~/.fonts"), os.path.expanduser("~/.local/share/fonts")]}[platform.system()]
t0 = time.perf_counter()
files = []
for d in DIRS:
    for ext in ("ttf", "otf", "ttc", "TTF", "OTF", "TTC"):
        files += glob.glob(os.path.join(d, "**", "*." + ext), recursive=True)
files = sorted(set(files))
t1 = time.perf_counter()
print(f"{platform.system()}: {len(files)} font files found in {t1 - t0:.2f} s (directory walk)")
records = []   # (path, index, family, cmap set, fsType, colour tables)
for p in files:
    try:
        faces = TTCollection(p, lazy=True).fonts if p.lower().endswith(".ttc") else [TTFont(p, lazy=True)]
        for n, t in enumerate(faces):
            fs = t["OS/2"].fsType if "OS/2" in t else None
            col = [x for x in ("COLR", "CBDT", "sbix", "SVG ") if x in t]
            kind = "CFF" if "CFF " in t else "CFF2" if "CFF2" in t else "glyf" if "glyf" in t else "?"
            records.append((os.path.basename(p), n, t["name"].getDebugName(4) or "?", frozenset(t.getBestCmap() or ()), fs, col, kind))
    except Exception as e:
        pass
t2 = time.perf_counter()
print(f"opened {len(records)} faces and read their cmaps in {t2 - t1:.2f} s  (this is the one-off cost of building a coverage index; about {1000*(t2-t1)/max(len(records),1):.1f} ms per face)")
from collections import Counter
print("fsType values (0 installable, 4 print/preview OK, 8 editable OK, 2 restricted = must not embed):", dict(Counter(r[4] for r in records)))
print("faces with the restricted bit (2):", sum(1 for r in records if r[4] is not None and r[4] & 2))

GROUPS = {
 "Devanagari": range(0x915, 0x940), "Arabic": range(0x627, 0x64B), "Hebrew": range(0x5D0, 0x5EB),
 "Hiragana/Katakana": range(0x3042, 0x3094), "JIS kanji sample (日本語中文漢字)": [ord(c) for c in "日本語中文漢字学校"],
 "Simplified hanzi sample (你好汉字学习)": [ord(c) for c in "你好汉字学习"], "Hangul sample (한국어)": [ord(c) for c in "한국어"],
 "Emoji sample (😀🚀🐶🍎🎉🍕)": [ord(c) for c in "😀🚀🐶🍎🎉🍕"], "Thai": range(0xE01, 0xE3B), "Bengali": [0x995, 0x996, 0x9BE, 0x9BF], "Tamil": [0xB95, 0xB99, 0xBBE, 0xBBF],
 "Symbols sample (★✓→∑♠⭐⮩🎲)": [ord(c) for c in "★✓→∑♠⭐⮩🎲"],
}
print("\nfaces on this machine covering each group fully (family | file | fsType | outlines | colour tables)")
for g, cps in GROUPS.items():
    cps = list(cps)
    hits = [r for r in records if all(c in r[3] for c in cps)]
    hits.sort(key=lambda r: (r[4] is not None and bool(r[4] & 2), r[2]))
    print(f"\n  {g}: {len(hits)} faces")
    for r in hits[:5]:
        print(f"     {r[2][:34]:36}{r[0]:18} fsType={r[4]!s:4} {r[6]:5} {','.join(r[5])}")

# colour table versions of the emoji font here
for name in ("seguiemj.ttf",):
    p = os.path.join(DIRS[0], name)
    if os.path.exists(p):
        t = TTFont(p, lazy=True)
        print(f"\n{name}: COLR version {t['COLR'].version if 'COLR' in t else None}; tables: {sorted(t.keys())[:30]}")
