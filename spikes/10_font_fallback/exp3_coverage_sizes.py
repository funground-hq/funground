"""Coverage of the candidate fonts over Unicode groups, and the size of subsets (raw and zlib-9 = wheel cost)."""
import io, os, zlib, warnings, logging
import regex
from fontTools.ttLib import TTFont, TTCollection
from fontTools import subset
from fontTools.varLib import instancer
logging.disable(logging.WARNING)
from fb import FONTS, DEJAVU

def load(n, num=0):
    p = n if os.path.isabs(n) else os.path.join(FONTS, n)
    return TTCollection(p).fonts[num] if p.endswith(".ttc") else TTFont(p)

def cps(prop):
    r = regex.compile(r"\p{%s}" % prop)
    return {c for c in range(0x110000) if r.match(chr(c))}

EP, EM, XP = cps("Emoji_Presentation"), cps("Emoji"), cps("Extended_Pictographic")
EM_NOASCII = {c for c in EM if c > 0xFF}
def blk(a, b): return set(range(a, b + 1))
groups = {
    "Emoji_Presentation (%d)" % len(EP): EP,
    "Emoji incl. text-style (%d, no ASCII/©®)" % len(EM_NOASCII): EM_NOASCII,
    "Extended_Pictographic (%d)" % len(XP): XP,
    "Misc Symbols 2600-26FF": blk(0x2600, 0x26FF),
    "Dingbats 2700-27BF": blk(0x2700, 0x27BF),
    "Arrows 2190-21FF + Sup 2900-297F + 2B00-2BFF": blk(0x2190, 0x21FF) | blk(0x2900, 0x297F) | blk(0x2B00, 0x2BFF),
    "Math operators 2200-22FF": blk(0x2200, 0x22FF),
    "Geometric/box/block 2500-25FF": blk(0x2500, 0x25FF),
    "Games: cards, mahjong, domino 1F000-1F0FF": blk(0x1F000, 0x1F0FF),
    "Chess/symbols ext 1FA00-1FAFF": blk(0x1FA00, 0x1FAFF),
    "Devanagari 0900-097F": blk(0x900, 0x97F),
    "Arabic 0600-06FF": blk(0x600, 0x6FF),
    "Hebrew 0590-05FF": blk(0x590, 0x5FF),
    "Hiragana+Katakana 3040-30FF": blk(0x3040, 0x30FF),
    "JIS X 0208 kanji (rows 16-84)": {ord(bytes([0x30 + r - 16 + 0x80, c + 0x80]).decode("euc_jp")) for r in range(16, 85) for c in range(0xA1 - 0x80, 0xFF - 0x80) if True} if False else set(),
}
def codec_set(codec, rows, lead_base=0xA0):
    out = set()
    for r in rows:
        for c in range(0xA1, 0xFF):
            try: ch = bytes([lead_base + r, c]).decode(codec)
            except Exception: continue
            if len(ch) == 1: out.add(ord(ch))
    return out
JIS_L1 = codec_set("euc_jp", range(16, 48)); JIS_L2 = codec_set("euc_jp", range(48, 85))
GB_L1 = codec_set("gb2312", range(16, 56)); GB_L2 = codec_set("gb2312", range(56, 88))
KS_H = codec_set("euc_kr", range(48, 73))
groups.pop("JIS X 0208 kanji (rows 16-84)")
groups[f"JIS X 0208 kanji level 1 ({len(JIS_L1)})"] = JIS_L1
groups[f"JIS X 0208 kanji level 2 ({len(JIS_L2)})"] = JIS_L2
groups[f"GB 2312 hanzi level 1 ({len(GB_L1)})"] = GB_L1
groups[f"KS X 1001 hangul ({len(KS_H)})"] = KS_H

fonts = {
    "DejaVu Sans": DEJAVU, "Noto Emoji (mono)": "NotoEmoji-VF.ttf", "Noto Sans Symbols 2": "NotoSansSymbols2-Regular.ttf",
    "Noto Sans Symbols": "NotoSansSymbols-Regular.ttf", "Noto Sans Math": "NotoSansMath-Regular.ttf",
    "Noto Sans Devanagari": "NotoSansDevanagari-Regular.ttf", "Noto Sans Arabic": "NotoSansArabic-Regular.ttf",
    "Noto Sans Hebrew": "NotoSansHebrew-Regular.ttf", "Noto Sans JP (subset OTF)": "NotoSansJP-Subset.otf",
    "Noto Sans CJK JP (TTC #0)": ("NotoSansCJK-Regular.ttc", 0), "Noto Sans CJK KR (#1)": ("NotoSansCJK-Regular.ttc", 1),
    "Noto Sans CJK SC (#2)": ("NotoSansCJK-Regular.ttc", 2), "Twemoji Mozilla (COLRv0)": "Twemoji.Mozilla.ttf",
    "Noto Color Emoji (COLRv1)": "NotoColorEmoji-Regular.ttf",
}
cm = {}
for k, v in fonts.items():
    t = load(*v) if isinstance(v, tuple) else load(v)
    cm[k] = set(t.getBestCmap())
names = list(fonts)
print("coverage: fraction of each group the font has (percent)\n")
print(f"{'group':52}" + "".join(f"{n[:13]:>14}" for n in names))
for g, s in groups.items():
    print(f"{g:52}" + "".join(f"{100*len(s & cm[n])/len(s):13.0f}%" for n in names))
dv = cm["DejaVu Sans"]
print("\nEmoji_Presentation chars DejaVu already has:", len(EP & dv), "of", len(EP),
      "| union of DejaVu+Noto Emoji:", len(EP & (dv | cm["Noto Emoji (mono)"])),
      "| union adding Symbols2:", len(EP & (dv | cm["Noto Emoji (mono)"] | cm["Noto Sans Symbols 2"])))

# ---- subset sizes ---------------------------------------------------------------------------
def sub_size(t, unicodes, drop_hints=True, layout=("kern", "liga", "ccmp", "locl", "mark", "mkmk", "calt", "rlig", "rclt", "init", "medi", "fina", "isol", "akhn", "rphf", "blwf", "half", "vatu", "pres", "abvs", "blws", "psts", "haln", "cjct", "nukt", "pref", "rkrf", "abvf", "blwf", "cswh", "dist", "curs", "vert", "vrt2", "locl")):
    o = subset.Options(); o.layout_features = ["*"]; o.hinting = not drop_hints; o.notdef_outline = True
    o.glyph_names = False; o.name_IDs = [0, 1, 2, 3, 4, 5, 6, 13, 14]; o.drop_tables += ["DSIG"]
    s = subset.Subsetter(o); s.populate(unicodes=unicodes); s.subset(t)
    b = io.BytesIO(); t.save(b); raw = b.getvalue()
    return len(raw), len(zlib.compress(raw, 9))
def row(label, t_loader, unis):
    t = t_loader()
    n0 = t["maxp"].numGlyphs
    raw, z = sub_size(t, unis)
    print(f"{label:62}{raw/1e6:8.2f} MB raw {z/1e6:7.2f} MB zlib   ({t['maxp'].numGlyphs} of {n0} glyphs)")
print("\nsubset sizes (hinting dropped; all layout features kept)\n")
def whole(n, num=0): return lambda: load(n, num)
def static400(): return instancer.instantiateVariableFont(load("NotoEmoji-VF.ttf"), {"wght": 400})
full = lambda k: cm[k]
row("Noto Emoji VF, whole cmap, still variable", whole("NotoEmoji-VF.ttf"), full("Noto Emoji (mono)"))
row("Noto Emoji static wght=400, whole cmap", static400, full("Noto Emoji (mono)"))
row("Noto Emoji static 400, Emoji_Presentation + text emoji only", static400, EM_NOASCII & full("Noto Emoji (mono)") | EP & full("Noto Emoji (mono)"))
row("Noto Sans Symbols 2 whole", whole("NotoSansSymbols2-Regular.ttf"), full("Noto Sans Symbols 2"))
row("Noto Sans Symbols whole", whole("NotoSansSymbols-Regular.ttf"), full("Noto Sans Symbols"))
row("Noto Sans Math whole", whole("NotoSansMath-Regular.ttf"), full("Noto Sans Math"))
row("Noto Sans Devanagari whole", whole("NotoSansDevanagari-Regular.ttf"), full("Noto Sans Devanagari"))
row("Noto Sans Arabic whole", whole("NotoSansArabic-Regular.ttf"), full("Noto Sans Arabic"))
row("Noto Sans Hebrew whole", whole("NotoSansHebrew-Regular.ttf"), full("Noto Sans Hebrew"))
kana = blk(0x3000, 0x30FF) | blk(0xFF00, 0xFFEF)
row("CJK JP: kana + CJK punctuation only", whole("NotoSansCJK-Regular.ttc", 0), kana)
row("CJK JP: kana + JIS level 1 kanji (2965)", whole("NotoSansCJK-Regular.ttc", 0), kana | JIS_L1)
row("CJK JP: kana + JIS L1 + L2 (6355 kanji)", whole("NotoSansCJK-Regular.ttc", 0), kana | JIS_L1 | JIS_L2)
row("CJK SC: GB2312 level 1 (3755 hanzi) + punct", whole("NotoSansCJK-Regular.ttc", 2), kana & blk(0x3000, 0x303F) | blk(0xFF00, 0xFFEF) | GB_L1)
row("CJK KR: KS X 1001 hangul (2350) + punct", whole("NotoSansCJK-Regular.ttc", 1), blk(0x3000, 0x303F) | blk(0xFF00, 0xFFEF) | KS_H)
row("CJK JP+SC+KR in ONE font? no: three files above; whole TTC file", whole("NotoSansCJK-Regular.ttc", 0), set())  # placeholder: 0 chars
print("\nfile sizes on disk (MB):")
for k, v in fonts.items():
    p = v[0] if isinstance(v, tuple) else v
    p = p if os.path.isabs(p) else os.path.join(FONTS, p)
    print(f"  {k:30}{os.path.getsize(p)/1e6:8.2f}")
