"""Draw-op IR: ops are data, frames are ordered, serialisation round-trips (S-018)."""
from __future__ import annotations

import json

import pytest

from playground import ir
from playground.color import Color
from playground.geometry import Path, Transform
from playground.state import GraphicsState


def test_ops_are_frozen_hashable_data():
    s = GraphicsState()
    a = ir.Circle(1, 2, 3, s)
    assert a == ir.Circle(1, 2, 3, s) and hash(a) == hash(ir.Circle(1, 2, 3, s))
    with pytest.raises(AttributeError):
        a.x = 9  # type: ignore[misc]


def test_frame_preserves_order_and_clears():
    f = ir.Frame()
    f.append(ir.Clear(Color(1, 1, 1)))
    f.append(ir.Rect(0, 0, 1, 1, GraphicsState()))
    assert [type(o).__name__ for o in f] == ["Clear", "Rect"]
    assert len(f) == 2 and f
    f.clear()
    assert len(f) == 0 and not f


def test_every_op_round_trips_through_json():
    s = GraphicsState(fill=None, stroke=Color(1, 2, 3, 4), stroke_width=5, text_size=9)
    path = Path.rect(0, 0, 2, 2).quad_to(3, 3, 4, 4)
    ops = [
        ir.Clear(Color(255, 0, 0)),
        ir.Circle(1.5, 2, 3, s),
        ir.Ellipse(1, 2, 3, 4, s),
        ir.Rect(1, 2, 3, 4, s),
        ir.Line(1, 2, 3, 4, s),
        ir.Point(1, 2, s),
        ir.Text("hi", 1, 2, Color(0, 0, 0), s),
        ir.Save(),
        ir.Restore(),
        ir.Concat(Transform.rotation(30)),
        ir.ClipPath(path),
        ir.ResetClip(),
        ir.FillPath(path, Color(9, 9, 9)),
        ir.StrokePath(path, Color(9, 9, 9), 2.5),
        ir.StrokePath(path, Color(1, 2, 3), 4.0, "butt", "bevel", 4.0, (6.0, 2.0), 1.5),
        ir.SetAntialias(False),
        ir.ResetMatrix(),
    ]
    assert {type(o) for o in ops} == set(ir.OP_TYPES.values()), "add new ops to this test"
    text = json.dumps(ir.Frame(ops).to_jsonable(), sort_keys=True)
    back = ir.Frame.from_jsonable(json.loads(text))
    assert list(back) == ops


def test_serialised_form_is_plain_json_and_stable():
    f = ir.Frame([ir.Rect(1, 2, 3, 4, GraphicsState())])
    d = f.to_jsonable()[0]
    assert d == {
        "op": "Rect", "x": 1, "y": 2, "width": 3, "height": 4,
        "style": {"fill": [255, 255, 255, 255], "stroke": [0, 0, 0, 255], "stroke_width": 1, "text_size": 20},
    }


def test_new_style_fields_are_omitted_when_default_so_old_snapshots_stay_valid():
    """S-042: fields added after the format froze are serialised only when not default."""
    plain = ir.op_to_jsonable(ir.Rect(0, 0, 1, 1, GraphicsState()))
    assert set(plain["style"]) == {"fill", "stroke", "stroke_width", "text_size"}
    styled = ir.op_to_jsonable(ir.Rect(0, 0, 1, 1, GraphicsState(stroke_cap="butt", dash=(4.0, 2.0))))
    assert styled["style"]["stroke_cap"] == "butt" and styled["style"]["dash"] == [4.0, 2.0]
    assert ir.op_from_jsonable(styled) == ir.Rect(0, 0, 1, 1, GraphicsState(stroke_cap="butt", dash=(4.0, 2.0)))
