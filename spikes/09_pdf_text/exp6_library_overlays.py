"""Q2/Q3: let a library embed the font and write the invisible text, then merge that page over Cairo's.
  C = reportlab (BSD) overlay, one text string per HarfBuzz cluster, render mode 3
  D = fpdf2 (LGPL) overlay with its own HarfBuzz shaping, text_mode INVISIBLE
Both are merged onto the Cairo page with pypdf (merge_page)."""
import io
from pypdf import PdfReader, PdfWriter
from common import *
runs = layout(); H = page_h(); base = os.path.join(OUT, "exp2_base.pdf"); make_base(base)

def clusters(text, size):
    """[(x_left_px, text_of_cluster)] in logical order, from HarfBuzz."""
    g, _ = shape(text, size); starts = sorted({c[3] for c in g}); res = []
    for i, st in enumerate(starts):
        end = starts[i+1] if i + 1 < len(starts) else len(text)
        xs = [c[1] for c in g if c[3] == st]; res.append((min(xs), text[st:end]))
    return res

def merge(overlay_bytes, dst):
    w = PdfWriter(); w.append(PdfReader(base)); w.pages[0].merge_page(PdfReader(io.BytesIO(overlay_bytes)).pages[0])
    w.write(dst)

# ---- C: reportlab
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont as RLFont
pdfmetrics.registerFont(RLFont("DV", FONT))
buf = io.BytesIO(); c = canvas.Canvas(buf, pagesize=(PAGE_W, H), pageCompression=1)
for text, x, base_y, size in runs:
    t = c.beginText(); t.setFont("DV", size); t.setTextRenderMode(3)
    for cx, s in (reversed(clusters(text, size)) if is_rtl(text) else clusters(text, size)):
        t.setTextOrigin(x + cx, H - base_y); t.textOut(s)
    c.drawText(t)
c.save(); dst = os.path.join(OUT, "exp6_C_reportlab.pdf"); merge(buf.getvalue(), dst)
print("##### C reportlab overlay  (+%d B)" % (os.path.getsize(dst) - os.path.getsize(base))); report(dst)

# ---- D: fpdf2
from fpdf import FPDF
pdf = FPDF(unit="pt", format=(PAGE_W, H)); pdf.set_auto_page_break(False); pdf.add_page()
pdf.add_font("DV", fname=FONT); pdf.set_text_shaping(True); pdf.text_mode = "INVISIBLE"
for text, x, base_y, size in runs:
    pdf.set_font("DV", size=size); pdf.text(x, base_y, text)
dst = os.path.join(OUT, "exp6_D_fpdf2.pdf"); merge(bytes(pdf.output()), dst)
print(); print("##### D fpdf2 overlay  (+%d B)" % (os.path.getsize(dst) - os.path.getsize(base))); report(dst)
