"""Fonts and text styles (S-054, contract T11/T12)."""
from __future__ import annotations

import shutil

import pytest

from funground import api, ir, typography
from funground.color import BLACK
from funground.state import GraphicsState

from conftest import ROOT

FONTS_DIR = ROOT / "funground" / "fonts"
BOLD = FONTS_DIR / "DejaVuSans-Bold.ttf"
ITALIC = FONTS_DIR / "DejaVuSans-Oblique.ttf"
BOLD_ITALIC = FONTS_DIR / "DejaVuSans-BoldOblique.ttf"
MONO = ROOT / "examples" / "gallery" / "text" / "fonts" / "DejaVuSansMono.ttf"


@pytest.fixture(autouse=True)
def _isolated_font_registry():
    """Each test gets its own registry, so key assignment ("name", "name~2", ...) never
    depends on what other tests (or other modules run in the same session) loaded first."""
    saved_registry = dict(typography._registry)
    saved_paths = dict(typography._path_to_key)
    typography._registry.clear()
    typography._path_to_key.clear()
    yield
    typography._registry.clear()
    typography._registry.update(saved_registry)
    typography._path_to_key.clear()
    typography._path_to_key.update(saved_paths)


# ---------------------------------------------------------------- built-in styles (T12)
def test_each_built_in_style_shapes_with_its_own_bundled_file():
    for style, filename in typography.STYLE_FILES.items():
        font = typography.effective_font(GraphicsState(text_style=style))
        assert font.path.endswith(filename)


def test_bold_text_is_wider_than_normal():
    import funground as p

    p.text_size(24)
    p.text_style("normal")
    normal_width = p.text_width("Hello")
    p.text_style("bold")
    bold_width = p.text_width("Hello")
    assert bold_width > normal_width


def test_unknown_text_style_lists_the_four_choices():
    import funground as p

    with pytest.raises(ValueError) as excinfo:
        p.text_style("heavy")
    message = str(excinfo.value)
    for name in typography.TEXT_STYLES:
        assert name in message


# ---------------------------------------------------------------- saved_state (F2)
def test_text_style_and_font_are_saved_and_restored(canvas):
    import funground as p

    p.text_style("bold")
    with p.saved_state():
        font = p.load_font(str(BOLD_ITALIC))
        p.text_font(font)
        p.text_style("italic")           # remembered, though ignored while font is loaded
        assert api.active_sketch().style.font == font.name
        assert api.active_sketch().style.text_style == "italic"
    state = api.active_sketch().style
    assert state.font is None
    assert state.text_style == "bold"


# ---------------------------------------------------------------- relative path resolution (T11)
def test_relative_path_resolves_next_to_the_sketch_file(tmp_path):
    from funground.sketch import Sketch

    sketch_dir = tmp_path / "sketch_folder"
    sketch_dir.mkdir()
    shutil.copy(BOLD, sketch_dir / "Rel.ttf")

    s = Sketch()
    font = s.load_font("Rel.ttf", base_dir=str(sketch_dir))
    assert font.name == "Rel.ttf"


def test_relative_path_falls_back_to_the_current_folder(tmp_path, monkeypatch):
    from funground.sketch import Sketch

    shutil.copy(BOLD, tmp_path / "Cwd.ttf")
    monkeypatch.chdir(tmp_path)

    s = Sketch()
    font = s.load_font("Cwd.ttf")
    assert font.name == "Cwd.ttf"


def test_api_load_font_resolves_relative_to_the_caller_sketch_file(tmp_path, monkeypatch):
    """f.load_font() finds the calling sketch's __file__ from the caller frame's globals,
    the same way f.run() finds the sketch namespace (contract T11)."""
    sketch_dir = tmp_path / "mysketch"
    sketch_dir.mkdir()
    shutil.copy(BOLD, sketch_dir / "Rel2.ttf")
    script = sketch_dir / "sketch.py"
    script.write_text(
        "import funground as f\nfont = f.load_font('Rel2.ttf')\n", encoding="utf-8"
    )

    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)

    namespace = {"__name__": "__sketch_under_test__", "__file__": str(script)}
    exec(compile(script.read_text(encoding="utf-8"), str(script), "exec"), namespace)
    assert namespace["font"].name == "Rel2.ttf"


# ---------------------------------------------------------------- errors (T11)
def test_missing_file_names_both_places_looked(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    beside = tmp_path / "beside_the_sketch"
    with pytest.raises(FileNotFoundError) as excinfo:
        typography.load_font("nope.ttf", base_dir=str(beside))
    message = str(excinfo.value)
    assert str(beside / "nope.ttf") in message
    assert str(tmp_path / "nope.ttf") in message


def test_non_font_file_raises_value_error(tmp_path):
    bad = tmp_path / "notafont.ttf"
    bad.write_text("this is plain text, not a font", encoding="utf-8")
    with pytest.raises(ValueError):
        typography.load_font(str(bad))


# ---------------------------------------------------------------- a loaded font (T11/T12)
def test_loaded_font_measures_differently_and_ignores_text_style():
    import funground as p

    p.text_size(24)
    p.text_style("bold")
    bold_width = p.text_width("Hello")

    mono = p.load_font(str(MONO))
    p.text_font(mono)
    mono_width = p.text_width("Hello")
    assert mono_width != bold_width

    p.text_style("italic")               # has no effect while a font is loaded (T12)
    assert p.text_width("Hello") == mono_width

    p.text_font(None)                    # back to the built-in family
    expected = typography.text_width(
        "Hello", 24, typography.effective_font(GraphicsState(text_style="italic"))
    )
    assert p.text_width("Hello") == expected      # the remembered style (italic) applies again


# ---------------------------------------------------------------- IR (T11)
def test_default_font_and_style_omitted_from_the_ir():
    op = ir.Text("Hi", 0, 0, BLACK, GraphicsState())
    data = ir.op_to_jsonable(op)
    assert "font" not in data["style"] and "text_style" not in data["style"]
    assert ir.op_from_jsonable(data) == op


def test_loaded_font_recorded_as_its_file_name_and_round_trips():
    import funground as p

    mono = p.load_font(str(MONO))
    p.text_font(mono)
    state = api.active_sketch().style
    op = ir.Text("Hi", 0, 0, BLACK, state)
    data = ir.op_to_jsonable(op)
    assert data["style"]["font"] == "DejaVuSansMono.ttf"
    assert ir.op_from_jsonable(data) == op


def test_two_different_files_with_the_same_name_get_distinct_keys(tmp_path):
    dir_a, dir_b = tmp_path / "a", tmp_path / "b"
    dir_a.mkdir()
    dir_b.mkdir()
    shutil.copy(BOLD, dir_a / "Custom.ttf")
    shutil.copy(ITALIC, dir_b / "Custom.ttf")

    first = typography.load_font(str(dir_a / "Custom.ttf"))
    second = typography.load_font(str(dir_b / "Custom.ttf"))
    assert first.name == "Custom.ttf"
    assert second.name == "Custom.ttf~2"

    again = typography.load_font(str(dir_a / "Custom.ttf"))    # same file again: same key
    assert again.name == "Custom.ttf"


# ---------------------------------------------------------------- export (T11)
def test_pdf_export_of_text_in_a_loaded_font(tmp_path):
    import funground as p

    out = tmp_path / "text.pdf"

    def draw():
        p.background("white")
        p.fill("black")
        font = p.load_font(str(MONO))
        p.text_font(font)
        p.text("Hello, PDF!", 20, 20)
        if p.frame_count == 1:
            p.save(str(out))

    api.active_sketch().run_namespace({"draw": draw}, max_frames=3)
    assert out.exists()
    data = out.read_bytes()
    assert len(data) > 0
    assert data[:5] == b"%PDF-"
