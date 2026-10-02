"""What can an outline-only renderer show of emoji?
 (1) monochrome Noto Emoji, shaped with HarfBuzz: ZWJ / flag / skin-tone sequences -> one glyph?
 (2) COLRv0 (Twemoji Mozilla): layers of solid colours drawn from outlines with fontTools alone. Renders out/exp4_emoji.png
 (3) COLRv1 (Noto Color Emoji): which Paint formats the 3 800+ colour glyphs need -> effort estimate."""
import os, collections, logging
import cairo
from fontTools.ttLib import TTFont
from fontTools.pens.cairoPen import CairoPen
from fontTools.varLib import instancer
import uharfbuzz as hb
logging.disable(logging.WARNING)
from fb import FONTS

SEQ = {
 "grinning": "\U0001F600", "rocket": "\U0001F680", "thumbs+tone": "\U0001F44D\U0001F3FD",
 "flag IN": "\U0001F1EE\U0001F1F3", "family ZWJ": "\U0001F468‍\U0001F469‍\U0001F467",
 "rainbow flag": "\U0001F3F3️‍\U0001F308", "keycap 1": "1️⃣", "woman technologist": "\U0001F469\U0001F3FD‍\U0001F4BB",
 "England flag (tags)": "\U0001F3F4\U000E0067\U000E0062\U000E0065\U000E006E\U000E0067\U000E007F", "heart": "❤️",
}
def hb_glyphs(path, text):
    f = hb.Font(hb.Face(hb.Blob.from_file_path(path))); buf = hb.Buffer(); buf.add_str(text); buf.guess_segment_properties()
    hb.shape(f, buf, {"kern": True, "liga": True, "ccmp": True})
    return [i.codepoint for i in buf.glyph_infos]
print("(1) glyphs per sequence (1 = the font composes the sequence into one picture; >1 = parts drawn side by side)")
print(f"{'sequence':22}{'Noto Emoji mono':>16}{'Twemoji COLRv0':>16}{'Noto Color COLRv1':>19}")
for k, s in SEQ.items():
    cells = []
    for fn in ("NotoEmoji-VF.ttf", "Twemoji.Mozilla.ttf", "NotoColorEmoji-Regular.ttf"):
        g = hb_glyphs(os.path.join(FONTS, fn), s); cells.append(f"{len(g)}{' (tofu)' if 0 in g else ''}")
    print(f"{k:22}{cells[0]:>16}{cells[1]:>16}{cells[2]:>19}")

# (2) draw with Noto Emoji (mono, instanced at 400) and Twemoji COLRv0 layers
mono = instancer.instantiateVariableFont(TTFont(os.path.join(FONTS, "NotoEmoji-VF.ttf")), {"wght": 400})
tw = TTFont(os.path.join(FONTS, "Twemoji.Mozilla.ttf"))
colr, cpal = tw["COLR"], tw["CPAL"].palettes[0]
print("\n(2) Twemoji COLR version", colr.version, "| base glyphs with layers:", len(colr.ColorLayers), "| palette entries:", len(cpal),
      "| layers per glyph: min/median/max =", end=" ")
ls = sorted(len(v) for v in colr.ColorLayers.values()); print(ls[0], ls[len(ls)//2], ls[-1])
def cmapname(tt, ch): return tt.getBestCmap().get(ord(ch))
chars = "\U0001F600\U0001F680\U0001F436\U0001F34E❤\U0001F308\U0001F389\U0001F355"
size, pad = 96, 12
W, H = pad + len(chars) * (size + pad), pad * 3 + 2 * size + 30
surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); ctx = cairo.Context(surf)
ctx.set_source_rgb(1, 1, 1); ctx.paint()
def draw_glyph(tt, name, x, y, size, rgba):
    gs = tt.getGlyphSet(); s = size / tt["head"].unitsPerEm
    ctx.save(); ctx.translate(x, y); ctx.scale(s, -s)
    gs[name].draw(CairoPen(gs, ctx)); ctx.restore()
    ctx.set_source_rgba(*rgba); ctx.fill()
n_layers = 0
for i, ch in enumerate(chars):
    x = pad + i * (size + pad)
    nm = cmapname(mono, ch)
    if nm: draw_glyph(mono, nm, x, pad + size * 0.85, size, (0, 0, 0, 1))
    nm = cmapname(tw, ch)
    if nm:
        for layer in colr.ColorLayers.get(nm, []):
            c = cpal[layer.colorID]; n_layers += 1
            rgba = (c.red / 255, c.green / 255, c.blue / 255, c.alpha / 255) if layer.colorID != 0xFFFF else (0, 0, 0, 1)
            draw_glyph(tw, layer.name, x, 2 * pad + size * 1.85, size, rgba)
surf.write_to_png(os.path.join(os.path.dirname(os.path.abspath(__file__)), "out", "exp4_emoji.png"))
print("   drew", len(chars), "emoji in mono (top row) and as COLRv0 layers (bottom row),", n_layers, "layer fills in total -> out/exp4_emoji.png")

# (3) COLRv1 paint formats used by Noto Color Emoji
nc = TTFont(os.path.join(FONTS, "NotoColorEmoji-Regular.ttf"))
table = nc["COLR"].table
print("\n(3) Noto Color Emoji COLR version", nc["COLR"].version, "| BaseGlyphList records:", table.BaseGlyphList.BaseGlyphCount,
      "| LayerList paints:", table.LayerList.LayerCount, "| ClipBoxes:", table.ClipList is not None)
from fontTools.ttLib.tables import otTables as ot
names = {v: k for k, v in vars(ot.PaintFormat).items() if isinstance(v, int)}
cnt = collections.Counter()
def walk(p):
    cnt[names.get(p.Format, p.Format)] += 1
    for a in ("Paint", "SourcePaint", "BackdropPaint"):
        if hasattr(p, a) and getattr(p, a) is not None: walk(getattr(p, a))
    if p.Format == ot.PaintFormat.PaintColrLayers:
        for q in table.LayerList.Paint[p.FirstLayerIndex:p.FirstLayerIndex + p.NumLayers]: walk(q)
for rec in table.BaseGlyphList.BaseGlyphPaintRecord[:400]:
    walk(rec.Paint)
print("   paint nodes used by the first 400 emoji (count each):")
for k, v in cnt.most_common(): print(f"     {k:28}{v:7}")
comp = [rec.BaseGlyph for rec in table.BaseGlyphList.BaseGlyphPaintRecord]

# (4) does a COLRv1 table also carry COLRv0 layer records (a fallback drawable with v0 code only)?
for label, p in (("Noto Color Emoji", os.path.join(FONTS, "NotoColorEmoji-Regular.ttf")), ("Segoe UI Emoji (this machine)", r"C:\Windows\Fonts\seguiemj.ttf")):
    if os.path.exists(p):
        t = TTFont(p, lazy=True)["COLR"].table
        v0 = getattr(t, "BaseGlyphRecordCount", 0); v1 = t.BaseGlyphList.BaseGlyphCount if t.BaseGlyphList else 0
        print(f"\n(4) {label}: COLR v{t.Version}: v0 base-glyph records = {v0}, v1 paint records = {v1}")
