"""Loading SVG drawings (S-092, contract P11, D-041): f.load_svg() and f.svg_paths().

Every SVG file is written here, by hand; nothing is downloaded.
"""
from __future__ import annotations

import re
import zlib

import pytest

import funground as p
from funground import api
from funground.picture import Picture
from funground.platform.headless import HeadlessPlatform
from funground.sketch import Sketch

from conftest import run_sketch

NS = 'xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"'


def svg_text(body: str, size: str = 'width="100" height="100"') -> str:
    return f'<svg {NS} {size}>{body}</svg>'


def write(tmp_path, body: str, size: str = 'width="100" height="100"', name: str = "a.svg") -> str:
    path = tmp_path / name
    path.write_text(svg_text(body, size), encoding="utf-8")
    return str(path)


def fresh(width=120, height=120):
    s = api.use_sketch(Sketch(platform=HeadlessPlatform()))
    p.size(width, height)
    return s


def script_sketch():
    return api.use_sketch(Sketch(platform=HeadlessPlatform()))


def px(pic: Picture, x: float, y: float) -> tuple[int, int, int, int]:
    """The colour at logical (x, y) of a picture, as (r, g, b, a) with the colour un-premultiplied."""
    pic._flush()
    surf = pic._sketch._renderer.surface
    surf.flush()
    data = surf.get_data()
    sx = int(x * pic._scale)
    sy = int(y * pic._scale)
    i = sy * surf.get_stride() + sx * 4
    b, g, r, a = data[i], data[i + 1], data[i + 2], data[i + 3]
    if a in (0, 255):
        return (r, g, b, a)
    return (round(r * 255 / a), round(g * 255 / a), round(b * 255 / a), a)


def near(a, b, tol=3):
    return all(abs(x - y) <= tol for x, y in zip(a, b))


RED, GREEN, BLUE, CLEAR = (255, 0, 0, 255), (0, 128, 0, 255), (0, 0, 255, 255), (0, 0, 0, 0)


# ---- size ----------------------------------------------------------------------------------------
def test_size_comes_from_width_and_height(tmp_path):
    pic = p.load_svg(write(tmp_path, "", 'width="64" height="40"'))
    assert isinstance(pic, Picture)
    assert (pic.width, pic.height) == (64, 40)
    assert repr(pic) == "<Picture 64 x 40>"


def test_size_comes_from_the_viewbox_when_width_and_height_are_missing(tmp_path):
    pic = p.load_svg(write(tmp_path, "", 'viewBox="0 0 30 20"'))
    assert (pic.width, pic.height) == (30, 20)


def test_css_units_are_96_to_the_inch(tmp_path):
    pic = p.load_svg(write(tmp_path, "", 'width="2in" height="1in"'))
    assert (pic.width, pic.height) == (192, 96)
    pic = p.load_svg(write(tmp_path, "", 'width="25.4mm" height="10px"', name="b.svg"))
    assert (pic.width, pic.height) == (96, 10)


def test_one_side_and_a_viewbox_keep_the_viewbox_shape(tmp_path):
    pic = p.load_svg(write(tmp_path, "", 'width="100" viewBox="0 0 50 25"'))
    assert (pic.width, pic.height) == (100, 50)


def test_the_viewbox_scales_the_drawing_to_the_size(tmp_path):
    pic = p.load_svg(write(tmp_path, '<rect width="10" height="10" fill="red"/>', 'width="100" height="100" viewBox="0 0 10 10"'))
    assert px(pic, 95, 95) == RED
    assert px(pic, 5, 5) == RED


def test_an_svg_with_no_size_at_all_is_a_value_error(tmp_path):
    with pytest.raises(ValueError, match="no size"):
        p.load_svg(write(tmp_path, "", ""))


def test_the_background_stays_transparent(tmp_path):
    pic = p.load_svg(write(tmp_path, '<rect x="50" width="10" height="10" fill="red"/>'))
    assert px(pic, 5, 5) == CLEAR
    assert px(pic, 95, 95) == CLEAR


# ---- basic shapes ----------------------------------------------------------------------------------
def test_rect(tmp_path):
    pic = p.load_svg(write(tmp_path, '<rect x="10" y="20" width="30" height="40" fill="red"/>'))
    assert px(pic, 25, 40) == RED
    assert px(pic, 5, 40) == CLEAR and px(pic, 25, 65) == CLEAR


def test_a_rounded_rect_has_round_corners(tmp_path):
    pic = p.load_svg(write(tmp_path, '<rect x="10" y="10" width="60" height="60" rx="20" fill="red"/>'))
    assert px(pic, 11, 11) == CLEAR
    assert px(pic, 40, 40) == RED


def test_circle_and_ellipse(tmp_path):
    pic = p.load_svg(write(tmp_path, '<circle cx="30" cy="30" r="20" fill="red"/>'
                                     '<ellipse cx="70" cy="70" rx="25" ry="10" fill="blue"/>'))
    assert px(pic, 30, 30) == RED and px(pic, 30, 8) == CLEAR
    assert px(pic, 70, 70) == BLUE and px(pic, 70, 55) == CLEAR and px(pic, 50, 70) == BLUE


def test_line_is_stroked_and_never_filled(tmp_path):
    pic = p.load_svg(write(tmp_path, '<line x1="10" y1="50" x2="90" y2="50" stroke="red" stroke-width="10"/>'))
    assert px(pic, 50, 50) == RED and px(pic, 50, 40) == CLEAR


def test_polyline_and_polygon(tmp_path):
    pic = p.load_svg(write(tmp_path, '<polygon points="10,10 50,10 10,50" fill="red"/>'
                                     '<polyline points="60,60 90,60 90,90" fill="none" stroke="blue" stroke-width="6"/>'))
    assert px(pic, 20, 20) == RED and px(pic, 45, 45) == CLEAR
    assert px(pic, 75, 60) == BLUE and px(pic, 75, 80) == CLEAR       # the polyline stays open


def test_path_with_lines_curves_and_arcs(tmp_path):
    pic = p.load_svg(write(tmp_path, '<path d="M 10 10 H 60 V 60 Z" fill="red"/>'
                                     '<path d="M 20 90 Q 50 60 80 90 Z" fill="blue"/>'
                                     '<path d="M 70 20 A 10 10 0 1 1 70 40 Z" fill="green"/>'))
    assert px(pic, 50, 20) == RED
    assert px(pic, 50, 85) == BLUE
    assert px(pic, 76, 30) == GREEN and px(pic, 66, 30) == CLEAR and px(pic, 85, 30) == CLEAR


def test_an_open_path_is_filled_as_if_closed_but_stroked_open(tmp_path):
    path = write(tmp_path, '<path d="M 10 10 L 90 10 L 90 90" fill="red" stroke="blue" stroke-width="4"/>')
    pic = p.load_svg(path)
    assert px(pic, 80, 30) == RED                       # inside the closed triangle
    assert px(pic, 50, 10) == BLUE                      # the stroke along the top
    assert px(pic, 50, 50)[:3] == (255, 0, 0)           # the closing diagonal was never stroked blue
    (shape,) = p.svg_paths(path)
    assert not shape.is_closed


def test_display_none_draws_nothing(tmp_path):
    pic = p.load_svg(write(tmp_path, '<rect width="50" height="50" fill="red" display="none"/>'))
    assert px(pic, 10, 10) == CLEAR


# ---- groups, use and transforms ----------------------------------------------------------------------
def test_a_group_transform_moves_and_scales_its_shapes(tmp_path):
    pic = p.load_svg(write(tmp_path, '<g transform="translate(40 10) scale(2)"><rect width="10" height="10" fill="red"/></g>'))
    assert px(pic, 50, 20) == RED
    assert px(pic, 61, 20) == CLEAR and px(pic, 50, 31) == CLEAR


def test_nested_groups_and_rotation(tmp_path):
    pic = p.load_svg(write(tmp_path, '<g transform="translate(50 50)"><g transform="rotate(90)">'
                                     '<rect x="0" y="-5" width="30" height="10" fill="red"/></g></g>'))
    assert px(pic, 50, 70) == RED                        # turned a quarter: it points down
    assert px(pic, 70, 50) == CLEAR


def test_use_draws_a_shape_again_where_asked(tmp_path):
    body = ('<defs><rect id="box" width="20" height="20" fill="blue"/></defs>'
            '<use xlink:href="#box" x="10" y="10"/>'
            '<use href="#box" transform="translate(60 60)"/>')
    pic = p.load_svg(write(tmp_path, body))
    assert px(pic, 20, 20) == BLUE and px(pic, 70, 70) == BLUE
    assert px(pic, 5, 5) == CLEAR and px(pic, 45, 45) == CLEAR       # the <defs> copy is not drawn


def test_shapes_are_drawn_in_document_order(tmp_path):
    pic = p.load_svg(write(tmp_path, '<rect width="60" height="60" fill="red"/><rect x="30" y="30" width="60" height="60" fill="blue"/>'))
    assert px(pic, 40, 40) == BLUE and px(pic, 10, 10) == RED


# ---- colours and opacity -----------------------------------------------------------------------------
def test_fill_and_stroke_colours_in_every_form(tmp_path):
    body = ('<rect width="20" height="20" fill="#f00"/>'
            '<rect x="30" width="20" height="20" fill="rgb(0, 0, 255)"/>'
            '<rect x="60" width="20" height="20" style="fill:green"/>'
            '<rect y="30" width="20" height="20" fill="none" stroke="red" stroke-width="8"/>')
    pic = p.load_svg(write(tmp_path, body))
    assert px(pic, 10, 10) == RED and px(pic, 40, 10) == BLUE and px(pic, 70, 10) == GREEN
    assert px(pic, 10, 30) == RED and px(pic, 10, 40) == CLEAR


def test_a_shape_with_no_fill_attribute_is_black(tmp_path):
    pic = p.load_svg(write(tmp_path, '<rect width="20" height="20"/>'))
    assert px(pic, 10, 10) == (0, 0, 0, 255)


def test_fill_opacity_and_opacity_both_apply(tmp_path):
    body = ('<rect width="20" height="20" fill="red" fill-opacity="0.5"/>'
            '<rect x="30" width="20" height="20" fill="red" opacity="0.5"/>'
            '<g opacity="0.5"><rect x="60" width="20" height="20" fill="red" fill-opacity="0.5"/></g>'
            '<rect y="30" width="20" height="20" fill="none" stroke="blue" stroke-width="10" stroke-opacity="0.5"/>')
    pic = p.load_svg(write(tmp_path, body))
    assert near(px(pic, 10, 10), (255, 0, 0, 128), 2)
    assert near(px(pic, 40, 10), (255, 0, 0, 128), 2)
    assert near(px(pic, 70, 10), (255, 0, 0, 64), 2)
    assert near(px(pic, 10, 30), (0, 0, 255, 128), 2)


# ---- strokes ---------------------------------------------------------------------------------------
def test_stroke_width_follows_the_transform(tmp_path):
    body = ('<line x1="10" y1="20" x2="90" y2="20" stroke="red" stroke-width="4"/>'
            '<g transform="scale(2)"><line x1="5" y1="30" x2="45" y2="30" stroke="red" stroke-width="4"/></g>')
    pic = p.load_svg(write(tmp_path, body))
    assert px(pic, 50, 21) == RED and px(pic, 50, 23) == CLEAR       # width 4: 18 to 22
    assert px(pic, 50, 63) == RED and px(pic, 50, 65) == CLEAR       # width 8 at y = 60: 56 to 64


def test_a_stroke_width_that_is_a_fraction_is_kept(tmp_path):
    path = write(tmp_path, '<line x1="10" y1="50" x2="90" y2="50" stroke="red" stroke-width="0.5"/>')
    pic = p.load_svg(path)
    assert px(pic, 50, 50)[3] < 200 and px(pic, 50, 50)[3] > 0       # a thin, partly covered pixel row
    assert pic._history, "the drawing history holds the strokes"
    widths = {op.width for op in pic._history if hasattr(op, "width") and type(op).__name__ == "StrokePath"}
    assert widths == {0.5}


def test_stroke_caps(tmp_path):
    body = ''.join(f'<line x1="30" y1="{y}" x2="70" y2="{y}" stroke="red" stroke-width="12" stroke-linecap="{cap}"/>'
                   for y, cap in ((20, "butt"), (50, "round"), (80, "square")))
    body += '<line x1="30" y1="95" x2="70" y2="95" stroke="blue" stroke-width="6"/>'    # no cap given: butt
    pic = p.load_svg(write(tmp_path, body))
    assert px(pic, 27, 20) == CLEAR                                    # butt stops at 30
    assert px(pic, 25, 50) == RED and px(pic, 25, 45) == CLEAR         # round: a half circle, so its corner is cut
    assert px(pic, 25, 75) == RED and px(pic, 23, 80) == CLEAR         # square reaches 24, corners and all
    assert px(pic, 25, 76) == RED
    assert px(pic, 27, 95) == CLEAR


def test_stroke_joins(tmp_path):
    corner = 'points="20,80 20,20 80,20" fill="none" stroke="red" stroke-width="16" stroke-linejoin="{}"'
    miter = p.load_svg(write(tmp_path, f'<polyline {corner.format("miter")}/>'))
    bevel = p.load_svg(write(tmp_path, f'<polyline {corner.format("bevel")}/>', name="b.svg"))
    rounded = p.load_svg(write(tmp_path, f'<polyline {corner.format("round")}/>', name="c.svg"))
    default = p.load_svg(write(tmp_path, '<polyline points="20,80 20,20 80,20" fill="none" stroke="red" stroke-width="16"/>', name="d.svg"))
    assert px(miter, 13, 13) == RED                                    # the sharp outer corner
    assert px(bevel, 13, 13) == CLEAR and px(rounded, 13, 13) == CLEAR
    assert px(bevel, 20, 20) == RED
    assert px(default, 13, 13) == RED                                  # SVG's default join is miter


def test_dashes_and_their_offset(tmp_path):
    pic = p.load_svg(write(tmp_path, '<line x1="0" y1="20" x2="100" y2="20" stroke="red" stroke-width="8" stroke-dasharray="20 10" stroke-linecap="butt"/>'
                                     '<line x1="0" y1="50" x2="100" y2="50" stroke="red" stroke-width="8" stroke-dasharray="20 10" stroke-dashoffset="20"/>'
                                     '<g transform="scale(2)"><line x1="0" y1="40" x2="50" y2="40" stroke="red" stroke-width="4" stroke-dasharray="10 5"/></g>'))
    assert px(pic, 10, 20) == RED and px(pic, 25, 20) == CLEAR and px(pic, 35, 20) == RED
    assert px(pic, 10, 50) == CLEAR or px(pic, 5, 50) == CLEAR         # the offset moves the pattern
    assert px(pic, 25, 50) == RED
    assert px(pic, 10, 80) == RED and px(pic, 25, 80) == CLEAR         # dashes are scaled by the transform: 20 on, 10 off


def test_an_odd_dash_list_repeats(tmp_path):
    pic = p.load_svg(write(tmp_path, '<line x1="0" y1="20" x2="100" y2="20" stroke="red" stroke-width="8" stroke-dasharray="10 5 5" stroke-linecap="butt"/>'))
    # 10 on, 5 off, 5 on, then 10 off, 5 on, 5 off: the pattern is 30 long
    assert px(pic, 5, 20) == RED and px(pic, 12, 20) == CLEAR and px(pic, 17, 20) == RED and px(pic, 25, 20) == CLEAR


# ---- fill rule -------------------------------------------------------------------------------------
HOLE = 'd="M 10 10 H 90 V 90 H 10 Z M 30 30 H 70 V 70 H 30 Z"'          # both squares run the same way


def test_evenodd_leaves_a_hole(tmp_path):
    pic = p.load_svg(write(tmp_path, f'<path {HOLE} fill="red" fill-rule="evenodd"/>'))
    assert px(pic, 50, 50) == CLEAR
    assert px(pic, 20, 20) == RED


def test_nonzero_fills_the_hole_and_is_the_default(tmp_path):
    for rule, name in (('fill-rule="nonzero"', "a.svg"), ("", "b.svg")):
        pic = p.load_svg(write(tmp_path, f'<path {HOLE} fill="red" {rule}/>', name=name))
        assert px(pic, 50, 50) == RED


def test_evenodd_in_a_style_and_on_a_star(tmp_path):
    star = 'points="50,5 80,95 5,38 95,38 20,95"'
    pic = p.load_svg(write(tmp_path, f'<polygon {star} fill="red" style="fill-rule:evenodd"/>'))
    assert px(pic, 50, 50) == CLEAR                                    # the pentagon in the middle
    nonzero = p.load_svg(write(tmp_path, f'<polygon {star} fill="red"/>', name="b.svg"))
    assert px(nonzero, 50, 50) == RED


def test_the_stroke_of_an_evenodd_shape_still_goes_round_every_edge(tmp_path):
    pic = p.load_svg(write(tmp_path, f'<path {HOLE} fill="red" fill-rule="evenodd" stroke="blue" stroke-width="4"/>'))
    assert px(pic, 50, 30) == BLUE and px(pic, 50, 50) == CLEAR and px(pic, 20, 20) == RED


# ---- fallbacks and what is ignored ---------------------------------------------------------------
def test_a_gradient_fill_uses_its_first_colour(tmp_path):
    body = ('<defs><linearGradient id="g"><stop offset="0" stop-color="#ff0000"/><stop offset="1" stop-color="blue"/></linearGradient>'
            '<radialGradient id="r"><stop offset="0" style="stop-color:blue"/><stop offset="1" stop-color="red"/></radialGradient>'
            '<linearGradient id="chain" xlink:href="#g"/></defs>'
            '<rect width="20" height="20" fill="url(#g)"/>'
            '<rect x="30" width="20" height="20" fill="url(#r)"/>'
            '<rect x="60" width="20" height="20" fill="url(#chain)"/>'
            '<rect y="30" width="20" height="20" fill="none" stroke="url(#g)" stroke-width="8"/>'
            '<rect y="60" width="20" height="20" fill="url(#missing) green"/>')
    pic = p.load_svg(write(tmp_path, body))
    assert px(pic, 10, 10) == RED and px(pic, 10, 19) == RED           # not a gradient
    assert px(pic, 40, 10) == BLUE
    assert px(pic, 70, 10) == RED
    assert px(pic, 10, 30) == RED
    assert px(pic, 10, 70) == GREEN                                    # the colour written after an unknown url


def test_a_pattern_fill_uses_its_first_colour(tmp_path):
    body = ('<defs><pattern id="dots" width="10" height="10" patternUnits="userSpaceOnUse">'
            '<circle cx="5" cy="5" r="3" fill="blue"/></pattern></defs>'
            '<rect width="40" height="40" fill="url(#dots)"/>')
    pic = p.load_svg(write(tmp_path, body))
    assert px(pic, 20, 20) == BLUE and px(pic, 31, 31) == BLUE        # solid, with no dots


def test_text_images_filters_masks_and_clips_are_ignored_without_error(tmp_path):
    body = ('<text x="10" y="40" font-size="30" fill="red">Hello</text>'
            '<image x="0" y="0" width="50" height="50" xlink:href="missing.png"/>'
            '<filter id="blur"><feGaussianBlur stdDeviation="3"/></filter>'
            '<mask id="m"><rect width="100" height="100" fill="white"/></mask>'
            '<symbol id="s"><rect width="50" height="50" fill="red"/></symbol>'
            '<marker id="mk"><circle r="20" fill="red"/></marker>'
            '<rect x="60" y="60" width="30" height="30" fill="blue" filter="url(#blur)" mask="url(#m)"/>')
    pic = p.load_svg(write(tmp_path, body))
    assert px(pic, 20, 20) == CLEAR and px(pic, 30, 35) == CLEAR       # nothing from text, image, mask, symbol, marker
    assert px(pic, 75, 75) == BLUE                                     # the shape itself still draws


def test_a_symbol_is_drawn_only_where_it_is_used(tmp_path):
    body = '<symbol id="s"><rect width="20" height="20" fill="red"/></symbol><use href="#s" x="50" y="50"/>'
    pic = p.load_svg(write(tmp_path, body))
    assert px(pic, 10, 10) == CLEAR and px(pic, 60, 60) == RED


# ---- the picture it makes ----------------------------------------------------------------------------
def test_the_picture_keeps_a_vector_drawing_history(tmp_path):
    pic = p.load_svg(write(tmp_path, '<rect width="20" height="20" fill="red" stroke="blue"/>'))
    snap = pic._snapshot()
    assert snap.history is not None
    names = [type(op).__name__ for op in snap.history if type(op).__name__ not in ("Save", "Restore")]
    assert names == ["FillPath", "StrokePath"]                          # one fill, one stroke


def test_state_is_back_to_the_defaults_after_loading(tmp_path):
    pic = p.load_svg(write(tmp_path, '<rect width="20" height="20" fill="red" stroke="blue" stroke-width="7" stroke-dasharray="3"/>'))
    style = pic._sketch.style
    assert style.fill.rgb == (255, 255, 255) and style.stroke.rgb == (0, 0, 0)
    assert style.stroke_width == 1 and style.dash == () and style.stroke_cap == "round"


def test_the_picture_can_be_drawn_on_like_any_picture(tmp_path):
    pic = p.load_svg(write(tmp_path, '<rect width="20" height="20" fill="red"/>'))
    pic.no_stroke()
    pic.fill("blue")
    pic.rect(50, 50, 10, 10)
    assert px(pic, 10, 10) == RED and px(pic, 55, 55) == BLUE


def test_pictures_are_named_from_the_same_counter(tmp_path):
    fresh()
    first = p.create_graphics(10, 10)
    second = p.load_svg(write(tmp_path, ""))
    assert (first.name, second.name) == ("graphics-1", "graphics-2")


def test_it_draws_in_the_window_at_any_size(tmp_path):
    s = fresh(200, 120)
    pic = p.load_svg(write(tmp_path, '<rect x="10" y="10" width="40" height="40" fill="red"/>', 'width="60" height="60"'))
    s.run_namespace({"draw": lambda: (p.background("white"), p.image(pic, 0, 0), p.image(pic, 70, 0, 120, 120))}, max_frames=1)
    (w, _h), rgb = s.last_frame

    def at(x, y):
        return tuple(rgb[(y * w + x) * 3:(y * w + x) * 3 + 3])

    assert at(30, 30) == (255, 0, 0)
    assert at(70 + 60, 60) == (255, 0, 0)
    assert at(70 + 10, 60) == (255, 255, 255) and at(70 + 110, 60) == (255, 255, 255)    # outside the big rect
    assert at(70 + 25, 25) == (255, 0, 0) and at(70 + 95, 95) == (255, 0, 0)             # its corners, scaled by 2


def test_it_stays_vector_in_a_pdf(tmp_path):
    s = fresh(120, 120)
    pic = p.load_svg(write(tmp_path, '<path d="M 10 10 L 90 10 L 50 90 Z" fill="red"/><circle cx="30" cy="70" r="15" fill="blue"/>'))
    out = tmp_path / "out.pdf"

    def draw():
        p.background("white")
        p.image(pic, 0, 0)
        p.save(str(out))

    s.run_namespace({"draw": draw}, max_frames=1)
    data = out.read_bytes()
    assert b"/Subtype /Image" not in data
    # Keep the line end before "endstream": compressed data may itself end in a CR or LF byte, and
    # cutting it off made this test fail at random. decompressobj ignores what follows the stream.
    streams = [zlib.decompressobj().decompress(m) for m in re.findall(rb"stream\r?\n(.*?)endstream", data, re.S)
               if m[:1] == b"x"]
    content = b"\n".join(streams) if streams else data
    for operator in (rb"m", rb"l", rb"c"):                              # move, line and curve operators
        assert re.search(rb"\d " + operator + rb"\s", content), operator


def test_it_stays_vector_in_an_svg_file(tmp_path):
    s = fresh(120, 120)
    pic = p.load_svg(write(tmp_path, '<path d="M 10 10 L 90 10 L 50 90 Z" fill="red"/>'))
    out = tmp_path / "out.svg"

    def draw():
        p.background("white")
        p.image(pic, 0, 0)
        p.save(str(out))

    s.run_namespace({"draw": draw}, max_frames=1)
    text = out.read_text(encoding="utf-8")
    assert "<image" not in text and "<path" in text


# ---- svg_paths ---------------------------------------------------------------------------------------
def test_svg_paths_gives_one_path_per_shape_in_order(tmp_path):
    body = ('<rect x="10" y="20" width="30" height="40"/>'
            '<g transform="translate(100 0)"><circle cx="20" cy="20" r="10"/></g>'
            '<polyline points="0,0 10,10 20,0" fill="none" stroke="black"/>'
            '<text>ignored</text>')
    paths = p.svg_paths(write(tmp_path, body, 'width="200" height="100"'))
    assert len(paths) == 3
    assert all(isinstance(shape, p.path().__class__) for shape in paths)
    x, y, w, h = paths[0].bounds()
    assert (x, y, w, h) == pytest.approx((10, 20, 30, 40))
    cx, cy, cw, ch = paths[1].bounds()
    assert (cx, cy, cw, ch) == pytest.approx((110, 10, 20, 20), abs=0.1)         # the transform is applied
    assert paths[0].is_closed and not paths[2].is_closed


def test_svg_paths_uses_the_viewbox_scaling_and_turns_arcs_into_cubics(tmp_path):
    path = write(tmp_path, '<path d="M 0 0 A 5 5 0 0 1 10 0 Z"/>', 'width="100" height="100" viewBox="0 0 10 10"')
    (shape,) = p.svg_paths(path)
    kinds = {seg[0] for seg in shape.geometry.segments}
    assert kinds <= {"move", "line", "cubic", "close"} and "cubic" in kinds
    assert shape.bounds()[2] == pytest.approx(100, abs=0.5)


def test_svg_paths_work_with_booleans_and_contains(tmp_path):
    shapes = p.svg_paths(write(tmp_path, '<rect width="60" height="60"/><rect x="30" y="30" width="60" height="60"/>'))
    both = shapes[0] & shapes[1]
    assert both.bounds() == pytest.approx((30, 30, 30, 30))
    assert shapes[0].contains(10, 10) and not shapes[0].contains(80, 80)


def test_svg_paths_keeps_the_hole_of_an_evenodd_shape_out_of_the_geometry_but_in_the_path_data(tmp_path):
    (shape,) = p.svg_paths(write(tmp_path, f'<path {HOLE} fill-rule="evenodd"/>'))
    assert len([seg for seg in shape.geometry.segments if seg[0] == "move"]) == 2


def test_svg_paths_gives_an_evenodd_shape_with_its_hole_open(tmp_path):
    """P11: the returned path fills like the SVG, so the hole stays empty with draw_path and contains."""
    (shape,) = p.svg_paths(write(tmp_path, f'<path {HOLE} fill-rule="evenodd"/>'))
    x, y, w, h = shape.bounds()
    assert not shape.contains(x + w / 2, y + h / 2)
    assert shape.contains(x + 1, y + 1)


def test_svg_paths_returns_a_list_of_independent_builders(tmp_path):
    path = write(tmp_path, '<rect width="10" height="10"/>')
    first, second = p.svg_paths(path), p.svg_paths(path)
    assert first is not second and first[0] is not second[0]
    first[0].move_to(5, 5)
    assert len(second[0]) != len(first[0])


# ---- errors --------------------------------------------------------------------------------------------
def test_a_missing_file_is_file_not_found(tmp_path):
    with pytest.raises(FileNotFoundError, match="nope.svg"):
        p.load_svg(str(tmp_path / "nope.svg"))
    with pytest.raises(FileNotFoundError, match="nope.svg"):
        p.svg_paths(str(tmp_path / "nope.svg"))


@pytest.mark.parametrize("text", [
    "this is not xml at all",
    "<html><body>hello</body></html>",
    "<svg xmlns='http://www.w3.org/2000/svg' width='10'",
    "",
])
def test_a_file_that_is_not_svg_is_a_value_error(tmp_path, text):
    path = tmp_path / "x.svg"
    path.write_text(text, encoding="utf-8")
    with pytest.raises(ValueError, match="not an SVG"):
        p.load_svg(str(path))
    with pytest.raises(ValueError, match="not an SVG"):
        p.svg_paths(str(path))


def test_an_image_file_is_a_value_error(tmp_path):
    path = tmp_path / "x.svg"
    path.write_bytes(b"\x89PNG\r\n\x1a\n\x00\x00")
    with pytest.raises(ValueError):
        p.load_svg(str(path))


def test_load_image_on_an_svg_points_to_load_svg(tmp_path):
    with pytest.raises(ValueError, match=r"f\.load_svg\(\)"):
        p.load_image(write(tmp_path, ""))


def test_odd_shapes_do_not_stop_the_rest_loading(tmp_path):
    body = ('<path d="M 10 10 L oops"/>'
            '<rect width="-5" height="10" fill="red"/>'
            '<circle r="0" fill="red"/>'
            '<path d="M 0 0 A 0 0 0 0 1 10 10" fill="none" stroke="red"/>'
            '<rect x="40" y="40" width="20" height="20" fill="blue"/>')
    pic = p.load_svg(write(tmp_path, body))
    assert px(pic, 50, 50) == BLUE


# ---- where the file is looked for (P4, T11) and before size() --------------------------------------------
def run_text(path, text):
    path.write_text(text, encoding="utf-8")
    return run_sketch(path, frames=2)


def test_a_relative_path_is_found_next_to_the_sketch_file_first(tmp_path, monkeypatch):
    sketch_dir, other = tmp_path / "sketch", tmp_path / "elsewhere"
    sketch_dir.mkdir(), other.mkdir()
    write(sketch_dir, '<rect width="60" height="40" fill="red"/>', 'width="60" height="40"', "pic.svg")
    write(other, '<rect width="60" height="40" fill="lime"/>', 'width="60" height="40"', "pic.svg")
    monkeypatch.chdir(other)
    (w, _h), rgb = run_text(sketch_dir / "s.py", (
        "import funground as f\n"
        "pic = f.load_svg('pic.svg')\n"
        "shapes = f.svg_paths('pic.svg')\n"
        "def setup():\n    f.size(60, 40)\n"
        "def draw():\n    f.image(pic, 0, 0)\n"
        "f.run()\n"))
    assert tuple(rgb[(20 * w + 20) * 3:(20 * w + 20) * 3 + 3]) == (255, 0, 0)           # not the lime one


def test_then_the_current_folder(tmp_path, monkeypatch):
    sketch_dir, other = tmp_path / "sketch", tmp_path / "elsewhere"
    sketch_dir.mkdir(), other.mkdir()
    write(other, '<rect width="60" height="40" fill="red"/>', 'width="60" height="40"', "only_here.svg")
    monkeypatch.chdir(other)
    (w, _h), rgb = run_text(sketch_dir / "s.py", (
        "import funground as f\n"
        "def setup():\n    f.size(60, 40)\n"
        "def draw():\n    f.image(f.load_svg('only_here.svg'), 0, 0)\n"
        "f.run()\n"))
    assert tuple(rgb[(20 * w + 20) * 3:(20 * w + 20) * 3 + 3]) == (255, 0, 0)


def test_a_missing_relative_file_names_both_places(tmp_path, monkeypatch):
    sketch_dir, other = tmp_path / "sketch", tmp_path / "elsewhere"
    sketch_dir.mkdir(), other.mkdir()
    monkeypatch.chdir(other)
    with pytest.raises(FileNotFoundError) as caught:
        run_text(sketch_dir / "s.py", "import funground as f\nf.load_svg('nope.svg')\nf.size(10, 10)\n")
    message = str(caught.value)
    assert str(sketch_dir) in message and str(other) in message and "nope.svg" in message


def test_it_works_before_size_is_called(tmp_path):
    script_sketch()
    pic = p.load_svg(write(tmp_path, '<rect width="20" height="20" fill="red"/>'))
    assert (pic.width, pic.height) == (100, 100) and px(pic, 10, 10) == RED
    assert len(p.svg_paths(write(tmp_path, '<rect width="20" height="20"/>', name="b.svg"))) == 1
