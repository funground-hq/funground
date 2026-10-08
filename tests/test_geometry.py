"""Transform and Path (story S-018.3)."""
from __future__ import annotations

import math

import pytest

from funground.geometry import Path, Transform


def close(p, q, eps=1e-9):
    return all(abs(a - b) < eps for a, b in zip(p, q))


# ---------------------------------------------------------------- Transform
def test_identity_and_translation():
    assert Transform().is_identity
    assert Transform.translation(10, 20).apply(1, 2) == (11, 22)


def test_rotation_is_degrees_clockwise_on_screen():
    # +90° with y-down turns +x into +y (visually clockwise), contract C1/F1.
    assert close(Transform.rotation(90).apply(1, 0), (0, 1))
    assert close(Transform.rotation(180).apply(1, 0), (-1, 0))
    assert close(Transform.rotation(360).apply(3, 4), (3, 4))


def test_scaling():
    assert Transform.scaling(2).apply(3, 4) == (6, 8)
    assert Transform.scaling(2, 0.5).apply(3, 4) == (6, 2)


def test_then_applies_left_first():
    t = Transform.scaling(2).then(Transform.translation(10, 0))
    assert t.apply(1, 1) == (12, 2)             # scale first, then translate
    u = Transform.translation(10, 0).then(Transform.scaling(2))
    assert u.apply(1, 1) == (22, 2)             # translate first, then scale


def test_concat_matches_translate_then_rotate_call_order():
    # p.translate(100, 50); p.rotate(90); draw at (10, 0) -> rotate applies to the local point first
    ctm = Transform().concat(Transform.translation(100, 50)).concat(Transform.rotation(90))
    assert close(ctm.apply(10, 0), (100, 60))


def test_invert_roundtrip_and_singular():
    t = Transform.translation(3, 4).then(Transform.rotation(30)).then(Transform.scaling(2, 3))
    x, y = t.invert().apply(*t.apply(7, -2))
    assert close((x, y), (7, -2))
    with pytest.raises(ValueError):
        Transform.scaling(0).invert()


def test_transform_is_hashable_and_immutable():
    assert len({Transform(), Transform.identity()}) == 1
    with pytest.raises(AttributeError):
        Transform().a = 2  # type: ignore[misc]


# ---------------------------------------------------------------- Path
def test_builders_are_immutable_and_chain():
    p = Path().move_to(0, 0).line_to(10, 0)
    q = p.line_to(10, 10).close()
    assert len(p) == 2 and len(q) == 4
    assert q.segments[-1] == ("close",)


def test_rect_and_ellipse_helpers():
    r = Path.rect(1, 2, 3, 4)
    assert r.bounds() == (1, 2, 4, 6)
    e = Path.ellipse(50, 50, 20, 10)
    assert len(e) == 6 and e.segments[0] == ("move", (70, 50))
    x0, y0, x1, y1 = e.bounds()
    assert x0 == 30 and x1 == 70 and y0 == 40 and y1 == 60


def test_quad_to_becomes_cubic():
    p = Path().move_to(0, 0).quad_to(3, 3, 6, 0)
    seg = p.segments[1]
    assert seg[0] == "cubic" and close(seg[1], (2, 2)) and close(seg[2], (4, 2)) and seg[3] == (6, 0)


def test_current_point_follows_close():
    p = Path().move_to(1, 1).line_to(5, 5).close()
    assert p.current_point() == (1, 1)
    with pytest.raises(ValueError):
        Path().current_point()


def test_transformed_applies_to_every_point():
    p = Path.rect(0, 0, 10, 10).transformed(Transform.translation(5, 5))
    assert p.bounds() == (5, 5, 15, 15)
    assert Path.rect(0, 0, 1, 1).transformed(Transform()) is not None


def test_translated_moves_every_point():
    p = Path().move_to(0, 0).cubic_to(1, 2, 3, 4, 5, 6).line_to(7, 8).close()
    moved = p.translated(10, -1)
    assert moved.segments == (
        ("move", (10, -1)), ("cubic", (11, 1), (13, 3), (15, 5)), ("line", (17, 7)), ("close",))


def test_translated_returns_a_new_path_and_leaves_the_original():
    p = Path.rect(0, 0, 10, 10)
    before = p.segments
    moved = p.translated(5, 5)
    assert moved is not p
    assert p.segments == before
    assert Path().translated(3, 4) == Path()


@pytest.mark.parametrize("dx,dy", [(5, 5), (3.5, -2.25), (0, 0), (0.1, 0.7)])
def test_translated_equals_transformed_by_a_translation(dx, dy):
    p = Path().move_to(0.3, 1.7).cubic_to(2.1, 3.3, -4.4, 5.5, 6.6, -7.7).close()
    assert p.translated(dx, dy) == p.transformed(Transform.translation(dx, dy))


def test_translated_refuses_a_non_number():
    with pytest.raises(TypeError):
        Path.rect(0, 0, 1, 1).translated("5", 0)


def test_path_is_hashable():
    assert hash(Path.rect(0, 0, 1, 1)) == hash(Path.rect(0, 0, 1, 1))
