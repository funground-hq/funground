"""Area, Grid and guides (S-132 part 4, contracts G1 and G2, D-073)."""
from __future__ import annotations

import copy
import json
import pickle

import pygame
import pytest

import funground as f
from funground import api, exploring, ir
from funground.export import motion
from funground.platform.headless import HeadlessPlatform
from funground.sketch import Sketch
from funground.surface import Area, Cell, Ground, Grid

RED = (255, 0, 0)
SVG_RED = 'stroke="rgb(100%, 0%, 0%)"'      # how Cairo writes a red stroke in an SVG


@pytest.fixture(autouse=True)
def fresh_sketch(monkeypatch, tmp_path):
    monkeypatch.setenv("FUNGROUND_HEADLESS", "1")
    monkeypatch.chdir(tmp_path)
    # f.keep() writes next to the sketch file. Here the caller is this test file, so keep it in tmp_path.
    monkeypatch.setattr(exploring, "sketch_file", lambda frame: None)
    api.use_sketch(Sketch(platform=HeadlessPlatform()))
    yield
    api.use_sketch(None)


def edges(a) -> tuple:
    return (a.left, a.top, a.width, a.height)


# ---------------------------------------------------------------- Area
def test_area_fields_and_derived_edges():
    a = f.area(10, 20, 100, 50)
    assert isinstance(a, Area)
    assert edges(a) == (10, 20, 100, 50)
    assert (a.right, a.bottom, a.cx, a.cy) == (110, 70, 60, 45)
    assert repr(a) == "Area(left=10, top=20, right=110, bottom=70, width=100, height=50)"


def test_area_is_an_immutable_value():
    a = f.area(0, 0, 10, 10)
    with pytest.raises(AttributeError, match="cannot be changed"):
        a.left = 5
    with pytest.raises(AttributeError):
        del a.width
    assert a == f.area(0, 0, 10, 10) and hash(a) == hash(f.area(0, 0, 10, 10))
    assert a != f.area(0, 0, 10, 11)
    assert copy.copy(a) is a and copy.deepcopy(a) is a
    assert pickle.loads(pickle.dumps(a)) == a


def test_zero_sized_areas_are_allowed():
    assert f.area(5, 5, 0, 0).right == 5
    assert f.area(0, 0, 10, 0).height == 0


@pytest.mark.parametrize("args, error, match", [
    ((0, 0, -1, 10), ValueError, "cannot be negative"),
    ((0, 0, 10, -0.5), ValueError, "cannot be negative"),
    ((0, 0, float("inf"), 10), ValueError, "finite"),
    ((0, float("nan"), 10, 10), ValueError, "finite"),
    (("0", 0, 10, 10), TypeError, "number"),
    ((0, 0, True, 10), TypeError, "number"),
])
def test_area_errors(args, error, match):
    with pytest.raises(error, match=match):
        f.area(*args)


def test_inset_one_number_and_sides():
    a = f.area(0, 0, 200, 100)
    assert edges(a.inset(10)) == (10, 10, 180, 80)
    assert edges(a.inset(top=5)) == (0, 5, 200, 95)
    assert edges(a.inset(top=1, right=2, bottom=3, left=4)) == (4, 1, 194, 96)
    assert edges(a.inset(10, left=0)) == (0, 10, 190, 80)          # a named side wins over the one number
    assert a.inset() == a
    assert edges(a) == (0, 0, 200, 100)                            # the area itself never changes


def test_inset_returns_a_plain_area_from_ground_and_cells():
    f.size(300, 200, margin=10)
    assert type(f.ground.inset(5)) is Area
    assert type(f.grid(2, 2)[0].inset(1)) is Area


def test_negative_inset_grows_the_area():
    assert edges(f.area(10, 10, 100, 100).inset(-5)) == (5, 5, 110, 110)
    f.size(300, 200)
    assert edges(f.ground.inset(-9)) == (-9, -9, 318, 218)        # a bleed


def test_inset_may_reach_zero_but_not_below():
    assert f.area(0, 0, 100, 40).inset(top=20, bottom=20).height == 0
    with pytest.raises(ValueError, match=r"left and right insets \(60 \+ 60\) are more than the width, 100"):
        f.area(0, 0, 100, 40).inset(left=60, right=60)
    with pytest.raises(ValueError, match=r"top and bottom insets \(30 \+ 30\) are more than the height, 40"):
        f.area(0, 0, 100, 40).inset(30)
    with pytest.raises(TypeError):
        f.area(0, 0, 100, 40).inset("5")


def test_ground_and_content_are_areas():
    f.size(300, 200, margin=(10, 20, 30, 40))
    g, c = f.ground, f.ground.content
    assert isinstance(g, Area) and isinstance(c, Area) and isinstance(g, Ground)
    assert edges(c) == (40, 10, 240, 160) and c.margin == (0, 0, 0, 0)
    assert len(c.grid(2, 2)) == 4


def test_cells_are_areas_with_col_row_and_index():
    f.size(300, 200)
    cell = f.grid(3, 2)[4]
    assert isinstance(cell, Area) and isinstance(cell, Cell)
    assert (cell.col, cell.row, cell.index) == (1, 1, 4)
    assert not hasattr(cell, "w") and not hasattr(cell, "x")       # one name for each edge (D-073)
    assert repr(cell).startswith("Cell(col=1, row=1, index=4, left=100, top=100")


# ---------------------------------------------------------------- Grid: a sequence of cells
def test_grid_is_a_grid_that_behaves_like_the_old_list():
    f.size(300, 200)
    g = f.grid(3, 2)
    assert isinstance(g, Grid) and not isinstance(g, list)
    assert len(g) == 6
    assert [c.index for c in g] == [0, 1, 2, 3, 4, 5]               # row by row, left to right
    assert g[0].index == 0 and g[5].index == 5
    assert g[-1] is g[5] and g[-6] is g[0]
    assert [c.index for c in g[1:3]] == [1, 2] and isinstance(g[1:3], list)
    assert [c.index for c in g[::-2]] == [5, 3, 1]
    assert [c.index for c in reversed(g)] == [5, 4, 3, 2, 1, 0]
    assert g[2] in g and f.area(0, 0, 1, 1) not in g
    assert list(g) == g[:]
    a, b, *rest = f.grid(2, 1)
    assert (a.col, b.col, rest) == (0, 1, [])
    assert [(c.col, v) for c, v in zip(g, "ab")] == [(0, "a"), (1, "b")]
    assert list(enumerate(f.grid(1, 2)))[1][0] == 1


def test_grid_indexing_errors():
    f.size(300, 200)
    g = f.grid(3, 2)
    with pytest.raises(IndexError, match=r"cell 6 is not in this grid: it has 6 cells, 0 to 5 \(or -6 to -1"):
        g[6]
    with pytest.raises(IndexError):
        g[-7]
    with pytest.raises(TypeError, match="g.cell"):
        g[1.0]


def test_grid_is_an_immutable_value():
    f.size(300, 200)
    g = f.grid(2, 2, gutter=5)
    with pytest.raises(AttributeError):
        g.gutter = 0
    assert g == f.grid(2, 2, gutter=5) and g != f.grid(2, 2) and hash(g) == hash(f.grid(2, 2, gutter=5))
    assert copy.copy(g) is g
    assert pickle.loads(pickle.dumps(g)) == g
    assert repr(g).startswith("Grid(2 columns x 2 rows, gutter=(5, 5), area=Ground(")


def test_grid_counts_area_and_gutter():
    f.size(300, 200, margin=10)
    g = f.grid(4, 3, gutter=(6, 8))
    assert (g.column_count, g.row_count) == (4, 3)
    assert g.gutter == (6, 8)
    assert g.area == f.ground.content
    assert f.grid(2, 2, gutter=3).gutter == (3, 3)


# ---------------------------------------------------------------- cell and span
def test_cell_is_zero_based_by_column_and_row():
    f.size(300, 200)
    g = f.grid(3, 2)
    assert g.cell(0, 0) is g[0]
    assert g.cell(2, 0) is g[2]
    assert g.cell(1, 1) is g[4] and (g.cell(1, 1).col, g.cell(1, 1).row) == (1, 1)


@pytest.mark.parametrize("col, row, error, match", [
    (3, 0, IndexError, "column 3 is not in this grid. Its columns are 0 to 2"),
    (0, 2, IndexError, "row 2 is not in this grid. Its rows are 0 to 1"),
    (-1, 0, IndexError, "Its columns are 0 to 2"),
    (0.5, 0, TypeError, "whole number"),
])
def test_cell_errors_name_the_valid_range(col, row, error, match):
    f.size(300, 200)
    with pytest.raises(error, match=match):
        f.grid(3, 2).cell(col, row)


def test_span_includes_the_inner_gutters_exactly():
    # 4 columns of (420 - 3 * 20) / 4 = 90 across 420, 3 rows of (330 - 2 * 15) / 3 = 100 down 330.
    g = f.area(30, 40, 420, 330).grid(4, 3, gutter=(20, 15))
    assert edges(g.cell(1, 1)) == (140, 155, 90, 100)
    s = g.span(1, 0, cols=3, rows=2)
    assert edges(s) == (140, 40, 3 * 90 + 2 * 20, 2 * 100 + 15)       # (140, 40, 310, 215)
    assert s.right == g.cell(3, 1).right == 450 and s.bottom == g.cell(3, 1).bottom == 255
    assert type(s) is Area
    assert edges(g.span(0, 0)) == edges(g.cell(0, 0))
    assert edges(g.span(0, 0, 4, 3)) == edges(g.area)                  # every cell is the whole area


@pytest.mark.parametrize("args, error, match", [
    ((0, 0, 0, 1), ValueError, "cols must be 1 or more"),
    ((0, 0, 1, 0), ValueError, "rows must be 1 or more"),
    ((2, 0, 3, 1), IndexError, r"3 columns from column 2 would reach column 4, but this grid's columns are 0 to 3"),
    ((0, 1, 1, 3), IndexError, r"3 rows from row 1 would reach row 3, but this grid's rows are 0 to 2"),
    ((4, 0, 1, 1), IndexError, "column 4 is not in this grid"),
    ((0, 0, 1.5, 1), TypeError, "whole number"),
])
def test_span_errors(args, error, match):
    with pytest.raises(error, match=match):
        f.area(0, 0, 400, 300).grid(4, 3).span(*args)


def test_columns_and_rows_are_full_areas():
    g = f.area(10, 20, 320, 200).grid(3, 2, gutter=10)                 # columns 100 wide, rows 95 high
    cols = g.columns
    assert [edges(c) for c in cols] == [(10, 20, 100, 200), (120, 20, 100, 200), (230, 20, 100, 200)]
    assert [edges(r) for r in g.rows] == [(10, 20, 320, 95), (10, 125, 320, 95)]
    assert all(type(a) is Area for a in [*cols, *g.rows])


def test_a_grid_nests_in_a_cell_and_in_an_area():
    f.size(300, 200)
    outer = f.grid(2, 1, gutter=10)                                     # cells 145 wide
    inner = outer[1].grid(2, 2, gutter=5)
    assert inner.area is outer[1]
    assert edges(inner[0]) == (155, 0, 70, 97.5)
    assert inner[3].right == 300 and inner[3].bottom == 200
    assert f.grid(2, 2, gutter=5, area=outer[1]) == inner
    deeper = inner.span(0, 0, 2, 1).inset(2).grid(3, 1)
    assert deeper[0].left == 157 and deeper[2].right == 298


def test_area_grid_errors_name_area_grid():
    with pytest.raises(ValueError, match=r"area\.grid\(\) needs cols above 0"):
        f.area(0, 0, 10, 10).grid(0, 1)
    with pytest.raises(ValueError, match="no room"):
        f.area(0, 0, 10, 0).grid(1, 1)                                  # a zero area has no room for cells


# ---------------------------------------------------------------- guides (contract G2)
def guides_area_grid():
    # Lines at x = 20.5, 70.5, 120.5 and y = 20.5, 80.5: a 1-unit line covers whole pixels 20, 70, 120.
    return f.area(20.5, 20.5, 100, 60).grid(2, 1)


def pixel(pixels, x, y) -> tuple:
    i = (y * pixels.width + x) * 4
    b, g, r, _ = bytes(pixels.data)[i:i + 4]
    return (r, g, b)


def state_of(sketch) -> tuple:
    return (sketch.style, sketch._states.depth, sketch._transform_now(), tuple(sketch.frame.ops))


def test_show_leaves_the_drawing_state_and_the_frame_unchanged():
    f.size(200, 120)
    s = api.active_sketch()
    f.fill("navy")
    f.stroke_width(7)
    f.push()
    f.translate(3, 4)
    f.clip(f.path().rect(0, 0, 50, 50))
    before = state_of(s)
    guides_area_grid().show(color="red")
    assert state_of(s) == before                                        # nothing drawn, nothing changed
    assert len(s._guides) > 0
    f.pop()


def test_show_in_files_is_one_op_and_changes_no_state():
    f.size(200, 120)
    s = api.active_sketch()
    f.fill("navy")
    f.translate(3, 4)
    style, depth, transform, ops = state_of(s)
    guides_area_grid().show(color="red", in_files=True)
    assert (s.style, s._states.depth, s._transform_now()) == (style, depth, transform)
    new = s.frame.ops[len(ops):]
    assert [type(op) for op in new] == [ir.StrokePath]
    assert new[0].width == 1 and new[0].color.rgba == (255, 0, 0, 255)
    assert not s._guides


def test_guides_in_a_script_are_left_out_of_png_pdf_svg_and_keep(tmp_path, monkeypatch):
    f.size(200, 120)
    f.background("white")
    guides_area_grid().show(color="red")
    s = api.active_sketch()
    s._sync_canvas()
    assert pixel(s._view_pixels(guides=True), 20, 40) == RED           # what the window shows
    assert pixel(s._view_pixels(), 20, 40) == (255, 255, 255)
    f.save("a.png")
    f.save("a.svg")
    saved = []
    import funground.export as export

    original = export.save_frame
    monkeypatch.setattr(export, "save_frame", lambda frame, *a, **k: (saved.append(list(frame)), original(frame, *a, **k)))
    f.save("a.pdf")
    f.keep("guides are not kept", pdf=True)
    png = pygame.image.load(str(tmp_path / "a.png"))
    assert tuple(png.get_at((20, 40)))[:3] == (255, 255, 255)
    assert SVG_RED not in (tmp_path / "a.svg").read_text(encoding="utf-8")
    assert saved and all(not any(type(op) is ir.StrokePath for op in frame) for frame in saved)
    kept = pygame.image.load(str(tmp_path / "studio" / "001.png"))
    assert tuple(kept.get_at((20, 40)))[:3] == (255, 255, 255)


def test_guides_in_files_are_saved(tmp_path):
    f.size(200, 120)
    f.background("white")
    guides_area_grid().show(color="red", in_files=True)
    f.save("b.png")
    f.save("b.svg")
    f.keep("guides kept")
    assert tuple(pygame.image.load(str(tmp_path / "b.png")).get_at((20, 40)))[:3] == RED
    assert SVG_RED in (tmp_path / "b.svg").read_text(encoding="utf-8")
    assert tuple(pygame.image.load(str(tmp_path / "studio" / "001.png")).get_at((20, 40)))[:3] == RED


def test_guides_follow_the_current_transform_but_not_the_clip():
    f.size(200, 120)
    f.background("white")
    s = api.active_sketch()
    with f.saved_state():
        f.translate(30, 0)
        f.clip(f.path().rect(0, 0, 1, 1))
        guides_area_grid().show(color="red")
    s._sync_canvas()
    shown = s._view_pixels(guides=True)
    assert pixel(shown, 50, 40) == RED and pixel(shown, 20, 40) == (255, 255, 255)


def test_guides_in_a_layer_use_the_layer_and_go_on_top():
    f.size(200, 120)
    f.background("white")
    s = api.canvas_sketch()
    with f.layer("top"):
        f.translate(30, 0)
        guides_area_grid().show(color="red")
        f.fill("blue")
        f.no_stroke()
        f.rect(-30, 0, 200, 120)                                       # covers the whole canvas in the layer
    s._sync_canvas()
    shown = s._view_pixels(guides=True)
    assert pixel(shown, 50, 40) == RED and pixel(shown, 45, 40) == (0, 0, 255)


def test_show_is_refused_in_a_mark_unless_in_files():
    f.size(200, 120)
    with pytest.raises(RuntimeError, match=r"grid\.show\(\) cannot be used inside a `with f\.mark"):
        with f.mark():
            guides_area_grid().show()
    with f.mark() as m:
        guides_area_grid().show(in_files=True)
    assert [type(op) for op in m._ops] == [ir.StrokePath]


def test_show_needs_true_or_false_for_in_files():
    f.size(200, 120)
    with pytest.raises(TypeError, match="in_files"):
        guides_area_grid().show(in_files="yes")


class OneLook:
    """A platform that opens a window, shows one picture and is closed at once, so show() can be tested."""

    def __init__(self) -> None:
        self.inner = HeadlessPlatform()
        self.shown = []

    def __getattr__(self, name):
        return getattr(self.inner, name)

    def present(self, pixels) -> None:
        self.shown.append(pixels)

    def poll(self) -> bool:
        return False

    def events(self) -> list:
        return []


def test_show_puts_the_guides_in_the_script_window_page_by_page():
    platform = OneLook()
    api.use_sketch(Sketch(platform=platform))
    f.size(200, 120)
    f.background("white")
    guides_area_grid().show(color="red")
    f.new_page()
    f.background("white")
    f.show()                                                            # opens on the last page: no guides there
    assert pixel(platform.shown[-1], 20, 40) == (255, 255, 255)
    s = api.canvas_sketch()
    assert len(s._pages_guides) == 1 and s._pages_guides[0] and not s._guides

    platform = OneLook()
    api.use_sketch(Sketch(platform=platform))
    f.size(200, 120)
    f.background("white")
    guides_area_grid().show(color="red")
    f.show()
    assert pixel(platform.shown[-1], 20, 40) == RED


def test_guides_in_an_animated_sketch_reach_the_window_only(tmp_path, monkeypatch):
    frames = []
    monkeypatch.setattr(motion, "require_encoder", lambda kind: None)
    monkeypatch.setattr(motion, "write_gif", lambda path, got, size, durations: frames.extend(got))

    def setup():
        f.size(200, 120)
        f.save_gif("a.gif", 2 / 60)

    def draw():
        f.background("white")
        guides_area_grid().show(color="red")
        if f.frame_count == 1:
            f.save("frame.png")
            f.save("frame.svg")
            f.keep("animated")
        if f.frame_count == 2:
            f.save_frames("seq/##.png", 1)

    sketch = api.active_sketch()
    sketch.run_namespace({"setup": setup, "draw": draw}, max_frames=4)
    (w, h), rgb = sketch.last_frame                                     # what the window showed
    i = (40 * w + 20) * 3
    assert tuple(rgb[i:i + 3]) == RED
    for name in ("frame.png", "studio/001.png", "seq/01.png"):
        assert tuple(pygame.image.load(str(tmp_path / name)).get_at((20, 40)))[:3] == (255, 255, 255), name
    assert SVG_RED not in (tmp_path / "frame.svg").read_text(encoding="utf-8")
    assert len(frames) == 2 and all(tuple(fr[i:i + 3]) == (255, 255, 255) for fr in frames)
    assert json.loads((tmp_path / "studio" / "001.json").read_text(encoding="utf-8"))["frame_count"] == 1


def test_guides_last_one_frame():
    def draw():
        f.background("white")
        if f.frame_count == 0:
            guides_area_grid().show(color="red")

    sketch = api.active_sketch()
    sketch.run_namespace({"setup": lambda: f.size(200, 120), "draw": draw}, max_frames=2)
    (w, h), rgb = sketch.last_frame
    i = (40 * w + 20) * 3
    assert tuple(rgb[i:i + 3]) == (255, 255, 255)
