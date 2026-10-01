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
