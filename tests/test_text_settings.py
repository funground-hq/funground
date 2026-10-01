"""Tracking, OpenType features and variable fonts (story S-090; contract row T13).

Rule pinned here: tracking is added after every glyph, the last one included, so a run of n
glyphs is n x tracking wider. (n counts shaped glyphs: a ligature is one glyph.)
"""
from __future__ import annotations

import pytest

import funground as p
from funground import api, ir, typography
from funground.platform.headless import HeadlessPlatform
from funground.sketch import Sketch
from funground.state import GraphicsState

from fontmaker import make_variable_font


def text_ops(draw) -> list[ir.Text]:
    s = api.use_sketch(Sketch(platform=HeadlessPlatform()))
    s.run_namespace({"setup": lambda: p.size(400, 200), "draw": draw}, max_frames=1)
    return [op for op in s.last_ops if isinstance(op, ir.Text)]


def segs(path):
    return path._path.segments


def glyph_count(text: str, **settings) -> int:
    return len(typography.default_font().shape(text, 20, **settings).glyphs)


@pytest.fixture
def variable_font(tmp_path):
    return make_variable_font(tmp_path)


@pytest.fixture(autouse=True)
def _isolated_font_registry():
    saved, saved_paths = dict(typography._registry), dict(typography._path_to_key)
    yield
    typography._registry.clear()
    typography._registry.update(saved)
    typography._path_to_key.clear()
    typography._path_to_key.update(saved_paths)


# ---------------------------------------------------------------- tracking
def test_tracking_widens_every_glyph_including_the_last(canvas):
    p.text_size(20)
    plain = p.text_width("Spacing")
    p.text_tracking(5)
    assert p.text_width("Spacing") == pytest.approx(plain + 7 * 5)
    assert p.text_width("") == 0.0


def test_negative_tracking_tightens(canvas):
    p.text_size(20)
    plain = p.text_width("Spacing")
    p.text_tracking(-1.5)
    assert p.text_width("Spacing") == pytest.approx(plain - 7 * 1.5)


def test_tracking_counts_glyphs_so_a_ligature_is_one(canvas):
    assert glyph_count("office") == 4            # o, ffi, c, e
    p.text_size(20)
    plain = p.text_width("office")
    p.text_tracking(10)
    assert p.text_width("office") == pytest.approx(plain + 4 * 10)


def test_tracking_moves_each_letter_in_the_outlines(canvas):
    p.text_size(40)
    base = p.text_path("II", 0, 0).bounds()
    p.text_tracking(30)
    wide = p.text_path("II", 0, 0).bounds()
    # the second letter moved 30 pixels to the right; the first did not move
    assert wide[0] == pytest.approx(base[0])
    assert (wide[0] + wide[2]) - (base[0] + base[2]) == pytest.approx(30)


def test_alignment_follows_tracking():
    def draw():
        p.text_size(30)
        p.text_tracking(8)
        draw.width = p.text_width("Hello")
        for h in ("left", "center", "right"):
            p.text_align(h)
            p.text("Hello", 200, 100)

    ops = text_ops(draw)
    assert [op.x for op in ops] == pytest.approx([200, 200 - draw.width / 2, 200 - draw.width])


def test_wrapping_follows_tracking(canvas):
    p.text_size(20)
    message = "aaa aaa aaa"
    box = p.text_width("aaa aaa") + 1
    p.text_box(message, 0, 0, box)               # sanity: two words fit in the first line
    lines, _ = typography.wrap_lines(message, box, 20)
    assert lines == ["aaa aaa", "aaa"]
    wide, _ = typography.wrap_lines(message, box, 20, tracking=4.0)
    assert wide == ["aaa", "aaa", "aaa"]


def test_text_box_uses_tracking(canvas):
    p.text_size(20)
    box = p.text_width("aaa aaa") + 1
    p.text_tracking(4)
    rest = p.text_box("aaa aaa aaa", 0, 0, box, 25)      # room for one line only
    assert rest == "aaa aaa"


def test_text_tracking_must_be_a_number(canvas):
    with pytest.raises(TypeError, match="f.text_tracking"):
        p.text_tracking("wide")
    with pytest.raises(TypeError, match="f.text_tracking"):
        p.text_tracking(True)


# ---------------------------------------------------------------- features
def test_liga_off_gives_more_glyphs_and_a_different_width(canvas):
    assert glyph_count("office") == 4
    assert glyph_count("office", features=(("liga", False),)) == 6
    p.text_size(40)
    with_liga = p.text_width("office")
    p.text_features(liga=False)
    assert p.text_width("office") != with_liga


def test_text_features_without_arguments_resets(canvas):
    p.text_size(40)
    before = p.text_width("office")
    p.text_features(liga=False)
    p.text_features()
    assert p.text_width("office") == before
    assert api.active_sketch().style.text_features == ()


def test_features_are_merged_and_stored_sorted_and_padded(canvas):
    p.text_features(salt=True)
    p.text_features(liga=False, salt=False)
    assert api.active_sketch().style.text_features == (("liga", False), ("salt", False))
    p.text_features()
    p.text_features(ss1=True)
    assert api.active_sketch().style.text_features == (("ss1 ", True),)    # a short tag is padded


def test_a_feature_changes_the_letters_drawn(canvas):
    p.text_size(40)
    plain = segs(p.text_path("agave", 0, 0))
    p.text_features(salt=True)
    assert segs(p.text_path("agave", 0, 0)) != plain


def test_text_features_checks_its_input(canvas):
    with pytest.raises(TypeError, match="f.text_features"):
        p.text_features(liga=1)
    with pytest.raises(ValueError, match="f.text_features"):
        p.text_features(ligature=False)
    with pytest.raises(ValueError, match="f.text_features"):
        p.text_features(**{"": True})


# ---------------------------------------------------------------- variable fonts
def test_variable_font_changes_outline_and_advance(canvas, variable_font):
    p.text_font(p.load_font(variable_font), 100)
    thin_width = p.text_width("A")
    thin = segs(p.text_path("A", 0, 0))
    p.font_variations(wght=900)
    assert p.text_width("A") == pytest.approx(thin_width * 2)        # advances 400 and 800 of 1000
    assert segs(p.text_path("A", 0, 0)) != thin
    p.font_variations(wght=500)
    assert p.text_width("A") == pytest.approx(thin_width * 1.5)       # halfway between the masters
    p.font_variations()
    assert p.text_width("A") == pytest.approx(thin_width)
    assert segs(p.text_path("A", 0, 0)) == thin


def test_outlines_and_spacing_agree_at_the_same_variation(canvas, variable_font):
    p.text_font(p.load_font(variable_font), 100)
    p.font_variations(wght=900)
    left, top, w, h = p.text_path("A", 0, 0).bounds()
    assert left == pytest.approx(10)                       # the box starts at 100 units of 1000
    assert left + w == pytest.approx(70)                   # and ends at 700, as the heavy master
    assert p.text_width("A") == pytest.approx(80)


def test_unknown_axis_is_ignored(canvas, variable_font):
    p.text_font(p.load_font(variable_font), 100)
    plain = p.text_width("A")
    plain_path = segs(p.text_path("A", 0, 0))
    p.font_variations(wdth=50, slnt=-10)
    assert p.text_width("A") == plain
    assert segs(p.text_path("A", 0, 0)) == plain_path
    p.font_variations(wght=900, wdth=50)                    # the known one still applies
    assert p.text_width("A") == pytest.approx(plain * 2)


def test_static_font_with_variations_is_harmless(canvas):
    p.text_size(30)
    plain_width = p.text_width("Hello")
    plain = segs(p.text_path("Hello", 0, 0))
    p.font_variations(wght=900, wdth=75)
    assert p.text_width("Hello") == plain_width
    assert segs(p.text_path("Hello", 0, 0)) == plain


def test_font_variations_checks_its_input(canvas):
    with pytest.raises(TypeError, match="f.font_variations"):
        p.font_variations(wght="bold")
    with pytest.raises(ValueError, match="f.font_variations"):
        p.font_variations(weight=700)


def test_variations_stored_sorted_as_floats(canvas):
    p.font_variations(wght=700, wdth=80)
    assert api.active_sketch().style.font_variations == (("wdth", 80.0), ("wght", 700.0))


def test_variations_do_not_change_the_shared_font(variable_font):
    font = typography.FontResource(variable_font)
    heavy = font.shape("A", 100, variations=(("wght", 900.0),)).advance
    plain = font.shape("A", 100).advance
    assert heavy == pytest.approx(plain * 2)
    assert font.shape("A", 100).advance == pytest.approx(plain)    # the default font object is unchanged


# ---------------------------------------------------------------- saved state and pictures
def test_settings_are_part_of_the_saved_state(canvas):
    p.text_tracking(3)
    p.text_features(liga=False)
    p.font_variations(wght=700)
    with p.saved_state():
        p.text_tracking(9)
        p.text_features()
        p.font_variations()
        assert api.active_sketch().style.text_tracking == 9
    state = api.active_sketch().style
    assert state.text_tracking == 3
    assert state.text_features == (("liga", False),)
    assert state.font_variations == (("wght", 700.0),)


def test_pictures_have_the_three_functions_and_their_own_settings(canvas):
    from funground.picture import ALLOWED_METHODS
    assert {"text_tracking", "text_features", "font_variations"} <= ALLOWED_METHODS
    g = p.create_graphics(200, 50)
    g.text_size(20)
    plain = g.text_width("Spacing")
    g.text_tracking(5)
    assert g.text_width("Spacing") == pytest.approx(plain + 35)
    g.text_features(liga=False)
    g.font_variations(wght=900)
    assert g.text_width("office") == pytest.approx(
        typography.text_width("office", 20, features=(("liga", False),), tracking=5.0))
    assert p.text_width("Spacing") == pytest.approx(plain)       # the window's own settings are untouched


# ---------------------------------------------------------------- text_path
def test_text_path_honours_all_three(canvas, variable_font):
    p.text_size(40)
    base = segs(p.text_path("office", 0, 0))
    p.text_tracking(6)
    assert segs(p.text_path("office", 0, 0)) != base
    p.text_tracking(0)
    p.text_features(liga=False)
    assert segs(p.text_path("office", 0, 0)) != base
    p.text_features()
    p.text_font(p.load_font(variable_font), 100)
    thin = segs(p.text_path("A", 0, 0))
    p.font_variations(wght=900)
    assert segs(p.text_path("A", 0, 0)) != thin


# ---------------------------------------------------------------- IR
def test_defaults_are_left_out_of_the_ir():
    data = ir.op_to_jsonable(ir.Text("Hi", 0, 0, p.color(0), GraphicsState()))
    for name in ("text_tracking", "text_features", "font_variations"):
        assert name not in data["style"]


def test_settings_are_recorded_and_round_trip():
    state = GraphicsState(text_tracking=2.5, text_features=(("liga", False),), font_variations=(("wght", 650.0),))
    op = ir.Text("Hi", 0, 0, p.color(0), state)
    data = ir.op_to_jsonable(op)
    assert data["style"]["text_tracking"] == 2.5
    assert data["style"]["text_features"] == [["liga", False]]
    assert data["style"]["font_variations"] == [["wght", 650.0]]
    assert ir.op_from_jsonable(data) == op


def test_the_text_op_carries_the_settings():
    def draw():
        p.text_tracking(4)
        p.text("Hi", 10, 10)

    [op] = text_ops(draw)
    assert op.style.text_tracking == 4.0


# ---------------------------------------------------------------- the renderer's run cache
def ink_rows(px, x0, x1, y0, y1) -> bytes:
    stride = px.width * 4
    data = bytes(px.data)
    return b"".join(data[y * stride + x0 * 4: y * stride + x1 * 4] for y in range(y0, y1))


def test_same_text_with_different_settings_is_drawn_differently_in_one_frame(canvas):
    p.background(0)
    p.fill(255)
    p.no_stroke()
    p.text_size(20)
    p.text("iii", 5, 5)                    # tracking 0
    p.text_tracking(20)
    p.text("iii", 5, 45)                   # same text, same size, same font: tracking 20
    p.text_tracking(0)
    p.text_features(liga=False)
    p.text("ffi", 5, 75)
    p.text_features()
    p.text("ffi", 105, 75)
    px = canvas._pixels()
    first, second = ink_rows(px, 0, 150, 5, 30), ink_rows(px, 0, 150, 45, 70)
    assert first != second
    assert ink_rows(px, 0, 100, 75, 95) != ink_rows(px, 100, 200, 75, 95)
    keys = list(api.active_sketch()._renderer._text_runs)
    assert len(keys) == 4                  # each setting got its own cached run


def test_a_cached_run_is_not_reused_across_settings(canvas):
    r = api.active_sketch()._renderer
    p.text_size(20)
    p.text("Hi", 5, 5)
    p.text_tracking(10)
    p.text("Hi", 5, 40)
    canvas._pixels()
    runs = {key: run for key, run in r._text_runs.items()}
    assert sorted(run.tracking for run in runs.values()) == [0.0, 10.0]
    # the plain key is exactly the one the S-037 cache tests pin
    assert ("Hi", 20) in runs


def test_the_cache_key_includes_features_and_variations(canvas, variable_font):
    r = api.active_sketch()._renderer
    p.text_font(p.load_font(variable_font), 40)
    p.text("A", 5, 5)
    p.font_variations(wght=900)
    p.text("A", 5, 55)
    canvas._pixels()
    locations = sorted(run.location for run in r._text_runs.values())
    assert locations == [(), (("wght", 900.0),)]
    assert len(r._text_runs) == 2
    p.font_variations()
    p.text_features(liga=False)
    p.text("A", 5, 5)
    canvas._pixels()
    assert len(r._text_runs) == 3
