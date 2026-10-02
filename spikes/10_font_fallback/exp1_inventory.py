"""Inventory of candidate fallback fonts: file size, fsType, licence string, tables, coverage, subset size."""
import glob, io, os, sys
from fontTools.ttLib import TTFont, TTCollection
from fontTools import subset
HERE = os.path.dirname(os.path.abspath(__file__))
files = sorted(glob.glob(os.path.join(HERE, "fonts", "*.tt[fc]")) + glob.glob(os.path.join(HERE, "fonts", "*.otf")))
files.append(os.path.join(HERE, "..", "..", "funground", "fonts", "DejaVuSans.ttf"))
print(f"{'file':36}{'MB':>7} {'glyphs':>7} {'cmap':>7} fsType  outline   colour tables   licence")
for p in files:
    mb = os.path.getsize(p) / 1e6
    if p.endswith(".ttc"):
        tt = TTCollection(p).fonts[0]
    else:
        tt = TTFont(p, fontNumber=0)
    n = tt["maxp"].numGlyphs
    cm = tt.getBestCmap() or {}
    fs = tt["OS/2"].fsType if "OS/2" in tt else None
    outl = "glyf" if "glyf" in tt else "CFF " if "CFF " in tt else "CFF2" if "CFF2" in tt else "-"
    col = [t for t in ("COLR", "CPAL", "CBDT", "CBLC", "sbix", "SVG ") if t in tt]
    colv = f"COLRv{tt['COLR'].version}" if "COLR" in tt else ""
    lic = (tt["name"].getDebugName(13) or "")[:44]
    print(f"{os.path.basename(p):36}{mb:7.2f} {n:7} {len(cm):7} {fs!s:6}  {outl:7} {','.join(col)} {colv}  {lic}")
    if "fvar" in tt: print("   variable axes:", [(a.axisTag, a.minValue, a.defaultValue, a.maxValue) for a in tt["fvar"].axes])
