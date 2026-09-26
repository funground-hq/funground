"""Gradients (S-050, contract S13): a paint wherever a colour goes; follows the transform; vector in PDF."""
from __future__ import annotations

import zlib

import pytest

import funground as p
from funground import api, ir
from funground.paint import Gradient
from funground.platform.headless import HeadlessPlatform
from funground.sketch import Sketch


def render(draw, size=(100, 100)):
    s = api.use_sketch(Sketch(platform=HeadlessPlatform()))
    s.run_namespace({"setup": lambda: p.size(*size), "draw": draw}, max_frames=1)
    (w, _h), rgb = s.last_frame

    def px(x, y):
        i = (y * w + x) * 3
        return tuple(rgb[i:i + 3])

    return px, s


def near(a, b, tol=12):
    return all(abs(x - y) <= tol for x, y in zip(a, b))


def test_linear_fill_blends_along_the_line():
    def draw():
        p.background("white")
        p.no_stroke()
        p.fill(p.linear_gradient(0, 0, 100, 0, ["red", "blue"]))
        p.rect(0, 0, 100, 100)

    px, _ = render(draw)
    assert near(px(0, 50), (255, 0, 0)) and near(px(99, 50), (0, 0, 255))
    assert near(px(50, 50), (127, 0, 127), tol=6)
    assert px(50, 10) == px(50, 90)                     # constant across the line's direction


def test_stops_place_the_colours():
    def draw():
        p.no_stroke()
        p.fill(p.linear_gradient(0, 0, 100, 0, ["black", "white", "white"], stops=[0, 0.2, 1]))
        p.rect(0, 0, 100, 100)

    px, _ = render(draw)
    assert near(px(10, 50), (127, 127, 127), tol=8) and px(60, 50) == (255, 255, 255)


def test_radial_goes_from_the_centre_outwards():
    def draw():
        p.background("black")
        p.no_stroke()
        p.fill(p.radial_gradient(50, 50, 40, ["white", "black"]))
        p.rect(0, 0, 100, 100)

    px, _ = render(draw)
    assert near(px(50, 50), (255, 255, 255), tol=8) and px(95, 50) == (0, 0, 0)
    assert near(px(70, 50), (127, 127, 127), tol=10)


def test_gradient_follows_the_transform():
    def draw():
        p.no_stroke()
        p.translate(50, 50)
        p.rotate(90)                                     # the left-to-right gradient now runs top to bottom
        p.fill(p.linear_gradient(-50, 0, 50, 0, ["red", "blue"]))
        p.rect(-50, -50, 100, 100)

    px, _ = render(draw)
    assert near(px(50, 1), (255, 0, 0)) and near(px(50, 98), (0, 0, 255))
    assert px(10, 50) == px(90, 50)


def test_stroke_background_and_text_accept_gradients():
    g = p.linear_gradient(0, 0, 100, 0, ["red", "blue"])

    def draw():
        p.background(g)
        p.stroke(g)
        p.stroke_width(10)
        p.line(0, 80, 100, 80)
        p.fill(g)
        p.text_size(40)
        p.text("W", 0, 0)
        p.text("W", 60, 30, color=g)

    px, s = render(draw)
    assert near(px(2, 50), (255, 0, 0)) and near(px(97, 50), (0, 0, 255))
    kinds = {type(op).__name__ for op in s.last_ops}
    assert {"Clear", "Line", "Text"} <= kinds


def test_gradient_ops_round_trip_through_the_snapshot_format():
    def draw():
        p.fill(p.radial_gradient(10, 20, 30, ["red", (0, 0, 255, 128)], stops=[0.25, 1]))
        p.rect(0, 0, 50, 50)

    _, s = render(draw)
    [op] = [op for op in s.last_ops if isinstance(op, ir.Rect)]
    data = ir.op_to_jsonable(op)
    assert data["style"]["fill"] == {"gradient": "radial", "points": [10.0, 20.0, 30.0],
                                     "stops": [[0.25, [255, 0, 0, 255]], [1.0, [0, 0, 255, 128]]]}
    assert ir.op_from_jsonable(data) == op


def test_pdf_keeps_a_vector_gradient(tmp_path):
    out = tmp_path / "g.pdf"

    def draw():
        p.no_stroke()
        p.fill(p.linear_gradient(0, 0, 100, 0, ["red", "blue"]))
        p.rect(0, 0, 100, 100)
        p.save(str(out))

    render(draw)
    data = out.read_bytes()
    streams = [data]
    for chunk in data.split(b"stream")[1:]:
        try:
            streams.append(zlib.decompress(chunk.lstrip(b"\r\n").split(b"endstream")[0]))
        except zlib.error:
            pass
    assert any(b"/ShadingType" in s for s in streams), "expected a PDF shading, not pixels"
    assert b"/Subtype /Image" not in data


def test_learner_mistakes_are_explained():
    with pytest.raises(ValueError, match="at least two colours"):
        p.linear_gradient(0, 0, 1, 1, ["red"])
    with pytest.raises(ValueError, match="at least two colours"):
        p.linear_gradient(0, 0, 1, 1, "red")
    with pytest.raises(ValueError, match="one stop per colour"):
        p.linear_gradient(0, 0, 1, 1, ["red", "blue"], stops=[0, 0.5, 1])
    with pytest.raises(ValueError, match="never go backwards"):
        p.linear_gradient(0, 0, 1, 1, ["red", "blue"], stops=[1, 0])
    with pytest.raises(ValueError, match="radius above 0"):
        p.radial_gradient(0, 0, 0, ["red", "blue"])
    with pytest.raises(ValueError):
        p.linear_gradient(0, 0, 1, 1, ["red", "not-a-colour"])
    assert isinstance(p.linear_gradient(0, 0, 1, 1, ("red", (0, 0, 255))), Gradient)
