"""Probe 2 (options b and d): rewrite a funground/Cairo RGB PDF to DeviceCMYK with pypdf.

  rgb_to_cmyk.py in.pdf out.pdf naive
  rgb_to_cmyk.py in.pdf out.pdf icc cmyk_profile.icc

naive = K = 1 - max(r,g,b), the textbook formula (no profile, pure Python).
icc   = each colour through littleCMS (Pillow ImageCms): sRGB to the CMYK profile, relative
        colorimetric with black point compensation. Needs Pillow's _imagingcms (not in Pyodide).
Handles: rg/RG operators, Form XObjects (nested), shading dictionaries (and their Type 2/3
functions, resampled), RGB images, transparency-group colour spaces. Counts what it changed.
"""
import sys
import time

from pypdf import PdfReader, PdfWriter
from pypdf.generic import (ArrayObject, ContentStream, DictionaryObject, FloatObject,
                           NameObject, NumberObject)

MODE = "naive"
XFORM = None
STATS = {}


def bump(k, n=1):
    STATS[k] = STATS.get(k, 0) + n


def naive(r, g, b):
    k = 1 - max(r, g, b)
    if k >= 1:
        return (0.0, 0.0, 0.0, 1.0)
    return ((1 - r - k) / (1 - k), (1 - g - k) / (1 - k), (1 - b - k) / (1 - k), k)


def icc_many(rgbs):
    from PIL import Image, ImageCms
    im = Image.new("RGB", (len(rgbs), 1))
    im.putdata([tuple(round(c * 255) for c in t) for t in rgbs])
    out = ImageCms.applyTransform(im, XFORM)
    return [tuple(v / 255 for v in px) for px in out.getdata()]


def conv(rgb):
    return icc_many([rgb])[0] if MODE == "icc" else naive(*rgb)


def fl(x):
    return FloatObject(f"{x:.4f}")


def rewrite_ops(ops):
    out = []
    for operands, op in ops:
        if op in (b"rg", b"RG"):
            c = conv(tuple(float(x) for x in operands))
            out.append(([fl(v) for v in c], b"k" if op == b"rg" else b"K"))
            bump("rg/RG operators")
        else:
            out.append((operands, op))
    return out


def _sub(f, u):
    c0, c1, n = [float(x) for x in f["/C0"]], [float(x) for x in f["/C1"]], float(f["/N"])
    return tuple(a + (u ** n) * (b - a) for a, b in zip(c0, c1))


def _eval(fn, t):
    if fn["/FunctionType"] == 2:
        return _sub(fn, t)
    bounds = [0.0] + [float(x) for x in fn["/Bounds"]] + [1.0]
    enc = [float(x) for x in fn["/Encode"]]
    for i in range(len(bounds) - 1):
        if t <= bounds[i + 1] or i == len(bounds) - 2:
            lo, hi = bounds[i], bounds[i + 1]
            u = (t - lo) / (hi - lo) if hi > lo else 0
            u = enc[2 * i] + u * (enc[2 * i + 1] - enc[2 * i])
            return _sub(fn["/Functions"][i].get_object(), u)


def convert_function(fn, steps=16):
    """A new Type 3 function: the RGB gradient sampled at `steps` and pushed through the transform."""
    fn = fn.get_object()
    pts = [_eval(fn, i / steps) for i in range(steps + 1)]
    cm = icc_many(pts) if MODE == "icc" else [naive(*p) for p in pts]
    subs = ArrayObject()
    for i in range(steps):
        subs.append(DictionaryObject({
            NameObject("/FunctionType"): NumberObject(2),
            NameObject("/Domain"): ArrayObject([NumberObject(0), NumberObject(1)]),
            NameObject("/C0"): ArrayObject([fl(v) for v in cm[i]]),
            NameObject("/C1"): ArrayObject([fl(v) for v in cm[i + 1]]),
            NameObject("/N"): NumberObject(1)}))
    return DictionaryObject({
        NameObject("/FunctionType"): NumberObject(3),
        NameObject("/Domain"): ArrayObject([NumberObject(0), NumberObject(1)]),
        NameObject("/Functions"): subs,
        NameObject("/Bounds"): ArrayObject([fl(i / steps) for i in range(1, steps)]),
        NameObject("/Encode"): ArrayObject([NumberObject(v) for _ in range(steps) for v in (0, 1)])})


def convert_image(x):
    from PIL import Image
    w, h = int(x["/Width"]), int(x["/Height"])
    raw = x.get_data()
    if len(raw) != w * h * 3:
        bump("images skipped (unexpected data)")
        return
    t0 = time.time()
    if MODE == "icc":
        from PIL import ImageCms
        out = ImageCms.applyTransform(Image.frombytes("RGB", (w, h), raw), XFORM).tobytes()
    else:
        cache, buf = {}, bytearray()
        for i in range(0, len(raw), 3):
            key = raw[i:i + 3]
            v = cache.get(key)
            if v is None:
                c = naive(key[0] / 255, key[1] / 255, key[2] / 255)
                v = cache[key] = bytes(round(q * 255) for q in c)
            buf += v
        out = bytes(buf)
    x.set_data(out)
    x[NameObject("/ColorSpace")] = NameObject("/DeviceCMYK")
    bump("image pixels", w * h)
    bump("image ms", int((time.time() - t0) * 1000))


def convert_shadings(shadings, seen):
    for v in list(shadings.values()):
        sh = v.get_object()
        if id(sh) in seen:
            continue
        seen.add(id(sh))
        if sh.get("/ColorSpace") == "/DeviceRGB":
            sh[NameObject("/ColorSpace")] = NameObject("/DeviceCMYK")
            sh[NameObject("/Function")] = convert_function(sh["/Function"])
            bump("shadings")


def walk(res, seen):
    if res is None:
        return
    res = res.get_object()
    convert_shadings(res.get("/Shading") or {}, seen)
    for v in list((res.get("/Pattern") or {}).values()):
        p = v.get_object()
        if id(p) in seen:
            continue
        seen.add(id(p))
        bump("patterns")
        if "/Shading" in p:
            convert_shadings({"/s": p["/Shading"]}, seen)
        if "/Resources" in p:
            walk(p["/Resources"], seen)
    for v in list((res.get("/XObject") or {}).values()):
        x = v.get_object()
        if id(x) in seen:
            continue
        seen.add(id(x))
        if x.get("/Subtype") == "/Image":
            if x.get("/ColorSpace") == "/DeviceRGB":
                convert_image(x)
        else:
            grp = x.get("/Group")
            if grp and grp.get_object().get("/CS") == "/DeviceRGB":
                grp.get_object()[NameObject("/CS")] = NameObject("/DeviceCMYK")
                bump("group colour spaces")
            cs = ContentStream(x, None)
            cs.operations = rewrite_ops(cs.operations)
            x.set_data(cs.get_data())
            bump("form xobjects")
            walk(x.get("/Resources"), seen)


def main(src, dst, mode, profile=None):
    global MODE, XFORM
    MODE = mode
    if mode == "icc":
        from PIL import ImageCms
        XFORM = ImageCms.buildTransform(
            ImageCms.createProfile("sRGB"), ImageCms.getOpenProfile(profile), "RGB", "CMYK",
            renderingIntent=ImageCms.Intent.RELATIVE_COLORIMETRIC,
            flags=ImageCms.Flags.BLACKPOINTCOMPENSATION)
    r = PdfReader(src)
    w = PdfWriter(clone_from=r)
    seen = set()
    for p in w.pages:
        grp = p.get("/Group")
        if grp and grp.get_object().get("/CS") == "/DeviceRGB":
            grp.get_object()[NameObject("/CS")] = NameObject("/DeviceCMYK")
            bump("page group colour spaces")
        cs = ContentStream(p.get_contents(), w)
        cs.operations = rewrite_ops(cs.operations)
        p.replace_contents(cs)
        walk(p.get("/Resources"), seen)
    w.write(dst)
    print(STATS)


if __name__ == "__main__":
    main(*sys.argv[1:])
