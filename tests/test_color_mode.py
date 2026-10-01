"""Colour mode (S-082, D-031, contract S15) and grey numbers (D-032, contract S16)."""
from __future__ import annotations

import json

import pytest

import funground as p
from funground import api, ir
from funground.color import Color
from funground.platform.headless import HeadlessPlatform
from funground.sketch import Sketch


def last(sketch):
    return sketch.frame.ops[-1]


def fill_of(sketch, *args):
    """Set fill with *args*, draw a rect and return the fill it recorded."""
    p.fill(*args)
    p.rect(0, 0, 10, 10)
    return last(sketch).style.fill.rgba


# ---- S15: the default mode is S1 ------------------------------------------------------
def test_default_mode_is_exactly_s1(canvas, sketch):
    assert fill_of(sketch, (211.8, 0, 255)) == (211, 0, 255, 255)        # truncated, not rounded
    assert fill_of(sketch, (10, 20, 30, 40)) == (10, 20, 30, 40)
    assert fill_of(sketch, [1, 2, 3]) == (1, 2, 3, 255)
    with pytest.raises(ValueError):
        p.fill((256, 0, 0))


def test_default_mode_after_explicit_rgb_255_is_still_s1(canvas, sketch):
    p.color_mode("rgb", 255)
    assert fill_of(sketch, (211.8, 0, 0)) == (211, 0, 0, 255)


@pytest.mark.parametrize("parts", [(0, 100, 100), (120, 100, 100), (200, 50, 80), (370, 40, 60), (90, 30, 30, 128)])
def test_hsb_with_default_ranges_matches_the_hsb_function(canvas, sketch, parts):
    p.color_mode("hsb")
    h, s, b = parts[:3]
    a = parts[3] / 255 if len(parts) == 4 else 1          # p5's alpha range is 1
    expected = p.hsb(h, s, b, round(a * 255))
    assert p.color(parts[:3] + ((a,) if len(parts) == 4 else ())) == expected
    assert fill_of(sketch, parts[:3] + ((a,) if len(parts) == 4 else ())) == expected.rgba


@pytest.mark.parametrize("parts", [(0, 100, 50), (210, 60, 40), (330, 20, 90)])
def test_hsl_with_default_ranges_matches_the_hsl_function(canvas, sketch, parts):
    p.color_mode("hsl")
    assert fill_of(sketch, parts) == p.hsl(*parts).rgba


# ---- the range forms ------------------------------------------------------------------
def test_one_range_sets_all_four(canvas):
    p.color_mode("rgb", 1)
    assert p.color((1, 0.5, 0, 0.5)).rgba == (255, 128, 0, 128)
    p.color_mode("hsb", 10)
    assert p.color((5, 10, 10)) == p.hsb(180, 100, 100)
    assert p.color((5, 10, 10, 5)).alpha == 128


def test_three_ranges_keep_the_alpha_range(canvas):
    p.color_mode("rgb", 1)                                  # alpha range 1
    p.color_mode("rgb", 100, 100, 100)
    assert p.color((100, 50, 0, 1)).rgba == (255, 128, 0, 255)       # alpha still on 0-1
    assert p.color((100, 50, 0)).alpha == 255


def test_four_ranges_set_all_four(canvas):
    p.color_mode("rgb", 10, 20, 30, 40)
    assert p.color((10, 20, 30, 40)).rgba == (255, 255, 255, 255)
    assert p.color((5, 10, 15, 20)).rgba == (128, 128, 128, 128)


def test_mode_alone_keeps_that_modes_ranges(canvas):
    p.color_mode("rgb", 1)
    p.color_mode("rgb")
    assert p.color((1, 1, 1)).rgba == (255, 255, 255, 255)
    p.color_mode("rgb", 255)
    p.color_mode("rgb")
    assert p.color((255, 0, 0)).rgba == (255, 0, 0, 255)


def test_each_mode_remembers_its_own_ranges(canvas):
    p.color_mode("rgb", 1)
    p.color_mode("hsb", 360, 100, 100)
    p.color_mode("hsb", 1)
    p.color_mode("rgb")                                     # back to rgb: still 0-1
    assert p.color((1, 0, 0)).rgba == (255, 0, 0, 255)
    p.color_mode("hsb")                                     # back to hsb: still 0-1
    assert p.color((0.5, 1, 1)) == p.hsb(180, 100, 100)
    p.color_mode("hsl")                                     # hsl never changed: p5's defaults
    assert p.color((180, 100, 50)) == p.hsl(180, 100, 50)


def test_rgb_ranges_are_independent_of_hsb_ranges(canvas):
    p.color_mode("hsb", 1)
    p.color_mode("rgb")
    assert p.color((255, 0, 0)).rgba == (255, 0, 0, 255)    # rgb is still 0-255


# ---- hue wraps, others clamp, results are rounded -------------------------------------
def test_hue_wraps_on_its_own_range(canvas):
    p.color_mode("hsb")
    assert p.color((370, 100, 100)) == p.color((10, 100, 100))
    assert p.color((-10, 100, 100)) == p.color((350, 100, 100))
    p.color_mode("hsb", 1, 1, 1)
    assert p.color((1.25, 1, 1)) == p.color((0.25, 1, 1))


def test_other_parts_clamp_to_their_range(canvas):
    p.color_mode("hsb")
    assert p.color((0, 150, 100)) == p.color((0, 100, 100))
    assert p.color((0, -5, 100)) == p.color((0, 0, 100))
    assert p.color((0, 100, 300)) == p.color((0, 100, 100))
    p.color_mode("rgb", 1)
    assert p.color((2, -1, 0.5)).rgba == (255, 0, 128, 255)
    assert p.color((0, 0, 0, 5)).alpha == 255


def test_results_are_rounded_not_truncated(canvas):
    p.color_mode("rgb", 1)
    assert p.color((0.999, 0.4, 0.6)).rgba == (255, 102, 153, 255)
    assert p.color((0.5, 0.5, 0.5)).rgba == (128, 128, 128, 255)


# ---- forms that are not numbers are untouched -----------------------------------------
@pytest.mark.parametrize("mode, rng", [("hsb", (1,)), ("hsl", (1,)), ("rgb", (1,))])
def test_names_hex_strings_and_objects_are_unaffected(canvas, sketch, mode, rng):
    p.color_mode(mode, *rng)
    assert fill_of(sketch, "tomato") == (255, 99, 71, 255)
    assert fill_of(sketch, "#FF634780") == (255, 99, 71, 128)
    assert fill_of(sketch, "0xFF6347") == (255, 99, 71, 255)
    assert fill_of(sketch, Color(1, 2, 3, 4)) == (1, 2, 3, 4)

    class Duck:
        r, g, b, a = 9, 8, 7, 6

    assert fill_of(sketch, Duck()) == (9, 8, 7, 6)
    assert p.color("tomato").rgba == (255, 99, 71, 255)


def test_functions_hsb_hsl_lerp_and_getters_keep_fixed_ranges(canvas):
    p.color_mode("hsb", 1)
    assert p.hsb(120, 100, 100).rgba == (0, 255, 0, 255)
    assert p.hsl(120, 100, 50).rgba == (0, 255, 0, 255)
    assert p.lerp_color((0, 0, 0), (255, 255, 255), 0.5).rgba == (128, 128, 128, 255)
    c = p.color("tomato")
    assert (c.red, c.green, c.blue, c.alpha) == (255, 99, 71, 255)
    assert 0 <= c.hue <= 360 and 0 <= c.saturation <= 100 and 0 <= c.brightness <= 100 and 0 <= c.lightness <= 100


# ---- everything that takes a colour follows the mode ----------------------------------
def test_fill_stroke_and_background_follow_the_mode(canvas, sketch):
    p.color_mode("rgb", 1)
    p.stroke((1, 0, 0))
    p.fill((0, 1, 0))
    p.rect(0, 0, 10, 10)
    assert last(sketch).style.stroke.rgb == (255, 0, 0)
    assert last(sketch).style.fill.rgb == (0, 255, 0)
    p.background((0, 0, 1))
    assert last(sketch).color.rgba == (0, 0, 255, 255)


def test_text_color_follows_the_mode(canvas, sketch):
    p.color_mode("rgb", 1)
    p.text("hi", 5, 5, color=(1, 0, 0))
    assert last(sketch).color.rgba == (255, 0, 0, 255)


def test_shadow_follows_the_mode(canvas, sketch):
    p.color_mode("rgb", 1)
    p.shadow(2, 2, 3, (0, 0, 1, 0.5))
    p.rect(0, 0, 10, 10)
    assert last(sketch).style.shadow[3].rgba == (0, 0, 255, 128)


def test_default_shadow_colour_is_not_changed_by_the_mode(canvas, sketch):
    p.color_mode("rgb", 1)
    p.shadow(2, 2)
    p.rect(0, 0, 10, 10)
    assert last(sketch).style.shadow[3].rgba == (0, 0, 0, 128)


def test_gradient_colours_are_read_when_the_gradient_is_made(canvas, sketch):
    p.color_mode("rgb", 1)
    grad = p.linear_gradient(0, 0, 10, 0, [(1, 0, 0), "blue", (0, 1, 0, 0.5)])
    radial = p.radial_gradient(5, 5, 5, [(1, 1, 1), (0, 0, 0)])
    p.color_mode("rgb", 255)                                 # changing the mode afterwards changes nothing
    assert [c.rgba for _, c in grad.stops] == [(255, 0, 0, 255), (0, 0, 255, 255), (0, 255, 0, 128)]
    assert [c.rgb for _, c in radial.stops] == [(255, 255, 255), (0, 0, 0)]
    p.fill(grad)
    p.rect(0, 0, 10, 10)
    assert last(sketch).style.fill is grad


def test_color_function_follows_the_mode(canvas):
    p.color_mode("rgb", 1)
    assert p.color(1, 0.5, 0).rgba == (255, 128, 0, 255)
    assert p.color(1, 0.5, 0, 0.5).rgba == (255, 128, 0, 128)
    assert p.color((1, 0.5, 0)).rgba == (255, 128, 0, 255)
    p.color_mode("hsb", 360, 100, 100)
    assert p.color(120, 100, 100) == p.hsb(120, 100, 100)


def test_single_non_number_colour_does_not_follow_the_mode(canvas):
    p.color_mode("hsb", 1)
    assert p.color("tomato").rgba == (255, 99, 71, 255)
    assert p.color(Color(1, 2, 3)).rgba == (1, 2, 3, 255)


# ---- saved state, frames, pictures, scripts -------------------------------------------
def test_saved_state_restores_the_mode_and_ranges(canvas):
    p.color_mode("rgb", 1)
    with p.saved_state():
        p.color_mode("hsb", 1)
        p.color_mode("rgb", 100)
        assert p.color((100, 0, 0)).rgba == (255, 0, 0, 255)
    assert p.color((1, 0, 0)).rgba == (255, 0, 0, 255)
    p.push()
    p.color_mode("rgb", 255)
    p.pop()
    assert p.color((1, 1, 1)).rgba == (255, 255, 255, 255)


def test_mode_persists_across_frames():
    s = api.use_sketch(Sketch(platform=HeadlessPlatform()))
    seen = []

    def setup():
        p.size(40, 40)
        p.color_mode("rgb", 1)

    def draw():
        seen.append(p.color((1, 0, 0)).rgba)

    s.run_namespace({"setup": setup, "draw": draw}, max_frames=3)
    assert seen == [(255, 0, 0, 255)] * 3


def test_a_picture_keeps_its_own_mode(canvas, sketch):
    g = p.create_graphics(20, 20)
    g.color_mode("rgb", 1)
    g.fill((1, 0, 0))
    g.rect(0, 0, 5, 5)
    assert g._sketch.frame.ops[-1].style.fill.rgb == (255, 0, 0)
    assert p.color((255, 0, 0)).rgba == (255, 0, 0, 255)       # the window is still 0-255
    p.color_mode("hsb", 1)
    assert g._sketch.read_color((1, 1, 1)).rgb == (255, 255, 255)   # and the picture is unchanged


def test_color_mode_works_in_a_script(tmp_path):
    api.use_sketch(Sketch(platform=HeadlessPlatform()))
    p.size(20, 20)
    p.color_mode("rgb", 1)
    p.background((1, 0, 0))
    out = tmp_path / "a.png"
    p.save(str(out))
    import pygame
    assert tuple(pygame.image.load(str(out)).get_at((5, 5)))[:3] == (255, 0, 0)


# ---- serialising ----------------------------------------------------------------------
def test_default_ops_serialise_without_new_fields(canvas, sketch):
    p.fill((1, 2, 3))
    p.rect(0, 0, 10, 10)
    text = json.dumps(ir.Frame(list(sketch.frame.ops)).to_jsonable())
    assert "color_mode" not in text and "color_ranges" not in text


def test_non_default_mode_serialises_and_round_trips(canvas, sketch):
    p.color_mode("hsb", 1)
    p.rect(0, 0, 10, 10)
    data = ir.Frame(list(sketch.frame.ops)).to_jsonable()
    assert data[-1]["style"]["color_mode"] == "hsb"
    assert ir.Frame.from_jsonable(json.loads(json.dumps(data))).ops[-1] == last(sketch)


# ---- the errors -----------------------------------------------------------------------
def test_unknown_mode_is_an_error(canvas):
    with pytest.raises(ValueError, match=r"f\.color_mode"):
        p.color_mode("cmyk")


@pytest.mark.parametrize("args", [(0,), (-1,), (1, 0, 1), (1, 1, -2), (1, 1, 1, 0), ("a",), (True,), (float("nan"),)])
def test_a_range_of_zero_or_less_is_an_error(canvas, args):
    with pytest.raises(ValueError, match=r"f\.color_mode"):
        p.color_mode("rgb", *args)


def test_two_ranges_are_an_error(canvas):
    with pytest.raises(ValueError, match=r"f\.color_mode"):
        p.color_mode("rgb", 1, 1)


def test_a_failed_color_mode_changes_nothing(canvas):
    with pytest.raises(ValueError):
        p.color_mode("hsb", 1, 0, 1)
    assert p.color((255, 0, 0)).rgba == (255, 0, 0, 255)


def test_non_numbers_in_a_non_default_mode_are_errors(canvas):
    p.color_mode("rgb", 1)
    with pytest.raises(ValueError):
        p.fill(("a", 0, 0))
    with pytest.raises(ValueError):
        p.fill((float("nan"), 0, 0))
    with pytest.raises(ValueError):
        p.fill((0,))


# ---- S16: one or two numbers are grey -------------------------------------------------
def test_one_number_is_a_grey(canvas, sketch):
    assert fill_of(sketch, 128) == (128, 128, 128, 255)
    assert fill_of(sketch, 0) == (0, 0, 0, 255)
    assert fill_of(sketch, 255) == (255, 255, 255, 255)
    assert p.color(128).rgba == (128, 128, 128, 255)


def test_two_numbers_are_grey_and_alpha(canvas, sketch):
    assert fill_of(sketch, 128, 100) == (128, 128, 128, 100)
    assert fill_of(sketch, (128, 100)) == (128, 128, 128, 100)
    assert fill_of(sketch, [128, 100]) == (128, 128, 128, 100)
    assert p.color(128, 100).rgba == (128, 128, 128, 100)
    assert p.color((128, 100)).rgba == (128, 128, 128, 100)


def test_grey_works_for_stroke_and_background(canvas, sketch):
    p.stroke(10, 20)
    p.rect(0, 0, 5, 5)
    assert last(sketch).style.stroke.rgba == (10, 10, 10, 20)
    p.background(200)
    assert last(sketch).color.rgba == (200, 200, 200, 255)
    p.background(200, 50)
    assert last(sketch).color.rgba == (200, 200, 200, 50)


def test_grey_in_text_color_shadow_and_gradients(canvas, sketch):
    p.text("x", 0, 0, color=90)
    assert last(sketch).color.rgb == (90, 90, 90)
    p.shadow(1, 1, 2, (40, 50))
    p.rect(0, 0, 5, 5)
    assert last(sketch).style.shadow[3].rgba == (40, 40, 40, 50)
    grad = p.linear_gradient(0, 0, 5, 0, [0, 255])
    assert [c.rgb for _, c in grad.stops] == [(0, 0, 0), (255, 255, 255)]


def test_default_mode_grey_truncates_fractions_like_s1(canvas):
    assert p.color(211.8).rgba == (211, 211, 211, 255)
    assert p.color(100.9, 50.9).rgba == (100, 100, 100, 50)


def test_default_mode_grey_out_of_range_is_an_error(canvas):
    for bad in (256, -1):
        with pytest.raises(ValueError):
            p.fill(bad)


def test_grey_is_read_on_the_third_range_in_rgb(canvas):
    p.color_mode("rgb", 1)
    assert p.color(0.5).rgba == (128, 128, 128, 255)
    assert p.color(1, 0.5).rgba == (255, 255, 255, 128)
    p.color_mode("rgb", 100, 100, 50, 10)
    assert p.color(25).rgba == (128, 128, 128, 255)
    assert p.color(50, 5).rgba == (255, 255, 255, 128)


def test_grey_is_brightness_or_lightness_in_hsb_and_hsl(canvas):
    p.color_mode("hsb")
    assert p.color(50) == p.hsb(0, 0, 50)
    assert p.color(100).rgb == (255, 255, 255)
    assert p.color(0).rgb == (0, 0, 0)
    assert p.color(50, 0.5) == p.hsb(0, 0, 50, 128)
    p.color_mode("hsl")
    assert p.color(50) == p.hsl(0, 0, 50)
    assert p.color(50, 1).alpha == 255


def test_packed_integers_are_gone_but_hex_strings_stay(canvas, sketch):
    with pytest.raises(ValueError):
        p.fill(0xFF634780)                         # far above 255: a grey out of range, not a colour
    assert fill_of(sketch, "0xFF6347") == (255, 99, 71, 255)
    assert fill_of(sketch, "0xFF634780") == (255, 99, 71, 128)


def test_a_bool_is_a_type_error(canvas):
    for call in (lambda: p.fill(True), lambda: p.stroke(False), lambda: p.background(True),
                 lambda: p.fill(True, 100), lambda: p.fill(100, True), lambda: p.color(True),
                 lambda: p.color(1, True), lambda: p.text("x", 0, 0, color=True)):
        with pytest.raises(TypeError):
            call()
    p.color_mode("rgb", 1)
    with pytest.raises(TypeError):
        p.fill(True)


def test_a_second_number_needs_a_number_first(canvas):
    with pytest.raises(ValueError):
        p.fill("red", 100)
    with pytest.raises(ValueError):
        p.fill(p.linear_gradient(0, 0, 1, 0, ["red", "blue"]), 100)


# ---- S16: separate numbers equal the tuple form ---------------------------------------
def test_separate_numbers_equal_one_tuple_in_the_default_mode(canvas, sketch):
    assert fill_of(sketch, 255, 0, 0) == (255, 0, 0, 255)
    assert fill_of(sketch, 255, 0, 0, 128) == (255, 0, 0, 128)
    assert fill_of(sketch, 211.8, 0, 0) == fill_of(sketch, (211.8, 0, 0))
    assert fill_of(sketch, 128) == fill_of(sketch, (128,)[0])
    assert p.color(255, 0, 0) == p.color((255, 0, 0))


def test_separate_numbers_equal_one_tuple_in_hsb(canvas, sketch):
    p.color_mode("hsb")
    assert fill_of(sketch, 120, 100, 100) == fill_of(sketch, (120, 100, 100))
    assert fill_of(sketch, 120, 100, 100, 0.5) == fill_of(sketch, (120, 100, 100, 0.5))
    assert fill_of(sketch, 50, 0.5) == fill_of(sketch, (50, 0.5))
    p.color_mode("rgb", 1)
    assert fill_of(sketch, 1, 0, 0) == (255, 0, 0, 255)


def test_stroke_and_background_take_separate_numbers(canvas, sketch):
    p.stroke(128)
    p.stroke(10, 20, 30, 40)
    p.rect(0, 0, 5, 5)
    assert last(sketch).style.stroke.rgba == (10, 20, 30, 40)
    p.background(30, 30, 60)
    assert last(sketch).color.rgba == (30, 30, 60, 255)
    p.background(0, 0, 0, 0)
    assert last(sketch).color.rgba == (0, 0, 0, 0)


@pytest.mark.parametrize("n", [2, 3, 4])
def test_two_to_four_arguments_are_accepted(canvas, sketch, n):
    p.fill(*range(10, 10 + n))
    p.rect(0, 0, 5, 5)
    assert last(sketch).style.fill is not None


def test_more_than_four_arguments_is_an_error(canvas):
    with pytest.raises(ValueError):
        p.fill(1, 2, 3, 4, 5)
    with pytest.raises(ValueError):
        p.color(1, 2, 3, 4, 5)


def test_separate_arguments_with_a_non_number_first_are_an_error(canvas):
    for call in (lambda: p.fill("red", 100), lambda: p.stroke("#FF0000", 1, 2), lambda: p.background("red", 5),
                 lambda: p.fill(Color(1, 2, 3), 5)):
        with pytest.raises(ValueError, match="more than one argument"):
            call()


def test_a_bool_among_separate_arguments_is_a_type_error(canvas):
    with pytest.raises(TypeError):
        p.fill(255, True, 0)


def test_pictures_take_separate_numbers(canvas):
    g = p.create_graphics(10, 10)
    g.fill(255, 0, 0)
    g.rect(0, 0, 5, 5)
    assert g._sketch.frame.ops[-1].style.fill.rgba == (255, 0, 0, 255)
