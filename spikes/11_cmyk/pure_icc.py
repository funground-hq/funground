"""Probe 8 (option d without littleCMS): a pure-Python sRGB -> CMYK converter for one CMYK ICC profile
(PCS to device table B2A1 of type 'mft2', which most press profiles use), to see whether the
ICC route could work in Pyodide where Pillow has no ImageCms.

  pure_icc.py profile.icc      compares with littleCMS (Pillow) on a handful of colours

Scope kept small on purpose: mft2 (lut16) tables, Lab PCS, sRGB input, relative colorimetric, no
black point compensation. About 60 lines of real work; compare with lcms to see the error.
"""
import struct
import sys
from bisect import bisect_right


def load(path, tag=b"B2A1"):
    d = open(path, "rb").read()
    assert d[16:20] == b"CMYK" and d[20:24] == b"Lab ", "this probe handles CMYK profiles with Lab PCS"
    n = struct.unpack(">I", d[128:132])[0]
    for i in range(n):
        sig, off, size = struct.unpack(">4sII", d[132 + 12 * i:144 + 12 * i])
        if sig == tag:
            break
    t = d[off:off + size]
    assert t[:4] == b"mft2"
    nin, nout, grid = t[8], t[9], t[10]
    nie, noe = struct.unpack(">HH", t[48:52])
    p = 52
    inp = [struct.unpack(f">{nie}H", t[p + 2 * nie * i:p + 2 * nie * (i + 1)]) for i in range(nin)]
    p += 2 * nie * nin
    clut_n = grid ** nin * nout
    clut = struct.unpack(f">{clut_n}H", t[p:p + 2 * clut_n])
    p += 2 * clut_n
    out = [struct.unpack(f">{noe}H", t[p + 2 * noe * i:p + 2 * noe * (i + 1)]) for i in range(nout)]
    return nin, nout, grid, inp, clut, out


def curve(tab, x):                       # x in 0..1, linear interpolation in a 16-bit table
    f = x * (len(tab) - 1)
    i = min(int(f), len(tab) - 2)
    return (tab[i] + (f - i) * (tab[i + 1] - tab[i])) / 65535


def srgb_to_lab(r, g, b):
    def lin(c):
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = lin(r), lin(g), lin(b)
    # sRGB (D65) to XYZ, Bradford-adapted to D50 (the ICC PCS white)
    X = 0.4360747 * r + 0.3850649 * g + 0.1430804 * b
    Y = 0.2225045 * r + 0.7168786 * g + 0.0606169 * b
    Z = 0.0139322 * r + 0.0971045 * g + 0.7141733 * b
    wx, wy, wz = 0.9642, 1.0, 0.8249

    def f(t):
        return t ** (1 / 3) if t > 216 / 24389 else (24389 / 27 * t + 16) / 116
    fx, fy, fz = f(X / wx), f(Y / wy), f(Z / wz)
    return 116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz)


def to_cmyk(prof, rgb):
    nin, nout, grid, inp, clut, out = prof
    L, a, b = srgb_to_lab(*rgb)
    v16 = (L / 100 * 65280, (a + 128) / 255 * 65280, (b + 128) / 255 * 65280)     # legacy 16-bit Lab
    x = [curve(inp[i], min(max(v / 65535, 0), 1)) for i, v in enumerate(v16)]
    pos = [xi * (grid - 1) for xi in x]
    i0 = [min(int(p), grid - 2) for p in pos]
    fr = [p - i for p, i in zip(pos, i0)]
    res = [0.0] * nout
    for corner in range(8):
        w, idx = 1.0, 0
        for k in range(3):
            bit = (corner >> k) & 1
            w *= fr[k] if bit else 1 - fr[k]
            idx = idx * grid + i0[k] + bit
        if w:
            base = idx * nout
            for o in range(nout):
                res[o] += w * clut[base + o]
    return [curve(out[o], res[o] / 65535) for o in range(nout)]


if __name__ == "__main__":
    import warnings
    warnings.simplefilter("ignore")
    from PIL import Image, ImageCms
    prof = load(sys.argv[1])
    t = ImageCms.buildTransform(ImageCms.createProfile("sRGB"), ImageCms.getOpenProfile(sys.argv[1]), "RGB", "CMYK",
                                renderingIntent=ImageCms.Intent.RELATIVE_COLORIMETRIC)
    worst = 0
    for name, rgb in {"black": (0, 0, 0), "grey": (128, 128, 128), "red": (255, 0, 0), "lime": (0, 255, 0), "blue": (0, 0, 255),
                      "gold": (255, 215, 0), "tomato": (255, 99, 71), "navy": (25, 25, 112), "skin": (224, 172, 150)}.items():
        ref = [v / 2.55 for v in ImageCms.applyTransform(Image.new("RGB", (1, 1), rgb), t).getpixel((0, 0))]
        mine = [v * 100 for v in to_cmyk(prof, [c / 255 for c in rgb])]
        d = max(abs(a - b) for a, b in zip(ref, mine))
        worst = max(worst, d)
        print(f"{name:7} lcms {[round(v) for v in ref]}  pure {[round(v) for v in mine]}  max diff {d:.1f} points")
    print("worst difference (percentage points of ink):", round(worst, 1))
