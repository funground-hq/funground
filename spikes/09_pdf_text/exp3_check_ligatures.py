"""Does DejaVu really form 'fi' / 'ffi' ligature glyphs under HarfBuzz (so the copy-out test is meaningful)?"""
from common import *
from fontTools.ttLib import TTFont
order = TTFont(FONT).getGlyphOrder()
for t in ("fi office", "שלום", "مرحبا"):
    g, w = shape(t, 24)
    print(repr(t), "->", len(t), "chars,", len(g), "glyphs:", [(order[x[0]], x[3]) for x in g])
