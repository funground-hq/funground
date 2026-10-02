"""Font fallback (story S-102; contract row T18, decision D-052 = C).

When the current font lacks a character, the next font in the chain that has it draws it. The chain is
the learner's fonts (`f.text_fallback`), then the bundled Noto Emoji, Noto Sans Symbols 2 and Noto Sans
Devanagari. Tests use fonts generated in the test and the bundled fonts, never the computer's own fonts,
except one `system_font` test against a temporary folder.
"""
from __future__ import annotations

import os
import tomllib
from pathlib import Path as FilePath

import pytest
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont

import funground as p
from funground import api, ir, typography
from funground.platform.headless import HeadlessPlatform
from funground.sketch import Sketch
from funground.state import GraphicsState
from funground.typography import ShapedLine, TextRun

from conftest import ROOT
from fontmaker import make_static_font

EMOJI = "NotoEmoji-Regular.ttf"
DEVANAGARI = "NotoSansDevanagari-Regular.ttf"
HINDI = "नमस्ते"
FAMILY = "\U0001F468\u200d\U0001F469\u200d\U0001F467"
FLAG = "\U0001F1EE\U0001F1F3"
ROCKET = "\U0001F680"
GRIN = "\U0001F600"                      # DejaVu has this one too


@pytest.fixture(autouse=True)
def _isolated_font_registry():
    saved, saved_paths = dict(typography._registry), dict(typography._path_to_key)
    yield
    typography._registry.clear()
    typography._registry.update(saved)
    typography._path_to_key.clear()
    typography._path_to_key.update(saved_paths)


def names(line) -> list[str]:
    return [os.path.basename(run.font.path) for run in line.runs]


def shape(text: str, fallback=(), font=None, size=20):
    return (font or typography.default_font()).shape(text, size, fallback=fallback)


def make_font(folder, name: str, chars: str, ascent: int = 800) -> str:
    """A tiny font with a box glyph for each of *chars* and a space, with the given ascent."""
    order = [".notdef", "space", *(f"u{ord(c):04X}" for c in chars)]
    fb = FontBuilder(1000, isTTF=True)
    fb.setupGlyphOrder(order)
    fb.setupCharacterMap({32: "space", **{ord(c): f"u{ord(c):04X}" for c in chars}})
    glyphs = {}
    for glyph in order:
        pen = TTGlyphPen(None)
        if glyph not in ("space",):
            pen.moveTo((80, 0)); pen.lineTo((80, 700)); pen.lineTo((520, 700)); pen.lineTo((520, 0)); pen.closePath()
        glyphs[glyph] = pen.glyph()
    fb.setupGlyf(glyphs)
    fb.setupHorizontalMetrics({g: (600, 50) for g in order})
    fb.setupHorizontalHeader(ascent=ascent, descent=-200)
    fb.setupNameTable({"familyName": name, "styleName": "Regular"})
    fb.setupOS2(sTypoAscender=ascent, sTypoDescender=-200, usWinAscent=ascent, usWinDescent=200)
    fb.setupPost()
    out = FilePath(folder) / f"{name}.ttf"
    fb.save(str(out))
    return str(out)


def ys(path) -> list[float]:
    return [pt[1] for seg in path.segments for pt in seg[1:]]


# ------------------------------------------------------------------ the fast path
def test_plain_text_is_shaped_exactly_as_before():
    d = typography.default_font()
    for text in ("Hello, world", "fl ffi café", "Tab\there", "★ → ∑"):
        with_fallback = d.shape(text, 20, fallback=())
        assert isinstance(with_fallback, TextRun)
        assert with_fallback == d.shape(text, 20)                # the same glyphs, advances and run


def test_plain_text_leaves_the_ir_and_the_pixels_alone(canvas):
    p.background("white"); p.fill("black"); p.no_stroke()
    p.text("Hello, world", 10, 10)
    ops = [op for op in api.active_sketch().frame.ops if isinstance(op, ir.Text)]
    assert "text_fallback" not in ir.op_to_jsonable(ops[0])["style"]
    drawn = bytes(canvas._pixels().data)
    p.background("white"); p.fill("black"); p.no_stroke()
    p.text_fallback(None)
    p.text("Hello, world", 10, 10)
    assert bytes(canvas._pixels().data) == drawn


def test_a_line_the_font_can_draw_is_one_plain_run_even_with_a_chain(tmp_path):
    other = make_font(tmp_path, "Other", "XYZ")
    line = shape("Hello", fallback=(typography.load_font(other).name,))
    assert isinstance(line, TextRun)


# ------------------------------------------------------------------ itemising
def test_a_hindi_word_and_an_emoji_get_their_own_fonts():
    line = shape(f"Hello {HINDI} {ROCKET}")
    assert isinstance(line, ShapedLine)
    assert names(line) == ["DejaVuSans.ttf", DEVANAGARI, EMOJI]
    assert "".join(run.text for run in line.runs) == f"Hello {HINDI} {ROCKET}"
    assert all(g.gid != 0 for run in line.runs for g in run.glyphs)           # no .notdef anywhere


def test_a_run_shapes_with_its_own_font_at_its_own_scale():
    line = shape(f"a{HINDI}")
    plain, hindi = line.runs
    assert plain.font.units_per_em == 2048 and hindi.font.units_per_em == 1000
    assert hindi.scale == pytest.approx(20 / 1000)


def test_a_zwj_family_and_a_flag_stay_single_clusters():
    assert typography.clusters(FAMILY) == [(0, len(FAMILY))]
    assert typography.clusters(FLAG) == [(0, 2)]
    assert typography.clusters("a\u0301b") == [(0, 2), (2, 3)]
    conjunct = "क्ष"
    assert typography.clusters(conjunct) == [(0, len(conjunct))]
    for text in (FAMILY, FLAG):
        line = shape(f"x {text} y")
        emoji_runs = [run for run in line.runs if run.font.path.endswith(EMOJI)]
        assert [run.text for run in emoji_runs] == [text]
        assert len(emoji_runs[0].glyphs) == 1                                   # drawn as one glyph


def test_spaces_never_come_from_the_emoji_font():
    line = shape(f"{ROCKET} {ROCKET}  {ROCKET}")
    assert names(line) == [EMOJI, "DejaVuSans.ttf", EMOJI, "DejaVuSans.ttf", EMOJI]
    for run in line.runs:
        if run.font.path.endswith(EMOJI):
            assert " " not in run.text


def test_an_emoji_the_font_has_still_comes_from_the_emoji_font():
    assert typography.default_font().has_text(GRIN)
    assert names(shape(f"a {GRIN}")) == ["DejaVuSans.ttf", EMOJI]


def test_a_heart_with_a_variation_selector_counts_as_an_emoji():
    assert typography.has_emoji("\u2764\ufe0f") and not typography.has_emoji("\u2764 plain")
    assert not typography.has_emoji("Hello") and typography.has_emoji(GRIN)


def test_punctuation_stays_with_the_run_before_it():
    line = shape(f"{HINDI}, {HINDI}. ok")
    assert names(line) == [DEVANAGARI, "DejaVuSans.ttf"]
    assert line.runs[0].text == f"{HINDI}, {HINDI}. "


def test_a_character_nobody_has_is_the_current_fonts_notdef():
    line = shape("a\U00010380b")                                                # Old Persian: no bundled font
    assert isinstance(line, TextRun)
    assert 0 in [g.gid for g in line.glyphs]


def test_itemising_is_remembered():
    d = typography.default_font()
    text = f"remember {ROCKET}"
    first = typography._itemise(text, d, ())
    assert typography._itemise(text, d, ()) is first


def test_the_bundled_fonts_load_only_when_needed():
    typography._bundled_cache.clear()
    shape("Hello")
    assert not typography._bundled_cache
    shape(f"Hello {ROCKET}")
    assert set(typography._bundled_cache) == {EMOJI}


# ------------------------------------------------------------------ the learner's chain
def test_the_learners_fonts_come_before_the_bundled_ones(tmp_path):
    key = typography.load_font(make_font(tmp_path, "Mine", "日" + HINDI[0])).name
    line = shape(f"a日{HINDI[0]}", fallback=(key,))
    assert names(line) == ["DejaVuSans.ttf", "Mine.ttf"]                      # even the Devanagari letter: Mine is first
    assert line.runs[1].text == f"日{HINDI[0]}"


def test_a_loaded_primary_falls_back_to_dejavu_last(tmp_path):
    primary = typography._registry[typography.load_font(make_static_font(tmp_path)).name]   # letters A to E
    line = shape("AB xyz", font=primary)
    assert names(line) == ["TestStatic.ttf", "DejaVuSans.ttf"]


# ------------------------------------------------------------------ one baseline
def test_every_run_sits_on_the_primary_fonts_baseline(tmp_path):
    primary = typography._registry[typography.load_font(make_static_font(tmp_path)).name]  # ascent 800
    tall = typography.load_font(make_font(tmp_path, "Tall", "XY", ascent=1500)).name
    line = shape("AXBY", fallback=(tall,), font=primary, size=100)
    assert names(line) == ["TestStatic.ttf", "Tall.ttf", "TestStatic.ttf", "Tall.ttf"]
    baseline = 50 + 800 * 0.1
    ops = line.outline_ops(10, 50, p.color(0))
    assert len(ops) == 4
    for op in ops:
        assert max(ys(op.path)) == pytest.approx(baseline)                      # every glyph stands on y = baseline
    placed = line.placements(10, 50)
    assert {round(y, 6) for _, _, y in placed} == {round(baseline, 6)}
    assert placed[1][1] == pytest.approx(10 + 60)                              # the second glyph starts after the first


def test_metrics_follow_the_current_font(tmp_path):
    p.size(300, 100)
    p.text_size(20)
    ascent, descent = p.text_ascent(), p.text_descent()
    p.text_fallback()
    assert (p.text_ascent(), p.text_descent()) == (ascent, descent)


# ------------------------------------------------------------------ measuring and wrapping
def test_text_width_is_the_sum_of_the_runs():
    p.size(300, 100)
    p.text_size(20)
    text = f"Hello {HINDI} {ROCKET} end"
    line = shape(text)
    assert p.text_width(text) == pytest.approx(sum(run.advance for run in line.runs))
    assert p.text_width(text) == pytest.approx(
        p.text_width("Hello ") + p.text_width(HINDI) + p.text_width(" ") + p.text_width(ROCKET) + p.text_width(" end"),
        rel=0.02)


def test_wrapping_keeps_every_line_inside_the_box():
    d = typography.default_font()
    text = f"go {ROCKET} now {HINDI} and {HINDI} again {FAMILY} finish the line"
    lines, rests = typography.wrap_lines(text, 130, 20, d, fallback=())
    assert len(lines) > 2
    for line in lines:
        assert typography.text_width(line, 20, d, fallback=()) <= 130
    assert " ".join(lines) == text


def test_text_box_returns_the_rest_with_mixed_runs():
    p.size(300, 200)
    p.text_size(20)
    rest = p.text_box(f"go {ROCKET} now {HINDI} and more words here", 0, 0, 120, 60)
    assert rest != "" and rest in f"go {ROCKET} now {HINDI} and more words here"
    ops = [op for op in api.active_sketch().frame.ops if isinstance(op, ir.Text)]
    assert len(ops) == 2


# ------------------------------------------------------------------ turning it off, and drawing state
def test_fallback_off_gives_todays_notdef():
    p.size(300, 100)
    style = api.active_sketch().style
    font = typography.effective_font(style)
    on = font.shape(ROCKET, 20, **typography.text_settings(style))
    assert on.runs[0].glyphs[0].gid not in (0,)
    p.text_fallback(None)
    style = api.active_sketch().style
    off = font.shape(ROCKET, 20, **typography.text_settings(style))
    assert isinstance(off, TextRun) and off.glyphs[0].gid == 0
    assert off == font.shape(ROCKET, 20)                                       # exactly the old behaviour
    p.text_fallback()
    assert api.active_sketch().style.text_fallback == ()


def test_push_and_pop_restore_the_chain(tmp_path):
    p.size(300, 100)
    mine = p.load_font(make_font(tmp_path, "Mine", "XY"))
    p.push()
    p.text_fallback(mine)
    assert api.active_sketch().style.text_fallback == (mine.name,)
    p.push()
    p.text_fallback(None)
    assert api.active_sketch().style.text_fallback is None
    p.pop()
    assert api.active_sketch().style.text_fallback == (mine.name,)
    p.pop()
    assert api.active_sketch().style.text_fallback == ()


def test_text_fallback_checks_its_arguments():
    p.size(300, 100)
    with pytest.raises(TypeError):
        p.text_fallback(3)
    with pytest.raises(TypeError):
        p.text_fallback(None, None)


def test_the_chain_is_in_the_ir_only_when_set(tmp_path):
    p.size(300, 100)
    mine = p.load_font(make_font(tmp_path, "Mine", "XY"))
    for value, expected in (((mine.name,), [mine.name]), (None, None)):
        state = GraphicsState(text_fallback=value)
        op = ir.Text("Hi", 0, 0, p.color(0), state)
        data = ir.op_to_jsonable(op)
        assert data["style"]["text_fallback"] == expected
        assert ir.op_from_jsonable(data) == op
    assert "text_fallback" not in ir.op_to_jsonable(ir.Text("Hi", 0, 0, p.color(0), GraphicsState()))["style"]


def test_the_chain_changes_what_is_drawn_and_a_picture_carries_it(tmp_path):
    p.size(200, 100)
    mine = p.load_font(make_font(tmp_path, "Mine", "XY"))
    g = p.create_graphics(100, 50)
    g.text_font(p.load_font(make_static_font(tmp_path)))
    g.text_fallback(mine)
    assert g.text_width("AXB") == pytest.approx(36)                            # three 12 px glyphs, X from "Mine"
    g.text_fallback()
    assert g.text_width("AXB") != pytest.approx(36)                            # X now comes from DejaVu Sans


def test_text_path_and_text_to_points_use_the_runs():
    p.size(300, 100)
    p.text_size(40)
    with_emoji = p.text_path(f"a{ROCKET}", 0, 0).geometry
    p.text_fallback(None)
    tofu = p.text_path(f"a{ROCKET}", 0, 0).geometry
    assert with_emoji != tofu
    p.text_fallback()
    points = p.text_to_points(HINDI, 0, 0, 3)
    assert len(points) > 20


def test_formatted_text_uses_the_chain():
    p.size(400, 100)
    p.text_size(20)
    fs = p.FormattedString()
    fs.append("Hi ")
    fs.append(f"{ROCKET}", size=30)
    assert p.text_width(fs) > p.text_width("Hi ")
    shaped = shape(ROCKET, size=30)
    assert p.text_width(fs) == pytest.approx(p.text_width("Hi ") + shaped.advance)
    assert p.text_path(fs, 0, 0).geometry.segments


# ------------------------------------------------------------------ PDF text
def test_pdf_text_embeds_one_subset_per_font(tmp_path):
    pytest.importorskip("pypdfium2")
    from test_pdf_text import fonts, texts, words

    out = tmp_path / "mixed.pdf"
    p.size(320, 100)
    p.background("white")
    p.fill("black")
    p.text_size(24)
    p.text(f"Hello {HINDI} {ROCKET} end", 10, 30)
    p.save(str(out))
    embedded = sorted(str(font["/BaseFont"]).split("+")[1] for font in fonts(out))
    assert embedded == ["DejaVuSans", "NotoEmoji-Regular", "NotoSansDevanagari-Regular"]
    by_pypdf, by_pdfium = texts(out)
    for engine in (by_pypdf[0], by_pdfium[0]):
        assert "Hello" in engine and "end" in engine
    assert HINDI in by_pdfium[0]
    assert ROCKET in by_pdfium[0]


def test_pdf_text_with_the_same_font_twice_is_one_subset(tmp_path):
    pytest.importorskip("pypdfium2")
    from test_pdf_text import fonts

    out = tmp_path / "twice.pdf"
    p.size(320, 100)
    p.background("white")
    p.fill("black")
    p.text(f"{ROCKET} a", 10, 10)
    p.text(f"b {ROCKET}", 10, 50)
    p.save(str(out))
    assert len(fonts(out)) == 2


# ------------------------------------------------------------------ system fonts
def test_system_font_finds_a_family_by_name(tmp_path, monkeypatch):
    regular = make_static_font(tmp_path, "Sample Family")
    bold = tmp_path / "AAA-first-alphabetically.ttf"
    tt = TTFont(regular)
    for record in tt["name"].names:
        if record.nameID in (2, 4, 6):
            record.string = "Bold"
    tt.save(str(bold))
    make_static_font(tmp_path, "Another")
    monkeypatch.setattr(typography, "_system_font_dirs", lambda: [str(tmp_path)])
    font = p.system_font("sample FAMILY")
    assert font.family() == "Sample Family"
    assert font.style() == "Regular"                                           # the Regular face, not the first file
    assert font._resource().path.endswith("Sample Family.ttf")
    p.size(100, 100)
    p.text_fallback(font)                                                      # usable as a fallback font
    assert api.active_sketch().style.text_fallback == (font.name,)


def test_system_font_not_found_names_the_font(tmp_path, monkeypatch):
    monkeypatch.setattr(typography, "_system_font_dirs", lambda: [str(tmp_path)])
    with pytest.raises(FileNotFoundError, match="No Such Family"):
        p.system_font("No Such Family")
    with pytest.raises(TypeError):
        p.system_font(3)


def test_the_system_folders_cover_the_three_systems(monkeypatch):
    monkeypatch.setenv("WINDIR", "C:\\Windows")
    monkeypatch.setattr(os.path, "isdir", lambda path: True)
    folders = [f.replace("\\", "/") for f in typography._system_font_dirs()]
    for expected in ("C:/Windows/Fonts", "/System/Library/Fonts", "/Library/Fonts", "/usr/share/fonts"):
        assert expected in folders
    assert any(f.endswith("/.local/share/fonts") for f in folders)
    assert any(f.endswith("/.fonts") for f in folders) and any(f.endswith("/Library/Fonts") for f in folders)


# ------------------------------------------------------------------ the package
def test_the_bundled_fonts_and_licence_are_in_the_package():
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    patterns = pyproject["tool"]["setuptools"]["package-data"]["funground"]
    assert "fonts/*.ttf" in patterns and "fonts/*.txt" in patterns
    assert "funground/fonts/Noto-OFL.txt" in pyproject["project"]["license-files"]
    folder = ROOT / "funground" / "fonts"
    for name in (EMOJI, "NotoSansSymbols2-Regular.ttf", DEVANAGARI, "Noto-OFL.txt"):
        assert (folder / name).is_file(), name
    licence = (folder / "Noto-OFL.txt").read_text(encoding="utf-8")
    for line in ("Copyright 2013 Google LLC", "The Noto Project Authors (https://github.com/notofonts/symbols)",
                 "The Noto Project Authors (https://github.com/notofonts/devanagari)", "SIL OPEN FONT LICENSE"):
        assert line in licence
    assert "Noto Emoji" in (ROOT / "THIRD_PARTY_LICENSES.md").read_text(encoding="utf-8")


def test_the_bundled_emoji_font_is_a_static_font_with_every_glyph():
    tt = TTFont(ROOT / "funground" / "fonts" / EMOJI)
    assert "fvar" not in tt and len(tt.getGlyphOrder()) == 1891
    assert tt["name"].getDebugName(1) == "Noto Emoji" and tt["name"].getDebugName(2) == "Regular"
