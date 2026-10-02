"""Font information (story S-106; contract row T17)."""
from __future__ import annotations

import pytest

import funground as p
from funground import api, typography
from funground.platform.headless import HeadlessPlatform
from funground.sketch import Sketch
from funground.typography import Font

from fontmaker import make_static_font, make_variable_font


@pytest.fixture(autouse=True)
def sketch():
    s = api.use_sketch(Sketch(platform=HeadlessPlatform()))
    p.size(200, 100)
    saved, saved_paths = dict(typography._registry), dict(typography._path_to_key)
    yield s
    typography._registry.clear()
    typography._registry.update(saved)
    typography._path_to_key.clear()
    typography._path_to_key.update(saved_paths)


def test_built_in_font_names():
    font = p.current_font()
    assert isinstance(font, Font)
    assert font.family() == "DejaVu Sans"
    assert font.style() == "Book"


def test_text_style_changes_the_current_font():
    p.text_style("bold")
    assert p.current_font().style() == "Bold"
    p.text_style("italic")
    assert p.current_font().style() == "Oblique"
    p.text_style("bold_italic")
    assert p.current_font().style() == "Bold Oblique"
    assert p.current_font().family() == "DejaVu Sans"


def test_current_font_after_text_font(tmp_path):
    loaded = p.load_font(make_static_font(tmp_path, name="Boxy"))
    p.text_font(loaded)
    assert p.current_font() == loaded
    assert p.current_font().family() == "Boxy"
    assert p.current_font().style() == "Regular"
    p.text_style("bold")                                  # ignored once a font is loaded (T12)
    assert p.current_font() == loaded
    p.text_font(None)
    assert p.current_font().family() == "DejaVu Sans"


def test_font_object_is_hashable_and_keeps_slots():
    font = p.current_font()
    assert hash(font) == hash(Font(font.name))
    assert {font: 1}[Font(font.name)] == 1
    assert not hasattr(font, "__dict__")
    with pytest.raises(AttributeError):
        font.extra = 1


def test_variations_of_a_variable_font(tmp_path):
    font = p.load_font(make_variable_font(tmp_path))
    assert font.variations() == {"wght": (100.0, 100.0, 900.0)}
    assert font.family() == "TestVar"


def test_variations_of_a_static_font_is_empty(tmp_path):
    assert p.current_font().variations() == {}
    assert p.load_font(make_static_font(tmp_path)).variations() == {}


def test_features_of_dejavu():
    features = p.current_font().features()
    assert features == sorted(set(features))
    assert "liga" in features and "kern" in features


def test_features_of_a_font_without_layout_tables(tmp_path):
    assert p.load_font(make_static_font(tmp_path)).features() == []


def test_contains():
    font = p.current_font()
    assert font.contains("Hello, world")
    assert font.contains("")
    assert font.contains("café")
    assert not font.contains("中")                    # a Chinese character: not in DejaVu Sans
    assert not font.contains("abc中")


def test_contains_spaces_and_control_characters(tmp_path):
    assert p.current_font().contains("a b")               # a space needs a glyph like any letter
    assert p.current_font().contains("one\ntwo")          # a new line is a line break, not a glyph
    assert not p.current_font().contains("\t")            # other control characters are checked
    box = p.load_font(make_static_font(tmp_path))         # letters A to E and a space
    assert box.contains("A B")
    assert not box.contains("AF")
    assert box.contains("A\nB")


def test_asking_changes_no_state(tmp_path):
    p.text_style("bold")
    before = p.current_font()
    before.family(); before.style(); before.variations(); before.features(); before.contains("a")
    assert p.current_font() == before
