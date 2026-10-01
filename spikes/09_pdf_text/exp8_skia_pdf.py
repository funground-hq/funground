"""Q3: an alternative PDF backend for text: skia-python (BSD, Skia's SkPDF). Real text from a TTF file with
HarfBuzz glyph ids and positions. (Visible text here, to judge embedding/extraction; Skia has no Tr 3.)"""
import skia
from common import *
runs = layout(); pdf = os.path.join(OUT, "exp8_skia.pdf")
stream = skia.FILEWStream(pdf); doc = skia.PDF.MakeDocument(stream); canvas = doc.beginPage(PAGE_W, page_h())
tf = skia.Typeface.MakeFromFile(FONT); font = skia.Font(tf, SIZE); paint = skia.Paint(Color=skia.ColorBLACK, AntiAlias=True)
for text, x, base, size in runs:
    g, _ = shape(text, size); font.setSize(size)
    b = skia.TextBlobBuilder(); b.allocRunPos(font, [q[0] for q in g], [skia.Point(q[1], q[2]) for q in g])
    canvas.drawTextBlob(b.make(), x, base, paint)
doc.endPage(); doc.close(); stream.flush(); del stream
report(pdf)
