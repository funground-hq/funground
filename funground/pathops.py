"""Path booleans (story S-086, contract F11, ADR-005).

This is the only module that imports the ``pathops`` package (skia-pathops).
It converts a funground :class:`~funground.geometry.Path` to a Skia path and
back. Inputs are read with the non-zero fill rule; open sub-paths are dropped
before the operation, because Skia would otherwise close and fill them.
Quadratic pieces in a result are raised exactly to cubics, so funground keeps
one curve kind.
"""
from __future__ import annotations

import pathops as _sk

from .geometry import Path

_VERB = _sk.PathVerb


def _closed_subpaths(path: Path) -> list[list[tuple]]:
    """Split *path* into its closed sub-paths (each a list of segments, ending in close)."""
    out: list[list[tuple]] = []
    current: list[tuple] = []
    start = None
    drew = False
    for seg in path.segments:
        kind = seg[0]
        if kind == "move":
            current, start, drew = [seg], seg[1], False
        elif kind == "close":
            if drew:
                out.append(current + [seg])
            current, drew = [], False
            if start is not None:
                current = [("move", start)]   # drawing after close() resumes at the start
        else:
            if not current and start is not None:
                current = [("move", start)]
            current.append(seg)
            drew = True
    return out


def to_skia(path: Path) -> "_sk.Path":
    """A Skia path holding only the closed sub-paths of *path*, fill type WINDING."""
    sk = _sk.Path()
    sk.fillType = _sk.FillType.WINDING
    for sub in _closed_subpaths(path):
        for seg in sub:
            kind = seg[0]
            if kind == "move":
                sk.moveTo(*seg[1])
            elif kind == "line":
                sk.lineTo(*seg[1])
            elif kind == "cubic":
                sk.cubicTo(*seg[1], *seg[2], *seg[3])
            else:
                sk.close()
    return sk


def from_skia(sk: "_sk.Path") -> Path:
    """The funground Path for a Skia path (quadratics become their exact cubics)."""
    segs: list[tuple] = []
    cur = (0.0, 0.0)
    start = cur
    for verb, pts in sk:
        if verb == _VERB.MOVE:
            cur = start = pts[0]
            segs.append(("move", cur))
        elif verb == _VERB.LINE:
            cur = pts[0]
            segs.append(("line", cur))
        elif verb == _VERB.QUAD:
            (cx, cy), (x, y) = pts
            px, py = cur
            segs.append(("cubic",
                         (px + 2 / 3 * (cx - px), py + 2 / 3 * (cy - py)),
                         (x + 2 / 3 * (cx - x), y + 2 / 3 * (cy - y)),
                         (x, y)))
            cur = (x, y)
        elif verb == _VERB.CUBIC:
            segs.append(("cubic", pts[0], pts[1], pts[2]))
            cur = pts[2]
        elif verb == _VERB.CLOSE:
            segs.append(("close",))
            cur = start
        else:
            raise ValueError(f"path operation produced an unsupported segment ({verb.name})")
    return Path(tuple(segs))


def _combine(a: Path, b: Path, op) -> Path:
    return from_skia(_sk.op(to_skia(a), to_skia(b), op))


def union(a: Path, b: Path) -> Path:
    return _combine(a, b, _sk.PathOp.UNION)


def intersection(a: Path, b: Path) -> Path:
    return _combine(a, b, _sk.PathOp.INTERSECTION)


def difference(a: Path, b: Path) -> Path:
    return _combine(a, b, _sk.PathOp.DIFFERENCE)


def xor(a: Path, b: Path) -> Path:
    return _combine(a, b, _sk.PathOp.XOR)


def remove_overlap(a: Path) -> Path:
    return from_skia(_sk.simplify(to_skia(a), fix_winding=True))


def even_odd_to_nonzero(a: Path) -> Path:
    """The same area as *a* read with the even-odd rule, as a path the non-zero rule fills (S-092).

    Used for SVG's ``fill-rule="evenodd"``: funground fills with the non-zero rule only (F3).
    Open sub-paths are dropped, as in every other operation here."""
    sk = to_skia(a)
    sk.fillType = _sk.FillType.EVEN_ODD
    return from_skia(_sk.simplify(sk, fix_winding=True))


# ---- stroke outlines and queries (story S-087, contract F12)

_CAPS = {"round": _sk.LineCap.ROUND_CAP, "square": _sk.LineCap.SQUARE_CAP, "butt": _sk.LineCap.BUTT_CAP}
_JOINS = {"round": _sk.LineJoin.ROUND_JOIN, "miter": _sk.LineJoin.MITER_JOIN, "bevel": _sk.LineJoin.BEVEL_JOIN}


def _stroked_skia(path: Path) -> "_sk.Path":
    """A Skia path with every sub-path that draws something, open ones too."""
    sk = _sk.Path()
    sk.fillType = _sk.FillType.WINDING
    for seg in path.segments:
        kind = seg[0]
        if kind == "move":
            sk.moveTo(*seg[1])
        elif kind == "line":
            sk.lineTo(*seg[1])
        elif kind == "cubic":
            sk.cubicTo(*seg[1], *seg[2], *seg[3])
        else:
            sk.close()
    return sk


def expand_stroke(path: Path, width: float, cap: str, join: str, miter_limit: float, dash) -> Path:
    """The outline a stroke of *width* would paint, with overlaps removed."""
    if not isinstance(width, (int, float)) or isinstance(width, bool) or not width > 0:
        raise ValueError(f"expand_stroke() needs a width above 0, not {width!r}")
    if cap not in _CAPS:
        raise ValueError(f"expand_stroke() cap must be one of {', '.join(map(repr, _CAPS))}, not {cap!r}")
    if join not in _JOINS:
        raise ValueError(f"expand_stroke() join must be one of {', '.join(map(repr, _JOINS))}, not {join!r}")
    if not isinstance(miter_limit, (int, float)) or miter_limit < 1:
        raise ValueError("expand_stroke() miter_limit must be at least 1")
    dash_array = None
    if dash is not None:
        values = [dash] if isinstance(dash, (int, float)) else list(dash)
        if not values or any((not isinstance(v, (int, float))) or v < 0 for v in values) or sum(values) == 0:
            raise ValueError("expand_stroke() dash needs one or more lengths of 0 or more, not all 0, e.g. [10, 5]")
        if len(values) % 2:
            values = values * 2          # Skia wants pairs; an odd list repeats, as in canvas drawing
        dash_array = [float(v) for v in values]
    if path.is_empty:
        return Path()
    sk = _stroked_skia(path)
    sk.stroke(float(width), _CAPS[cap], _JOINS[join], float(miter_limit), dash_array, 0.0)
    sk.convertConicsToQuads()           # round caps and joins come out as conics
    sk.fillType = _sk.FillType.WINDING
    return from_skia(_sk.simplify(sk, fix_winding=True))


def exact_bounds(path: Path):
    """(x, y, w, h) of the tight extent of the closed and open parts, or None."""
    if path.is_empty or not any(seg[0] in ("line", "cubic") for seg in path.segments):
        return None
    x0, y0, x1, y1 = _stroked_skia(path).bounds
    return (x0, y0, x1 - x0, y1 - y0)


def contains(path: Path, x: float, y: float) -> bool:
    """True when (x, y) is inside what the closed sub-paths fill (non-zero rule)."""
    return bool(to_skia(path).contains((float(x), float(y))))
