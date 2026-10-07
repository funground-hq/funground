"""Ground (S-132 part 1, contract G1): page names and margins in size(), f.ground, f.grid, f.mm, f.inch.

Area and Grid themselves (S-132 part 4) are in tests/test_areas.py."""
from __future__ import annotations


import pytest

import funground as f
from funground import api
from funground.platform.headless import HeadlessPlatform
from funground.sketch import Sketch


@pytest.fixture(autouse=True)
def fresh_sketch():
    api.use_sketch(Sketch(platform=HeadlessPlatform()))
    yield
    api.use_sketch(None)


# ---- size(): page names and landscape
def test_page_name():
    f.size("A4")
    assert (f.width, f.height) == f.page_size("A4") == (595, 842)


def test_page_name_landscape():
    f.size("A4", landscape=True)
    assert (f.width, f.height) == (842, 595)
    f.size("a5landscape")
    assert (f.width, f.height) == (595, 420)


def test_page_name_errors():
    with pytest.raises(ValueError, match="without a height"):
        f.size("A4", 100)
    with pytest.raises(ValueError, match="unknown page size"):
        f.size("Nope")
    with pytest.raises(ValueError, match="landscape"):
        f.size(300, 200, landscape=True)
    with pytest.raises(ValueError, match="both width and height"):
        f.size(300)


def test_plain_size_is_unchanged():
    f.size(300, 200, title="t", fps=30)
    assert (f.width, f.height) == (300, 200)
    assert f.ground.margin == (0, 0, 0, 0)


# ---- margins
def test_margin_one_number():
    f.size(300, 200, margin=20)
    assert f.ground.margin == (20, 20, 20, 20)


def test_margin_four_numbers_is_top_right_bottom_left():
    f.size(300, 200, margin=(10, 20, 30, 40))
    assert f.ground.margin == (10, 20, 30, 40)
    c = f.ground.content
    assert (c.left, c.top, c.right, c.bottom) == (40, 10, 280, 170)


@pytest.mark.parametrize("bad", [-1, (1, 2, -3, 4)])
def test_negative_margin_is_an_error(bad):
    with pytest.raises(ValueError, match="negative"):
        f.size(300, 200, margin=bad)


def test_margin_with_no_content_area_is_an_error():
    with pytest.raises(ValueError, match="left and right"):
        f.size(300, 200, margin=(0, 150, 0, 150))
    with pytest.raises(ValueError, match="top and bottom"):
        f.size(300, 200, margin=100)


def test_margin_wrong_shape_is_an_error():
    with pytest.raises(ValueError, match="four"):
        f.size(300, 200, margin=(1, 2, 3))
    with pytest.raises(TypeError):
        f.size(300, 200, margin="big")


def test_a_failed_size_changes_nothing():
    f.size(300, 200, margin=10)
    with pytest.raises(ValueError):
        f.size(400, 400, margin=-5)
    assert (f.width, f.height) == (300, 200)
    assert f.ground.margin == (10, 10, 10, 10)


def test_margin_does_not_change_the_drawing():
    f.size(100, 80)
    f.circle(50, 40, 30)
    plain = list(api.canvas_sketch().frame)
    api.use_sketch(Sketch(platform=HeadlessPlatform()))
    f.size(100, 80, margin=10)
    f.circle(50, 40, 30)
    assert list(api.canvas_sketch().frame) == plain       # a margin is a guide, not a clip or a shift


# ---- f.ground
def test_ground_values():
    f.size(300, 200)
    g = f.ground
    assert (g.left, g.top, g.right, g.bottom) == (0, 0, 300, 200)
    assert (g.width, g.height, g.cx, g.cy) == (300, 200, 150, 100)
    assert g.margin == (0, 0, 0, 0)
    assert g.content is g


def test_ground_content_values():
    f.size(300, 200, margin=(10, 20, 30, 40))
    g = f.ground
    assert (g.left, g.top, g.width, g.height) == (0, 0, 300, 200)
    c = g.content
    assert (c.left, c.top, c.width, c.height) == (40, 10, 240, 160)
    assert (c.right, c.bottom, c.cx, c.cy) == (280, 170, 160, 90)
    assert c.margin == (0, 0, 0, 0)
    assert c.content is c


def test_ground_is_live_and_read_only():
    f.size(300, 200)
    assert "ground" not in vars(f)
    with pytest.raises(Exception):
        f.ground.width = 5
    f.size(100, 100, margin=5)
    assert f.ground.width == 100 and f.ground.content.width == 90


def test_ground_repr():
    f.size(300, 200, margin=10)
    assert repr(f.ground) == ("Ground(left=0, top=0, right=300, bottom=200, width=300, height=200, "
                              "margin=(10, 10, 10, 10))")


def test_ground_follows_new_page_and_keeps_the_margin():
    f.size(300, 200, margin=10)
    f.new_page("A5")
    assert f.ground.width == 420 and f.ground.height == 595
    assert f.ground.margin == (10, 10, 10, 10)
    assert f.ground.content.width == 400
    f.new_page()
    assert f.ground.margin == (10, 10, 10, 10)


def test_new_page_too_small_for_the_margin_is_an_error():
    f.size(300, 200, margin=50)
    with pytest.raises(ValueError, match="no room"):
        f.new_page(80, 80)
    assert (f.width, f.height) == (300, 200)


def test_ground_follows_resize_canvas_and_keeps_the_margin():
    f.size(300, 200, margin=(5, 6, 7, 8))
    api.canvas_sketch().resize_canvas(500, 400)
    assert f.ground.width == 500 and f.ground.height == 400
    assert f.ground.margin == (5, 6, 7, 8)
    assert f.ground.content.width == 486


def test_ground_is_the_canvas_inside_a_layer():
    f.size(300, 200, margin=10)
    with f.layer("top"):
        assert f.ground.width == 300
        assert f.ground.content.width == 280


# ---- f.grid
def test_grid_order_and_cells():
    f.size(300, 200)
    cells = f.grid(3, 2)
    assert len(cells) == 6
    assert [(c.col, c.row, c.index) for c in cells] == [(0, 0, 0), (1, 0, 1), (2, 0, 2), (0, 1, 3), (1, 1, 4), (2, 1, 5)]
    c = cells[4]
    assert (c.left, c.top, c.width, c.height) == (100, 100, 100, 100)
    assert (c.cx, c.cy) == (150, 150)
    assert (c.left, c.top, c.right, c.bottom, c.width, c.height) == (100, 100, 200, 200, 100, 100)


def test_grid_uses_the_content_area():
    f.size(300, 200, margin=(10, 20, 30, 40))
    cells = f.grid(2, 1)
    assert (cells[0].left, cells[0].top, cells[0].width, cells[0].height) == (40, 10, 120, 160)
    assert cells[1].right == 280


def test_grid_gutter_one_number():
    f.size(300, 200)
    cells = f.grid(3, 2, gutter=10)
    assert cells[0].width == pytest.approx((300 - 20) / 3)
    assert cells[0].height == pytest.approx((200 - 10) / 2)
    assert cells[1].left == pytest.approx(cells[0].right + 10)
    assert cells[3].top == pytest.approx(cells[0].bottom + 10)
    assert cells[2].right == pytest.approx(300)
    assert cells[5].bottom == pytest.approx(200)


def test_grid_gutter_two_numbers():
    f.size(300, 200)
    cells = f.grid(2, 2, gutter=(20, 0))
    assert cells[0].width == 140
    assert cells[1].left == 160
    assert cells[0].height == 100 and cells[2].top == 100


def test_grid_in_an_area_nests():
    f.size(300, 200)
    outer = f.grid(2, 1)
    inner = f.grid(2, 2, area=outer[1])
    assert (inner[0].left, inner[0].top, inner[0].width, inner[0].height) == (150, 0, 75, 100)
    assert inner[3].right == 300 and inner[3].bottom == 200
    assert len(f.grid(1, 1, area=f.ground)) == 1


def test_grid_area_can_be_any_object_with_edges():
    class Box:
        left, top, width, height = 10, 20, 100, 50

    cell = f.grid(1, 1, area=Box())[0]
    assert (cell.left, cell.top, cell.width, cell.height) == (10, 20, 100, 50)


def test_grid_errors():
    f.size(300, 200)
    for cols, rows in ((0, 2), (2, 0), (-1, 2)):
        with pytest.raises(ValueError, match="above 0"):
            f.grid(cols, rows)
    with pytest.raises(TypeError):
        f.grid(2.5, 2)
    with pytest.raises(ValueError, match="negative"):
        f.grid(2, 2, gutter=-1)
    with pytest.raises(ValueError, match="no room"):
        f.grid(3, 2, gutter=150)
    with pytest.raises(ValueError, match="no room"):
        f.grid(2, 2, gutter=(0, 200))
    with pytest.raises(ValueError, match="one number or two"):
        f.grid(2, 2, gutter=(1, 2, 3))
    with pytest.raises(TypeError, match="left, top, width and height"):
        f.grid(2, 2, area=object())


# ---- units
def test_mm_and_inch():
    assert f.inch(1) == 72
    assert f.inch(0.5) == 36
    assert f.mm(25.4) == pytest.approx(72)
    assert f.mm(210) == pytest.approx(595.2756, abs=1e-3)       # A4 is 210 mm wide: page_size("A4")[0] is 595
    assert abs(f.mm(297) - f.page_size("A4")[1]) < 1
    assert f.mm(0) == 0


def test_mm_and_inch_need_numbers():
    with pytest.raises(TypeError):
        f.mm("5")
    with pytest.raises(TypeError):
        f.inch(True)


def test_mm_margin_end_to_end():
    f.size("A4", margin=f.mm(10))
    assert f.ground.content.left == pytest.approx(28.3465, abs=1e-3)


# ---- evidence is untouched

