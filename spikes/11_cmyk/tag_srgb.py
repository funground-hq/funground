"""Probe 7 (option c2): keep the colours as RGB but tag them as ICCBased sRGB, then add a CMYK
OutputIntent. No colour maths of ours: the print shop's RIP converts. This is how PDF/X-4 (ISO
15930-7) lets a file carry RGB.

  tag_srgb.py in.pdf out.pdf

The sRGB profile comes from littleCMS via Pillow (ImageCms.createProfile) here; in the product it
could be a small profile built by our own code (a matrix profile is about 500 bytes).
"""
import sys

from pypdf import PdfReader, PdfWriter
from pypdf.generic import (ArrayObject, ContentStream, DecodedStreamObject, DictionaryObject,
                           NameObject, NumberObject)

STATS = {}


def bump(k):
    STATS[k] = STATS.get(k, 0) + 1


def main(src, dst):
    from PIL import ImageCms
    profile = ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes()
    w = PdfWriter(clone_from=PdfReader(src))
    s = DecodedStreamObject()
    s.set_data(profile)
    s[NameObject("/N")] = NumberObject(3)
    s[NameObject("/Alternate")] = NameObject("/DeviceRGB")
    cs = ArrayObject([NameObject("/ICCBased"), w._add_object(s)])
    STATS["profile bytes"] = len(profile)
    seen = set()

    def tag_resources(res):
        res = res.get_object()
        d = res.get("/ColorSpace")
        if d is None:
            d = DictionaryObject()
            res[NameObject("/ColorSpace")] = d
        d[NameObject("/FunSRGB")] = cs

    def ops(obj, setter):
        c = ContentStream(obj, w)
        out = []
        for operands, op in c.operations:
            if op in (b"rg", b"RG"):
                out.append(([NameObject("/FunSRGB")], b"cs" if op == b"rg" else b"CS"))
                out.append((operands, b"sc" if op == b"rg" else b"SC"))
                bump("rg/RG operators")
            else:
                out.append((operands, op))
        c.operations = out
        setter(c)

    def walk(res):
        if res is None:
            return
        res = res.get_object()
        for v in list((res.get("/Shading") or {}).values()):
            sh = v.get_object()
            if id(sh) not in seen:
                seen.add(id(sh))
                if sh.get("/ColorSpace") == "/DeviceRGB":
                    sh[NameObject("/ColorSpace")] = cs
                    bump("shadings")
        for v in list((res.get("/XObject") or {}).values()):
            x = v.get_object()
            if id(x) in seen:
                continue
            seen.add(id(x))
            if x.get("/Subtype") == "/Image":
                if x.get("/ColorSpace") == "/DeviceRGB":
                    x[NameObject("/ColorSpace")] = cs
                    bump("images")
            else:
                g = x.get("/Group")
                if g and g.get_object().get("/CS") == "/DeviceRGB":
                    g.get_object()[NameObject("/CS")] = cs
                    bump("group colour spaces")
                if x.get("/Resources") is None:
                    x[NameObject("/Resources")] = DictionaryObject()
                tag_resources(x["/Resources"])
                ops(x, lambda c, x=x: x.set_data(c.get_data()))
                bump("form xobjects")
                walk(x.get("/Resources"))

    for p in w.pages:
        g = p.get("/Group")
        if g and g.get_object().get("/CS") == "/DeviceRGB":
            g.get_object()[NameObject("/CS")] = cs
        tag_resources(p["/Resources"])
        ops(p.get_contents(), lambda c, p=p: p.replace_contents(c))
        walk(p.get("/Resources"))
    w.write(dst)
    print(STATS)


if __name__ == "__main__":
    main(*sys.argv[1:])
