"""Test-only helper: build a tiny variable font with fontTools (nothing is downloaded).

The font has one axis, ``wght`` from 100 to 900 (default 100), and one letter, "A": a box that is
thin and narrow at 100 and wide at 900, so both the outline and the advance change with the axis.
"""
from __future__ import annotations

from pathlib import Path

from fontTools.designspaceLib import AxisDescriptor, DesignSpaceDocument, SourceDescriptor
from fontTools.fontBuilder import FontBuilder
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
