"""Q2: keep Cairo's outlines, then add an INVISIBLE text layer (Tr 3) in a post-processing step.

Pure Python: pypdf (BSD) writes the extra objects; fontTools (already a funground dependency)
subsets the TTF to just the glyphs used; HarfBuzz glyph ids/positions are reused as-is.
Variants:  A = ToUnicode only      B = ToUnicode + /ActualText per run (logical order for RTL)
"""
import io, sys
from fontTools import subset
from fontTools.ttLib import TTFont
from pypdf import PdfReader, PdfWriter
from pypdf.generic import (NameObject, DictionaryObject, ArrayObject, NumberObject, FloatObject,
                           StreamObject, DecodedStreamObject, TextStringObject, ByteStringObject)
from common import *

def build_font(runs, path=FONT):
    """Subset the font to the used glyphs; return (ttf bytes, {orig gid -> new gid}, widths, to_unicode)."""
    tt = TTFont(path); order = tt.getGlyphOrder(); upem = tt["head"].unitsPerEm
    used, tounicode = {}, {}
    for text, x, base, size in runs:
        glyphs, _ = shape(text, size, path)
        for k, (gid, gx, gy, cl) in enumerate(glyphs):
            used[gid] = True
            nxt = next((g[3] for g in glyphs[k+1:] if g[3] != cl), None)
            # text of this glyph's cluster (cluster = start offset into text; RTL clusters run backwards)
            starts = sorted({g[3] for g in glyphs}); i = starts.index(cl)
            end = starts[i+1] if i+1 < len(starts) else len(text)
            tounicode.setdefault(gid, text[cl:end])
    opts = subset.Options(); opts.layout_features = []; opts.glyph_names = True; opts.notdef_outline = True
    opts.hinting = False; opts.name_IDs = []; opts.drop_tables += ["GSUB", "GPOS", "GDEF", "kern"]
    sub = subset.Subsetter(opts); sub.populate(glyphs=[order[g] for g in used]); f = TTFont(path); sub.subset(f)
    new_order = f.getGlyphOrder(); remap = {g: new_order.index(order[g]) for g in used}
    widths = {remap[g]: f["hmtx"][order[g]][0] * 1000 / upem for g in used}
    buf = io.BytesIO(); f.save(buf)
    return buf.getvalue(), remap, widths, {remap[g]: t for g, t in tounicode.items()}, {g: f["hmtx"][order[g]][0] for g in used}, upem

def cmap(tounicode):
    lines = ["/CIDInit /ProcSet findresource begin 12 dict begin begincmap",
             "/CMapName /Adobe-Identity-UCS def /CMapType 2 def",
             "1 begincodespacerange <0000> <FFFF> endcodespacerange", f"{len(tounicode)} beginbfchar"]
    for gid, t in sorted(tounicode.items()):
        lines.append(f"<{gid:04X}> <{t.encode('utf-16-be').hex().upper()}>")
    lines += ["endbfchar", "endcmap CMapName currentdict /CMap defineresource pop end end"]
    return "\n".join(lines).encode()

def add_invisible_layer(src, dst, runs, actual_text=True, mode="tm", path=FONT):
    ttf, remap, widths, tou, adv_units, upem = build_font(runs, path)
    r = PdfReader(src); w = PdfWriter(); w.append(r)
    def stream(data, **d):
        so = DecodedStreamObject(); so.set_data(data)
        for k, v in d.items(): so[NameObject("/" + k)] = v
        return w._add_object(so.flate_encode())
    ff = stream(ttf, Length1=NumberObject(len(ttf)))
    desc = w._add_object(DictionaryObject({
        NameObject("/Type"): NameObject("/FontDescriptor"), NameObject("/FontName"): NameObject("/ABCDEF+DejaVuSans"),
        NameObject("/Flags"): NumberObject(4), NameObject("/FontBBox"): ArrayObject(NumberObject(v) for v in (-1000, -400, 2000, 1200)),
        NameObject("/ItalicAngle"): NumberObject(0), NameObject("/Ascent"): NumberObject(928), NameObject("/Descent"): NumberObject(-236),
        NameObject("/CapHeight"): NumberObject(729), NameObject("/StemV"): NumberObject(80), NameObject("/FontFile2"): ff}))
    W = ArrayObject(); [W.extend([NumberObject(g), ArrayObject([FloatObject(round(v, 1))])]) for g, v in sorted(widths.items())]
    cid = w._add_object(DictionaryObject({
        NameObject("/Type"): NameObject("/Font"), NameObject("/Subtype"): NameObject("/CIDFontType2"),
        NameObject("/BaseFont"): NameObject("/ABCDEF+DejaVuSans"),
        NameObject("/CIDSystemInfo"): DictionaryObject({NameObject("/Registry"): TextStringObject("Adobe"),
                                                       NameObject("/Ordering"): TextStringObject("Identity"), NameObject("/Supplement"): NumberObject(0)}),
        NameObject("/FontDescriptor"): desc, NameObject("/CIDToGIDMap"): NameObject("/Identity"), NameObject("/W"): W}))
    font = w._add_object(DictionaryObject({
        NameObject("/Type"): NameObject("/Font"), NameObject("/Subtype"): NameObject("/Type0"), NameObject("/BaseFont"): NameObject("/ABCDEF+DejaVuSans"),
        NameObject("/Encoding"): NameObject("/Identity-H"), NameObject("/DescendantFonts"): ArrayObject([cid]),
        NameObject("/ToUnicode"): stream(cmap(tou))}))
    # content, one BT..ET per run.
    #  mode "tj"  : one TJ in HarfBuzz (visual, left-to-right) order; adjustments reproduce HarfBuzz's positions
    #  mode "tm"  : every glyph placed with its own text matrix, written in LOGICAL order (reversed for RTL),
    #               so content-stream order = reading order while positions = what is drawn
    out = []; H = page_h(runs); nl = chr(10)
    for text, x, base, size in runs:
        glyphs, total = shape(text, size, path)
        if actual_text: out.append(f"/Span <</ActualText <FEFF{text.encode('utf-16-be').hex().upper()}>>> BDC")
        out.append(f"BT 3 Tr /FInv {size} Tf")
        if mode == "tj":
            pen = 0.0; parts = []
            for gid, gx, gy, cl in glyphs:
                if abs(gx - pen) > 0.01: parts.append(f"{-(gx - pen) * 1000 / size:.1f}")
                parts.append(f"<{remap[gid]:04X}>"); pen = gx + adv_units[gid] * size / upem
            out.append(f"{x:.3f} {H - base:.3f} Td [" + " ".join(parts) + "] TJ ET")
        else:
            seq = list(reversed(glyphs)) if is_rtl(text) else glyphs
            for gid, gx, gy, cl in seq:
                out.append(f"1 0 0 1 {x + gx:.3f} {H - base - gy:.3f} Tm <{remap[gid]:04X}> Tj")
            out.append("ET")
        if actual_text: out.append("EMC")
    page = w.pages[0]
    res = page["/Resources"]; fonts = res.get("/Font") or DictionaryObject(); res[NameObject("/Font")] = fonts
    fonts[NameObject("/FInv")] = font
    # append our content as a second content stream (separate q/Q state: Cairo's stream is balanced)
    # Cairo's stream starts with an unbalanced "1 0 0 -1 0 H cm" (y-flip), so isolate it with q ... Q
    old = page["/Contents"]; arr = ArrayObject([stream(b"q")])
    arr.extend(old if isinstance(old, ArrayObject) else [page.raw_get("/Contents")]); arr.append(stream(b"Q"))
    arr.append(stream(nl.join(out).encode())); page[NameObject("/Contents")] = arr
    with open(dst, "wb") as fh: w.write(fh)

if __name__ == "__main__":
    base = os.path.join(OUT, "exp2_base.pdf"); runs = make_base(base)
    for name, at, mode in (("A_tj_visual", False, "tj"), ("B_tm_logical", False, "tm"), ("C_tm_logical_actualtext", True, "tm")):
        dst = os.path.join(OUT, f"exp2_{name}.pdf"); add_invisible_layer(base, dst, runs, actual_text=at, mode=mode)
        print(); print("##### variant", name, " (+%d bytes over outlines-only)" % (os.path.getsize(dst) - os.path.getsize(base))); report(dst)
