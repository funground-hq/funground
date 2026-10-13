"""Probe 5 (option c): turn a converted PDF into a PDF/X-4-shaped file and run a self-made checklist.

  make_pdfx_probe.py in_cmyk.pdf out.pdf profile.icc [rgb]

Adds: OutputIntent (GTS_PDFX, embedded CMYK ICC profile), Info /GTS_PDFXVersion /Trapped /Title,
XMP with pdfxid:GTSPDFXVersion, trailer /ID, TrimBox/BleedBox (S-164 will supply real ones).
With the 4th argument "rgb" the content keeps its RGB colours but they are tagged as ICCBased sRGB
(the PDF/X-4 way to leave RGB for the printer to convert).
This is NOT a conformance claim: no PDF/X validator (veraPDF, Acrobat preflight) was available.
"""
import sys
import zlib

from pypdf import PdfReader, PdfWriter
from pypdf.generic import (ArrayObject, ContentStream, DecodedStreamObject, DictionaryObject,
                           FloatObject, NameObject, NumberObject, TextStringObject)

XMP = """<?xpacket begin="﻿" id="W5M0MpCehiHzreSzNTczkc9d"?>
<x:xmpmeta xmlns:x="adobe:ns:meta/"><rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
<rdf:Description rdf:about="" xmlns:pdfxid="http://www.npes.org/pdfx/ns/id/" xmlns:dc="http://purl.org/dc/elements/1.1/"
 xmlns:xmp="http://ns.adobe.com/xap/1.0/" xmlns:pdf="http://ns.adobe.com/pdf/1.3/">
<pdfxid:GTSPDFXVersion>PDF/X-4</pdfxid:GTSPDFXVersion>
<dc:title><rdf:Alt><rdf:li xml:lang="x-default">funground probe</rdf:li></rdf:Alt></dc:title>
<pdf:Trapped>False</pdf:Trapped>
</rdf:Description></rdf:RDF></x:xmpmeta>
<?xpacket end="w"?>"""


def stream(w, data: bytes, **entries):
    s = DecodedStreamObject()
    s.set_data(data)
    for k, v in entries.items():
        s[NameObject("/" + k)] = v
    return w._add_object(s)


def main(src, dst, profile, mode="cmyk"):
    w = PdfWriter(clone_from=PdfReader(src))
    icc = open(profile, "rb").read()
    n = 4
    prof = stream(w, icc, N=NumberObject(n), Alternate=NameObject("/DeviceCMYK"))
    oi = DictionaryObject({
        NameObject("/Type"): NameObject("/OutputIntent"), NameObject("/S"): NameObject("/GTS_PDFX"),
        NameObject("/OutputConditionIdentifier"): TextStringObject("probe CMYK"),
        NameObject("/Info"): TextStringObject("probe CMYK profile"),
        NameObject("/RegistryName"): TextStringObject("http://www.color.org"),
        NameObject("/DestOutputProfile"): prof})
    w._root_object[NameObject("/OutputIntents")] = ArrayObject([w._add_object(oi)])
    w._root_object[NameObject("/Metadata")] = stream(w, XMP.encode("utf-8"), Type=NameObject("/Metadata"), Subtype=NameObject("/XML"))
    w.add_metadata({"/Title": "funground probe", "/GTS_PDFXVersion": "PDF/X-4", "/Trapped": "/False"})
    for p in w.pages:
        mb = [float(x) for x in p.mediabox]
        p[NameObject("/TrimBox")] = ArrayObject([FloatObject(v) for v in mb])
        p[NameObject("/BleedBox")] = ArrayObject([FloatObject(v) for v in mb])
    w.pdf_header = b"%PDF-1.6"          # X-4 is PDF 1.6; Cairo writes 1.3
    import hashlib
    ident = TextStringObject(hashlib.md5(open(src, "rb").read()).hexdigest())
    w._ID = ArrayObject([ident, ident])  # trailer /ID is required
    w.write(dst)


def check(path):
    """Self-made checklist against the main PDF/X-4 (ISO 15930-7) rules we can test without a validator."""
    r = PdfReader(path)
    root = r.trailer["/Root"]
    raw = open(path, "rb").read()
    res = {}
    res["header version"] = raw[:8].decode()
    res["OutputIntent GTS_PDFX + profile"] = bool(root.get("/OutputIntents")) and "/DestOutputProfile" in root["/OutputIntents"][0]
    res["XMP pdfxid"] = b"GTSPDFXVersion" in root["/Metadata"].get_data() if "/Metadata" in root else False
    info = r.metadata or {}
    res["Info GTS_PDFXVersion / Title / Trapped"] = all(k in info for k in ("/GTS_PDFXVersion", "/Title", "/Trapped"))
    res["trailer /ID"] = "/ID" in r.trailer
    res["no /Encrypt"] = "/Encrypt" not in r.trailer
    res["TrimBox + BleedBox"] = all("/TrimBox" in p and "/BleedBox" in p for p in r.pages)
    fonts, unembedded = 0, 0
    seen = set()

    def fonts_in(resd):
        nonlocal fonts, unembedded
        if resd is None:
            return
        resd = resd.get_object()
        for v in (resd.get("/Font") or {}).values():
            f = v.get_object()
            if id(f) in seen:
                continue
            seen.add(id(f)); fonts += 1
            d = f["/DescendantFonts"][0].get_object() if "/DescendantFonts" in f else f
            fd = d.get("/FontDescriptor")
            if fd is None or not any(k in fd.get_object() for k in ("/FontFile", "/FontFile2", "/FontFile3")):
                unembedded += 1
        for v in (resd.get("/XObject") or {}).values():
            x = v.get_object()
            if id(x) not in seen and x.get("/Subtype") == "/Form":
                seen.add(id(x)); fonts_in(x.get("/Resources"))
    for p in r.pages:
        fonts_in(p.get("/Resources"))
    res[f"fonts embedded ({fonts} fonts)"] = unembedded == 0
    return res


if __name__ == "__main__":
    if sys.argv[1] == "check":
        for k, v in check(sys.argv[2]).items():
            print(("PASS " if v is True else "FAIL " if v is False else "     ") + k + ("" if isinstance(v, bool) else f": {v}"))
    else:
        main(*sys.argv[1:])
