"""The draw-op IR (story S-018): what a sketch *asked* for, as plain data.

Public drawing calls append ops to the sketch's current Frame; a renderer
consumes the whole Frame once per loop iteration. Ops are frozen dataclasses,
hashable and JSON-serialisable (see `to_jsonable`), so tests can snapshot them
and any backend can replay them.

Ops carrying `style` hold the GraphicsState *snapshot* they were issued under
(it is immutable, so this is free). Internal-only ops (Save, Restore, Concat,
ClipPath, FillPath, StrokePath) exist for the vector renderer and Phase 2; no
public API emits them yet (PROCESS: internal capability first).
"""
from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from typing import Any, Iterator, Union

from .color import Color
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


# ---- internal ops (no public API yet)
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
class ClipPath(Op):
    path: Path


@dataclass(frozen=True, slots=True)
class FillPath(Op):
    path: Path
    color: Color


@dataclass(frozen=True, slots=True)
class StrokePath(Op):
    path: Path
    color: Color
    width: float


AnyOp = Union[Clear, Circle, Ellipse, Rect, Line, Point, Text, Save, Restore, Concat, ClipPath, FillPath, StrokePath]
OP_TYPES: dict[str, type] = {
    cls.__name__: cls
    for cls in (Clear, Circle, Ellipse, Rect, Line, Point, Text, Save, Restore, Concat, ClipPath, FillPath, StrokePath)
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
def _value_to_jsonable(v: Any) -> Any:
    if isinstance(v, Color):
        return list(v.rgba)
    if isinstance(v, Transform):
        return list(v.as_tuple())
    if isinstance(v, Path):
        return [list(seg[:1]) + [list(pt) for pt in seg[1:]] for seg in v.segments]
    if isinstance(v, GraphicsState):
        return {f.name: _value_to_jsonable(getattr(v, f.name)) for f in fields(v)}
    if isinstance(v, (str, int, float, bool)) or v is None:
        return v
    raise TypeError(f"cannot serialise {type(v).__name__}")


def op_to_jsonable(op: Op) -> dict[str, Any]:
    assert is_dataclass(op)
    d: dict[str, Any] = {"op": type(op).__name__}
    for f in fields(op):
        d[f.name] = _value_to_jsonable(getattr(op, f.name))
    return d


def _state_from_jsonable(d: dict[str, Any]) -> GraphicsState:
    return GraphicsState(
        fill=Color(*d["fill"]) if d["fill"] is not None else None,
        stroke=Color(*d["stroke"]) if d["stroke"] is not None else None,
        stroke_width=d["stroke_width"],
        text_size=d["text_size"],
    )


def _path_from_jsonable(segs: list) -> Path:
    return Path(tuple((s[0], *(tuple(pt) for pt in s[1:])) for s in segs))


def op_from_jsonable(d: dict[str, Any]) -> Op:
    cls = OP_TYPES[d["op"]]
    kwargs: dict[str, Any] = {}
    for f in fields(cls):
        v = d[f.name]
        if f.name == "style":
            kwargs[f.name] = _state_from_jsonable(v)
        elif f.name == "color":
            kwargs[f.name] = Color(*v)
        elif f.name == "transform":
            kwargs[f.name] = Transform(*v)
        elif f.name == "path":
            kwargs[f.name] = _path_from_jsonable(v)
        else:
            kwargs[f.name] = v
    return cls(**kwargs)
