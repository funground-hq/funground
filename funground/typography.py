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

import bisect
import io
import os
import re
import unicodedata
from collections import OrderedDict
from collections.abc import Callable
from dataclasses import dataclass, replace
from numbers import Real

import uharfbuzz as hb
from fontTools.pens.basePen import BasePen
from fontTools.ttLib import TTFont

from . import ir, web_fonts
from .color import Color
from .geometry import Path

FONT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")
DEFAULT_FONT = os.path.join(FONT_DIR, "DejaVuSans.ttf")

# The browser (S-211, D-114): the bundled fonts are not in the browser wheel. The host installs a fetcher,
# `fetcher(file name) -> bytes`, and a bundled font is fetched and written the first time funground opens it.
# On a computer no fetcher is installed and the fonts are the files of the package, so nothing here runs.
_font_fetcher: Callable[[str], bytes] | None = None


def set_font_fetcher(fetcher: Callable[[str], bytes] | None) -> None:
    """Install (or, with None, remove) the function that supplies a bundled font that is missing from disk."""
    global _font_fetcher
    _font_fetcher = fetcher


def _ensure_bundled(path: str) -> None:
    """Make sure a bundled font file exists before it is read: fetch it when it is missing and a fetcher is installed."""
    if _font_fetcher is None or os.path.exists(path):
        return
    folder = os.path.abspath(FONT_DIR)
    if os.path.dirname(os.path.abspath(path)) != folder:
        return
    data = _font_fetcher(os.path.basename(path))
    os.makedirs(folder, exist_ok=True)
    with open(path, "wb") as fh:
        fh.write(data)

# Shaped texts kept per font (`FontResource._shape_one`): the glyphs of a text do not depend on the size,
# so a text whose size changes every frame is shaped once. Room for a page of words, and little memory.
SHAPE_CACHE_SIZE = 2048

# T12 (D-022 = A): the built-in family is four real bundled files, one per style.
STYLE_FILES = {
    "normal": "DejaVuSans.ttf",
    "bold": "DejaVuSans-Bold.ttf",
    "italic": "DejaVuSans-Oblique.ttf",
    "bold_italic": "DejaVuSans-BoldOblique.ttf",
}
TEXT_STYLES = tuple(STYLE_FILES)
STYLE_MEANINGS = {      # each style and what it looks like (D-092); same words as STYLE_FILES
    "normal": "Upright letters of the usual weight. The default.",
    "bold": "Thicker, heavier letters, for emphasis and headlines.",
    "italic": "Letters slanted to the right (the built-in font's oblique).",
    "bold_italic": "Bold and slanted.",
}

# T23 (S-160): a place where a word may break. It is never drawn and has no width, except where a line
# breaks at it: there the line ends with a hyphen.
SOFT_HYPHEN = "\u00ad"


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
    cluster: int = 0                      # S-094: HarfBuzz cluster (index into the run's text), for PDF text


class FontResource:
    """One loaded font: HarfBuzz font + fontTools glyph set + outline cache."""

    def __init__(self, path: str = DEFAULT_FONT, face: int = 0, defaults: tuple = ()) -> None:
        _ensure_bundled(path)             # every bundled font is opened here (the browser fetches it on first use)
        self.path = path
        self.face = face                  # S-119: which font of a .ttc/.otc collection (0 for a plain file)
        self.defaults = tuple(defaults)   # S-230: variation settings ((tag, value) pairs) a sketch's own settings override
        self._tt = TTFont(path, fontNumber=face)
        unpacked = None
        if self._tt.flavor == "woff":     # S-230: HarfBuzz cannot read a compressed WOFF; give it the unpacked font
            self._tt.flavor = None
            buffer = io.BytesIO()
            self._tt.save(buffer)
            self._tt.close()
            unpacked = buffer.getvalue()
            self._tt = TTFont(io.BytesIO(unpacked))
        self.units_per_em: int = self._tt["head"].unitsPerEm
        self.ascent: int = self._tt["hhea"].ascent
        self.descent: int = self._tt["hhea"].descent
        self._order = self._tt.getGlyphOrder()
        self._glyph_set = self._tt.getGlyphSet()
        if unpacked is None:
            with open(path, "rb") as fh:
                unpacked = fh.read()
        self._face = hb.Face(unpacked, face)
        self._hb = hb.Font(self._face)
        self._hb.scale = (self.units_per_em, self.units_per_em)
        # S-090: a variable font's axes (tag -> (min, max)); empty for a static font.
        self.axes: dict[str, tuple[float, float]] = (
            {a.axisTag: (a.minValue, a.maxValue) for a in self._tt["fvar"].axes} if "fvar" in self._tt else {}
        )
        self._outlines: dict[tuple, Path] = {}
        self._shaped: OrderedDict[tuple, tuple] = OrderedDict()  # (text, features, location) -> glyphs; least recently used first
        self._located: dict[tuple, tuple] = {}      # location -> (hb font, glyph set), built once each
        self._cmap = self._tt.getBestCmap()
        # T18: a symbol or emoji font never supplies spaces, punctuation or plain letters; set for the
        # bundled ones, worked out from the cmap for any other (see `symbolic`).
        self._symbolic: bool | None = None

    @property
    def family(self) -> str:
        return self._tt["name"].getDebugName(1) or os.path.basename(self.path)

    @property
    def style_name(self) -> str:
        """The style name from the `name` table ("Regular", "Bold", "Oblique", ...)."""
        return self._tt["name"].getDebugName(2) or ""

    def axis_ranges(self) -> dict[str, tuple[float, float, float]]:
        """Variable axes as tag -> (minimum, default, maximum); {} for a static font (T17)."""
        if "fvar" not in self._tt:
            return {}
        return {a.axisTag: (a.minValue, a.defaultValue, a.maxValue) for a in self._tt["fvar"].axes}

    def feature_tags(self) -> list[str]:
        """Sorted, de-duplicated OpenType feature tags from GSUB and GPOS (T17)."""
        tags: set[str] = set()
        for name in ("GSUB", "GPOS"):
            if name in self._tt:
                feature_list = self._tt[name].table.FeatureList
                if feature_list is not None:
                    tags.update(r.FeatureTag for r in feature_list.FeatureRecord)
        return sorted(tags)

    def has_text(self, text: str) -> bool:
        """True when the cmap has a glyph for every character of *text* (T17). A space is checked
        like any letter. A new line is skipped: `f.text` turns it into a new line and never draws it.
        Other control characters (tab, ...) are checked, and most fonts have no glyph for them."""
        cmap = self._cmap
        return all(ch == chr(10) or ord(ch) in cmap for ch in text)

    @property
    def symbolic(self) -> bool:
        """True for a font of symbols or emoji: it has no letters, so it never supplies spaces or punctuation (T18)."""
        if self._symbolic is None:
            self._symbolic = not any(unicodedata.category(chr(cp))[0] == "L" for cp in self._cmap)
        return self._symbolic

    def location(self, variations: tuple = ()) -> tuple:
        """The variation settings this font can use: only its own axes, sorted (S-090, T13).
        An axis the font lacks is ignored, so a static font always gives (). A font loaded with a default
        (`load_font(..., weight=700)` of a variable font, S-230) starts from it; each setting in *variations*
        replaces the default of its axis."""
        own = tuple((tag, float(v)) for tag, v in variations if tag in self.axes)
        if not self.defaults:
            return own
        merged = {tag: float(v) for tag, v in self.defaults if tag in self.axes}
        merged.update(own)
        return tuple(sorted(merged.items()))

    def _at(self, location: tuple):
        """(HarfBuzz font, glyph set) at *location*; the plain ones for ()."""
        if not location:
            return self._hb, self._glyph_set
        pair = self._located.get(location)
        if pair is None:
            font = hb.Font(self._face)                  # a copy: the shared font is never changed
            font.scale = (self.units_per_em, self.units_per_em)
            font.set_variations(dict(location))
            pair = self._located[location] = (font, self._tt.getGlyphSet(location=dict(location)))
        return pair

    def outline(self, gid: int, location: tuple = ()) -> Path:
        """Glyph outline in font units, y-up; cached — built once per glyph, never per frame.
        *location* is a `location()` result: the outline at that variation."""
        key = (location, gid)
        p = self._outlines.get(key)
        if p is None:
            glyph_set = self._at(location)[1]
            pen = _PathPen(glyph_set)
            glyph_set[self._order[gid]].draw(pen)
            p = self._outlines[key] = pen.path
        return p

    def shape(self, text: str, size: float, tracking: float = 0.0, features: tuple = (),
              variations: tuple = (), fallback: tuple | None = None,
              word_spacing: float = 0.0) -> "TextRun | ShapedLine":
        """Shape *text*. *tracking* (pixels, after every glyph), *features* ((tag, bool) pairs) and
        *variations* ((tag, number) pairs) are the T13 settings. *word_spacing* (T22, pixels) is added
        after every space, which is how a justified line is stretched. Soft hyphens (T23) are left out of
        the text: they have no glyph and no width.

        *fallback* is the T18 setting: None (the default here) shapes with this font alone. A tuple
        (the keys of the learner's fallback fonts, () for none) lets other fonts supply the characters
        this font lacks. When this font has every character and the text has no emoji, the result is
        the plain `TextRun`, exactly as without fallback; otherwise a `ShapedLine` of several runs."""
        text = text.replace(SOFT_HYPHEN, "")
        if fallback is None or (self.has_text(text) and not has_emoji(text)):
            return self._shape_one(text, size, tracking, features, variations, word_spacing)
        items = _itemise(text, self, fallback)
        if len(items) == 1 and items[0][0] is self:
            return self._shape_one(text, size, tracking, features, variations, word_spacing)
        runs = tuple(font._shape_one(text[a:b], size, tracking, features, variations, word_spacing)
                     for font, a, b in items)
        return ShapedLine(self, text, size, runs, tuple(a for _, a, _ in items))

    def _shape_one(self, text: str, size: float, tracking: float = 0.0, features: tuple = (),
                   variations: tuple = (), word_spacing: float = 0.0) -> "TextRun":
        """Shape *text* with this font alone."""
        location = self.location(variations)
        if not text:                                  # HarfBuzz gives no glyph list for an empty text
            return TextRun(self, text, size, (), float(tracking), location, float(word_spacing))
        return TextRun(self, text, size, self._glyphs(text, features, location), float(tracking), location,
                       float(word_spacing))

    def _glyphs(self, text: str, features: tuple, location: tuple) -> tuple[Glyph, ...]:
        """The shaped glyphs of *text*, in font units. They do not depend on the size, so they are kept
        (least recently used dropped first, `SHAPE_CACHE_SIZE`) and a text that grows is shaped once (S-171)."""
        key = (text, features, location)
        cache = self._shaped
        glyphs = cache.get(key)
        if glyphs is None:
            buf = hb.Buffer()
            buf.add_str(text)
            buf.guess_segment_properties()
            hb.shape(self._at(location)[0], buf, {"kern": True, "liga": True, **dict(features)})
            glyphs = tuple(
                Glyph(i.codepoint, p.x_advance, p.x_offset, p.y_offset, i.cluster)
                for i, p in zip(buf.glyph_infos, buf.glyph_positions)
            )
            cache[key] = glyphs
            if len(cache) > SHAPE_CACHE_SIZE:
                cache.popitem(last=False)
        else:
            cache.move_to_end(key)
        return glyphs


def _placed(outline: Path, scale: float, x: float, y: float) -> Path:
    """A glyph *outline* (font units, y up) at *scale*, flipped to y down, with its origin at (x, y).
    One pass, whatever the size: a text size never needs an outline of its own (S-171). The floats are
    those of scaling and then moving the outline."""
    flip = -scale
    return Path(tuple((seg[0], *((px * scale + x, py * flip + y) for px, py in seg[1:])) for seg in outline.segments))


@dataclass(frozen=True, slots=True)
class TextRun:
    font: FontResource
    text: str
    size: float
    glyphs: tuple[Glyph, ...]
    tracking: float = 0.0                 # S-090: pixels added after every glyph (T13)
    location: tuple = ()                  # S-090: the variation the outlines are drawn at
    word_spacing: float = 0.0             # S-159: pixels added after every space (T22)

    @property
    def scale(self) -> float:
        return self.size / self.font.units_per_em

    def at_size(self, size: float) -> "TextRun":
        """The same shaped run at another *size* (S-171): the glyphs are in font units, so only the size changes."""
        return self if size == self.size else replace(self, size=size)

    @property
    def advance(self) -> float:
        total = sum(g.x_advance for g in self.glyphs) * self.scale + self.tracking * len(self.glyphs)
        return total + self.word_spacing * self.spaces

    @property
    def spaces(self) -> int:
        """How many glyphs are spaces, the ones `word_spacing` widens (0 when it is not set)."""
        if not self.word_spacing:
            return 0
        return sum(1 for g in self.glyphs if self.text[g.cluster] == " ")

    def _step(self, g: Glyph, s: float) -> float:
        """How far the pen moves after glyph *g* at scale *s*: its advance, the tracking, and the word
        spacing when it is a space."""
        step = g.x_advance * s + self.tracking
        if self.word_spacing and self.text[g.cluster] == " ":
            step += self.word_spacing
        return step

    def placements(self, x: float, y: float) -> list[tuple[Glyph, float, float]]:
        """Each glyph with its origin on the baseline, anchored top-left at (x, y): exactly where
        `outline_ops` puts its outline (S-094, real text in PDFs)."""
        s = self.scale
        baseline = y + self.font.ascent * s
        pen_x = x
        out = []
        for g in self.glyphs:
            out.append((g, pen_x + g.x_offset * s, baseline - g.y_offset * s))
            pen_x += self._step(g, s)
        return out

    def cluster_spans(self) -> list[tuple[int, int, float]]:
        """The letters of the run as they are drawn, left to right (S-161, text on a path): for each HarfBuzz
        cluster, (start, end, advance), the part of `text` it stands for and how far the pen moves over it.
        A ligature is one cluster; so is a letter with its accent."""
        s = self.scale
        starts = sorted({g.cluster for g in self.glyphs})
        ends = {c: (starts[i + 1] if i + 1 < len(starts) else len(self.text)) for i, c in enumerate(starts)}
        spans: list[list] = []
        for g in self.glyphs:
            if spans and spans[-1][0] == g.cluster:
                spans[-1][2] += self._step(g, s)
            else:
                spans.append([g.cluster, ends[g.cluster], self._step(g, s)])
        return [(start, end, advance) for start, end, advance in spans]

    def outline_ops(self, x: float, y: float, color: Color) -> list[ir.FillPath]:
        """Materialise as FillPath ops anchored top-left at (x, y)."""
        s = self.scale
        baseline = y + self.font.ascent * s
        pen_x = x
        ops: list[ir.FillPath] = []
        for g in self.glyphs:
            outline = self.font.outline(g.gid, self.location)
            if not outline.is_empty:
                ops.append(ir.FillPath(_placed(outline, s, pen_x + g.x_offset * s, baseline - g.y_offset * s), color))
            pen_x += self._step(g, s)
        return ops


@dataclass(frozen=True, slots=True)
class ShapedLine:
    """A line shaped with more than one font (T18): one `TextRun` per stretch of text, each in the font
    that has its characters. Every run sits on the baseline of `font`, the primary (current) font, so
    the line is as tall as the primary font says. It offers what `TextRun` offers to its callers."""

    font: FontResource                    # the primary font: its ascent sets the baseline
    text: str
    size: float
    runs: tuple[TextRun, ...]
    spans: tuple[int, ...]                # where each run's text starts in `text`

    @property
    def scale(self) -> float:
        return self.size / self.font.units_per_em

    def at_size(self, size: float) -> "ShapedLine":
        """The same line at another *size* (S-171), every run in it too."""
        if size == self.size:
            return self
        return replace(self, size=size, runs=tuple(r.at_size(size) for r in self.runs))

    @property
    def advance(self) -> float:
        return sum(r.advance for r in self.runs)

    @property
    def glyphs(self) -> tuple[Glyph, ...]:
        return tuple(g for r in self.runs for g in r.glyphs)

    def parts(self, x: float, y: float) -> list[tuple[TextRun, float, float]]:
        """Each run with the top-left (x, y) at which to draw it so that all share one baseline."""
        baseline = y + self.font.ascent * self.scale
        out = []
        pen_x = x
        for run in self.runs:
            top = y if run.font is self.font else baseline - run.font.ascent * run.scale
            out.append((run, pen_x, top))
            pen_x += run.advance
        return out

    def placements(self, x: float, y: float) -> list[tuple[Glyph, float, float]]:
        """Every glyph of every run with its origin on the shared baseline (as `TextRun.placements`)."""
        return [item for run, rx, ry in self.parts(x, y) for item in run.placements(rx, ry)]

    def cluster_spans(self) -> list[tuple[int, int, float]]:
        """(start, end, advance) of each letter of every run, left to right, in the line's own text (as `TextRun.cluster_spans`)."""
        return [(start + a, end + a, advance)
                for run, a in zip(self.runs, self.spans) for start, end, advance in run.cluster_spans()]

    def outline_ops(self, x: float, y: float, color: Color) -> list[ir.FillPath]:
        """Materialise as FillPath ops anchored top-left at (x, y)."""
        return [op for run, rx, ry in self.parts(x, y) for op in run.outline_ops(rx, ry, color)]


# ---- font fallback (S-102, contract T18)
BUNDLED_FALLBACKS = ("NotoEmoji-Regular.ttf", "NotoSansSymbols2-Regular.ttf", "NotoSansDevanagari-Regular.ttf")
_EMOJI_FONT = BUNDLED_FALLBACKS[0]
_SYMBOL_FONTS = frozenset(BUNDLED_FALLBACKS[:2])
_bundled_cache: dict[str, FontResource] = {}

# Characters with the Emoji_Presentation property (Unicode 16): drawn as emoji unless a text
# variation selector asks otherwise. 80 ranges, from the Unicode data files.
_EMOJI_RANGES = (
    (8986, 8987), (9193, 9196), (9200, 9200), (9203, 9203), (9725, 9726), (9748, 9749), (9800, 9811),
    (9855, 9855), (9875, 9875), (9889, 9889), (9898, 9899), (9917, 9918), (9924, 9925), (9934, 9934),
    (9940, 9940), (9962, 9962), (9970, 9971), (9973, 9973), (9978, 9978), (9981, 9981), (9989, 9989),
    (9994, 9995), (10024, 10024), (10060, 10060), (10062, 10062), (10067, 10069), (10071, 10071),
    (10133, 10135), (10160, 10160), (10175, 10175), (11035, 11036), (11088, 11088), (11093, 11093),
    (126980, 126980), (127183, 127183), (127374, 127374), (127377, 127386), (127462, 127487),
    (127489, 127489), (127514, 127514), (127535, 127535), (127538, 127542), (127544, 127546),
    (127568, 127569), (127744, 127776), (127789, 127797), (127799, 127868), (127870, 127891),
    (127904, 127946), (127951, 127955), (127968, 127984), (127988, 127988), (127992, 128062),
    (128064, 128064), (128066, 128252), (128255, 128317), (128331, 128334), (128336, 128359),
    (128378, 128378), (128405, 128406), (128420, 128420), (128507, 128591), (128640, 128709),
    (128716, 128716), (128720, 128722), (128725, 128729), (128732, 128735), (128747, 128748),
    (128756, 128764), (128992, 129003), (129008, 129008), (129292, 129338), (129340, 129349),
    (129351, 129535), (129648, 129660), (129664, 129734), (129736, 129736), (129740, 129757),
    (129759, 129771), (129775, 129786),
)
_EMOJI_STARTS = tuple(a for a, _ in _EMOJI_RANGES)
_FIRST_EMOJI = chr(_EMOJI_RANGES[0][0])         # nothing below this is an emoji, so Latin text skips the check
_VS16 = "\ufe0f"

# Characters that join a cluster but are never drawn alone: they must not decide the font.
_NEUTRAL = frozenset({0x200C, 0x200D, 0x200E, 0x200F, 0x2060, *range(0xFE00, 0xFE10),
                      *range(0xE0100, 0xE01F0), *range(0xE0020, 0xE0080)})
_REGIONAL = range(0x1F1E6, 0x1F200)
_SKIN_TONES = range(0x1F3FB, 0x1F400)


def _emoji_presentation(cp: int) -> bool:
    i = bisect.bisect_right(_EMOJI_STARTS, cp) - 1
    return i >= 0 and cp <= _EMOJI_RANGES[i][1]


def has_emoji(text: str) -> bool:
    """True when *text* has an emoji cluster: a character with Emoji_Presentation, or any character
    followed by U+FE0F (T18)."""
    if max(text, default="") < _FIRST_EMOJI:
        return False
    return _VS16 in text or any(_emoji_presentation(ord(c)) for c in text)


def clusters(text: str) -> list[tuple[int, int]]:
    """Grapheme clusters of *text* as (start, end) pairs, with the standard library only: a base with its
    marks, joiners, variation selectors, tag characters and skin tones; a joiner binds the next character;
    a virama binds a following letter (a Devanagari conjunct); two regional indicators make a flag."""
    out, i, n = [], 0, len(text)
    while i < n:
        j = i + 1
        if text[i] == "\r" and j < n and text[j] == "\n":
            j += 1
        else:
            flag = ord(text[i]) in _REGIONAL
            while j < n:
                c, cp, prev = text[j], ord(text[j]), text[j - 1]
                if (unicodedata.category(c) in ("Mn", "Mc", "Me") or cp in _NEUTRAL or cp in _SKIN_TONES
                        or prev == "\u200d"
                        or unicodedata.combining(prev) == 9 and unicodedata.category(c) == "Lo"
                        or flag and cp in _REGIONAL and j == i + 1):
                    j += 1
                else:
                    break
        out.append((i, j))
        i = j
    return out


def _bundled(name: str) -> FontResource:
    """A bundled fallback font, loaded the first time it is needed."""
    resource = _bundled_cache.get(name)
    if resource is None:
        resource = _bundled_cache[name] = FontResource(os.path.join(FONT_DIR, name))
        resource._symbolic = name in _SYMBOL_FONTS or None
    return resource


def _has_all(font: FontResource, cluster: str) -> bool:
    cmap = font._cmap
    return all(ord(c) in cmap for c in cluster if ord(c) not in _NEUTRAL and c != "\n")


def _order(primary: FontResource, learner: tuple, emoji: bool):
    """The fonts to try for one cluster, in order, loading a font only when the ones before it fail.
    An emoji cluster tries the learner's fonts, then Noto Emoji, before the current font."""
    if emoji:
        for key in learner:
            yield Font(key)._resource()
        yield _bundled(_EMOJI_FONT)
        yield primary
    else:
        yield primary
        for key in learner:
            yield Font(key)._resource()
    for name in BUNDLED_FALLBACKS:
        yield _bundled(name)
    if os.path.basename(primary.path) not in STYLE_FILES.values():
        yield default_font()


_ITEMISE_CACHE: dict[tuple, tuple] = {}
_ITEMISE_CACHE_SIZE = 2048


def _itemise(text: str, primary: FontResource, learner: tuple) -> tuple:
    """Split *text* into runs (font, start, end), each cluster given to the first font that has all of it (T18).
    Spaces and punctuation stay with the run before them when its font is a text font and has them.
    Memoised: the answer depends only on the text, the primary font and the chain."""
    key = (text, primary.path, primary.face, learner)
    hit = _ITEMISE_CACHE.get(key)
    if hit is not None:
        return hit
    runs: list[list] = []
    for a, b in clusters(text):
        cluster = text[a:b]
        emoji = _VS16 in cluster or any(_emoji_presentation(ord(c)) for c in cluster)
        plain = all(unicodedata.category(c)[0] in "ZP" for c in cluster)
        font = None
        if plain and runs and not runs[-1][0].symbolic and _has_all(runs[-1][0], cluster):
            font = runs[-1][0]
        else:
            for candidate in _order(primary, learner, emoji):
                if candidate.symbolic and not emoji and (ord(cluster[0]) < 0x80 or unicodedata.category(cluster[0])[0] in "ZPC"):
                    continue                       # never a space, punctuation or plain letter from a symbol font
                if _has_all(candidate, cluster):
                    font = candidate
                    break
        if font is None:
            font = primary                         # nobody has it: the primary draws its own .notdef
        if runs and runs[-1][0] is font:
            runs[-1][2] = b
        else:
            runs.append([font, a, b])
    result = tuple((f, a, b) for f, a, b in runs)
    if len(_ITEMISE_CACHE) >= _ITEMISE_CACHE_SIZE:
        _ITEMISE_CACHE.clear()
    _ITEMISE_CACHE[key] = result
    return result


def text_size_value(size: object, who: str) -> int | float:
    """A text size checked and ready to keep (T3, S-171): any finite number above 0. A whole size is kept as
    an int, so state, caches and snapshots read as they always did; a fraction is kept as a float."""
    if isinstance(size, bool) or not isinstance(size, Real):
        raise TypeError(f"{who} needs the text size as a number of pixels, not {size!r}")
    if not 0 < size < float("inf"):
        raise ValueError(f"{who} needs a text size above 0 pixels, not {size!r}")
    return int(size) if size == int(size) else float(size)


def text_metrics(size: float, font: FontResource | None = None) -> tuple[float, float]:
    """(ascent, descent) of *font* (the default font if not given) at *size*, both positive,
    in logical pixels (T8)."""
    font = font or default_font()
    scale = size / font.units_per_em
    return font.ascent * scale, -font.descent * scale


def text_settings(state) -> dict:
    """The T13 settings of a GraphicsState as keyword arguments for `shape`, `text_width`, `wrap_lines`."""
    return {"tracking": state.text_tracking, "features": state.text_features,
            "variations": state.font_variations, "fallback": state.text_fallback}


def soft_hyphen_cuts(word: str) -> list[int]:
    """Where *word* may break at a soft hyphen (T23): the position of each U+00AD that has letters
    on both sides, the last one first, so a caller tries the longest first part first."""
    return [i for i in reversed(range(len(word)))
            if word[i] == SOFT_HYPHEN and word[:i].replace(SOFT_HYPHEN, "") and word[i + 1:].replace(SOFT_HYPHEN, "")]


def paragraph_ends(text: str, starts: list[int]) -> list[bool]:
    """For each line of *text*, whether it is the last line of its paragraph (T22): the last line of all, or
    one that the next line follows with a new line. *starts[i]* is where line i begins in *text*. A justified
    line is stretched unless it ends its paragraph."""
    return [i + 1 == len(starts) or text[starts[i + 1] - 1] == "\n" for i in range(len(starts))]


def word_gap(line: str, width: float, size: float, font: FontResource | None = None, **settings) -> float:
    """The pixels to add after each space of *line* so that it is *width* wide (T22), by the settings
    of `text_width`. 0 when the line has no space, or is already as wide as *width*."""
    spaces = line.count(" ")
    if not spaces:
        return 0.0
    return max(0.0, (width - text_width(line, size, font, **settings)) / spaces)


def wrap_lines(text: str, width: float, size: float, font: FontResource | None = None,
               **settings) -> tuple[list[str], list[str]]:
    """Break *text* into lines no wider than *width* at *size* in *font* (contract T10, T23).

    Returns (lines, rests): rests[i] is the text from the start of line i onward, so a caller that
    shows only the first n lines can hand back rests[n] as the overflow. Lines break at spaces;
    '\\n' always breaks. A word that does not fit in the rest of the line is broken at a soft hyphen
    (U+00AD), the last one that lets the first part and a hyphen fit, and the line ends with the hyphen.
    A word with no such place that is wider than the box is broken between letters. A soft hyphen where
    no break is made stays in the line: it has no width.
    """
    font = font or default_font()
    lines: list[str] = []
    rests: list[str] = []

    def fits(s: str) -> bool:
        return text_width(s, size, font, **settings) <= width

    def emit(line: str, start: int) -> None:
        lines.append(line)
        rests.append(text[start:])

    offset = 0
    for paragraph in text.split("\n"):
        words: list[str] = []
        start: int | None = None
        for m in re.finditer(r"[^ ]+", paragraph):
            word, at = m.group(), offset + m.start()
            while not fits(" ".join(words + [word])):
                first = start if words else at
                cut = next((i for i in soft_hyphen_cuts(word) if fits(" ".join(words + [word[:i]]) + "-")), None)
                if cut is not None:                                  # a soft hyphen: break there
                    emit(" ".join(words + [word[:cut]]) + "-", first)
                    word, at = word[cut + 1:], at + cut + 1
                    words, start = [], None
                elif words:                                          # the word goes to the next line
                    emit(" ".join(words), first)
                    words, start = [], None
                elif len(word) > 1:                                  # a word wider than the box
                    cut = len(word) - 1
                    while cut > 1 and not fits(word[:cut]):
                        cut -= 1
                    emit(word[:cut], at)
                    word, at = word[cut:], at + cut
                else:
                    break
            words.append(word)
            start = at if start is None else start
        emit(" ".join(words), offset if start is None else start)
        offset += len(paragraph) + 1
    return lines, rests


def text_width(text: str, size: float, font: FontResource | None = None, **settings) -> float:
    """Advance width of *text* in logical pixels at *size* in *font* (S-037, T11): what
    `f.text` moves the pen by. Uses the default font when *font* is not given."""
    if not text:
        return 0.0
    return (font or default_font()).shape(text, size, **settings).advance


# ---- font registry (S-054, contract T11/T12): FontResource objects, cached by key. Built-in
# keys are the bundled file names; a loaded file's key is its own file name, disambiguated with
# "~2", "~3", ... when another loaded file already has that name.
_registry: dict[str, FontResource] = {}
_path_to_key: dict[str, str] = {}


def file_font_mark() -> int:
    """How many font files have been loaded so far. Pass it to `forget_file_fonts()` later (S-157)."""
    return len(_path_to_key)


def forget_file_fonts(mark: int) -> None:
    """Forget the fonts that `load_font()` loaded after *mark* (from `file_font_mark()`), so the next
    run reads those files again and gives their names afresh. The bundled fonts stay (S-157, D-083)."""
    for cache_key in list(_path_to_key)[mark:]:
        _registry.pop(_path_to_key.pop(cache_key), None)
    web_fonts.forget()


class Font:
    """A font that you can pass to f.text_font(), or ask questions about.

    You get one from f.load_font(path) (a font file), f.system_font(name) (a font installed on this
    computer) or f.current_font() (the font in use now). The font's name, which funground uses to find it,
    is font.name: the file name, or the file name with ~2, ~3 and so on when two files share a name. A
    font from a collection (.ttc) file has # and the face number after the file name.

    Two fonts are equal when they have the same name.

    Example:
        face = f.load_font("MyFont.ttf")   # your own file
        f.text_font(face)
        print(face.family(), face.style())

    See also: load_font, system_font, current_font, text_font
    """

    __slots__ = ("name",)

    def __init__(self, name: str) -> None:
        self.name = name              # the registry key: the file name, or "name~2" etc.

    def __repr__(self) -> str:
        return f"Font({self.name!r})"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Font) and self.name == other.name

    def __hash__(self) -> int:
        return hash(self.name)

    def _resource(self) -> FontResource:
        resource = _registry.get(self.name)
        if resource is None and self.name in STYLE_FILES.values():
            resource = _builtin(self.name)                    # a built-in style not used yet
        if resource is None:
            raise RuntimeError(f"no font loaded for key {self.name!r} (was it loaded in this process?)")
        return resource

    def family(self) -> str:
        """The family name of the font, as written in the font file.

        Returns:
            the name, such as "DejaVu Sans".

        Example:
            print(f.current_font().family())

        See also: style, variations, features
        """
        return self._resource().family

    def style(self) -> str:
        """The style name of the font, as written in the font file.

        Returns:
            the name, such as "Bold" or "Book".

        Example:
            print(f.current_font().style())

        See also: family
        """
        return self._resource().style_name

    def variations(self) -> dict[str, tuple[float, float, float]]:
        """The axes of a variable font and how far each one can go.

        An ordinary font has none. Use f.font_variations() to set an axis.

        Returns:
            a dictionary from the axis tag, such as "wght", to (minimum, default, maximum). It is {} for a font that is not variable.

        Example:
            for tag, (low, normal, high) in f.current_font().variations().items():
                print(tag, low, normal, high)

        See also: features, family
        """
        return self._resource().axis_ranges()

    def features(self) -> list[str]:
        """The OpenType features that the font has.

        Use f.text_features() to turn one on or off.

        Returns:
            a sorted list of four-letter tags, such as ["kern", "liga"].

        Example:
            print(f.current_font().features())

        See also: variations, contains
        """
        return self._resource().feature_tags()

    def contains(self, text: str) -> bool:
        """Whether the font has a shape for every character of some text.

        Spaces count. A new line is ignored.

        Arguments:
            text: the text to check.

        Returns:
            True when every character has a shape in the font, otherwise False.

        Example:
            if not f.current_font().contains("hello"):
                print("some letters are missing")

        See also: features, family
        """
        return self._resource().has_text(text)


def _builtin(filename: str) -> FontResource:
    resource = _registry.get(filename)
    if resource is None:
        resource = _registry[filename] = FontResource(os.path.join(FONT_DIR, filename))
    return resource


def default_font() -> FontResource:
    """The built-in family's normal style (module named typography so it never shadows api.text)."""
    return _builtin(STYLE_FILES["normal"])


# S-132 Play: every file found by _resolve_path in this process (images, SVGs, sounds, fonts), for f.keep()'s
# record. {absolute path: what} in the order first read.
files_read: dict[str, str] = {}


def _note_read(resolved: str, what: str) -> str:
    files_read.setdefault(os.path.abspath(resolved), what)
    return resolved


def _resolve_path(path: str, base_dir: str | None, who: str, what: str) -> str:
    """Contract T11/P4: a relative path is found next to the sketch file first, then the cwd."""
    if os.path.isabs(path):
        if os.path.exists(path):
            return _note_read(os.path.normpath(path), what)
        raise FileNotFoundError(f"{who}: no {what} file found at {path!r}")
    tried = []
    if base_dir is not None:
        candidate = os.path.join(base_dir, path)
        tried.append(candidate)
        if os.path.exists(candidate):
            return _note_read(os.path.normpath(candidate), what)
    candidate = os.path.join(os.getcwd(), path)
    tried.append(candidate)
    if os.path.exists(candidate):
        return _note_read(os.path.normpath(candidate), what)
    raise FileNotFoundError(
        f"{who}: no {what} file found at '{tried[0]}'" +
        (f" or '{tried[1]}'" if len(tried) > 1 else "")
    )


def _resolve_font_path(path: str, base_dir: str | None) -> str:
    return _resolve_path(path, base_dir, "f.load_font()", "font")


def _face_count(path: str) -> int:
    """How many fonts a file holds: the number in a .ttc/.otc collection, otherwise 1."""
    try:
        with open(path, "rb") as fh:
            head = fh.read(12)
    except OSError:
        return 1
    if head[:4] == b"ttcf" and len(head) == 12:
        return max(1, int.from_bytes(head[8:12], "big"))
    return 1


def _face_index(resolved: str, face, who: str = "f.load_font()") -> int:
    """The number of the face *face* names in the font file *resolved* (S-119, contract T11): a
    whole number, or a style name ("Bold") or a full name ("Nirmala UI Bold"), ignoring capitals.
    A face the file does not have raises `ValueError` that lists the faces it has."""
    count = _face_count(resolved)
    if isinstance(face, bool) or not isinstance(face, (int, str)):
        raise ValueError(f"{who}: face must be a whole number or a style name like 'Bold', not {face!r}")
    infos = _font_names(resolved)
    if isinstance(face, int):
        if not 0 <= face < count:
            raise ValueError(f"{who}: face {face} is not in this file, which has {count} "
                             f"{'face' if count == 1 else 'faces'} (numbered from 0)")
        return face
    wanted = face.strip().lower()
    if infos is not None:
        for i, (families, style, fulls) in enumerate(infos):
            if wanted and (wanted == style.lower() or wanted in fulls):
                return i
    listed = ", ".join(repr(info[1] or "?") for info in infos) if infos else "none readable"
    raise ValueError(f"{who}: no face called {face!r} in this file (its styles: {listed})")


def _refuse_woff2(path: str, name: str) -> None:
    """A WOFF2 file needs the Brotli package, which funground does not use: say so in one plain line (S-230)."""
    try:
        with open(path, "rb") as fh:
            magic = fh.read(4)
    except OSError:
        return
    if magic == b"wOF2":
        raise ValueError(f"f.load_font(): {name!r} is a WOFF2 file, which funground cannot read. "
                         "Use the .ttf version of the font; most font sites offer it.")


def check_font_file(path: str, shown: str, name: str) -> None:
    """Raise ValueError unless the file at *path* is a font funground can read (WOFF2 has its own line). *shown* is
    how the font is named in the error (its address), *name* its file name. Used on a download before it is kept."""
    _refuse_woff2(path, name)
    try:
        resource = FontResource(path)
    except Exception as exc:
        raise ValueError(f"f.load_font(): {shown!r} is not a font funground can read ({exc})") from exc
    resource._tt.close()                       # so the file can be renamed at once (Windows)


def _check_weight(weight, italic) -> None:
    if weight is not None and (isinstance(weight, bool) or not isinstance(weight, Real)):
        raise TypeError(f"f.load_font(): weight is a number such as 400 or 700, not {weight!r}")
    if weight is not None and not 1 <= weight <= 1000:
        raise ValueError(f"f.load_font(): weight is a number from 1 to 1000 (400 is normal, 700 is bold), not {weight!r}")
    if not isinstance(italic, bool):
        raise TypeError(f"f.load_font(): italic is True or False, not {italic!r}")


def load_font(path: str, base_dir: str | None = None, face: int | str = 0, *, provider: str | None = None,
              weight: float | None = None, italic: bool = False) -> Font:
    """Load a TrueType/OpenType font file and return a `Font` (contract T11).

    A relative *path* is looked for next to the sketch file (*base_dir*) first, then in the
    current folder. A missing file raises `FileNotFoundError` naming both places looked; a file
    that is not a font raises `ValueError`. Loading the same file again returns the same key;
    a different file with the same name gets "name~2", then "name~3".

    A .ttc or .otc file holds several fonts (S-119): *face* is the number of the one to use
    (0 is the first) or its style or full name, like "Bold" or "Nirmala UI Bold". Each face of a
    collection is its own font, with its own key ("name.ttc", then "name.ttc#1", ...).

    A *path* that starts with http:// or https:// is an address (S-230): the file is downloaded once and kept in
    `fonts/` beside the sketch (see `web_fonts`). With a *provider*, *path* is a family name and *weight* and
    *italic* choose the file. A WOFF font is unpacked; a WOFF2 font is refused.
    """
    if provider is None:
        if weight is not None or italic:
            raise TypeError("f.load_font(): weight and italic choose a file from a family that a provider finds, "
                            "so give provider= too, such as provider=f.CONSTANTS.PROVIDERS.GOOGLE_FONTS.")
        defaults: tuple = ()
    else:
        web_fonts.check_provider(provider)
        _check_weight(weight, italic)
        if not isinstance(path, str) or not path.strip():
            raise ValueError("f.load_font(): with a provider, give the family name, such as \"Lora\"")
        path, wght = web_fonts.google_font(path.strip(), weight, italic, base_dir)
        defaults = (("wght", wght),) if wght is not None else ()
    if web_fonts.is_address(path):
        address = web_fonts.raw_address(path)
        file_name = web_fonts.file_name_of(address)
        resolved = _note_read(web_fonts.font_path(
            path, base_dir, lambda tmp: check_font_file(tmp, address, file_name)), "font")
    else:
        resolved = _resolve_font_path(path, base_dir)
        _refuse_woff2(resolved, os.path.basename(resolved))
    number = _face_index(resolved, face)
    cache_key = (os.path.normcase(resolved), number, defaults)
    key = _path_to_key.get(cache_key)
    if key is None:
        try:
            resource = FontResource(resolved, number, defaults)
        except Exception as exc:
            raise ValueError(f"f.load_font(): {path!r} is not a font funground can read ({exc})") from exc
        name = os.path.basename(resolved) + (f"#{number}" if number else "")
        if defaults:                                   # the default setting is part of the name: Lora[wght].ttf@wght=700
            name += "@" + ",".join(f"{tag}={value:g}" for tag, value in defaults)
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


# ---- fonts installed on this computer (S-102, contract T18)
_system_names: dict[tuple, list | None] = {}       # (path, mtime) -> one (families, style, full names) per face, or None; read once each


def _system_font_dirs() -> list[str]:
    """The folders where this computer keeps its fonts (Windows, macOS and Linux), those that exist."""
    home = os.path.expanduser("~")
    candidates = [
        os.path.join(os.environ.get("WINDIR", ""), "Fonts") if os.environ.get("WINDIR") else "",
        os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "Windows", "Fonts") if os.environ.get("LOCALAPPDATA") else "",
        "/System/Library/Fonts", "/Library/Fonts", os.path.join(home, "Library", "Fonts"),
        "/usr/share/fonts", os.path.join(home, ".local", "share", "fonts"), os.path.join(home, ".fonts"),
    ]
    return [d for d in candidates if d and os.path.isdir(d)]


def _font_names(path: str):
    """For each face in a font file: (lower-case family names, style name, lower-case full names), read from
    its `name` table and cached; None if the file is unreadable. A plain font has one face; a collection
    (S-119) has one for each of its fonts. The full names are the `name` table's full name and every
    "family style" pair, so "Nirmala UI Bold" finds the Bold face."""
    try:
        key = (path, os.path.getmtime(path))
    except OSError:
        return None
    if key not in _system_names:
        infos = []
        try:
            for number in range(_face_count(path)):
                tt = TTFont(path, lazy=True, fontNumber=number)
                try:
                    table = tt["name"]
                    got = {i: table.getDebugName(i) for i in (1, 2, 4, 16, 17)}
                finally:
                    tt.close()
                families = {got[i].lower() for i in (1, 16) if got[i]}
                style = got[17] or got[2] or ""
                fulls = {got[4].lower()} if got[4] else set()
                for fam, sty in ((got[1], got[2]), (got[16], got[17])):
                    if fam and sty:
                        fulls.add(f"{fam} {sty}".lower())
                infos.append((families, style, fulls))
            _system_names[key] = infos if any(info[0] for info in infos) else None
        except Exception:
            _system_names[key] = None
    return _system_names[key]


_PLAIN_STYLES = ("regular", "book", "roman", "normal")


def system_font(name: str) -> Font:
    """The font installed on this computer whose family name is *name*, ignoring capitals (contract T18).
    *name* may also end in a style or be a full name ("Nirmala UI Bold"). When several faces share the
    family, the Regular one is used. Raises `FileNotFoundError` naming *name* when there is none. .ttf, .otf,
    .ttc and .otc files are read (a collection's faces each count); the font is loaded like `load_font`."""
    if not isinstance(name, str):
        raise TypeError(f"f.system_font() takes a family name, not {type(name).__name__}")
    wanted = name.strip().lower()
    found = []
    for folder in _system_font_dirs():
        for root, dirs, files in os.walk(folder):
            dirs.sort()
            for file in sorted(files):
                if not file.lower().endswith((".ttf", ".otf", ".ttc", ".otc")):
                    continue
                path = os.path.join(root, file)
                infos = _font_names(path)
                for number, (families, style, fulls) in enumerate(infos or ()):
                    if wanted in fulls:
                        found.append((0, path, number))                     # the exact style asked for
                    elif wanted in families:
                        found.append((0 if style.lower() in _PLAIN_STYLES else 1, path, number))
    if not found:
        raise FileNotFoundError(f"f.system_font(): no installed font with the family name {name!r}")
    _, path, number = min(found)
    return load_font(path, face=number)
