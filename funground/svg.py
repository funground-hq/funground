"""Reading SVG files (story S-092, contract P11, decision D-041).

This is the only module that imports ``svgelements``. It reads an SVG file and turns every shape
into funground geometry (a :class:`~funground.geometry.Path`) plus the style the file gives it.
``funground.sketch`` then draws those shapes onto a picture through the picture's normal drawing
commands, so a loaded SVG has a full drawing history and stays vector in PDF and SVG (P3).

What is read: paths and the basic shapes, groups, ``<use>``, transforms, solid fill and stroke
colours with opacity, stroke width, caps, joins, dashes and ``fill-rule``. A gradient or pattern
paints with its first colour. ``<text>``, images, filters, masks and animation are ignored.

Even-odd fills: funground fills with the non-zero rule only (contract F3), so a shape with
``fill-rule="evenodd"`` is turned into an outline that the non-zero rule fills the same way
(``pathops.even_odd_to_nonzero``). Its stroke is drawn from the original outline.
"""
from __future__ import annotations

import io
import math
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass

import svgelements as se

from . import pathops
from .geometry import Path

PPI = 96.0                                  # CSS: 96 pixels to the inch
# Parts of a file that must never draw where they stand: they only draw when something refers to them.
_NOT_DRAWN_IN_PLACE = {"mask", "marker", "symbol"}
_PAINT_SERVERS = {"linearGradient", "radialGradient", "pattern"}


@dataclass(frozen=True, slots=True)
class SvgShape:
    """One drawn shape: its outline (as in the file, transforms applied) and its style."""

    geometry: Path
    fill: tuple | None                      # (r, g, b, a) or None
    fill_geometry: Path                     # closed, and non-zero filled: what fill() paints
    stroke: tuple | None
    stroke_width: float
    cap: str
    join: str
    miter_limit: float
    dash: tuple
    dash_offset: float
    even_odd: bool = False                  # filled with fill-rule="evenodd" (fill_geometry is converted)


@dataclass(frozen=True, slots=True)
class SvgDocument:
    width: int
    height: int
    shapes: tuple


# ------------------------------------------------------------------ reading
def read(path: str, who: str) -> SvgDocument:
    """Read the SVG file at *path* (it exists). Raises ``ValueError`` for anything that is not SVG."""
    with open(path, "rb") as handle:
        data = handle.read()
    try:
        root = ET.fromstring(data)
    except ET.ParseError as exc:
        raise ValueError(f"{who}: {path!r} is not an SVG file ({exc})") from exc
    if _local(root.tag) != "svg":
        raise ValueError(f"{who}: {path!r} is not an SVG file (its first element is <{_local(root.tag)}>, not <svg>)")
    width, height = _size(root, path, who)
    servers = {el.get("id"): el for el in root.iter() if el.get("id") and _local(el.tag) in _PAINT_SERVERS}
    _park_unrendered(root)
    try:
        parsed = se.SVG.parse(io.BytesIO(ET.tostring(root)), reify=False, ppi=PPI, on_error="ignore")
    except Exception as exc:                                  # svgelements raises many kinds of error
        raise ValueError(f"{who}: {path!r} could not be read as SVG ({exc})") from exc
    shapes = []
    for element in parsed.elements():
        if isinstance(element, se.Shape):
            shape = _shape(element, servers)
            if shape is not None:
                shapes.append(shape)
    return SvgDocument(max(1, round(width)), max(1, round(height)), tuple(shapes))


def shapes_as_paths(doc: SvgDocument) -> list:
    """The outline of every shape in document order (geometry only), for ``f.svg_paths``. An even-odd
    filled shape gives its converted fill outline, so ``draw_path`` shows the same holes (P11)."""
    return [shape.fill_geometry if shape.even_odd else shape.geometry
            for shape in doc.shapes if not shape.geometry.is_empty]


def _local(tag) -> str:
    return tag.rsplit("}", 1)[-1] if isinstance(tag, str) else ""


def _length(text, default=None):
    """A CSS length such as ``2in`` or ``10`` as pixels; ``default`` for percentages, ``em`` and nonsense."""
    if text is None:
        return default
    try:
        value = se.Length(str(text).strip()).value(ppi=PPI)
    except Exception:
        return default
    return float(value) if isinstance(value, (int, float)) and math.isfinite(value) else default


def _size(root, path: str, who: str) -> tuple[float, float]:
    """The picture's size: ``width``/``height`` if given, else the ``viewBox``; the root gets both set."""
    box = None
    numbers = re.findall(r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?", root.get("viewBox") or "")
    if len(numbers) == 4:
        w_box, h_box = float(numbers[2]), float(numbers[3])
        if w_box > 0 and h_box > 0:
            box = (w_box, h_box)
    width = _length(root.get("width")) if not str(root.get("width") or "").strip().endswith("%") else None
    height = _length(root.get("height")) if not str(root.get("height") or "").strip().endswith("%") else None
    if width is None and height is None:
        if box is None:
            raise ValueError(f"{who}: {path!r} has no size: give the <svg> element a width and height, or a viewBox")
        width, height = box
    elif width is None or height is None:
        if box is None:
            raise ValueError(f"{who}: {path!r} has only one of width and height and no viewBox")
        if width is None:
            width = height * box[0] / box[1]
        else:
            height = width * box[1] / box[0]
    if not (width > 0 and height > 0):
        raise ValueError(f"{who}: {path!r} has no size above zero")
    root.set("width", repr(width))
    root.set("height", repr(height))
    return width, height


def _park_unrendered(root) -> None:
    """Move masks, markers and symbols into <defs>, so their shapes draw only where something uses them."""
    parents = {child: parent for parent in root.iter() for child in parent}
    found = [el for el in root.iter() if _local(el.tag) in _NOT_DRAWN_IN_PLACE]
    if not found:
        return
    ns = root.tag[: root.tag.index("}") + 1] if root.tag.startswith("{") else ""
    defs = ET.Element(ns + "defs")
    for el in found:
        parent = parents.get(el)
        if parent is not None:
            parent.remove(el)
            defs.append(el)
    root.insert(0, defs)


# ------------------------------------------------------------------ one shape
def _shape(element, servers) -> SvgShape | None:
    values = element.values or {}
    if str(values.get("visibility", "visible")).strip() in ("hidden", "collapse"):
        return None
    geometry = _geometry(element)
    if geometry is None or geometry.is_empty:
        return None
    scale = math.sqrt(abs(element.transform.determinant)) if element.apply else 1.0
    opacity = _fraction(values.get("opacity"), 1.0)

    fill = _paint(element.fill, values.get("fill"), values.get("fill-opacity"), opacity, servers)
    if isinstance(element, se.SimpleLine):          # a line has no inside
        fill = None
    fill_geometry = Path()
    even_odd = False
    if fill is not None and fill[3] > 0:
        fill_geometry = _closed(geometry)
        if str(values.get("fill-rule", "nonzero")).strip() == "evenodd":
            fill_geometry = pathops.even_odd_to_nonzero(fill_geometry)
            even_odd = True
    else:
        fill = None

    stroke = _paint(element.stroke, values.get("stroke"), values.get("stroke-opacity"), opacity, servers)
    width = element.implicit_stroke_width
    if stroke is None or stroke[3] == 0 or not isinstance(width, (int, float)) or not width > 0:
        stroke, width = None, 1.0

    cap = str(values.get("stroke-linecap", "butt")).strip()
    join = str(values.get("stroke-linejoin", "miter")).strip()
    if cap not in ("butt", "round", "square"):
        cap = "butt"
    if join not in ("miter", "round", "bevel"):
        join = "miter"                              # miter-clip and arcs are drawn as miter
    miter = max(1.0, _length(values.get("stroke-miterlimit"), 4.0) or 4.0)
    dash = _dashes(values.get("stroke-dasharray"), scale)
    offset = (_length(values.get("stroke-dashoffset"), 0.0) or 0.0) * scale if dash else 0.0
    if fill is None and stroke is None:
        return None
    return SvgShape(geometry, fill, fill_geometry, stroke, float(width), cap, join, miter, dash, offset, even_odd)


def _geometry(element) -> Path | None:
    """The element's outline in picture coordinates: arcs and quadratics become cubics."""
    path = Path()
    try:
        segments = list(element.segments(transformed=True))
    except Exception:
        return None
    for seg in segments:
        try:
            if isinstance(seg, se.Move):
                path = path.move_to(*_pt(seg.end))
            elif path.is_empty:
                return None                          # a path must start with a move
            elif isinstance(seg, se.Close):
                path = path.close()
            elif isinstance(seg, se.Line):
                path = path.line_to(*_pt(seg.end))
            elif isinstance(seg, se.CubicBezier):
                path = path.cubic_to(*_pt(seg.control1), *_pt(seg.control2), *_pt(seg.end))
            elif isinstance(seg, se.QuadraticBezier):
                path = path.quad_to(*_pt(seg.control), *_pt(seg.end))
            elif isinstance(seg, se.Arc):
                path = _arc(path, seg)
        except ValueError:
            return None                              # a coordinate was not a finite number
    return path


def _arc(path: Path, seg) -> Path:
    try:
        curves = list(seg.as_cubic_curves())
        pieces = [(_pt(c.control1), _pt(c.control2), _pt(c.end)) for c in curves]
    except (ValueError, ZeroDivisionError, TypeError):
        pieces = []
    if not pieces:
        return path.line_to(*_pt(seg.end))           # a flat or empty arc is a straight line, as in SVG
    for c1, c2, end in pieces:
        path = path.cubic_to(*c1, *c2, *end)
    return path


def _pt(point) -> tuple[float, float]:
    x, y = float(point.x), float(point.y)
    if not (math.isfinite(x) and math.isfinite(y)):
        raise ValueError("not finite")
    return (x, y)


def _closed(path: Path) -> Path:
    """The same outline with every sub-path closed: SVG fills open shapes as if they were closed."""
    out: list = []
    drawing = False
    for seg in path.segments:
        if seg[0] == "move":
            if drawing:
                out.append(("close",))
            drawing = False
        elif seg[0] == "close":
            drawing = False
        else:
            drawing = True
        out.append(seg)
    if drawing:
        out.append(("close",))
    return Path(tuple(out))


# ------------------------------------------------------------------ paint and strokes
def _fraction(text, default: float) -> float:
    if text is None:
        return default
    try:
        raw = str(text).strip()
        value = float(raw[:-1]) / 100 if raw.endswith("%") else float(raw)
    except ValueError:
        return default
    return min(1.0, max(0.0, value)) if math.isfinite(value) else default


def _paint(color, raw, own_opacity, opacity: float, servers):
    """(r, g, b, a) for a fill or stroke, or None for nothing. Gradients and patterns use their first colour."""
    text = str(raw).strip() if raw is not None else ""
    if text.startswith("url("):
        found = _server_colour(text, servers)
        if found is None:
            return None
        r, g, b, a = found
        a = a * _fraction(own_opacity, 1.0)
    else:
        if color is None or color.value is None:
            return None
        r, g, b, a = color.red, color.green, color.blue, color.alpha / 255
    return (int(r), int(g), int(b), max(0, min(255, round(a * opacity * 255))))


def _server_colour(text: str, servers):
    """The first colour of the gradient or pattern a ``url(#id)`` names, or the written fallback colour."""
    match = re.match(r"url\(\s*['\"]?#([^'\")\s]+)['\"]?\s*\)\s*(.*)$", text)
    if match is None:
        return None
    found = None
    element = servers.get(match.group(1))
    if element is not None:
        found = _first_colour(element, servers, 0)
    if found is None and match.group(2):
        fallback = se.Color(match.group(2))
        if fallback.value is not None:
            found = (fallback.red, fallback.green, fallback.blue, fallback.alpha / 255)
    return found


def _style_of(element, name: str):
    value = element.get(name)
    if value is None:
        for part in (element.get("style") or "").split(";"):
            key, _, text = part.partition(":")
            if key.strip() == name:
                return text.strip()
    return value


def _first_colour(element, servers, depth: int):
    kind = _local(element.tag)
    if kind == "pattern":
        for child in element.iter():
            if child is element:
                continue
            for name in ("fill", "stroke"):
                text = _style_of(child, name)
                if text and text != "none" and not text.startswith("url("):
                    c = se.Color(text)
                    if c.value is not None:
                        return (c.red, c.green, c.blue, c.alpha / 255)
        return None
    for child in element:
        if _local(child.tag) == "stop":
            c = se.Color(_style_of(child, "stop-color") or "black")
            if c.value is None:
                return None
            return (c.red, c.green, c.blue, c.alpha / 255 * _fraction(_style_of(child, "stop-opacity"), 1.0))
    href = element.get("{http://www.w3.org/1999/xlink}href") or element.get("href")
    if href and href.startswith("#") and depth < 8 and href[1:] in servers:
        return _first_colour(servers[href[1:]], servers, depth + 1)
    return None


def _dashes(text, scale: float) -> tuple:
    if text is None or str(text).strip() in ("", "none"):
        return ()
    values = []
    for token in re.split(r"[\s,]+", str(text).strip()):
        number = _length(token)
        if number is None or number < 0:
            return ()
        values.append(number * scale)
    if not values or sum(values) <= 0:
        return ()
    if len(values) % 2:
        values = values * 2                          # an odd list repeats once, as in SVG
    return tuple(values)


# ------------------------------------------------------------------ drawing
def draw(doc: SvgDocument, picture) -> None:
    """Draw every shape onto *picture* with its ordinary drawing commands (so the history is vector)."""
    picture.push()
    try:
        for shape in doc.shapes:
            if shape.fill is not None and not shape.fill_geometry.is_empty:
                picture.no_stroke()
                picture.fill(shape.fill)
                picture.draw_path(shape.fill_geometry)
            if shape.stroke is not None:
                picture.no_fill()
                picture.stroke(shape.stroke)
                # f.stroke_width() takes whole numbers; an SVG's widths are often fractions.
                picture._sketch._states.update(stroke_width=shape.stroke_width)
                picture.stroke_cap(shape.cap)
                picture.stroke_join(shape.join)
                picture.miter_limit(shape.miter_limit)
                if shape.dash:
                    picture.stroke_dash(list(shape.dash), shape.dash_offset)
                else:
                    picture.no_dash()
                picture.draw_path(shape.geometry)
    finally:
        picture.pop()
    picture._flush()
