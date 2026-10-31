"""f.COLORS and f.CONSTANTS (S-174, D-103): names whose values are the strings the functions already accept.

Checked in both directions: every group holds exactly the words its functions accept, and each ``Literal`` type
(what the editor suggests) equals the table in the code that validates the word.
"""
from __future__ import annotations

import importlib.util
import sys
import typing

import pytest

import funground as f
from funground import sound
from conftest import ROOT
from funground import _colornames, _options, color as _color_function, pages  # noqa: F401
from funground.sound import _synth as synth
from funground import marks, typography, web_fonts
from funground._namespaces import NAMESPACE_NAMES
from funground.export import TEXT_MODES
from funground.imaging import FILTER_KINDS
from funground.platform.base import CURSOR_KINDS, KEY_NAMES, MOUSE_BUTTONS
from funground.sketch import Sketch

_color = sys.modules["funground.color"]

_spec = importlib.util.spec_from_file_location("make_api_reference", ROOT / "tools" / "make_api_reference.py")
tool = importlib.util.module_from_spec(_spec)
sys.modules["make_api_reference"] = tool
_spec.loader.exec_module(tool)

PAGES = tuple(name for name in pages.PAGE_SIZES if name != "Square")   # "Square" is also a cap and a wave; strings still work

# (function, parameter) -> (the words the code accepts, the Literal type of that parameter)
ACCEPTED: dict[tuple[str, str], tuple[tuple[str, ...], object]] = {
    ("rect_mode", "mode"): (Sketch.RECT_MODES, _options.RectMode),
    ("ellipse_mode", "mode"): (Sketch.ELLIPSE_MODES, _options.EllipseMode),
    ("image_mode", "mode"): (Sketch.IMAGE_MODES, _options.ImageMode),
    ("arc", "mode"): (Sketch.ARC_MODES, _options.ArcMode),
    ("color_mode", "mode"): (_color.COLOR_MODES, _options.ColorMode),
    ("text_align", "horizontal"): (tuple(Sketch.TEXT_ALIGNS), _options.TextAlignX),
    ("text_align", "vertical"): (tuple(Sketch.TEXT_VALIGNS), _options.TextAlignY),
    ("text_style", "style"): (tuple(typography.TEXT_STYLES), _options.TextStyle),
    ("FormattedString.append", "style"): (tuple(typography.TEXT_STYLES), _options.TextStyle),
    ("stroke_cap", "cap"): (tuple(Sketch.STROKE_CAPS), _options.StrokeCap),
    ("PathBuilder.expand_stroke", "cap"): (tuple(Sketch.STROKE_CAPS), _options.StrokeCap),
    ("stroke_join", "join"): (tuple(Sketch.STROKE_JOINS), _options.StrokeJoin),
    ("PathBuilder.expand_stroke", "join"): (tuple(Sketch.STROKE_JOINS), _options.StrokeJoin),
    ("cursor", "kind"): (tuple(CURSOR_KINDS), _options.CursorKind),
    ("blend_mode", "mode"): (tuple(Sketch.BLEND_MODES), _options.BlendMode),
    ("filter", "kind"): (tuple(FILTER_KINDS), _options.FilterKind),
    ("apply_filter", "kind"): (tuple(FILTER_KINDS), _options.FilterKind),
    ("sound.tone", "wave"): (tuple(synth.WAVES), _options.Wave),
    ("sound.note", "wave"): (tuple(synth.WAVES), _options.Wave),
    ("sound.melody", "wave"): (tuple(synth.WAVES), _options.Wave),
    ("sound.melody", "tuning"): (("equal", "just"), _options.Tuning),          # no table in the code: an inline tuple
    ("Mark.place", "anchor"): (tuple(marks.ANCHORS), _options.MarkAnchor),
    ("Mark.place", "style"): (("own", "current"), _options.MarkStyle),   # no table in the code: an inline tuple
    ("load_font", "provider"): (web_fonts.PROVIDER_WORDS, _options.Provider),
    ("save", "text"): (TEXT_MODES, _options.SaveText),
    ("Picture.save", "text"): (TEXT_MODES, _options.SaveText),
    ("key_down", "key"): (tuple(KEY_NAMES), _options.KeyName),
    ("key", "value"): (tuple(KEY_NAMES), _options.KeyName),
    ("mouse_button", "value"): (MOUSE_BUTTONS, None),                    # a value you read, not a parameter
    ("size", "width"): (PAGES, _options.PageName),
    ("new_page", "width"): (PAGES, _options.PageName),
    ("page_size", "name"): (PAGES, _options.PageName),
}


def groups() -> dict:
    return f.CONSTANTS._members


def test_the_two_names_are_public_and_in_the_star_import():
    assert set(NAMESPACE_NAMES) == {"COLORS", "CONSTANTS"} <= set(f._PUBLIC_NAMES) and set(NAMESPACE_NAMES) <= set(f.__all__)
    namespace: dict = {}
    exec("from funground import *", namespace)
    assert namespace["COLORS"] is f.COLORS and namespace["CONSTANTS"] is f.CONSTANTS
    assert namespace["COLORS"].TOMATO == "tomato" and namespace["CONSTANTS"].ALIGN.CENTER == "center"


def test_colors_has_a_name_for_every_named_colour():
    assert len(f.COLORS) == len(_colornames.NAMED_COLORS) == 665
    assert {name: value for name, value in f.COLORS._members.items()} == {n.upper(): n for n in _colornames.NAMED_COLORS}
    assert f.COLORS.TOMATO == "tomato" and f.COLORS.ANTIQUEWHITE1 == "antiquewhite1" and f.COLORS.GRAY50 == "gray50"
    assert list(f.COLORS) == sorted(_colornames.NAMED_COLORS)
    assert "tomato" in f.COLORS and "nonsense" not in f.COLORS


def test_every_group_is_listed_in_the_tool_and_the_other_way_round():
    assert list(groups()) == list(tool.GROUP_PARAMS)
    assert len(groups()) == 19
    assert all(isinstance(group, type) for group in groups().values())


@pytest.mark.parametrize("group", list(tool.GROUP_PARAMS))
def test_a_group_holds_exactly_the_words_its_functions_accept(group):
    accepted: list[str] = []
    for key in tool.GROUP_PARAMS[group]:
        assert key in ACCEPTED, f"{key} has no row in ACCEPTED"
        accepted += [w for w in ACCEPTED[key][0] if w not in accepted]
    assert set(groups()[group]._members.values()) == set(accepted), group
    assert list(groups()[group]) == list(groups()[group]._members.values())


def test_every_option_parameter_is_in_a_group():
    in_groups = {key for keys in tool.GROUP_PARAMS.values() for key in keys}
    assert in_groups == set(ACCEPTED)


@pytest.mark.parametrize("key", [k for k, (_, literal) in ACCEPTED.items() if literal is not None])
def test_the_literal_type_lists_the_words_the_code_accepts(key):
    words, literal = ACCEPTED[key]
    typed = typing.get_args(literal)
    if literal is _options.PageName:
        typed = tuple(w for w in typed if w != "Square")
    assert set(typed) == set(words) and len(typed) == len(set(typed)), key


def test_the_annotations_use_those_types():
    import inspect

    for (name, parameter), (_, literal) in ACCEPTED.items():
        library = name.startswith("sound.")                    # the sound library's functions (S-246)
        if literal is None or ("." in name and not library) or parameter == "value":
            continue
        function = getattr(sound, name.removeprefix("sound.")) if library else getattr(f, name)
        annotation = inspect.signature(function).parameters[parameter].annotation
        alias = next(n for n, value in vars(_options).items() if value is literal)
        assert alias in annotation, f"{name}({parameter}) is annotated {annotation}, not with {alias}"


# One call for each parameter, to prove the real function takes every word (only a ValueError would be wrong here).
CALLS = {
    ("rect_mode", "mode"): lambda w: f.rect_mode(w),
    ("ellipse_mode", "mode"): lambda w: f.ellipse_mode(w),
    ("image_mode", "mode"): lambda w: f.image_mode(w),
    ("arc", "mode"): lambda w: f.arc(50, 50, 40, 40, 0, 90, w),
    ("color_mode", "mode"): lambda w: f.color_mode(w),
    ("text_align", "horizontal"): lambda w: f.text_align(w),
    ("text_align", "vertical"): lambda w: f.text_align("left", w),
    ("text_style", "style"): lambda w: f.text_style(w),
    ("FormattedString.append", "style"): lambda w: f.FormattedString().append("x", style=w),
    ("stroke_cap", "cap"): lambda w: f.stroke_cap(w),
    ("PathBuilder.expand_stroke", "cap"): lambda w: f.path().move_to(0, 0).line_to(10, 0).expand_stroke(2, cap=w),
    ("stroke_join", "join"): lambda w: f.stroke_join(w),
    ("PathBuilder.expand_stroke", "join"): lambda w: f.path().move_to(0, 0).line_to(10, 0).expand_stroke(2, join=w),
    ("blend_mode", "mode"): lambda w: f.blend_mode(w),
    ("sound.tone", "wave"): lambda w: sound.tone(440, 0.05, w),
    ("sound.note", "wave"): lambda w: sound.note("C4", 0.05, w),
    ("sound.melody", "wave"): lambda w: sound.melody("C4", wave=w),
    ("sound.melody", "tuning"): lambda w: sound.melody("S R", tuning=w, sa="C4"),
    ("key_down", "key"): lambda w: f.key_down(w),
    ("page_size", "name"): lambda w: f.page_size(w),
}


@pytest.mark.parametrize("key", list(CALLS))
def test_every_group_word_the_parameter_takes_is_accepted_by_the_function(key, canvas):
    group = next(g for g, keys in tool.GROUP_PARAMS.items() if key in keys)
    for word in groups()[group]:
        if word not in ACCEPTED[key][0]:
            continue                                    # a word of the group that this parameter does not take
        try:
            CALLS[key](word)
        except ValueError as error:
            pytest.fail(f"{key[0]}({word!r}) was refused: {error}")


def test_a_group_word_a_function_does_not_take_is_still_refused_when_it_runs(canvas):
    assert f.CONSTANTS.MODE.RADIUS == "radius"
    with pytest.raises(ValueError):
        f.image_mode(f.CONSTANTS.MODE.RADIUS)


def test_a_constant_does_what_its_string_does(canvas):
    f.background(f.COLORS.WHITE)
    f.no_stroke()
    f.fill(f.COLORS.TOMATO)
    f.rect(0, 0, 50, 50)
    f.fill("tomato")
    f.rect(100, 0, 50, 50)
    assert canvas.get_at((10, 10)) == canvas.get_at((110, 10)) != canvas.get_at((75, 10))


def test_text_align_takes_a_constant(canvas):
    f.text_align(f.CONSTANTS.ALIGN.CENTER)
    f.text_align(f.CONSTANTS.ALIGN.CENTER, f.CONSTANTS.ALIGN.BASELINE)
    f.blend_mode(f.CONSTANTS.BLEND.MULTIPLY)
    f.rect_mode(f.CONSTANTS.MODE.CENTER)


def test_everything_is_read_only():
    for namespace in (f.COLORS, f.CONSTANTS, f.CONSTANTS.ALIGN):
        with pytest.raises(AttributeError, match="cannot be changed"):
            namespace.NEW = "x"
        with pytest.raises(AttributeError, match="cannot be changed"):
            del namespace.NEW
    with pytest.raises(AttributeError, match="cannot be changed"):
        f.COLORS.TOMATO = "red"
    with pytest.raises(AttributeError, match="my_red"):
        f.CONSTANTS.ALIGN.LEFT = "x"
    assert f.COLORS.TOMATO == "tomato" and f.CONSTANTS.ALIGN.LEFT == "left"


def test_they_cannot_be_made():
    with pytest.raises(TypeError):
        f.COLORS()
    with pytest.raises(TypeError):
        f.CONSTANTS.ALIGN()


def test_iteration_length_and_membership():
    assert list(f.CONSTANTS.MOUSE) == ["left", "center", "right"]
    assert len(f.CONSTANTS.BLEND) == 17 and "multiply" in f.CONSTANTS.BLEND and "wide" not in f.CONSTANTS.BLEND
    assert list(f.CONSTANTS) == list(groups().values())          # CONSTANTS yields its groups
    assert len(f.CONSTANTS) == 19
    assert f.CONSTANTS.ANCHOR.TOP_LEFT == "top-left"
    assert f.CONSTANTS.PAGE.LETTER == "Letter" and f.CONSTANTS.PAGE.A4 == "A4"
    assert "COLORS" in repr(f.COLORS) and "ALIGN" in repr(f.CONSTANTS) and "BLEND" in repr(f.CONSTANTS)
    assert "LEFT" in repr(f.CONSTANTS.ALIGN)


def test_a_misspelt_name_says_did_you_mean():
    with pytest.raises(AttributeError, match=r"Did you mean TOMATO\?"):
        f.COLORS.TOMATOE
    with pytest.raises(AttributeError, match=r"Did you mean CENTER\?"):
        f.CONSTANTS.ALIGN.CENTRE
    with pytest.raises(AttributeError, match=r"Did you mean ALIGN\?"):
        f.CONSTANTS.ALLIGN
    with pytest.raises(AttributeError, match=r"Did you mean TOMATO\?"):
        f.COLORS.tomato                                           # lower case is the same word, in capitals
    with pytest.raises(AttributeError, match="no name 'ZZZZZZ'"):
        f.COLORS.ZZZZZZ


def test_holding_only_the_two_names_is_not_the_global_style():
    from funground import global_style

    assert not global_style.uses_global_style({"COLORS": f.COLORS, "CONSTANTS": f.CONSTANTS})
    assert global_style.clash_note({"circle": f.circle, "COLORS": ["red"]}) is None


def test_the_generated_colour_class_is_current():
    assert (ROOT / "funground" / "_color_names_class.py").read_bytes() == tool.colors_class_text().encode("utf-8")
