"""Sketch object and active-sketch facade (story S-013)."""
from __future__ import annotations

import playground as p
from playground import api
from playground.color import Color
from playground.sketch import Sketch


def test_two_sketches_do_not_share_state():
    a, b = Sketch(), Sketch()
    a.fill("tomato")
    a.stroke_width(7)
    a.text_size(40)
    a.width = 300
    assert b.style.fill == Color(255, 255, 255)
    assert b.style.stroke_width == 1 and b.style.text_size == 20
    assert b.width == 640


def test_two_sketches_have_independent_random_streams():
    a, b = Sketch(), Sketch()
    a.random_seed(1)
    b.random_seed(2)
    assert [a.random(10) for _ in range(3)] != [b.random(10) for _ in range(3)]
    a.random_seed(1)
    first = [a.random(10) for _ in range(3)]
    b.random_seed(1)
    assert [b.random(10) for _ in range(3)] == first


def test_public_functions_follow_the_active_sketch():
    first = api.active_sketch()
    p.fill("navy")
    other = api.use_sketch(Sketch())
    assert api.active_sketch() is other
    assert other.style.fill == Color(255, 255, 255)
    p.text_size(31)
    assert other.style.text_size == 31 and first.style.text_size == 20
    api.use_sketch(first)
    assert p.width == first.width


def test_live_values_resolve_through_the_active_sketch():
    s = api.active_sketch()
    s.width, s.height, s.frame_count = 123, 45, 6
    assert (p.width, p.height, p.frame_count) == (123, 45, 6)
    api.use_sketch(Sketch())
    assert p.width == 640


def test_sketch_state_stack_is_exception_safe_by_construction():
    s = Sketch()
    s.save_state()
    s.fill("red")
    s.restore_state()
    assert s.style.fill == Color(255, 255, 255)
