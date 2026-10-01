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

# T12 (D-022 = A): the built-in family is four real bundled files, one per style.
STYLE_FILES = {
    "normal": "DejaVuSans.ttf",
    "bold": "DejaVuSans-Bold.ttf",
    "italic": "DejaVuSans-Oblique.ttf",
    "bold_italic": "DejaVuSans-BoldOblique.ttf",
}
TEXT_STYLES = tuple(STYLE_FILES)


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


def text_metrics(size: float, font: FontResource | None = None) -> tuple[float, float]:
    """(ascent, descent) of *font* (the default font if not given) at *size*, both positive,
    in logical pixels (T8)."""
    font = font or default_font()
    scale = size / font.units_per_em
    return font.ascent * scale, -font.descent * scale


def wrap_lines(text: str, width: float, size: float, font: FontResource | None = None) -> tuple[list[str], list[str]]:
    """Break *text* into lines no wider than *width* at *size* in *font* (contract T10).

    Returns (lines, rests): rests[i] is the text from the start of line i onward, so a caller that
    shows only the first n lines can hand back rests[n] as the overflow. Lines break at spaces;
    a word wider than the box is broken between letters; '\\n' always breaks.
    """
    font = font or default_font()
    lines: list[str] = []
    rests: list[str] = []

    def fits(s: str) -> bool:
        return text_width(s, size, font) <= width

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


def text_width(text: str, size: float, font: FontResource | None = None) -> float:
    """Advance width of *text* in logical pixels at *size* in *font* (S-037, T11): what
    `f.text` moves the pen by. Uses the default font when *font* is not given."""
    if not text:
        return 0.0
    return (font or default_font()).shape(text, size).advance


# ---- font registry (S-054, contract T11/T12): FontResource objects, cached by key. Built-in
# keys are the bundled file names; a loaded file's key is its own file name, disambiguated with
# "~2", "~3", ... when another loaded file already has that name.
_registry: dict[str, FontResource] = {}
_path_to_key: dict[str, str] = {}


class Font:
    """A font loaded with `f.load_font()`; pass it to `f.text_font()` (contract T11)."""

    __slots__ = ("name",)

    def __init__(self, name: str) -> None:
        self.name = name              # the registry key: the file name, or "name~2" etc.

    def __repr__(self) -> str:
        return f"Font({self.name!r})"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Font) and self.name == other.name

    def __hash__(self) -> int:
        return hash(self.name)


def _builtin(filename: str) -> FontResource:
    resource = _registry.get(filename)
    if resource is None:
        resource = _registry[filename] = FontResource(os.path.join(FONT_DIR, filename))
    return resource


def default_font() -> FontResource:
    """The built-in family's normal style (module named typography so it never shadows api.text)."""
    return _builtin(STYLE_FILES["normal"])


def _resolve_path(path: str, base_dir: str | None, who: str, what: str) -> str:
    """Contract T11/P4: a relative path is found next to the sketch file first, then the cwd."""
    if os.path.isabs(path):
        if os.path.exists(path):
            return os.path.normpath(path)
        raise FileNotFoundError(f"{who}: no {what} file found at {path!r}")
    tried = []
    if base_dir is not None:
        candidate = os.path.join(base_dir, path)
        tried.append(candidate)
        if os.path.exists(candidate):
            return os.path.normpath(candidate)
    candidate = os.path.join(os.getcwd(), path)
    tried.append(candidate)
    if os.path.exists(candidate):
        return os.path.normpath(candidate)
    raise FileNotFoundError(
        f"{who}: no {what} file found at '{tried[0]}'" +
        (f" or '{tried[1]}'" if len(tried) > 1 else "")
    )


def _resolve_font_path(path: str, base_dir: str | None) -> str:
    return _resolve_path(path, base_dir, "f.load_font()", "font")


def load_font(path: str, base_dir: str | None = None) -> Font:
    """Load a TrueType/OpenType font file and return a `Font` (contract T11).

    A relative *path* is looked for next to the sketch file (*base_dir*) first, then in the
    current folder. A missing file raises `FileNotFoundError` naming both places looked; a file
    that is not a font raises `ValueError`. Loading the same file again returns the same key;
    a different file with the same name gets "name~2", then "name~3".
    """
    resolved = _resolve_font_path(path, base_dir)
    cache_key = os.path.normcase(resolved)
    key = _path_to_key.get(cache_key)
    if key is None:
        try:
            resource = FontResource(resolved)
        except Exception as exc:
            raise ValueError(f"f.load_font(): {path!r} is not a font funground can read ({exc})") from exc
        name = os.path.basename(resolved)
        key, n = name, 2
        while key in _registry:
            key = f"{name}~{n}"
            n += 1
        _registry[key] = resource
        _path_to_key[cache_key] = key
    return Font(key)


def effective_font(state) -> FontResource:
    """The font a Text op should shape with, from a GraphicsState (contract T11/T12):
    the built-in family for the current text_style when no font was loaded, otherwise the
    loaded font (text_style is then ignored, as p5 does)."""
    if state.font is None:
        return _builtin(STYLE_FILES[state.text_style])
    resource = _registry.get(state.font)
    if resource is None:
        raise RuntimeError(f"no font loaded for key {state.font!r} (was it loaded in this process?)")
    return resource
