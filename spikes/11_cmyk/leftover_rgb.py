"""Probe 6: scan EVERY object in a PDF (not just the ones reachable the way the converter walks) for leftover RGB."""
import re, sys, logging
logging.disable(logging.CRITICAL)
from pypdf import PdfReader
from pypdf.generic import ContentStream, StreamObject
r = PdfReader(sys.argv[1]); dr = 0; rg = 0; where = set()
for i in sorted(k for g in r.xref.values() for k in g):
    try: o = r.get_object(i)
    except Exception: continue
    if o is None: continue
    if hasattr(o, "items"):
        for k, v in o.items():
            if str(v) == "/DeviceRGB" or (isinstance(v, list) and any(str(x) == "/DeviceRGB" for x in v)): dr += 1; where.add(f"obj {i} {k} {o.get('/Type') or o.get('/ShadingType') or o.get('/Subtype')}")
    if isinstance(o, StreamObject) and o.get("/Subtype") == "/Form":
        for _, op in ContentStream(o, None).operations:
            if op in (b"rg", b"RG"): rg += 1; where.add(f"obj {i} stream rg")
print("leftover /DeviceRGB:", dr, "| leftover rg/RG in forms:", rg, sorted(where)[:6])
