"""Text subsystem v1 — the outline route (D-006, D-009, Spike 06).

    bundled TTF -> uharfbuzz (glyph ids, advances, offsets)
                -> fontTools glyph outlines, cached per glyph id
                -> FillPath ops in the IR

Deterministic on every platform and renderer. `TextRun` keeps the semantic
text and shaped glyphs so a later exporter can embed the font instead of
emitting outlines (S-032). Anchor is the top-left of the em box (contract T1):
baseline = y + ascent * scale.
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass

import uharfbuzz as hb
from fontTools.pens.basePen import BasePen
from fontTools.ttLib import TTFont

from . import ir
from .color import Color
from .geometry import Path, Transform

FONT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")
DEFAULT_FONT = os.path.join(FONT_DIR, "DejaVuSans.ttf")


class _PathPen(BasePen):
    def __init__(self, glyph_set) -> None:
        super().__init__(glyph_set)
        self.path = Path()

    def _moveTo(self, p): self.path = self.path.move_to(*p)
    def _lineTo(self, p): self.path = self.path.line_to(*p)
    def _curveToOne(self, c1, c2, p): self.path = self.path.cubic_to(*c1, *c2, *p)
    def _qCurveToOne(self, q, p): self.path = self.path.quad_to(*q, *p)
    def _closePath(self): self.path = self.path.close()
    def _endPath(self): self.path = self.path.close()


@dataclass(frozen=True, slots=True)
class Glyph:
    gid: int
    x_advance: float
    x_offset: float
    y_offset: float


class FontResource:
    """One loaded font: HarfBuzz font + fontTools glyph set + outline cache."""

    def __init__(self, path: str = DEFAULT_FONT) -> None:
        self.path = path
        self._tt = TTFont(path)
        self.units_per_em: int = self._tt["head"].unitsPerEm
        self.ascent: int = self._tt["hhea"].ascent
        self.descent: int = self._tt["hhea"].descent
        self._order = self._tt.getGlyphOrder()
        self._glyph_set = self._tt.getGlyphSet()
        with open(path, "rb") as fh:
            self._hb = hb.Font(hb.Face(fh.read()))
        self._hb.scale = (self.units_per_em, self.units_per_em)
        self._outlines: dict[int, Path] = {}

    @property
    def family(self) -> str:
        return self._tt["name"].getDebugName(1) or os.path.basename(self.path)

    def outline(self, gid: int) -> Path:
        """Glyph outline in font units, y-up; cached — built once per glyph, never per frame."""
        p = self._outlines.get(gid)
        if p is None:
            pen = _PathPen(self._glyph_set)
            self._glyph_set[self._order[gid]].draw(pen)
            p = self._outlines[gid] = pen.path
        return p

    def shape(self, text: str, size: float) -> "TextRun":
        buf = hb.Buffer()
        buf.add_str(text)
        buf.guess_segment_properties()
        hb.shape(self._hb, buf, {"kern": True, "liga": True})
        glyphs = tuple(
            Glyph(i.codepoint, p.x_advance, p.x_offset, p.y_offset)
            for i, p in zip(buf.glyph_infos, buf.glyph_positions)
        )
        return TextRun(self, text, size, glyphs)


@dataclass(frozen=True, slots=True)
class TextRun:
    font: FontResource
    text: str
    size: float
    glyphs: tuple[Glyph, ...]

    @property
    def scale(self) -> float:
        return self.size / self.font.units_per_em

    @property
    def advance(self) -> float:
        return sum(g.x_advance for g in self.glyphs) * self.scale

    def outline_ops(self, x: float, y: float, color: Color) -> list[ir.FillPath]:
        """Materialise as FillPath ops anchored top-left at (x, y)."""
        s = self.scale
        baseline = y + self.font.ascent * s
        pen_x = x
        ops: list[ir.FillPath] = []
        for g in self.glyphs:
            outline = self.font.outline(g.gid)
            if not outline.is_empty:
                t = Transform.scaling(s, -s).then(
                    Transform.translation(pen_x + g.x_offset * s, baseline - g.y_offset * s)
                )
                ops.append(ir.FillPath(outline.transformed(t), color))
            pen_x += g.x_advance * s
        return ops


def text_metrics(size: float) -> tuple[float, float]:
    """(ascent, descent) of the default font at *size*, both positive, in logical pixels (T8)."""
    font = default_font()
    scale = size / font.units_per_em
    return font.ascent * scale, -font.descent * scale


def wrap_lines(text: str, width: float, size: float) -> tuple[list[str], list[str]]:
    """Break *text* into lines no wider than *width* at *size* (contract T10).

    Returns (lines, rests): rests[i] is the text from the start of line i onward, so a caller that
    shows only the first n lines can hand back rests[n] as the overflow. Lines break at spaces;
    a word wider than the box is broken between letters; '\\n' always breaks.
    """
    lines: list[str] = []
    rests: list[str] = []

    def fits(s: str) -> bool:
        return text_width(s, size) <= width

    def emit(line: str, start: int) -> None:
        lines.append(line)
        rests.append(text[start:])

    offset = 0
    for paragraph in text.split("\n"):
        words: list[str] = []
        start: int | None = None
        for m in re.finditer(r"[^ ]+", paragraph):
            word, at = m.group(), offset + m.start()
            if fits(" ".join(words + [word])):
                words.append(word)
                start = at if start is None else start
                continue
            if words:
                emit(" ".join(words), start)
            while len(word) > 1 and not fits(word):        # a word wider than the box
                cut = len(word) - 1
                while cut > 1 and not fits(word[:cut]):
                    cut -= 1
                emit(word[:cut], at)
                word, at = word[cut:], at + cut
            words, start = [word], at
        emit(" ".join(words), offset if start is None else start)
        offset += len(paragraph) + 1
    return lines, rests


def text_width(text: str, size: float) -> float:
    """Advance width of *text* in logical pixels at *size* (S-037): what `p.text` moves the pen by."""
    if not text:
        return 0.0
    return default_font().shape(text, size).advance


_default: FontResource | None = None


def default_font() -> FontResource:
    global _default  # module is named typography so it never shadows api.text
    if _default is None:
        _default = FontResource(DEFAULT_FONT)
    return _default
