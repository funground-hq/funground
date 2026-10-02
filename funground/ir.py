"""The draw-op IR (story S-018): what a sketch *asked* for, as plain data.

Public drawing calls append ops to the sketch's current Frame; a renderer
consumes the whole Frame once per loop iteration. Ops are frozen dataclasses,
hashable and JSON-serialisable (see `to_jsonable`), so tests can snapshot them
and any backend can replay them.

Ops carrying `style` hold the GraphicsState *snapshot* they were issued under
(it is immutable, so this is free). The vector ops entered the IR before any
public API used them (PROCESS: internal capability first): Save / Restore /
Concat are emitted by `push` / `pop` / transforms since S-027, and ClipPath /
FillPath / StrokePath by `end_shape`, `draw_path` and `clip` since S-028.
"""
from __future__ import annotations

from dataclasses import dataclass, field, fields, is_dataclass
from typing import Any, Iterator, Union

from .color import Color
from .paint import Gradient
from .geometry import Path, Transform
from .state import GraphicsState


class Op:
    """Marker base class; every op is a frozen dataclass."""

    __slots__ = ()


@dataclass(frozen=True, slots=True)
class Clear(Op):
    color: Color


@dataclass(frozen=True, slots=True)
class Circle(Op):
    x: float
    y: float
    diameter: float
    style: GraphicsState


@dataclass(frozen=True, slots=True)
class Ellipse(Op):
    x: float
    y: float
    width: float
    height: float
    style: GraphicsState


@dataclass(frozen=True, slots=True)
class Rect(Op):
    x: float
    y: float
    width: float
    height: float
    style: GraphicsState
    radii: tuple = ()          # four clamped corner radii (tl, tr, br, bl); () = sharp corners (F14)


@dataclass(frozen=True, slots=True)
class Line(Op):
    x1: float
    y1: float
    x2: float
    y2: float
    style: GraphicsState


@dataclass(frozen=True, slots=True)
class Point(Op):
    x: float
    y: float
    style: GraphicsState


@dataclass(frozen=True, slots=True)
class Text(Op):
    text: str
    x: float
    y: float
    color: Color
    style: GraphicsState


# ---- vector ops (public since Sprint 4: S-027 transforms, S-028 paths)
@dataclass(frozen=True, slots=True)
class Save(Op):
    pass


@dataclass(frozen=True, slots=True)
class Restore(Op):
    pass


@dataclass(frozen=True, slots=True)
class Concat(Op):
    """Multiply the current transform by `transform` (local geometry first)."""

    transform: Transform


@dataclass(frozen=True, slots=True)
class ResetMatrix(Op):
    """Back to the untransformed coordinate system (S-043); undone by the enclosing Restore."""


@dataclass(frozen=True, slots=True)
class ClipPath(Op):
    path: Path


@dataclass(frozen=True, slots=True)
class ResetClip(Op):
    """Remove every clip until the enclosing Restore brings the previous one back (S-041)."""


@dataclass(frozen=True, slots=True)
class FillPath(Op):
    path: Path
    color: Color
    blend_mode: str = "normal"       # S-051: recorded only when not default
    opacity: int = 255
    shadow: tuple | None = None
    erase: int | None = None         # S-107 (F15): remove this much alpha instead of painting; recorded only when set


@dataclass(frozen=True, slots=True)
class StrokePath(Op):
    path: Path
    color: Color
    width: float
    cap: str = "round"
    join: str = "round"
    miter_limit: float = 10.0
    dash: tuple[float, ...] = ()
    dash_offset: float = 0.0
    blend_mode: str = "normal"       # S-051
    opacity: int = 255
    shadow: tuple | None = None
    erase: int | None = None         # S-107 (F15)


@dataclass(frozen=True, slots=True)
class SetAntialias(Op):
    """Smooth (anti-aliased) edges on or off for the rest of the frame (S-042, no_smooth)."""

    on: bool


@dataclass(frozen=True, slots=True)
class Image(Op):
    """Draw a Picture (S-052, contract P3): *source* is its name ("graphics-1", ...), numbered

    in creation order within a run; *version* is its content version at the moment of the
    call. *snapshot* carries the actual pixels/history so the op can be drawn - it is never
    serialised (see NEVER_SERIALISE) and never compared (a round trip loses only this field).
    """

    source: str
    version: int
    x: float
    y: float
    width: float
    height: float
    blend_mode: str = "normal"       # S-051, as FillPath/StrokePath
    opacity: int = 255
    tint: Color | None = None        # S-078 (P5): recorded only when set
    sx: float | None = None          # S-078 (P6): the part of the picture drawn, in its own logical
    sy: float | None = None          # pixels (already clipped to the picture); recorded only when given
    sw: float | None = None
    sh: float | None = None
    snapshot: Any = field(default=None, compare=False, repr=False)
    erase: int | None = None         # S-107 (F15): the fill strength; the picture's alpha is removed, not painted


@dataclass(frozen=True, slots=True)
class PixelBlock:
    """The pixels behind a ``Pixels`` op (S-079): premultiplied BGRA (Cairo's layout) at the
    physical resolution it was made at, *scale* physical pixels per logical one. Never serialised."""

    scale: float
    x: int            # physical left and top of the block
    y: int
    width: int        # physical size
    height: int
    bgra: bytes


@dataclass(frozen=True, slots=True)
class Pixels(Op):
    """Write pixels exactly as given (S-079, contract P7/P8): the logical region x, y, width, height.

    The renderer replaces what is there with the pixels, ignoring transform, clip, tint, opacity
    and blend mode. *checksum* is a CRC32 of the region's premultiplied BGRA bytes at logical
    resolution, so snapshots record the region and a checksum, never the pixels. *data* carries the
    pixels so the op can be drawn; like ``Image.snapshot`` it is never serialised or compared.
    """

    x: int
    y: int
    width: int
    height: int
    checksum: int
    data: Any = field(default=None, compare=False, repr=False)


AnyOp = Union[Clear, Circle, Ellipse, Rect, Line, Point, Text, Save, Restore, Concat, ClipPath, ResetClip, FillPath, StrokePath, SetAntialias, ResetMatrix, Image, Pixels]
OP_TYPES: dict[str, type] = {
    cls.__name__: cls
    for cls in (Clear, Circle, Ellipse, Rect, Line, Point, Text, Save, Restore, Concat, ClipPath, ResetClip, FillPath, StrokePath, SetAntialias, ResetMatrix, Image, Pixels)
}


class Frame:
    """An ordered, append-only list of ops for one loop iteration."""

    __slots__ = ("_ops",)

    def __init__(self, ops: list[Op] | None = None) -> None:
        self._ops: list[Op] = list(ops) if ops else []

    def append(self, op: Op) -> None:
        self._ops.append(op)

    def clear(self) -> None:
        self._ops.clear()

    @property
    def ops(self) -> tuple[Op, ...]:
        return tuple(self._ops)

    def ops_since(self, start: int) -> tuple[Op, ...]:
        """The ops from index *start* on, without copying the earlier ones (scripts call this often)."""
        return tuple(self._ops[start:])

    def __iter__(self) -> Iterator[Op]:
        return iter(self._ops)

    def __len__(self) -> int:
        return len(self._ops)

    def __bool__(self) -> bool:
        return bool(self._ops)

    def to_jsonable(self) -> list[dict[str, Any]]:
        return [op_to_jsonable(op) for op in self._ops]

    @classmethod
    def from_jsonable(cls, data: list[dict[str, Any]]) -> "Frame":
        return cls([op_from_jsonable(d) for d in data])


# ---- serialisation (for snapshots and, later, export replay)
# Fields added after the snapshot format was frozen (Sprint 2) are written only when they
# differ from their default, so every existing IR snapshot stays byte-identical (S-042).
OMIT_WHEN_DEFAULT = frozenset({"stroke_cap", "stroke_join", "miter_limit", "dash", "dash_offset", "cap", "join",
                               "curve_tightness", "text_align", "text_valign", "text_leading",
                               "blend_mode", "opacity", "shadow", "font", "text_style",
                               "rect_mode", "ellipse_mode", "image_mode", "color_mode", "color_ranges",
                               "tint", "sx", "sy", "sw", "sh", "radii",
                               "text_tracking", "text_features", "font_variations",
                               "erasing", "erase"})

# S-052: a Picture's live snapshot (pixels/history) is not data a JSON round trip can carry;
# op_to_jsonable skips it and op_from_jsonable leaves it at its dataclass default (None).
NEVER_SERIALISE = frozenset({"snapshot", "data"})


def _fields_to_jsonable(obj: Any) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for f in fields(obj):
        if f.name in NEVER_SERIALISE:
            continue
        value = getattr(obj, f.name)
        if f.name in OMIT_WHEN_DEFAULT and value == f.default:
            continue
        out[f.name] = _value_to_jsonable(value)
    return out


def _value_to_jsonable(v: Any) -> Any:
    if isinstance(v, Color):
        return list(v.rgba)
    if isinstance(v, Gradient):
        return {"gradient": v.kind, "points": list(v.points), "stops": [[o, list(c.rgba)] for o, c in v.stops]}
    if isinstance(v, Transform):
        return list(v.as_tuple())
    if isinstance(v, Path):
        return [list(seg[:1]) + [list(pt) for pt in seg[1:]] for seg in v.segments]
    if isinstance(v, GraphicsState):
        return _fields_to_jsonable(v)
    if isinstance(v, tuple):
        return [_value_to_jsonable(x) for x in v]
    if isinstance(v, (str, int, float, bool)) or v is None:
        return v
    raise TypeError(f"cannot serialise {type(v).__name__}")


def op_to_jsonable(op: Op) -> dict[str, Any]:
    assert is_dataclass(op)
    d: dict[str, Any] = {"op": type(op).__name__}
    d.update(_fields_to_jsonable(op))
    return d


def _state_from_jsonable(d: dict[str, Any]) -> GraphicsState:
    extra = {k: _extra_from_jsonable(k, d[k]) for k in OMIT_WHEN_DEFAULT if k in d}
    return GraphicsState(
        fill=_paint_from_jsonable(d["fill"]) if d["fill"] is not None else None,
        stroke=_paint_from_jsonable(d["stroke"]) if d["stroke"] is not None else None,
        stroke_width=d["stroke_width"],
        text_size=d["text_size"],
        **extra,
    )


def _extra_from_jsonable(name: str, v: Any) -> Any:
    if name == "dash":
        return tuple(v)
    if name == "color_ranges":
        return tuple(tuple(r) for r in v)
    if name == "shadow":
        return None if v is None else (v[0], v[1], v[2], Color(*v[3]))
    if name == "tint":
        return None if v is None else Color(*v)
    if name == "erasing":
        return None if v is None else tuple(v)
    if name in ("text_features", "font_variations"):
        return tuple((tag, value) for tag, value in v)
    return v


def _paint_from_jsonable(v: Any) -> Any:
    if isinstance(v, dict):
        return Gradient(v["gradient"], tuple(v["points"]), tuple((o, Color(*c)) for o, c in v["stops"]))
    return Color(*v)


def _path_from_jsonable(segs: list) -> Path:
    return Path(tuple((s[0], *(tuple(pt) for pt in s[1:])) for s in segs))


def op_from_jsonable(d: dict[str, Any]) -> Op:
    cls = OP_TYPES[d["op"]]
    kwargs: dict[str, Any] = {}
    for f in fields(cls):
        if f.name in NEVER_SERIALISE:
            continue                                   # left at its dataclass default (None)
        if f.name not in d and f.name in OMIT_WHEN_DEFAULT:
            continue                                   # omitted because it was the default
        v = d[f.name]
        if f.name == "radii":
            kwargs[f.name] = tuple(v)
        elif f.name in ("dash", "shadow", "tint"):
            kwargs[f.name] = _extra_from_jsonable(f.name, v)
        elif f.name == "style":
            kwargs[f.name] = _state_from_jsonable(v)
        elif f.name == "color":
            kwargs[f.name] = _paint_from_jsonable(v)
        elif f.name == "transform":
            kwargs[f.name] = Transform(*v)
        elif f.name == "path":
            kwargs[f.name] = _path_from_jsonable(v)
        else:
            kwargs[f.name] = v
    return cls(**kwargs)
