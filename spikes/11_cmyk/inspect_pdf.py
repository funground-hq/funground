"""Probe: list colour operators, colour spaces, images, shadings, blend modes in a PDF."""
import sys, re, collections
from pypdf import PdfReader
from pypdf.generic import ContentStream, IndirectObject

def walk(res, seen, out, label):
    if res is None: return
    res = res.get_object()
    for k, v in (res.get("/ColorSpace") or {}).items():
        out["colorspace resources"].add(str(v.get_object()) if not isinstance(v.get_object(), list) else str(v.get_object()[0]))
    for k, v in (res.get("/Shading") or {}).items():
        sh = v.get_object(); cs = sh.get("/ColorSpace"); out["shading ColorSpace"].add(str(cs)); out["shading types"].add(sh.get("/ShadingType"))
    for k, v in (res.get("/ExtGState") or {}).items():
        g = v.get_object()
        if "/BM" in g: out["BM"].add(str(g["/BM"]))
        if "/SMask" in g and g["/SMask"] != "/None": out["SMask"].add("yes")
        if "/CA" in g or "/ca" in g: out["opacity"].add("yes")
    for k, v in (res.get("/Pattern") or {}).items():
        p = v.get_object(); out["pattern types"].add(p.get("/PatternType"))
        if "/Shading" in p: 
            sh = p["/Shading"].get_object(); out["shading ColorSpace"].add(str(sh.get("/ColorSpace"))); out["shading types"].add(sh.get("/ShadingType"))
            f = sh.get("/Function")
            if f is not None: out["functions"].add(str(f.get_object().get("/FunctionType")))
        walk(p.get("/Resources"), seen, out, label)
    for k, v in (res.get("/XObject") or {}).items():
        x = v.get_object()
        if id(x) in seen: continue
        seen.add(id(x))
        if x.get("/Subtype") == "/Image":
            out["images"].add(f"{x.get('/ColorSpace')} bpc={x.get('/BitsPerComponent')} filter={x.get('/Filter')} smask={'/SMask' in x}")
        else:
            if "/Group" in x: out["groups"].add(str(x["/Group"].get_object().get("/CS")) + " " + str(x["/Group"].get_object().get("/S")))
            ops = ContentStream(x, None).operations
            count(ops, out)
            walk(x.get("/Resources"), seen, out, label)

def count(ops, out):
    for operands, op in ops:
        o = op.decode() if isinstance(op, bytes) else str(op)
        if o in ("rg","RG","k","K","g","G","sc","SC","scn","SCN","cs","CS"):
            out["ops"][o] += 1
            if o in ("cs","CS","scn","SCN"): out["op operands"].add(o + " " + " ".join(str(a) for a in operands if isinstance(a, str) or hasattr(a, "startswith")))

def main(path):
    r = PdfReader(path)
    out = collections.defaultdict(set); out["ops"] = collections.Counter()
    seen = set()
    for p in r.pages:
        count(ContentStream(p.get_contents(), r).operations, out)
        walk(p.get("/Resources"), seen, out, "page")
    root = r.trailer["/Root"]
    print("OutputIntents:", root.get("/OutputIntents") is not None, "| Metadata:", "/Metadata" in root)
    for pg in r.pages[:1]:
        print("boxes:", {b: [float(x) for x in getattr(pg, b)] for b in ("mediabox","trimbox","bleedbox")})
    for k, v in out.items():
        print(f"{k}: {dict(v) if isinstance(v, collections.Counter) else sorted(map(str, v))}")
main(sys.argv[1])
