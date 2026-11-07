"""Resting layers (S-258): an idle layer keeps only the box that holds its pixels.

Nothing here may show. A layer that has rested paints the same pixels, reads the same and saves the same as
one that never did (contract F16 is unchanged), so these tests compare the two, byte for byte.
"""
from __future__ import annotations

import re

import pytest

import funground as f
from funground import api, picture
from funground.picture import LAYER_REST_SHOWS, _visible_box
from funground.platform.headless import HeadlessPlatform
from funground.sketch import Sketch


def script(w=60, h=40) -> Sketch:
    s = api.use_sketch(Sketch(platform=HeadlessPlatform()))
    s.size(w, h)
    return s


def let_rest(s: Sketch) -> None:
    for _ in range(LAYER_REST_SHOWS + 2):
        s._view_pixels()


def dot(s: Sketch, name: str = "a", x: float = 20, y: float = 15):
    layer = s.layer(name)
    with layer:
        f.no_stroke()
        f.fill(200, 60, 40, 180)
        f.circle(x, y, 9)
    return layer


def scene(s: Sketch) -> None:
    """Soft edges and see-through colours over a canvas, with an empty, a hidden and a full-size layer."""
    f.background(250, 240, 200)
    f.fill(30, 90, 200, 120)
    f.circle(30, 20, 25)
    dot(s, "dot")
    s.layer("empty")
    with s.layer("line"):
        f.stroke(0, 120, 60, 90)
        f.stroke_width(3)
        f.line(2, 38, 57, 3)
    with s.layer("wash"):
        f.background(255, 0, 255, 40)
    dot(s, "hidden", 44, 30)
    s.hide_layer("hidden")


def same_svg(one, other) -> bool:
    """Cairo numbers its sources across the whole process, so two saves of one drawing differ only there."""
    plain = [re.sub(rb"source-\d+", b"source", path.read_bytes()) for path in (one, other)]
    return plain[0] == plain[1]


# ---- the box
@pytest.mark.parametrize("x, y", [(0, 0), (5, 0), (0, 3), (5, 3), (2, 1)])
def test_the_box_of_one_pixel(x, y):
    w, h = 6, 4
    pixels = bytearray(w * h * 4)
    pixels[(y * w + x) * 4 + 3] = 1
    assert _visible_box(pixels, w, h) == (x, y, x + 1, y + 1)


def test_the_box_of_nothing_and_of_everything():
    assert _visible_box(bytearray(24 * 4), 6, 4) == (0, 0, 0, 0)
    assert _visible_box(bytes([9]) * (24 * 4), 6, 4) == (0, 0, 6, 4)


def test_the_box_holds_the_widest_row():
    w, h = 6, 4
    pixels = bytearray(w * h * 4)
    pixels[(1 * w + 4) * 4] = 7                # a row that reaches to the right
    pixels[(2 * w + 1) * 4 + 2] = 7            # a row that reaches to the left
    assert _visible_box(pixels, w, h) == (1, 1, 5, 3)


# ---- resting
def test_an_unchanged_layer_rests_and_gives_up_its_surface():
    s = script(400, 300)
    layer = dot(s)
    let_rest(s)
    assert layer._sketch._renderer.surface is None
    assert 0 < len(layer._resting.snapshot.pixels) < 400 * 300 * 4 / 100


def test_showing_a_layer_makes_no_copy_of_it():
    s = script()
    layer = dot(s)
    s._view_pixels()
    assert not layer._snapshot_cache


def test_a_layer_that_changes_never_rests():
    s = script()
    for i in range(LAYER_REST_SHOWS * 3):
        layer = dot(s, x=i)
        s._view_pixels()
    assert layer._resting is None


def test_a_hidden_layer_rests_and_can_be_shown_again():
    s = script()
    layer = dot(s)
    s.hide_layer("a")
    before = bytes(s._view_pixels().data)
    let_rest(s)
    assert layer._resting is not None
    assert bytes(s._view_pixels().data) == before
    s.show_layer("a")
    assert bytes(s._view_pixels().data) != before


@pytest.mark.parametrize("density", [1, 1.5, 2])
def test_resting_changes_no_pixel(density, monkeypatch):
    monkeypatch.setenv("FUNGROUND_BACKING_SCALE", str(density))
    s = script()
    scene(s)
    never = bytes(s._view_pixels().data)
    let_rest(s)
    assert s._layers["dot"]._resting.snapshot.phys_width >= 9 * density
    assert s._layers["empty"]._resting.snapshot.phys_width == 0
    assert bytes(s._view_pixels().data) == never


def test_files_are_the_same_after_resting(tmp_path):
    s = script()
    scene(s)
    s.save(str(tmp_path / "before.svg"))
    s.save(str(tmp_path / "before.png"))
    let_rest(s)
    s.save(str(tmp_path / "after.svg"))
    s.save(str(tmp_path / "after.png"))
    assert same_svg(tmp_path / "before.svg", tmp_path / "after.svg")
    assert (tmp_path / "before.png").read_bytes() == (tmp_path / "after.png").read_bytes()


# ---- waking
def test_drawing_on_a_resting_layer_adds_to_what_it_kept():
    awake, rested = script(), script()
    for s in (awake, rested):
        api.use_sketch(s)
        dot(s, x=10)
    api.use_sketch(rested)
    let_rest(rested)
    for s in (awake, rested):
        api.use_sketch(s)
        dot(s, x=40)
    assert bytes(rested._view_pixels().data) == bytes(awake._view_pixels().data)
    assert rested._layers["a"]._resting is None


READS = {
    "get": lambda g: g.get(20, 15),
    "pixels": lambda g: (g.load_pixels(), bytes(g.pixels))[1],
    "set": lambda g: (g.set(1, 1, "red"), g.get(1, 1))[1],
    "filter": lambda g: (g.filter("invert"), g.get(20, 15))[1],
    "copy": lambda g: g.copy().get(20, 15),
    "resize": lambda g: (g.resize(30, 20), g.get(10, 7))[1],
    "snapshot": lambda g: g._snapshot().pixels,
}


@pytest.mark.parametrize("name", READS)
def test_reading_a_resting_layer_reads_the_whole_picture(name):
    awake, rested = script(), script()
    api.use_sketch(awake)
    expected = READS[name](dot(awake))
    api.use_sketch(rested)
    layer = dot(rested)
    let_rest(rested)
    assert layer._resting is not None
    assert READS[name](layer) == expected


def test_saving_a_resting_layer_alone(tmp_path):
    s = script()
    layer = dot(s)
    layer.save(str(tmp_path / "before.png"))
    let_rest(s)
    layer.save(str(tmp_path / "after.png"))
    assert (tmp_path / "before.png").read_bytes() == (tmp_path / "after.png").read_bytes()


def test_a_resting_layer_can_be_drawn_on_the_canvas():
    s = script()
    layer = dot(s)
    let_rest(s)
    s.hide_layer("a")
    f.image(layer, 10, 0)
    assert s.get(30, 15).r > 150


# ---- what a layer keeps in its context
@pytest.mark.parametrize("keep", [
    lambda g: g.translate(5, 5),
    lambda g: g.clip(g._sketch.path().rect(0, 0, 30, 30)),
    lambda g: g.no_smooth(),
    lambda g: g.push(),
], ids=["transform", "clip", "no_smooth", "push"])
def test_a_layer_with_state_outside_a_block_stays_awake(keep):
    s = script()
    layer = s.layer("a")
    keep(layer)
    layer.circle(10, 10, 8)
    let_rest(s)
    assert layer._resting is None


def test_a_transform_inside_a_block_does_not_stop_it_resting():
    s = script()
    with s.layer("a") as layer:
        f.translate(5, 5)
        f.circle(10, 10, 8)
    let_rest(s)
    assert layer._resting is not None


def test_a_layer_rests_only_outside_its_block():
    s = script()
    with s.layer("a") as layer:
        f.circle(10, 10, 8)
        let_rest(s)
        assert layer._resting is None


# ---- the cost this story is for
def test_many_idle_layers_hold_little(monkeypatch):
    s = script(400, 300)
    monkeypatch.setattr(picture, "LAYER_REST_SHOWS", 2)
    for i in range(200):
        dot(s, f"trail {i}", i * 2, 100)
    for _ in range(4):
        s._view_pixels()
    held = sum(len(layer._resting.snapshot.pixels) for layer in s._layers.values())
    assert held > 0
    assert all(layer._snapshot_cache == {} for layer in s._layers.values())
    assert held < 200 * 2_000


def test_a_pixel_set_on_a_resting_layer_shows():
    s = script()
    layer = dot(s)
    let_rest(s)
    layer.set(50, 30, "red")
    s._view_pixels()
    assert layer.get(50, 30).r == 255 and layer.get(20, 15).a > 0


def test_pixels_loaded_before_a_layer_rests_can_be_written_after():
    s = script()
    layer = dot(s)
    layer.load_pixels()
    let_rest(s)
    assert layer._resting is not None
    layer.pixels[0] = 255
    layer.pixels[3] = 255
    layer.update_pixels()
    s._view_pixels()
    assert layer.get(0, 0).r == 255 and layer.get(20, 15).a > 0
