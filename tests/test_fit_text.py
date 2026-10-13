"""A headline that fits (story S-162, contract row T21): f.fit_text_size(message, width, height=None)."""
from __future__ import annotations

import pytest

import funground as p
from funground import api, typography
from funground.web import Session

from fontmaker import make_variable_font


def width_at(message: str, size: float) -> float:
    """The widest line of *message* when set at *size* in the current state, measured directly."""
    style = api.active_sketch().style
    return max(typography.text_width(line, size, typography.effective_font(style),
                                     **typography.text_settings(style)) for line in message.split("\n"))


@pytest.fixture(autouse=True)
def _isolated_font_registry():
    saved, saved_paths = dict(typography._registry), dict(typography._path_to_key)
    yield
    typography._registry.clear()
    typography._registry.update(saved)
    typography._path_to_key.clear()
    typography._path_to_key.update(saved_paths)


@pytest.mark.parametrize("style", typography.TEXT_STYLES)
@pytest.mark.parametrize("tracking", [0, 6, -1.5])
@pytest.mark.parametrize("target", [120, 480.5])
def test_text_set_at_the_returned_size_is_the_width(canvas, style, tracking, target):
    p.text_style(style)
    p.text_tracking(tracking)
    size = p.fit_text_size("Spring Fair", target)
    assert abs(width_at("Spring Fair", size) - target) < 0.5
    assert width_at("Spring Fair", size + 0.01) > target - 0.5          # it is the largest size, not just a close one


def test_it_allows_for_features(canvas):
    p.text_features(liga=False)
    plain = p.fit_text_size("office waffle", 300)
    assert abs(width_at("office waffle", plain) - 300) < 0.5
    p.text_features(liga=True)
    ligatured = p.fit_text_size("office waffle", 300)
    assert abs(width_at("office waffle", ligatured) - 300) < 0.5


def test_it_allows_for_variations(canvas, tmp_path):
    p.text_font(p.load_font(make_variable_font(tmp_path)))
    p.font_variations(wght=100)
    light = p.fit_text_size("HEADLINE", 200)
    p.font_variations(wght=900)
    heavy = p.fit_text_size("HEADLINE", 200)
    assert abs(width_at("HEADLINE", heavy) - 200) < 0.5
    assert light != heavy


def test_tracking_is_a_fixed_space_not_scaled(canvas):
    plain = p.fit_text_size("Fit", 300)
    p.text_tracking(20)
    spaced = p.fit_text_size("Fit", 300)
    assert spaced < plain
    assert abs(width_at("Fit", spaced) - 300) < 0.5


def test_several_lines_are_fitted_by_their_widest(canvas):
    size = p.fit_text_size("Hi\nA much longer line", 250)
    assert abs(width_at("A much longer line", size) - 250) < 0.5
    assert width_at("Hi", size) < 250


def test_the_height_can_be_what_limits_the_size(canvas):
    wide_only = p.fit_text_size("one\ntwo\nthree", 900)
    size = p.fit_text_size("one\ntwo\nthree", 900, 150)
    assert size < wide_only
    ascent, descent = typography.text_metrics(size, typography.default_font())
    assert ascent + descent + size * 1.25 * 2 == pytest.approx(150, abs=0.1)     # the last line's bottom touches it


def test_the_height_uses_the_current_leading(canvas):
    p.text_leading(100)
    size = p.fit_text_size("one\ntwo", 900, 150)
    ascent, descent = typography.text_metrics(size, typography.default_font())
    assert ascent + descent + 100 == pytest.approx(150, abs=0.1)


def test_a_roomy_height_leaves_the_width_in_charge(canvas):
    assert p.fit_text_size("Wide", 200, 5000) == pytest.approx(p.fit_text_size("Wide", 200), abs=0.002)


def test_it_does_not_change_the_drawing_state(canvas):
    p.text_size(33)
    p.fit_text_size("Hello", 300)
    assert api.active_sketch().style.text_size == 33


@pytest.mark.parametrize("width, height", [(0, None), (-5, None), (100, 0), (100, -1), (float("inf"), None)])
def test_width_and_height_must_be_above_zero(canvas, width, height):
    with pytest.raises(ValueError, match="above 0"):
        p.fit_text_size("Hello", width, height)


@pytest.mark.parametrize("message", ["", "\n\n"])
def test_empty_text_is_an_error(canvas, message):
    with pytest.raises(ValueError, match="no letters"):
        p.fit_text_size(message, 100)


def test_wrong_kinds_of_value(canvas):
    with pytest.raises(TypeError, match="width"):
        p.fit_text_size("Hello", "wide")
    with pytest.raises(TypeError, match="height"):
        p.fit_text_size("Hello", 100, True)


def test_a_formatted_string_is_refused_clearly(canvas):
    with pytest.raises(TypeError, match="FormattedString"):
        p.fit_text_size(p.FormattedString().append("Hello"), 100)


def test_tracking_too_wide_for_the_space_says_so(canvas):
    p.text_tracking(50)
    with pytest.raises(ValueError, match="tracking"):
        p.fit_text_size("Hello", 100)

def run_in_session(source, width, height):
    """Run a script as the browser runner does; the host always ends a Session with stop() (web.py)."""
    session = Session(width, height)
    try:
        session.start(source, "sketch.py")
    finally:
        session.stop()


def test_it_works_under_a_web_session(tmp_path):
    answer = tmp_path / "size.txt"
    source = f"""
import funground as f
f.size(400, 200)
open({str(answer)!r}, "w").write(repr(f.fit_text_size("Spring Fair", 300)))
f.show()
"""
    run_in_session(source, 400, 200)
    assert float(answer.read_text()) > 0
