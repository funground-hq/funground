"""Q2 side-door: does Cairo's own PDF tagging (tag_begin) make outline text selectable? Cairo 1.18 has
TAG_CONTENT / TAG_LINK / TAG_DEST only; structure tags go in a structure tree but add no text-show operator."""
import cairo
from common import *
pdf = os.path.join(OUT, "exp7_tags.pdf"); s = cairo.PDFSurface(pdf, PAGE_W, 100); s.set_metadata(cairo.PDF_METADATA_TITLE, "t")
c = cairo.Context(s)
c.tag_begin("Document", ""); c.tag_begin("P", "")
draw_outlines(c, [("office", 20, 40, 24)]); c.tag_end("P"); c.tag_end("Document")
s.finish(); report(pdf)
import re; raw = open(pdf, "rb").read(); print("has /ActualText:", b"ActualText" in raw, " has /StructTreeRoot:", b"StructTreeRoot" in raw, " has 'Tj' or 'TJ':", bool(re.search(rb"\b(Tj|TJ)\b", raw)))
