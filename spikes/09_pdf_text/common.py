"""Shared helpers for the S-093 experiments (run with the throwaway .venv)."""
import os, sys
sys.stdout.reconfigure(encoding="utf-8")
import uharfbuzz as hb
HERE = os.path.dirname(os.path.abspath(__file__))
FONT = os.path.join(HERE, "..", "..", "funground", "fonts", "DejaVuSans.ttf")
OUT = os.path.join(HERE, "out"); os.makedirs(OUT, exist_ok=True)
# Test strings: ligature, ligature, Hebrew (RTL), Arabic (RTL, joining forms)
# Hebrew "shalom" and Arabic "marhaba" each get their own line: one direction per run
SAMPLES = ["fi office", "Search me", "\u05e9\u05dc\u05d5\u05dd", "\u0645\u0631\u062d\u0628\u0627"]

def shape(text, size, path=FONT, direction=None):
    """HarfBuzz shaping -> [(gid, x, y, cluster)] in pixels (y down), plus total advance."""
    blob = hb.Blob.from_file_path(path); face = hb.Face(blob); font = hb.Font(face)
    buf = hb.Buffer(); buf.add_str(text); buf.guess_segment_properties()
    hb.shape(font, buf)
    s = size / face.upem
    x = 0; out = []
    for i, p in zip(buf.glyph_infos, buf.glyph_positions):
        out.append((i.codepoint, (x + p.x_offset) * s, -p.y_offset * s, i.cluster)); x += p.x_advance
    return out, x * s

def is_rtl(text, path=FONT):
    buf = hb.Buffer(); buf.add_str(text); buf.guess_segment_properties(); return buf.direction == "rtl"

def report(pdf, quiet_fonts=False):
    """Extract text with four independent engines (pypdf, PyMuPDF/MuPDF, pdfminer.six, pdfium = Chrome/Edge's
    engine), list embedded fonts, and test that search finds each sample word."""
    import pypdf, pymupdf, pypdfium2
    from pdfminer.high_level import extract_text
    print("==", os.path.basename(pdf), os.path.getsize(pdf), "bytes")
    texts = {}
    texts["pypdf"] = pypdf.PdfReader(pdf).pages[0].extract_text()
    d = pymupdf.open(pdf); pg = d[0]; texts["pymupdf"] = pg.get_text().strip()
    texts["pdfminer"] = extract_text(pdf).strip()
    doc = pypdfium2.PdfDocument(pdf); tp = doc[0].get_textpage(); texts["pdfium"] = tp.get_text_range()
    for k, v in texts.items(): print(f" {k:9}:", repr(v))
    print(" fonts    :", [(f[3], f[2]) for f in pg.get_fonts()])
    words = ("office", "Search", "שלום", "مرحبا")
    print(" search (word found in extracted text, per engine):")
    for w in words:
        found = [k for k, v in texts.items() if w in v] + (["pymupdf.search_for"] if pg.search_for(w) else [])
        print(f"   {w!r:10}: {found}")
    ok = [w in texts["pdfium"] for w in words]
    return texts

# ---- base PDF: outlines drawn by Cairo, as funground does (fontTools outlines + HarfBuzz positions)
SIZE = 24; PAGE_W = 420; LINE_H = 50
def layout(samples=SAMPLES):
    """[(text, x, baseline, size)] one sample per line."""
    return [(t, 20, 40 + i * LINE_H, SIZE) for i, t in enumerate(samples)]
def page_h(samples=SAMPLES): return 20 + LINE_H * len(samples)

def draw_outlines(ctx, runs, path=FONT):
    from fontTools.ttLib import TTFont
    from fontTools.pens.basePen import BasePen
    tt = TTFont(path); gs = tt.getGlyphSet(); order = tt.getGlyphOrder(); upem = tt["head"].unitsPerEm
    class P(BasePen):
        def __init__(s, ctx, g): super().__init__(g); s.c = ctx
        def _moveTo(s, p): s.c.move_to(*p)
        def _lineTo(s, p): s.c.line_to(*p)
        def _curveToOne(s, a, b, c): s.c.curve_to(*a, *b, *c)
        def _qCurveToOne(s, q, p):          # quadratic -> cubic
            x0, y0 = s.c.get_current_point()   # already in transformed space; fine for a spike
            s.c.curve_to(x0 + 2/3*(q[0]-x0), y0 + 2/3*(q[1]-y0), p[0] + 2/3*(q[0]-p[0]), p[1] + 2/3*(q[1]-p[1]), *p)
        def _closePath(s): s.c.close_path()
    for text, x, base, size in runs:
        glyphs, _ = shape(text, size, path)
        for gid, gx, gy, _c in glyphs:
            ctx.save(); ctx.translate(x + gx, base + gy); ctx.scale(size / upem, -size / upem)
            # pen works in glyph units, the current point is read back in user space, so build the path first:
            ctx.new_path(); gs[order[gid]].draw(P(ctx, gs)); ctx.set_source_rgb(0, 0, 0); ctx.fill(); ctx.restore()

def make_base(pdf, runs=None, samples=SAMPLES):
    import cairo
    runs = runs or layout(samples)
    s = cairo.PDFSurface(pdf, PAGE_W, page_h(samples)); c = cairo.Context(s)
    draw_outlines(c, runs); s.finish(); return runs
