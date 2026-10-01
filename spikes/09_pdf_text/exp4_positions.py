"""Do the invisible glyphs sit on the drawn outlines, and is the page's look unchanged?
Render outlines-only and layered PDFs with PyMuPDF at 4x; compare pixels; compare each line's ink x-extent
with the x-extent of the extracted text boxes (word boxes from MuPDF)."""
import pymupdf, numpy as np
from common import *
base = os.path.join(OUT, "exp2_base.pdf"); lay = os.path.join(OUT, "exp2_B_tm_logical.pdf")
def render(p):
    pix = pymupdf.open(p)[0].get_pixmap(matrix=pymupdf.Matrix(4, 4), colorspace=pymupdf.csGRAY)
    return np.frombuffer(pix.samples, np.uint8).reshape(pix.h, pix.w)
a, b = render(base), render(lay)
print("pixels differing between outlines-only and layered render:", int((a != b).sum()))
words = pymupdf.open(lay)[0].get_text("words")
for (t, x, base_y, size) in layout():
    top, bot = int((base_y - size) * 4), int((base_y + size * 0.4) * 4)      # line band
    ink = np.where((a[top:bot] < 128).any(axis=0))[0]
    ws = [w for w in words if top / 4 <= (w[1] + w[3]) / 2 <= bot / 4]
    tx0, tx1 = min(w[0] for w in ws), max(w[2] for w in ws)
    print(f"{t!r:14} ink x {ink.min()/4:7.2f}..{ink.max()/4:7.2f}   text box x {tx0:7.2f}..{tx1:7.2f}   "
          f"(left {tx0-ink.min()/4:+.2f}, right {tx1-ink.max()/4:+.2f} pt)")
