"""Real text in PDFs (story S-094, contract T15, decision D-043).

funground draws text as glyph outlines (T2). For a PDF that would leave nothing to select, search
or copy, so the PDF exporters do this instead:

1. **While drawing.** The Cairo renderer is given a `PdfTextCollector`. For each text run it asks
   the collector for a *marker*: a large four-cornered shape around the run, in user space. The
   renderer pushes a group, clips to the marker, paints the run's colour or gradient, and paints
   the group back with the current clip, transform, opacity and blend mode. Cairo writes every
   such group as its own Form XObject, with the marker as a clip path whose corners carry Cairo's
   transform baked in. The collector records the run (glyphs, positions, font, variation).
2. **After ``surface.finish()``.** `PdfTextCollector.finish` opens the file with pypdf, finds every
   marker clip path, and replaces it with the run's glyphs as text in clip mode (``7 Tr``). The
   paint that Cairo wrote after the marker now fills exactly the glyphs, so the page looks the
   same and carries real text. One subset of each font (per variation location) is embedded per
   document, shared by every page, with a ToUnicode map built from HarfBuzz clusters.

How a marker is recognised. It is a quadrilateral P0, P1, Q, P2 (never a rectangle: Cairo reduces
an axis-aligned rectangle clip to a box cut to the page, which loses its corners). P1 - P0 and
P2 - P0 are the run's two axes; Q = P0 + a (P1 - P0) + b (P2 - P0) where (a, b) encode the run's
number. Affine maps keep a and b, so the number reads back whatever transform Cairo applied, and
the map from P0, P1, P2 to the emitted corners is the run's transform into the XObject's space.

Glyphs are written in reading order, each placed by its own text matrix at HarfBuzz's position.
Two cases also get an ActualText span, because pdfium (Chrome, Edge) reads them wrongly without
one: a right-to-left run (pdfium orders its words by position) and a cluster of several glyphs,
such as a letter and a combining accent (see `_glyph_ops`).

A run falls back to outlines (exactly today's drawing) when its font forbids embedding (OS/2
``fsType`` restricted-licence bit), cannot be embedded (not TrueType or CFF outlines, or a variable
font that cannot be instanced), or the transform is too degenerate to read back. Shadows stay
shapes (the renderer draws them from outlines before the run), SVG keeps outlines, and the window
and PNG never see any of this.
"""
from __future__ import annotations

import contextlib
import io
import logging
import math
import os
import re
from dataclasses import dataclass, field

from fontTools import subset
from fontTools.ttLib import TTFont
from pypdf import PdfReader, PdfWriter
from pypdf.generic import (ArrayObject, DecodedStreamObject, DictionaryObject, FloatObject, IndirectObject,
                           NameObject, NumberObject, TextStringObject)

RESTRICTED_LICENCE = 0x0002          # OS/2 fsType bit: the font must not be embedded

# Run numbers are encoded as Q's (a, b) on a 0.001 grid in [0.55, 0.95): 400 x 400 runs per file.
_GRID = 400
_STEP = 0.001
_LOW = 0.55
_TOLERANCE = 1e-4                    # how far a decoded a or b may sit from its grid value
MAX_RUNS = _GRID * _GRID             # past this, runs fall back to outlines
_MIN_DEVICE = 2000.0                 # the marker's short side in device units, at least (precision)
_MAX_DEVICE = 1.0e6                  # ... and its long side at most (Cairo's fixed-point range)

_NUM = rb"(-?(?:\d+\.?\d*|\.\d+))"
_MARKER = re.compile(
    _NUM + rb"\s+" + _NUM + rb"\s+m\s+"
    + _NUM + rb"\s+" + _NUM + rb"\s+l\s+"
    + _NUM + rb"\s+" + _NUM + rb"\s+l\s+"
    + _NUM + rb"\s+" + _NUM + rb"\s+l\s+h\s+"
    + rb"(?:-?[\d.]+\s+-?[\d.]+\s+m\s+)?W\s+n"
)


@dataclass(eq=False)                 # compared by identity: one per font file and location
class _Font:
    """One font file at one variation location, prepared for embedding."""

    tt: TTFont                       # the font (already instanced if variable); subset at the end
    cff: bool                        # CFF outlines (CIDFontType0) rather than TrueType (CIDFontType2)
    name: str                        # PostScript-style name, without the subset tag
    resource: str = ""               # the /Font resource name used in content streams
    ref: IndirectObject | None = None
    chars: dict[int, set[str]] = field(default_factory=dict)   # glyph id -> characters the font maps to it
    to_unicode: dict[int, str] = field(default_factory=dict)
    used: set[int] = field(default_factory=set)        # every glyph id drawn, for the subset


@dataclass
class PdfTextRun:
    """One text run drawn as a marker: what is needed to write it back as text."""

    number: int
    run: object                      # typography.TextRun
    x: float
    y: float
    corners: tuple                   # P0, P1, P2 in user space
    linear: tuple                    # the device matrix's (xx, yx, xy, yy) when it was drawn
    font: _Font


def _fmt(v: float) -> str:
    s = f"{v:.6f}".rstrip("0").rstrip(".")
    return "0" if s in ("", "-0") else s


@contextlib.contextmanager
def _quiet_fonttools():
    """fontTools logs notes such as "FFTM NOT subset" as warnings; a learner's save stays silent."""
    logger = logging.getLogger("fontTools")
    level = logger.level
    logger.setLevel(logging.ERROR)
    try:
        yield
    finally:
        logger.setLevel(level)


def _ps_name(tt: TTFont, path: str) -> str:
    name = None
    if "name" in tt:
        name = tt["name"].getDebugName(6) or tt["name"].getDebugName(4) or tt["name"].getDebugName(1)
    name = name or os.path.splitext(os.path.basename(path))[0]
    return re.sub(r"[^A-Za-z0-9_-]", "", name) or "Font"


def _prepare(path: str, location: tuple) -> _Font | None:
    """The font at *path*, instanced at *location* if variable, or None when it cannot be embedded."""
    tt = TTFont(path)
    if "OS/2" in tt and tt["OS/2"].fsType & RESTRICTED_LICENCE:
        return None
    name = _ps_name(tt, path)
    if "fvar" in tt:
        from fontTools.varLib import instancer

        full = {a.axisTag: a.defaultValue for a in tt["fvar"].axes}
        full.update(dict(location))
        tt = instancer.instantiateVariableFont(tt, full)
        if location:
            name += "-" + "-".join(f"{tag}{_fmt(v)}" for tag, v in location).replace(".", "_")
            name = re.sub(r"[^A-Za-z0-9_-]", "", name)
    if "glyf" in tt:
        cff = False
    elif "CFF " in tt:
        cff = True
    else:
        return None                   # CFF2 or bitmap-only: outlines it is
    chars: dict[int, set[str]] = {}
    for code, glyph in (tt.getBestCmap() or {}).items():
        chars.setdefault(tt.getGlyphID(glyph), set()).add(chr(code))
    return _Font(tt, cff, name, chars=chars)


class PdfTextCollector:
    """Collects text runs while a PDF is drawn, then writes them into the file as real text."""

    def __init__(self) -> None:
        self.runs: dict[int, PdfTextRun] = {}
        self._fonts: dict[tuple, _Font | None] = {}

    # ---- while drawing (called by the Cairo renderer)
    def add(self, run, x: float, y: float, matrix: tuple) -> list[tuple[float, float]] | None:
        """Record *run* drawn at (x, y) under the device *matrix* (Cairo's xx, yx, xy, yy, x0, y0).
        Return the marker's corners in user space, or None to draw outlines instead."""
        if not run.glyphs or len(self.runs) >= MAX_RUNS:
            return None
        font = self._font(run.font.path, run.location)
        if font is None:
            return None
        xx, yx, xy, yy = matrix[:4]
        if not all(math.isfinite(v) for v in matrix):
            return None
        det = xx * yy - xy * yx
        norm2 = xx * xx + xy * xy + yx * yx + yy * yy
        if abs(det) < 1e-12 or norm2 <= 0:
            return None
        s_max = math.sqrt((norm2 + math.sqrt(max(norm2 * norm2 - 4 * det * det, 0.0))) / 2)
        s_min = abs(det) / s_max
        # Big enough to hold every glyph with room to spare, and big in device space for precision.
        extent = abs(run.advance) + run.size * (1 + (run.font.ascent - run.font.descent) / run.font.units_per_em)
        half = max(4 * extent, min(_MIN_DEVICE / s_min, _MAX_DEVICE / (4 * s_max)))
        if half * 4 * s_max > _MAX_DEVICE or half * s_min < 200:
            return None
        number = len(self.runs)
        a = _LOW + (number % _GRID) * _STEP
        b = _LOW + (number // _GRID) * _STEP
        cx = x + run.advance / 2
        cy = y + run.size / 2
        p0 = (cx - half, cy - half)
        p1 = (cx + 3 * half, cy - half)
        p2 = (cx - half, cy + 3 * half)
        q = (p0[0] + 4 * half * a, p0[1] + 4 * half * b)
        self.runs[number] = PdfTextRun(number, run, x, y, (p0, p1, p2), (xx, yx, xy, yy), font)
        return [p0, p1, q, p2]

    def _font(self, path: str, location: tuple) -> _Font | None:
        key = (os.path.normcase(os.path.abspath(path)), location)
        if key not in self._fonts:
            try:
                with _quiet_fonttools():
                    self._fonts[key] = _prepare(path, location)
            except Exception:         # a font fontTools cannot instance or read: outlines it is
                self._fonts[key] = None
        return self._fonts[key]

    # ---- after surface.finish()
    def finish(self, path: str) -> None:
        """Replace every marker in the PDF at *path* with its run's text and embed the fonts."""
        if not self.runs:
            return
        with open(path, "rb") as fh:
            data = fh.read()
        writer = PdfWriter(clone_from=PdfReader(io.BytesIO(data)))
        self._writer = writer
        self._used: list[_Font] = []
        visited: set = set()
        changed = False
        for page in writer.pages:
            contents = page.get("/Contents")
            if contents is not None:
                streams = contents.get_object()
                streams = list(streams) if isinstance(streams, ArrayObject) else [contents]
                for s in streams:
                    changed |= self._rewrite(s.get_object(), page)
            changed |= self._visit(page.get("/Resources"), visited)
        if not changed:
            return
        with _quiet_fonttools():
            for font in self._used:
                self._build_font(font)
        out = io.BytesIO()
        writer.write(out)
        with open(path, "wb") as fh:
            fh.write(out.getvalue())

    def _visit(self, resources, visited: set) -> bool:
        """Rewrite every Form XObject (and tiling pattern, and soft mask group) reachable from
        *resources*, nested ones included."""
        if resources is None:
            return False
        res = resources.get_object()
        changed = False
        children = []
        for kind in ("/XObject", "/Pattern"):
            entries = res.get(kind)
            if entries is not None:
                children.extend(entries.get_object().values())
        states = res.get("/ExtGState")
        if states is not None:
            for gs in states.get_object().values():
                smask = gs.get_object().get("/SMask")
                if smask is not None and not isinstance(smask.get_object(), NameObject):
                    group = smask.get_object().get("/G")
                    if group is not None:
                        children.append(group)
        for ref in children:
            key = (ref.idnum, ref.generation) if isinstance(ref, IndirectObject) else id(ref.get_object())
            if key in visited:
                continue
            visited.add(key)
            obj = ref.get_object()
            if not hasattr(obj, "get_data"):
                continue
            if obj.get("/Subtype") == "/Form" or obj.get("/PatternType") == 1:
                changed |= self._rewrite(obj, obj)
                changed |= self._visit(obj.get("/Resources"), visited)
        return changed

    def _rewrite(self, stream, holder) -> bool:
        """Replace the markers in one content *stream*; fonts go into *holder*'s /Resources."""
        data = stream.get_data()
        if b"W" not in data:
            return False
        fonts: list[_Font] = []
        new = _MARKER.sub(lambda m: self._text_for(m, fonts), data)
        if not fonts:
            return False
        stream.set_data(new)
        if "/Resources" not in holder:
            holder[NameObject("/Resources")] = DictionaryObject()
        res = holder["/Resources"].get_object()
        if "/Font" not in res:
            res[NameObject("/Font")] = DictionaryObject()
        table = res["/Font"].get_object()
        for font in fonts:
            table[NameObject(font.resource)] = font.ref
        return True

    def _text_for(self, m: re.Match, fonts: list) -> bytes:
        """The text replacing one marker match, or the match unchanged when it is not a marker."""
        e0, e1, eq, e2 = ((float(m.group(i)), float(m.group(i + 1))) for i in (1, 3, 5, 7))
        v1 = (e1[0] - e0[0], e1[1] - e0[1])
        v2 = (e2[0] - e0[0], e2[1] - e0[1])
        dq = (eq[0] - e0[0], eq[1] - e0[1])
        det = v1[0] * v2[1] - v1[1] * v2[0]
        if abs(det) < 1e-9:
            return m.group(0)
        a = (dq[0] * v2[1] - dq[1] * v2[0]) / det
        b = (v1[0] * dq[1] - v1[1] * dq[0]) / det
        ia, ib = round((a - _LOW) / _STEP), round((b - _LOW) / _STEP)
        if not (0 <= ia < _GRID and 0 <= ib < _GRID):
            return m.group(0)
        if abs(a - (_LOW + ia * _STEP)) > _TOLERANCE or abs(b - (_LOW + ib * _STEP)) > _TOLERANCE:
            return m.group(0)
        entry = self.runs.get(ia + ib * _GRID)
        if entry is None:
            return m.group(0)
        p0, p1, p2 = entry.corners
        side = p1[0] - p0[0]
        # user space -> this stream's space: X = ma u + mc v + me, Y = mb u + md v + mf
        ma, mb = v1[0] / side, v1[1] / side
        mc, md = v2[0] / (p2[1] - p0[1]), v2[1] / (p2[1] - p0[1])
        scale = max(math.hypot(*entry.linear[:2]), math.hypot(*entry.linear[2:]))
        if any(abs(u - w) > 1e-3 * scale for u, w in zip((ma, mb, mc, md), entry.linear)):
            # A marker drawn under a different transform than Cairo's own: not one of ours after all,
            # or Cairo wrote it in a way this code does not understand. Refuse rather than guess.
            raise RuntimeError("PDF text marker found under an unexpected transform")
        me = e0[0] - (ma * p0[0] + mc * p0[1])
        mf = e0[1] - (mb * p0[0] + md * p0[1])
        font = entry.font
        if font.ref is None:
            font.resource = f"/FunText{len(self._used)}"
            font.ref = self._writer._add_object(DictionaryObject())
            self._used.append(font)
        if font not in fonts:
            fonts.append(font)
        return self._glyph_ops(entry, font, (ma, mb, mc, md, me, mf)).encode("ascii")

    @staticmethod
    def _glyph_ops(entry: PdfTextRun, font: _Font, m: tuple) -> str:
        """The run as text in clip mode, its glyphs in reading order, each at its own place.

        What a glyph copies as comes from its HarfBuzz cluster. A cluster of one glyph (a letter,
        or a ligature such as "fi") gives that glyph the cluster's text in the ToUnicode map; if
        the map already gives that glyph another meaning, an ActualText span says what it means
        here. A cluster of several glyphs (a letter and its accent) is wrapped in an ActualText
        span with the cluster's text, because pdfium cannot be told that a glyph stands for nothing
        and reads a raised accent as a line of its own. For readers that ignore ActualText, the
        map gives each glyph its own character when each is the font's glyph for the next
        character of the cluster, and otherwise gives the first glyph the whole text."""
        ma, mb, mc, md, me, mf = m
        run = entry.run
        placed = run.placements(entry.x, entry.y)
        rtl = len(placed) > 1 and placed[0][0].cluster > placed[-1][0].cluster
        if rtl:
            placed.reverse()                          # right-to-left: write in logical order
        starts = sorted({g.cluster for g, _, _ in placed})
        ends = {c: (starts[i + 1] if i + 1 < len(starts) else len(run.text)) for i, c in enumerate(starts)}
        clusters: list[list] = []
        for item in placed:
            if clusters and clusters[-1][0][0].cluster == item[0].cluster:
                clusters[-1].append(item)
            else:
                clusters.append([item])

        def span(text: str, body: str) -> str:
            # inside a right-to-left run the run's own ActualText already says it all
            return body if rtl else f"/Span <</ActualText <FEFF{_utf16(text)}>>> BDC {body} EMC"

        out = [f"BT {font.resource} {_fmt(run.size)} Tf 7 Tr 0 Tc 0 Tw 100 Tz 0 Ts"]
        if rtl:
            # pdfium orders right-to-left words by their position, so several words come out
            # swapped; the run's own text, in reading order, settles it.
            out.append(f"/Span <</ActualText <FEFF{_utf16(run.text)}>>> BDC")
        for cluster in clusters:
            text = run.text[cluster[0][0].cluster:ends[cluster[0][0].cluster]]
            shows = []
            for g, gx, gy in cluster:
                font.used.add(g.gid)
                tm = " ".join(_fmt(v) for v in (ma, mb, -mc, -md, ma * gx + mc * gy + me, mb * gx + md * gy + mf))
                shows.append(f"{tm} Tm <{g.gid:04X}> Tj")
            gids = [g.gid for g, _, _ in cluster]
            if len(gids) == 1:
                known = font.to_unicode.setdefault(gids[0], text)
                out.append(shows[0] if known == text else span(text, shows[0]))
                continue
            if len(gids) == len(text) and all(c in font.chars.get(gid, ()) for gid, c in zip(gids, text)):
                for gid, c in zip(gids, text):        # for readers that do not use ActualText
                    font.to_unicode.setdefault(gid, c)
            else:
                font.to_unicode.setdefault(gids[0], text)
            # pdfium would read a raised accent as a line of its own, or read nothing for a glyph
            # that stands for nothing: the span gives the cluster's text in one piece
            out.append(span(text, " ".join(shows)))
        if rtl:
            out.append("EMC")
        out.append("ET")
        return "\n".join(out)

    # ---- fonts
    def _stream(self, data: bytes, **entries) -> IndirectObject:
        s = DecodedStreamObject()
        s.set_data(data)
        for k, v in entries.items():
            s[NameObject("/" + k)] = v
        return self._writer._add_object(s.flate_encode())

    def _build_font(self, font: _Font) -> None:
        """Subset *font* to the glyphs used in the document and fill in its PDF objects."""
        tt = font.tt
        order = tt.getGlyphOrder()
        upem = tt["head"].unitsPerEm
        k = 1000 / upem
        gids = sorted(font.used | {0})
        widths = {g: tt["hmtx"][order[g]][0] * k for g in gids}
        head, hhea = tt["head"], tt["hhea"]
        os2 = tt["OS/2"] if "OS/2" in tt else None
        cap = getattr(os2, "sCapHeight", 0) if os2 is not None and os2.version >= 2 else 0
        italic = tt["post"].italicAngle if "post" in tt else 0
        bbox = [head.xMin * k, head.yMin * k, head.xMax * k, head.yMax * k]

        opts = subset.Options()
        opts.retain_gids = True                      # glyph ids stay HarfBuzz's: no remapping
        opts.notdef_outline = True
        opts.layout_features = []
        opts.hinting = False
        opts.glyph_names = False
        opts.name_IDs = ["*"]
        opts.name_languages = ["*"]
        opts.drop_tables += ["GSUB", "GPOS", "GDEF", "kern", "BASE", "JSTF", "MATH", "STAT", "DSIG"]
        subsetter = subset.Subsetter(opts)
        subsetter.populate(gids=gids)
        subsetter.subset(tt)
        buf = io.BytesIO()
        tt.save(buf)
        program = buf.getvalue()

        base = NameObject(f"/{self._tag(font)}+{font.name}")
        if font.cff:
            file_entry = (NameObject("/FontFile3"), self._stream(program, Subtype=NameObject("/OpenType")))
        else:
            file_entry = (NameObject("/FontFile2"), self._stream(program, Length1=NumberObject(len(program))))
        descriptor = self._writer._add_object(DictionaryObject({
            NameObject("/Type"): NameObject("/FontDescriptor"),
            NameObject("/FontName"): base,
            NameObject("/Flags"): NumberObject(4),
            NameObject("/FontBBox"): ArrayObject(FloatObject(round(v, 3)) for v in bbox),
            NameObject("/ItalicAngle"): FloatObject(italic),
            NameObject("/Ascent"): FloatObject(round(hhea.ascent * k, 3)),
            NameObject("/Descent"): FloatObject(round(hhea.descent * k, 3)),
            NameObject("/CapHeight"): FloatObject(round((cap or hhea.ascent) * k, 3)),
            NameObject("/StemV"): NumberObject(80),
            file_entry[0]: file_entry[1],
        }))
        w = ArrayObject()
        for g in gids:
            w.append(NumberObject(g))
            w.append(ArrayObject([FloatObject(round(widths[g], 3))]))
        cid = {
            NameObject("/Type"): NameObject("/Font"),
            NameObject("/Subtype"): NameObject("/CIDFontType0" if font.cff else "/CIDFontType2"),
            NameObject("/BaseFont"): base,
            NameObject("/CIDSystemInfo"): DictionaryObject({
                NameObject("/Registry"): TextStringObject("Adobe"),
                NameObject("/Ordering"): TextStringObject("Identity"),
                NameObject("/Supplement"): NumberObject(0),
            }),
            NameObject("/FontDescriptor"): descriptor,
            NameObject("/W"): w,
        }
        if not font.cff:
            cid[NameObject("/CIDToGIDMap")] = NameObject("/Identity")
        descendant = self._writer._add_object(DictionaryObject(cid))
        type0 = font.ref.get_object()
        type0.update({
            NameObject("/Type"): NameObject("/Font"),
            NameObject("/Subtype"): NameObject("/Type0"),
            NameObject("/BaseFont"): base,
            NameObject("/Encoding"): NameObject("/Identity-H"),
            NameObject("/DescendantFonts"): ArrayObject([descendant]),
            NameObject("/ToUnicode"): self._stream(_cmap(font.to_unicode)),
        })

    def _tag(self, font: _Font) -> str:
        """A six-capital-letter subset tag, different for each font in the document."""
        n = self._used.index(font)
        return "FUN" + "".join(chr(65 + (n // 26 ** i) % 26) for i in reversed(range(3)))


def _utf16(text: str) -> str:
    return text.encode("utf-16-be").hex().upper()


def _cmap(to_unicode: dict[int, str]) -> bytes:
    """A ToUnicode CMap: each glyph id to the characters it stands for."""
    lines = [
        "/CIDInit /ProcSet findresource begin 12 dict begin begincmap",
        "/CIDSystemInfo << /Registry (Adobe) /Ordering (UCS) /Supplement 0 >> def",
        "/CMapName /Adobe-Identity-UCS def /CMapType 2 def",
        "1 begincodespacerange <0000> <FFFF> endcodespacerange",
    ]
    items = sorted(to_unicode.items())
    for i in range(0, len(items), 100):
        chunk = items[i:i + 100]
        lines.append(f"{len(chunk)} beginbfchar")
        for gid, text in chunk:
            lines.append(f"<{gid:04X}> <{_utf16(text)}>")
        lines.append("endbfchar")
    lines += ["endcmap CMapName currentdict /CMap defineresource pop end end"]
    return "\n".join(lines).encode("ascii")
