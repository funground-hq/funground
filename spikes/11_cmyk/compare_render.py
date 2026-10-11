"""Probe 3: render PDFs with pdfium and compare to the RGB original (mean abs diff per channel, and a few sample pixels)."""
import sys
import pypdfium2 as pdfium
from PIL import Image, ImageChops, ImageStat
def render(p):
    return pdfium.PdfDocument(p)[0].render(scale=1).to_pil().convert("RGB")
base = render(sys.argv[1])
pts = {"gradient top": (240, 5), "gradient bottom": (440, 635), "red circle": (280, 150), "overlap r+g": (320, 150), "photo": (140, 380), "white text": (60, 515), "gold circle": (100, 100), "translucent card": (350, 380)}
print("pixel (RGB):", {k: base.getpixel(v) for k, v in pts.items()})
for p in sys.argv[2:]:
    im = render(p); d = ImageStat.Stat(ImageChops.difference(base, im)).mean
    print(p, "mean abs diff RGB:", [round(x, 1) for x in d], {k: im.getpixel(v) for k, v in pts.items()})
    im.save(p.replace(".pdf", "_render.png"))
base.save(sys.argv[1].replace(".pdf", "_render.png"))
