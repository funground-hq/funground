"""Q1: can pycairo get a font face from a TTF file? Does ToyFontFace embed DejaVu?"""
import cairo, os
from common import *
print("pycairo", cairo.version, "cairo", cairo.cairo_version_string(), "HAS_FT_FONT =", cairo.HAS_FT_FONT)
print("FontFace constructors available:", [n for n in dir(cairo) if "Face" in n])
print("any FT / file-path factory:", [n for n in dir(cairo) if "FT" in n.upper() and n != "HAS_FT_FONT"] or "none")
for fam in ("DejaVu Sans", "Arial", "NoSuchFontXYZ"):
    pdf = os.path.join(OUT, f"exp1_{fam.replace(' ', '_')}.pdf")
    s = cairo.PDFSurface(pdf, 300, 60); c = cairo.Context(s)
    c.set_font_face(cairo.ToyFontFace(fam)); c.set_font_size(24); c.move_to(10, 40)
    glyphs, _ = shape("fi office", 24)
    # pretend toy face glyph ids == HarfBuzz ids (they are not: toy ids are the platform font's own)
    c.show_glyphs([cairo.Glyph(g, 10 + x, 40 + y) for g, x, y, _ in glyphs])
    s.finish()
    print("\n--- ToyFontFace(", fam, ")"); report(pdf)

# What the toy face *can* do: show_text / show_text_glyphs with the platform's own font (here Arial).
pdf = os.path.join(OUT, "exp1_toy_show_text.pdf")
s = cairo.PDFSurface(pdf, 300, 60); c = cairo.Context(s)
c.select_font_face("DejaVu Sans"); c.set_font_size(24); c.move_to(10, 40)
c.show_text("fi office")                       # Cairo shapes it itself; HarfBuzz is bypassed
s.finish(); print("\n--- toy show_text (font chosen by the OS, not by us)"); report(pdf)
