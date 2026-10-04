"""Test-only helper: build tiny fonts with fontTools (nothing is downloaded).

``make_variable_font``: one axis, ``wght`` from 100 to 900 (default 100), and one letter, "A": a box
that is thin and narrow at 100 and wide at 900, so both the outline and the advance change with the
axis. ``make_static_font`` (S-094): the letters A to E and a space, each a different simple shape,
as TrueType or CFF outlines, with a chosen OS/2 ``fsType`` (embedding permission).
"""
from __future__ import annotations

from pathlib import Path

from fontTools.designspaceLib import AxisDescriptor, DesignSpaceDocument, SourceDescriptor
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.t2CharStringPen import T2CharStringPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.varLib import build as var_build

UPEM = 1000
# weight -> (box right edge, advance)
MASTERS = {100: (300, 400), 900: (700, 800)}


def _master(weight: int, path: Path) -> None:
    right, advance = MASTERS[weight]
    fb = FontBuilder(UPEM, isTTF=True)
    fb.setupGlyphOrder([".notdef", "A"])
    fb.setupCharacterMap({ord("A"): "A"})
    glyphs = {}
    for name in (".notdef", "A"):
        pen = TTGlyphPen(None)
        pen.moveTo((100, 0))
        pen.lineTo((100, 700))
        pen.lineTo((right, 700))
        pen.lineTo((right, 0))
        pen.closePath()
        glyphs[name] = pen.glyph()
    fb.setupGlyf(glyphs)
    fb.setupHorizontalMetrics({".notdef": (advance, 100), "A": (advance, 100)})
    fb.setupHorizontalHeader(ascent=800, descent=-200)
    fb.setupNameTable({"familyName": "TestVar", "styleName": f"W{weight}"})
    fb.setupOS2()
    fb.setupPost()
    fb.save(str(path))


def make_variable_font(folder: Path) -> str:
    """Write ``TestVar.ttf`` into *folder* and return its path."""
    folder = Path(folder)
    doc = DesignSpaceDocument()
    axis = AxisDescriptor()
    axis.name, axis.tag, axis.minimum, axis.default, axis.maximum = "Weight", "wght", 100, 100, 900
    doc.addAxis(axis)
    for weight in MASTERS:
        path = folder / f"master{weight}.ttf"
        _master(weight, path)
        source = SourceDescriptor()
        source.path = str(path)
        source.location = {"Weight": weight}
        doc.addSource(source)
    variable, _, _ = var_build(doc)
    out = folder / "TestVar.ttf"
    variable.save(str(out))
    return str(out)


# letter -> polygon (font units, y up); each letter a different shape so a misplaced one shows
_SHAPES = {
    "A": [(50, 0), (300, 700), (550, 0)],
    "B": [(80, 0), (80, 700), (500, 700), (500, 0)],
    "C": [(60, 350), (300, 700), (540, 350), (300, 0)],
    "D": [(80, 0), (80, 700), (520, 350)],
    "E": [(80, 0), (80, 700), (520, 700), (520, 560), (220, 560), (220, 140), (520, 140), (520, 0)],
}


def make_static_font(folder: Path, name: str = "TestStatic", cff: bool = False, fs_type: int = 0,
                     style: str = "Regular", advance: int = 600, filename: str | None = None) -> str:
    """Write ``<name>.ttf`` (or ``.otf`` with CFF outlines) into *folder* and return its path.
    *style* is the style name, *advance* the width of every letter, *filename* the file's own name."""
    order = [".notdef", "space", *_SHAPES]
    fb = FontBuilder(UPEM, isTTF=not cff)
    fb.setupGlyphOrder(order)
    fb.setupCharacterMap({32: "space", **{ord(c): c for c in _SHAPES}})
    shapes = {".notdef": [(50, 0), (50, 700), (450, 700), (450, 0)], "space": None, **_SHAPES}
    if cff:
        charstrings = {}
        for glyph, points in shapes.items():
            pen = T2CharStringPen(advance, None)
            if points:
                pen.moveTo(points[0])
                for pt in points[1:]:
                    pen.lineTo(pt)
                pen.closePath()
            charstrings[glyph] = pen.getCharString()
        fb.setupCFF(name, {"FullName": name}, charstrings, {})
    else:
        glyphs = {}
        for glyph, points in shapes.items():
            pen = TTGlyphPen(None)
            if points:
                pen.moveTo(points[0])
                for pt in points[1:]:
                    pen.lineTo(pt)
                pen.closePath()
            glyphs[glyph] = pen.glyph()
        fb.setupGlyf(glyphs)
    fb.setupHorizontalMetrics({g: (advance, 50) for g in order})
    fb.setupHorizontalHeader(ascent=800, descent=-200)
    fb.setupNameTable({"familyName": name, "styleName": style})
    fb.setupOS2(fsType=fs_type, sTypoAscender=800, sTypoDescender=-200, usWinAscent=800, usWinDescent=200)
    fb.setupPost()
    out = Path(folder) / (filename or f"{name}.{'otf' if cff else 'ttf'}")
    fb.save(str(out))
    return str(out)


def make_collection(folder: Path, name: str = "TestColl", styles: tuple = ("Regular", "Bold"),
                    extension: str = "ttc") -> str:
    """Write ``<name>.ttc`` (S-119): one face for each of *styles*, all in the family *name*. The first
    face has letters 600 units wide and each later one 100 wider, so the faces are told apart by width."""
    from fontTools.ttLib import TTFont
    from fontTools.ttLib.ttCollection import TTCollection

    folder = Path(folder)
    fonts = []
    for i, style in enumerate(styles):
        path = make_static_font(folder, name, style=style, advance=600 + 100 * i, filename=f"{name}-{style}.part")
        fonts.append(TTFont(path))
    collection = TTCollection()
    collection.fonts = fonts
    out = folder / f"{name}.{extension}"
    collection.save(str(out))
    return str(out)
