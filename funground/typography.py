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
import os
import re
import unicodedata
from collections import OrderedDict
from dataclasses import dataclass

import uharfbuzz as hb
from fontTools.pens.basePen import BasePen
from fontTools.ttLib import TTFont

from . import ir
from .color import Color
from .geometry import Path, Transform

FONT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")
DEFAULT_FONT = os.path.join(FONT_DIR, "DejaVuSans.ttf")

# Scaled glyph outlines kept per font (`FontResource.scaled_outline`): room for a few sizes of a full
# alphabet, plus accents, and about a megabyte or two of tuples at most.
SCALED_OUTLINE_CACHE_SIZE = 2048

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
    cluster: int = 0                      # S-094: HarfBuzz cluster (index into the run's text), for PDF text


def _translated(path: Path, dx: float, dy: float) -> Path:
    """*path* moved by (dx, dy): the points of `path.transformed(Transform.translation(dx, dy))`, with no
    transform built. Kept here, not on `Path`, so the public API does not grow (S-147)."""
    return Path(tuple((seg[0], *((x + dx, y + dy) for x, y in seg[1:])) for seg in path.segments))


class FontResource:
    """One loaded font: HarfBuzz font + fontTools glyph set + outline cache."""

    def __init__(self, path: str = DEFAULT_FONT, face: int = 0) -> None:
        self.path = path
        self.face = face                  # S-119: which font of a .ttc/.otc collection (0 for a plain file)
        self._tt = TTFont(path, fontNumber=face)
        self.units_per_em: int = self._tt["head"].unitsPerEm
        self.ascent: int = self._tt["hhea"].ascent
        self.descent: int = self._tt["hhea"].descent
        self._order = self._tt.getGlyphOrder()
        self._glyph_set = self._tt.getGlyphSet()
        with open(path, "rb") as fh:
            self._face = hb.Face(fh.read(), face)
        self._hb = hb.Font(self._face)
        self._hb.scale = (self.units_per_em, self.units_per_em)
        # S-090: a variable font's axes (tag -> (min, max)); empty for a static font.
        self.axes: dict[str, tuple[float, float]] = (
            {a.axisTag: (a.minValue, a.maxValue) for a in self._tt["fvar"].axes} if "fvar" in self._tt else {}
        )
        self._outlines: dict[tuple, Path] = {}
        self._scaled: OrderedDict[tuple, Path] = OrderedDict()   # least recently used first
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
        An axis the font lacks is ignored, so a static font always gives ()."""
        return tuple((tag, float(v)) for tag, v in variations if tag in self.axes)

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

    def scaled_outline(self, gid: int, location: tuple, size: float) -> Path:
        """Glyph outline at *size* pixels, y-down, with its origin at (0, 0): ready to be moved to a pen
        position with `_translated`. Cached, so a glyph is scaled once per size and not once per frame.
        A Path cannot be changed, so every caller can share the cached one.

        The cache holds at most `SCALED_OUTLINE_CACHE_SIZE` outlines, least recently used dropped first:
        a sketch that changes its text size every frame would otherwise add outlines without end."""
        key = (gid, location, size)
        cache = self._scaled
        path = cache.get(key)
        if path is None:
            s = size / self.units_per_em
            path = self.outline(gid, location).transformed(Transform.scaling(s, -s))
            cache[key] = path
            if len(cache) > SCALED_OUTLINE_CACHE_SIZE:
                cache.popitem(last=False)
        else:
            cache.move_to_end(key)
        return path

    def shape(self, text: str, size: float, tracking: float = 0.0, features: tuple = (),
              variations: tuple = (), fallback: tuple | None = None) -> "TextRun | ShapedLine":
        """Shape *text*. *tracking* (pixels, after every glyph), *features* ((tag, bool) pairs) and
        *variations* ((tag, number) pairs) are the T13 settings.

        *fallback* is the T18 setting: None (the default here) shapes with this font alone. A tuple
        (the keys of the learner's fallback fonts, () for none) lets other fonts supply the characters
        this font lacks. When this font has every character and the text has no emoji, the result is
        the plain `TextRun`, exactly as without fallback; otherwise a `ShapedLine` of several runs."""
        if fallback is None or (self.has_text(text) and not has_emoji(text)):
            return self._shape_one(text, size, tracking, features, variations)
        items = _itemise(text, self, fallback)
        if len(items) == 1 and items[0][0] is self:
            return self._shape_one(text, size, tracking, features, variations)
        runs = tuple(font._shape_one(text[a:b], size, tracking, features, variations) for font, a, b in items)
        return ShapedLine(self, text, size, runs, tuple(a for _, a, _ in items))

    def _shape_one(self, text: str, size: float, tracking: float = 0.0, features: tuple = (),
                   variations: tuple = ()) -> "TextRun":
        """Shape *text* with this font alone."""
        location = self.location(variations)
        buf = hb.Buffer()
        buf.add_str(text)
        buf.guess_segment_properties()
        hb.shape(self._at(location)[0], buf, {"kern": True, "liga": True, **dict(features)})
        glyphs = tuple(
            Glyph(i.codepoint, p.x_advance, p.x_offset, p.y_offset, i.cluster)
            for i, p in zip(buf.glyph_infos, buf.glyph_positions)
        )
        return TextRun(self, text, size, glyphs, float(tracking), location)


@dataclass(frozen=True, slots=True)
class TextRun:
    font: FontResource
    text: str
    size: float
    glyphs: tuple[Glyph, ...]
    tracking: float = 0.0                 # S-090: pixels added after every glyph (T13)
    location: tuple = ()                  # S-090: the variation the outlines are drawn at

    @property
    def scale(self) -> float:
        return self.size / self.font.units_per_em

    @property
    def advance(self) -> float:
        return sum(g.x_advance for g in self.glyphs) * self.scale + self.tracking * len(self.glyphs)

    def placements(self, x: float, y: float) -> list[tuple[Glyph, float, float]]:
        """Each glyph with its origin on the baseline, anchored top-left at (x, y): exactly where
        `outline_ops` puts its outline (S-094, real text in PDFs)."""
        s = self.scale
        baseline = y + self.font.ascent * s
        pen_x = x
        out = []
        for g in self.glyphs:
            out.append((g, pen_x + g.x_offset * s, baseline - g.y_offset * s))
            pen_x += g.x_advance * s + self.tracking
        return out

    def outline_ops(self, x: float, y: float, color: Color) -> list[ir.FillPath]:
        """Materialise as FillPath ops anchored top-left at (x, y)."""
        s = self.scale
        baseline = y + self.font.ascent * s
        pen_x = x
        ops: list[ir.FillPath] = []
        for g in self.glyphs:
            outline = self.font.scaled_outline(g.gid, self.location, self.size)
            if not outline.is_empty:
                ops.append(ir.FillPath(_translated(outline, pen_x + g.x_offset * s, baseline - g.y_offset * s), color))
            pen_x += g.x_advance * s + self.tracking
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


def wrap_lines(text: str, width: float, size: float, font: FontResource | None = None,
               **settings) -> tuple[list[str], list[str]]:
    """Break *text* into lines no wider than *width* at *size* in *font* (contract T10).

    Returns (lines, rests): rests[i] is the text from the start of line i onward, so a caller that
    shows only the first n lines can hand back rests[n] as the overflow. Lines break at spaces;
    a word wider than the box is broken between letters; '\\n' always breaks.
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


def load_font(path: str, base_dir: str | None = None, face: int | str = 0) -> Font:
    """Load a TrueType/OpenType font file and return a `Font` (contract T11).

    A relative *path* is looked for next to the sketch file (*base_dir*) first, then in the
    current folder. A missing file raises `FileNotFoundError` naming both places looked; a file
    that is not a font raises `ValueError`. Loading the same file again returns the same key;
    a different file with the same name gets "name~2", then "name~3".

    A .ttc or .otc file holds several fonts (S-119): *face* is the number of the one to use
    (0 is the first) or its style or full name, like "Bold" or "Nirmala UI Bold". Each face of a
    collection is its own font, with its own key ("name.ttc", then "name.ttc#1", ...).
    """
    resolved = _resolve_font_path(path, base_dir)
    number = _face_index(resolved, face)
    cache_key = (os.path.normcase(resolved), number)
    key = _path_to_key.get(cache_key)
    if key is None:
        try:
            resource = FontResource(resolved, number)
        except Exception as exc:
            raise ValueError(f"f.load_font(): {path!r} is not a font funground can read ({exc})") from exc
        name = os.path.basename(resolved) + (f"#{number}" if number else "")
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
