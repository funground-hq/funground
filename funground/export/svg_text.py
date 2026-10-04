"""Live, editable text in SVG files (story S-097, contract T19, decision D-059 = A).

funground draws text as glyph outlines (T2). In an SVG that would leave text nobody can edit, so the
SVG exporters write each line of text as a real ``<text>`` element instead, naming its font by family
(``font-family``, with ``font-weight`` and ``font-style``). Illustrator, Inkscape and browsers then
draw the text in the font installed on the computer, and it stays editable there. A browser also
gets a subset of each font, embedded as a CSS ``@font-face``, so it shows the right font even when it
is not installed. See ``docs/design/Text_In_Files_Note.md``.

1. **While drawing.** The Cairo renderer is given an `SvgTextCollector`. For each line of text (one
   ``ir.Text`` op, fallback runs of T18 included) it asks for a *marker*: the four-cornered shape of
   `pdf_text` (same grid, same transform read-back). The renderer pushes a group, clips to the
   marker, paints the line's colour or gradient, and paints the group back, exactly as for a PDF.
   Cairo writes the paint as a ``<rect>`` (or ``<path>``) inside a ``<g clip-path="url(#marker)">``.
2. **After ``surface.finish()``** (and after the layer step, S-096). `SvgTextCollector.finish` finds
   each marker clip path, and replaces the painted element in the group that uses it by the line's
   ``<text>``: same fill (colour or gradient) and opacity, placed at the line's start on its baseline,
   with the line's transform read back from the marker. The group keeps every clip, opacity and layer
   Cairo gave it. A gradient is given a ``gradientTransform`` that puts it where Cairo painted it.
   Then every ``<use>`` in the document body that leads to such a text is replaced by what it draws:
   Inkscape shows text inside a ``<use>`` as a clone that cannot be edited, and browsers do not let
   you select it.

Each ``<text>`` has one ``x`` and one ``y``, and its string as plain content (fallback runs as
``<tspan>`` elements with their own font). Per-glyph positions would match funground's spacing
exactly, but they make the text hard to edit in Illustrator; the program that opens the file shapes
the text itself, so spacing can differ slightly. Text drawn while erasing (F15) and text shadows stay
shapes (the renderer draws them from outlines), and a file with no text is left exactly as Cairo and
the layer step wrote it.
"""
from __future__ import annotations

import base64
import io
import os
import re
import unicodedata
import xml.etree.ElementTree as ET
from dataclasses import dataclass

from fontTools import subset
from fontTools.ttLib import TTFont

from .layers import _SVG_MARKER, SVG_NS, XLINK_NS, _svg_prefixes
from .pdf_text import MAX_RUNS, RESTRICTED_LICENCE, _fmt, _quiet_fonttools, marker_corners, marker_map, marker_number

XML_NS = "http://www.w3.org/XML/1998/namespace"
_URL = re.compile(r"url\(\s*#([^)\s]+)\s*\)")
_INVALID_XML = re.compile("[\x00-\x08\x0b\x0c\x0e-\x1f￾￿\ud800-\udfff]")
_MATRIX = re.compile(r"^\s*matrix\(\s*" + r"[\s,]*".join([r"(-?[\d.]+(?:[eE][-+]?\d+)?)"] * 6) + r"\s*\)\s*$")
# Where a <use> draws nothing editable: definitions, and what only feeds masks, clips and filters.
_HIDDEN = {f"{{{SVG_NS}}}{tag}" for tag in ("defs", "clipPath", "mask", "filter", "pattern", "marker", "symbol")}
_PAINTED = {f"{{{SVG_NS}}}{tag}" for tag in ("rect", "path")}
_GRADIENTS = {f"{{{SVG_NS}}}{tag}" for tag in ("linearGradient", "radialGradient")}
_PAINT_ATTRS = ("fill", "fill-opacity", "opacity")


@dataclass(frozen=True)
class _Face:
    """What the file says about one font: its family and style, and whether it may be embedded."""

    family: str                      # the family name from the font's name table
    weight: str                      # CSS font-weight: "normal", "bold" or a number
    style: str                       # CSS font-style: "normal", "italic" or "oblique"
    generic: str                     # the generic family to fall back on
    embeddable: bool                 # fsType allows embedding
    cff: bool                        # CFF outlines (OpenType) rather than TrueType

    def font_family(self) -> str:
        return f"{_css_string(self.family)}, {self.generic}" if self.family else self.generic


@dataclass
class _Line:
    """One line drawn as a marker: what is needed to write it back as text."""

    run: object                      # typography.TextRun or ShapedLine
    x: float
    y: float
    corners: tuple                   # P0, P1, P2 in user space
    linear: tuple                    # the device matrix's (xx, yx, xy, yy) when it was drawn
    features: tuple                  # the T13 OpenType feature settings, (tag, on) pairs


def _css_string(name: str) -> str:
    return "'" + name.replace("\\", "\\\\").replace("'", "\\'") + "'"


def _face(path: str, number: int = 0) -> _Face:
    tt = TTFont(path, lazy=True, fontNumber=number)
    try:
        family = ""
        if "name" in tt:
            family = tt["name"].getDebugName(16) or tt["name"].getDebugName(1) or ""
        family = _INVALID_XML.sub("", family).strip()
        os2 = tt["OS/2"] if "OS/2" in tt else None
        weight_class = getattr(os2, "usWeightClass", 400) if os2 is not None else 400
        weight = {400: "normal", 700: "bold"}.get(weight_class, str(weight_class))
        selection = getattr(os2, "fsSelection", 0) if os2 is not None else 0
        subfamily = (tt["name"].getDebugName(2) or "") if "name" in tt else ""
        if selection & (1 << 9) or "oblique" in subfamily.lower():
            style = "oblique"
        elif selection & 1 or "italic" in subfamily.lower():
            style = "italic"
        else:
            style = "normal"
        generic = "sans-serif"
        if "post" in tt and tt["post"].isFixedPitch:
            generic = "monospace"
        elif os2 is not None and getattr(os2, "panose", None) is not None:
            panose = os2.panose
            if panose.bFamilyType == 2 and 2 <= panose.bSerifStyle <= 10:
                generic = "serif"
        embeddable = not (os2 is not None and os2.fsType & RESTRICTED_LICENCE)
        cff = "glyf" not in tt and ("CFF " in tt or "CFF2" in tt)
        return _Face(family, weight, style, generic, embeddable, cff)
    finally:
        tt.close()


def _right_to_left(run) -> bool:
    """True for a single-font run whose first strong character is right to left (Hebrew, Arabic): the
    direction HarfBuzz guesses for it. The text stays in logical (reading) order in the file. A line
    in several fonts (T18) is laid out run after run from left to right, so it stays left to right."""
    if getattr(run, "runs", None) is not None:
        return False
    for ch in run.text:
        kind = unicodedata.bidirectional(ch)
        if kind == "L":
            return False
        if kind in ("R", "AL"):
            return True
    return False


def _matrix_of(value: str | None) -> tuple:
    """A ``matrix(a, b, c, d, e, f)`` attribute as a tuple; identity when absent. Anything else is a
    form this code does not understand: refuse rather than guess."""
    if value is None or not value.strip():
        return (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)
    m = _MATRIX.match(value)
    if m is None:
        raise RuntimeError(f"unexpected transform {value!r} next to a text marker")
    return tuple(float(v) for v in m.groups())


def _multiply(m: tuple, n: tuple) -> tuple:
    """The affine map m after n (SVG order: matrix m applied to the result of n)."""
    a, b, c, d, e, f = m
    a2, b2, c2, d2, e2, f2 = n
    return (a * a2 + c * b2, b * a2 + d * b2, a * c2 + c * d2, b * c2 + d * d2,
            a * e2 + c * f2 + e, b * e2 + d * f2 + f)


def _invert(m: tuple) -> tuple:
    a, b, c, d, e, f = m
    det = a * d - b * c
    if abs(det) < 1e-12:
        raise RuntimeError("a text transform cannot be inverted")
    return (d / det, -b / det, -c / det, a / det, (c * f - d * e) / det, (b * e - a * f) / det)


def _matrix_text(m: tuple) -> str:
    return "matrix(" + ", ".join(_fmt(v) for v in m) + ")"


class SvgTextCollector:
    """Collects lines of text while an SVG is drawn, then writes them into the file as live text."""

    def __init__(self) -> None:
        self.runs: dict[int, _Line] = {}
        self._faces: dict[tuple, _Face] = {}
        self.embedded: dict[str, int] = {}          # font path -> bytes of its embedded subset (after finish)

    # ---- while drawing (called by the Cairo renderer)
    def add(self, run, x: float, y: float, matrix: tuple, style) -> list[tuple[float, float]] | None:
        """Record the line *run* drawn at (x, y) under the device *matrix* (Cairo's xx, yx, xy, yy, x0,
        y0) with the graphics state *style*. Return the marker's corners in user space, or None to
        draw the outlines (nothing to write, too many lines, or a transform that cannot be read back)."""
        if not run.glyphs or not run.text.strip() or len(self.runs) >= MAX_RUNS:
            return None
        if _INVALID_XML.search(run.text):
            return None                               # an XML file cannot hold these characters
        number = len(self.runs)
        marker = marker_corners(run, x, y, matrix, number)
        if marker is None:
            return None
        corners, shape = marker
        features = tuple(getattr(style, "text_features", ()) or ())
        self.runs[number] = _Line(run, x, y, corners, tuple(matrix[:4]), features)
        return shape

    # ---- after surface.finish()
    def finish(self, path: str) -> None:
        """Replace every recorded line's painted marker in the SVG at *path* by its live ``<text>``."""
        if not self.runs:
            return
        tree = ET.parse(path)
        root = tree.getroot()
        parent = {child: el for el in root.iter() for child in el}
        clip_tag, path_tag, g_tag = f"{{{SVG_NS}}}clipPath", f"{{{SVG_NS}}}path", f"{{{SVG_NS}}}g"

        # 1. The marker clip paths, and the line each one stands for.
        markers: dict[str, tuple[ET.Element, int, list]] = {}
        for clip in root.iter(clip_tag):
            kids = list(clip)
            if len(kids) != 1 or kids[0].tag != path_tag or kids[0].get("transform") or clip.get("transform"):
                continue
            m = _SVG_MARKER.match(kids[0].get("d", ""))
            if m is None:
                continue
            corners = [(float(m.group(i)), float(m.group(i + 1))) for i in (1, 3, 5, 7)]
            number = marker_number(*corners)
            if number is not None and number in self.runs and clip.get("id"):
                markers[clip.get("id")] = (clip, number, corners)
        if not markers:
            return

        users: dict[str, list[ET.Element]] = {}
        for el in root.iter():
            value = el.get("clip-path")
            if value is not None:
                m = _URL.fullmatch(value.strip())
                if m is not None and m.group(1) in markers:
                    users.setdefault(m.group(1), []).append(el)
        ref_count = self._ref_count(root)
        by_id = {el.get("id"): el for el in root.iter() if el.get("id") is not None}

        # 2. Each marker's group: the painted element becomes the line's text; the marker clip goes.
        texts: set[ET.Element] = set()
        used: dict[tuple, set[str]] = {}                # (font path, face) -> characters drawn in it
        for clip_id, (clip, number, (e0, e1, _, e2)) in markers.items():
            found = users.get(clip_id, [])
            if len(found) > 1:
                raise RuntimeError("a text marker came out in a form this code does not understand")
            parent[clip].remove(clip)
            if not found:                             # Cairo drew nothing there: nothing to replace
                continue
            group = found[0]
            painted = list(group)
            if group.tag != g_tag or len(painted) != 1 or painted[0].tag not in _PAINTED:
                raise RuntimeError("a text marker came out in a form this code does not understand")
            painted = painted[0]
            line = self.runs[number]
            mapped = marker_map(line.corners, line.linear, e0, e1, e2)
            # The marker's corners come back on Cairo's 1/256 grid, so the offset is good to about
            # 0.002: two decimals say all there is to say.
            transform = tuple(mapped[:4]) + tuple(round(v, 2) for v in mapped[4:])
            own = _matrix_of(painted.get("transform"))
            text = self._text_element(line, transform, used)
            for name in _PAINT_ATTRS:
                if painted.get(name) is not None:
                    text.set(name, painted.get(name))
            fill = text.get("fill", "")
            m = _URL.fullmatch(fill.strip())
            if m is not None:
                # The gradient is in the painted element's space; the text's own space is the line's.
                text.set("fill", f"url(#{self._gradient_for(m.group(1), _multiply(_invert(transform), own), root, parent, by_id, ref_count)})")
            text.tail = painted.tail
            index = list(group).index(painted)
            group.remove(painted)
            group.insert(index, text)
            parent[text] = group
            del group.attrib["clip-path"]
            if not group.attrib:                      # an empty wrapper gives way to the text
                up = parent[group]
                index = list(up).index(group)
                text.tail = group.tail
                up.remove(group)
                up.insert(index, text)
                parent[text] = up
            texts.add(text)

        # 3. The fonts, for browsers; 4. the text drawn in place, not through a <use>.
        self._embed(root, used)
        self._inline(root, texts)
        with _svg_prefixes():
            tree.write(path, encoding="UTF-8", xml_declaration=True)

    # ---- the text element
    def _face_of(self, path: str, number: int = 0) -> _Face:
        key = (os.path.normcase(os.path.abspath(path)), number)
        if key not in self._faces:
            try:
                self._faces[key] = _face(path, number)
            except Exception:
                self._faces[key] = _Face("", "normal", "normal", "sans-serif", False, False)
        return self._faces[key]

    @staticmethod
    def _font_attrs(el: ET.Element, face: _Face, base: _Face | None = None) -> None:
        el.set("font-family", face.font_family())
        if base is None or face.weight != base.weight:
            if face.weight != "normal" or base is not None:
                el.set("font-weight", face.weight)
        if base is None or face.style != base.style:
            if face.style != "normal" or base is not None:
                el.set("font-style", face.style)

    @staticmethod
    def _variations(location: tuple) -> str:
        return ", ".join(f"'{tag}' {_fmt(v)}" for tag, v in location)

    def _text_element(self, line: _Line, transform: tuple, used: dict) -> ET.Element:
        run = line.run
        base = self._face_of(run.font.path, run.font.face)
        text = ET.Element(f"{{{SVG_NS}}}text")
        if transform != (1.0, 0.0, 0.0, 1.0, 0.0, 0.0):
            text.set("transform", _matrix_text(transform))
        if _right_to_left(run):
            # HarfBuzz shaped the whole run right to left: say so, so trailing marks and numbers sit
            # where funground put them. The run then starts at its right end.
            text.set("direction", "rtl")
            text.set("x", _fmt(line.x + run.advance))
        else:
            text.set("x", _fmt(line.x))
        text.set("y", _fmt(line.y + run.font.ascent * run.scale))
        self._font_attrs(text, base)
        text.set("font-size", _fmt(run.size))
        parts = getattr(run, "runs", None) or (run,)
        tracking = parts[0].tracking
        if tracking:
            text.set("letter-spacing", _fmt(tracking))
        if line.features:
            text.set("font-feature-settings", ", ".join(f"'{tag}' {1 if on else 0}" for tag, on in line.features))
        primary_location = next((p.location for p in parts if p.font is run.font), ())
        if primary_location:
            text.set("font-variation-settings", self._variations(primary_location))
        text.set(f"{{{XML_NS}}}space", "preserve")
        last: ET.Element | None = None
        for part in parts:
            used.setdefault((part.font.path, part.font.face), set()).update(part.text)
            if part.font is run.font:
                if last is None:
                    text.text = (text.text or "") + part.text
                else:
                    last.tail = (last.tail or "") + part.text
                continue
            span = ET.SubElement(text, f"{{{SVG_NS}}}tspan")
            self._font_attrs(span, self._face_of(part.font.path, part.font.face), base)
            if part.location != primary_location:
                span.set("font-variation-settings", self._variations(part.location) or "normal")
            span.text = part.text
            last = span
        return text

    # ---- gradients
    @staticmethod
    def _ref_count(root: ET.Element) -> dict[str, int]:
        hrefs = (f"{{{XLINK_NS}}}href", "href")
        count: dict[str, int] = {}
        for el in root.iter():
            for name, value in el.attrib.items():
                found = [value[1:]] if name in hrefs and value.startswith("#") else _URL.findall(value)
                for ref in found:
                    count[ref] = count.get(ref, 0) + 1
        return count

    @staticmethod
    def _gradient_for(gradient_id: str, to_painted: tuple, root, parent, by_id, ref_count) -> str:
        """The id of a gradient that paints the text as Cairo painted the marker. *to_painted* maps the
        text's own space to the painted element's space, where Cairo's gradient lives."""
        gradient = by_id.get(gradient_id)
        if gradient is None or gradient.tag not in _GRADIENTS or gradient.get("gradientUnits") != "userSpaceOnUse":
            raise RuntimeError("a text's paint came out in a form this code does not understand")
        moved = _matrix_text(_multiply(to_painted, _matrix_of(gradient.get("gradientTransform"))))
        if ref_count.get(gradient_id, 0) <= 1:
            gradient.set("gradientTransform", moved)
            return gradient_id
        copy = ET.Element(gradient.tag, dict(gradient.attrib))
        copy.extend(list(gradient))                    # the stops are shared, never changed
        n = 1
        while f"{gradient_id}-text-{n}" in by_id:
            n += 1
        new_id = f"{gradient_id}-text-{n}"
        copy.set("id", new_id)
        copy.set("gradientTransform", moved)
        host = parent[gradient]
        copy.tail = gradient.tail
        host.insert(list(host).index(gradient) + 1, copy)
        parent[copy] = host
        by_id[new_id] = copy
        return new_id

    # ---- embedded fonts, for browsers
    def _embed(self, root: ET.Element, used: dict[tuple, set[str]]) -> None:
        """A ``<style>`` with one ``@font-face`` per font used: a subset holding the characters drawn
        in it, as a data URI. A font whose fsType forbids embedding is left out; its text still names
        its family."""
        rules = []
        for (path, number), chars in sorted(used.items()):
            face = self._face_of(path, number)
            if not face.embeddable or not face.family:
                continue
            try:
                data = self._subset(path, chars, number)
            except Exception:
                continue                               # the text still names the font; only browsers lose
            self.embedded[path if not number else f"{path}#{number}"] = len(data)
            kind, mime = ("opentype", "font/otf") if face.cff else ("truetype", "font/ttf")
            rules.append(
                f"@font-face {{ font-family: {_css_string(face.family)}; font-weight: {face.weight}; "
                f"font-style: {face.style}; src: url(data:{mime};base64,{base64.b64encode(data).decode('ascii')}) "
                f"format('{kind}'); }}"
            )
        if not rules:
            return
        style = ET.Element(f"{{{SVG_NS}}}style", {"type": "text/css"})
        style.text = "\n" + "\n".join(rules) + "\n"
        style.tail = "\n"
        root.insert(0, style)

    @staticmethod
    def _subset(path: str, chars: set[str], number: int = 0) -> bytes:
        text = "".join(sorted(chars - {"\n"}))
        with _quiet_fonttools():
            tt = TTFont(path, fontNumber=number)
            opts = subset.Options()
            opts.layout_features = ["*"]               # the browser shapes the text: keep every feature
            opts.notdef_outline = True
            opts.hinting = False
            opts.glyph_names = False
            opts.name_IDs = ["*"]
            opts.name_languages = ["*"]
            subsetter = subset.Subsetter(opts)
            subsetter.populate(text=text)
            subsetter.subset(tt)
            buf = io.BytesIO()
            tt.save(buf)
            tt.close()
        return buf.getvalue()

    # ---- <use> in the document body
    @staticmethod
    def _inline(root: ET.Element, texts: set) -> None:
        """Replace each ``<use>`` in the document body that leads to one of *texts* by what it draws,
        when nothing else uses it: text inside a ``<use>`` cannot be edited or selected."""
        use_tag, g_tag, defs_tag = f"{{{SVG_NS}}}use", f"{{{SVG_NS}}}g", f"{{{SVG_NS}}}defs"
        hrefs = (f"{{{XLINK_NS}}}href", "href")
        parent = {child: el for el in root.iter() for child in el}
        by_id = {el.get("id"): el for el in root.iter() if el.get("id") is not None}
        href_count = SvgTextCollector._ref_count(root)

        def target_of(use: ET.Element) -> ET.Element | None:
            href = use.get(hrefs[0]) or use.get(hrefs[1]) or ""
            return by_id.get(href[1:]) if href.startswith("#") else None

        leads: dict[int, bool] = {}

        def leads_to_text(el: ET.Element) -> bool:
            key = id(el)
            if key not in leads:
                leads[key] = False                      # a cycle never leads anywhere
                found = False
                for sub in el.iter():
                    if sub in texts:
                        found = True
                        break
                    if sub.tag == use_tag:
                        target = target_of(sub)
                        if target is not None and leads_to_text(target):
                            found = True
                            break
                leads[key] = found
            return leads[key]

        def in_body(el: ET.Element) -> bool:
            while el is not None:
                if el.tag in _HIDDEN:
                    return False
                el = parent.get(el)
            return True

        pending = [root]
        while pending:
            container = pending.pop()
            for host in list(container.iter()):
                for index, el in enumerate(list(host)):
                    if el.tag != use_tag or not in_body(host):
                        continue
                    target = target_of(el)
                    href = (el.get(hrefs[0]) or el.get(hrefs[1]) or "")[1:]
                    if (target is None or target.tag != g_tag or href_count.get(href) != 1
                            or parent.get(target) is None or parent[target].tag != defs_tag
                            or not leads_to_text(target)):
                        continue
                    rest = {k: v for k, v in el.attrib.items() if k not in (*hrefs, "x", "y")}
                    x, y = el.get("x", "0"), el.get("y", "0")
                    if (x, y) != ("0", "0"):
                        rest["transform"] = (rest.get("transform", "") + f" translate({x}, {y})").strip()
                    parent[target].remove(target)
                    target.tail = None
                    content = target
                    if rest:
                        content = ET.Element(g_tag, rest)
                        content.text = "\n"
                        content.append(target)
                        parent[target] = content
                        target.tail = "\n"
                    content.tail = el.tail
                    host.remove(el)
                    host.insert(index, content)
                    parent[content] = host
                    pending.append(target)              # its own uses, now in the body
