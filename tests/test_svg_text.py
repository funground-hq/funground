"""Live, editable text in SVG files (S-097, contract T19, decision D-059 = A).

Every line of text in an SVG funground writes is a real ``<text>`` element that names its font by
family, so Illustrator, Inkscape and browsers draw it in the installed font and it stays editable.
A subset of each font is embedded as a CSS ``@font-face`` for browsers. SVGs are parsed with
ElementTree; "outlines only" files (the text step switched off) are what funground wrote before.
"""
from __future__ import annotations

import base64
import io
import math
import os
import re
import xml.etree.ElementTree as ET
from contextlib import contextmanager

import pytest
import uharfbuzz as hb
from fontTools.pens.recordingPen import RecordingPen
from fontTools.ttLib import TTFont

import funground as f
from funground import api, export
from funground.export import svg_text
from funground.platform.headless import HeadlessPlatform
from funground.sketch import Sketch
from funground.typography import BUNDLED_FALLBACKS, FONT_DIR, default_font

from fontmaker import make_static_font, make_variable_font

SVG = "{http://www.w3.org/2000/svg}"
XLINK = "{http://www.w3.org/1999/xlink}"
XML_SPACE = "{http://www.w3.org/XML/1998/namespace}space"
INKSCAPE = "{http://www.inkscape.org/namespaces/inkscape}"
HIDDEN = {f"{SVG}{t}" for t in ("defs", "clipPath", "mask", "filter", "pattern", "marker", "symbol")}
HEBREW = "שלום עולם"        # "hello world"
ARABIC = "مرحبا"                            # "welcome"
DEVANAGARI = "नमस्ते"                    # "hello"
DEJAVU = "'DejaVu Sans', sans-serif"


def script(width=240, height=120):
    api.use_sketch(Sketch(platform=HeadlessPlatform()))
    f.size(width, height)
    f.background("white")
    f.fill("black")
    f.text_size(20)


class _OutlinesOnly(svg_text.SvgTextCollector):
    """A collector that never takes a line: every line is drawn as outlines, as before S-097."""

    def add(self, run, x, y, matrix, style):
        return None


@contextmanager
def outlines_only(monkeypatch):
    with monkeypatch.context() as m:
        m.setattr(export, "SvgTextCollector", _OutlinesOnly)
        yield


def save_both(tmp_path, monkeypatch, name="page"):
    """Save the current script with live text and as outlines only; return both paths."""
    new, old = tmp_path / f"{name}.svg", tmp_path / f"{name}_outlines.svg"
    f.save(str(new))
    with outlines_only(monkeypatch):
        f.save(str(old))
    return new, old


def parse(path):
    root = ET.parse(str(path)).getroot()
    parent = {child: el for el in root.iter() for child in el}
    return root, parent


def texts(path) -> list[ET.Element]:
    root, _ = parse(path)
    return list(root.iter(f"{SVG}text"))


def content(t: ET.Element) -> str:
    return "".join(t.itertext())


def in_body(el, parent) -> bool:
    while el is not None:
        if el.tag in HIDDEN:
            return False
        el = parent.get(el)
    return True


def body_paths(path) -> int:
    """How many <path> elements the document body draws, following <use> links (glyph outlines are
    paths; the background is a rect)."""
    root, _ = parse(path)
    by_id = {el.get("id"): el for el in root.iter() if el.get("id")}
    count = 0

    def visit(el):
        nonlocal count
        if el.tag in HIDDEN:
            return
        if el.tag == f"{SVG}use":
            visit(by_id[(el.get(XLINK + "href") or el.get("href"))[1:]])
            return
        if el.tag == f"{SVG}path":
            count += 1
        for child in el:
            visit(child)

    visit(root)
    return count


def matrix_of(value) -> tuple:
    if not value:
        return (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)
    m = re.fullmatch(r"matrix\(([^)]*)\)", value)
    return tuple(float(v) for v in m.group(1).split(","))


def multiply(m, n):
    a, b, c, d, e, g = m
    a2, b2, c2, d2, e2, g2 = n
    return (a * a2 + c * b2, b * a2 + d * b2, a * c2 + c * d2, b * c2 + d * d2,
            a * e2 + c * g2 + e, b * e2 + d * g2 + g)


def baseline(y, size=20):
    return y + default_font().ascent * size / default_font().units_per_em


def font_faces(path) -> list[tuple[str, bytes]]:
    """(family, font bytes) for every @font-face in the file."""
    root, _ = parse(path)
    css = "".join(s.text or "" for s in root.iter(f"{SVG}style"))
    return [(fam, base64.b64decode(data)) for fam, data in
            re.findall(r"font-family: '([^']*)';[^}]*?base64,([A-Za-z0-9+/=]+)", css)]


# ---------------------------------------------------------------- structure
def test_a_line_is_live_text_and_its_outlines_are_gone(tmp_path, monkeypatch):
    script()
    f.fill(200, 30, 60)
    f.text("Hello, SVG world", 10, 10)
    new, old = save_both(tmp_path, monkeypatch)
    ET.parse(str(new))                                         # valid XML
    found = texts(new)
    assert [content(t) for t in found] == ["Hello, SVG world"]
    t = found[0]
    assert t.get("font-family") == DEJAVU
    assert t.get("font-weight") is None and t.get("font-style") is None
    assert t.get("font-size") == "20"
    assert t.get("fill") == "rgb(78.431373%, 11.764706%, 23.529412%)"
    assert t.get("fill-opacity") == "1"
    assert t.get(XML_SPACE) == "preserve"
    assert t.get("textLength") is None and t.get("direction") is None
    assert float(t.get("x")) == pytest.approx(10)              # one x and one y: easy to edit
    assert float(t.get("y")) == pytest.approx(baseline(10), abs=1e-3)
    assert t.get("transform") is None
    assert list(t) == []                                      # plain content, no per-glyph spans
    root, parent = parse(new)
    t = next(root.iter(f"{SVG}text"))
    assert in_body(t, parent), "editors only edit text that is drawn, not text inside <use> or <defs>"
    assert body_paths(old) > 10 and body_paths(new) == 0, "no glyph outlines are left"
    assert texts(old) == []


@pytest.mark.parametrize("style, weight, slant", [
    ("bold", "bold", None), ("italic", None, "oblique"), ("bold_italic", "bold", "oblique")])
def test_bold_and_oblique_name_the_style(tmp_path, style, weight, slant):
    script()
    f.text_style(style)
    f.text("Styled", 10, 10)
    f.save(str(tmp_path / "a.svg"))
    t = texts(tmp_path / "a.svg")[0]
    assert t.get("font-family") == DEJAVU
    assert t.get("font-weight") == weight
    assert t.get("font-style") == slant


def test_the_marker_clips_are_gone(tmp_path):
    script()
    f.text("No markers", 10, 10)
    f.save(str(tmp_path / "a.svg"))
    root, _ = parse(tmp_path / "a.svg")
    clips = [p.get("d") or "" for c in root.iter(f"{SVG}clipPath") for p in c.iter(f"{SVG}path")]
    assert not any(max((abs(float(v)) for v in re.findall(r"-?\d+\.?\d*", d)), default=0) > 1000 for d in clips)


@pytest.mark.parametrize("string", [
    "a < b & \"c\" > 'd'",
    "  two  spaces  ",
    HEBREW,
    ARABIC,
    DEVANAGARI,
    "office fluffy",               # ligatures in many fonts: the text is the letters
    "café naïve",
])
def test_every_string_stays_live_text_in_reading_order(tmp_path, string):
    script(300, 80)
    f.text(string, 10, 10)
    f.save(str(tmp_path / "a.svg"))
    assert "".join(content(t) for t in texts(tmp_path / "a.svg")) == string
    assert body_paths(tmp_path / "a.svg") == 0               # complex scripts too: never shapes


@pytest.mark.parametrize("string", [HEBREW, ARABIC])
def test_right_to_left_text_is_in_logical_order(tmp_path, string):
    script(300, 80)
    f.text_fallback(None)                                     # one font, one run
    f.text(string + "!", 10, 10)
    f.save(str(tmp_path / "a.svg"))
    t = texts(tmp_path / "a.svg")[0]
    assert content(t) == string + "!"                         # never visually reversed
    assert t.get("direction") == "rtl"
    width = default_font().shape(string + "!", 20).advance
    assert float(t.get("x")) == pytest.approx(10 + width, abs=1e-3)   # an rtl run starts at its right end


def test_text_box_gives_one_text_per_line(tmp_path):
    script(200, 200)
    f.text_box("A longer line that wraps inside a box", 10, 10, 120, 180)
    f.save(str(tmp_path / "a.svg"))
    lines = [content(t) for t in texts(tmp_path / "a.svg")]
    assert len(lines) > 1
    assert " ".join(lines).split() == "A longer line that wraps inside a box".split()
    ys = [float(t.get("y")) for t in texts(tmp_path / "a.svg")]
    assert ys == sorted(ys)


# ---------------------------------------------------------------- paint and settings
def test_tracking_is_letter_spacing(tmp_path):
    script(300, 80)
    f.text_tracking(5)
    f.text("Spread", 10, 10)
    f.save(str(tmp_path / "a.svg"))
    assert texts(tmp_path / "a.svg")[0].get("letter-spacing") == "5"


def test_features_are_carried_over(tmp_path):
    script(300, 80)
    f.text_features(liga=False, kern=True)
    f.text("office", 10, 10)
    f.save(str(tmp_path / "a.svg"))
    settings = texts(tmp_path / "a.svg")[0].get("font-feature-settings")
    assert sorted(s.strip() for s in settings.split(",")) == ["'kern' 1", "'liga' 0"]


def test_variations_are_carried_over(tmp_path):
    script(300, 80)
    f.text_font(f.load_font(make_variable_font(tmp_path)), 30)
    f.font_variations(wght=700)
    f.text("ABC", 10, 10)
    f.save(str(tmp_path / "a.svg"))
    t = texts(tmp_path / "a.svg")[0]
    assert t.get("font-variation-settings") == "'wght' 700"
    assert t.get("font-family") == "'TestVar', sans-serif"


def test_opacity_is_kept(tmp_path):
    script()
    f.fill(30, 90, 200)
    f.opacity(128)
    f.text("Faint", 10, 10)
    f.save(str(tmp_path / "a.svg"))
    assert texts(tmp_path / "a.svg")[0].get("fill-opacity") == "0.501961"


@pytest.mark.parametrize("kind", ["linear", "radial"])
def test_a_gradient_fill_references_the_gradient_where_cairo_put_it(tmp_path, monkeypatch, kind):
    script()
    f.translate(60, 40)
    f.rotate(25)
    if kind == "linear":
        f.fill(f.linear_gradient(0, 0, 150, 0, ["red", "blue"]))
    else:
        f.fill(f.radial_gradient(40, 10, 80, ["red", "blue"]))
    f.text("Rainbow", 0, 0)
    new, old = save_both(tmp_path, monkeypatch)
    t = texts(new)[0]
    ref = re.fullmatch(r"url\(#([^)]+)\)", t.get("fill")).group(1)
    root, _ = parse(new)
    gradient = next(el for el in root.iter() if el.get("id") == ref)
    assert gradient.tag == f"{SVG}{kind}Gradient"
    # The text's transform then the gradient's: the same place as Cairo's gradient for the outlines.
    placed = multiply(matrix_of(t.get("transform")), matrix_of(gradient.get("gradientTransform")))
    old_root, _ = parse(old)
    original = next(old_root.iter(f"{SVG}{kind}Gradient"))
    assert placed == pytest.approx(matrix_of(original.get("gradientTransform")), abs=0.01)


def test_a_blended_line_is_in_the_file(tmp_path):
    """Cairo draws a blend mode through filters; the text is there."""
    script()
    f.blend_mode("multiply")
    f.text("Mixed", 10, 10)
    f.save(str(tmp_path / "a.svg"))
    assert [content(t) for t in texts(tmp_path / "a.svg")] == ["Mixed"]


# ---------------------------------------------------------------- where it goes
def test_a_turned_line_carries_its_transform(tmp_path):
    script()
    f.translate(120, 60)
    f.rotate(30)
    f.scale(1.5, 0.8)
    f.text("Turned", -40, -10)
    f.save(str(tmp_path / "a.svg"))
    t = texts(tmp_path / "a.svg")[0]
    a, b, c, d, e, g = matrix_of(t.get("transform"))
    r = math.radians(30)
    assert (a, b, c, d) == pytest.approx((1.5 * math.cos(r), 1.5 * math.sin(r), -0.8 * math.sin(r), 0.8 * math.cos(r)),
                                         abs=1e-5)
    assert (e, g) == pytest.approx((120, 60), abs=0.01)
    assert float(t.get("x")) == pytest.approx(-40)
    assert float(t.get("y")) == pytest.approx(baseline(-10), abs=1e-3)


def test_a_clipped_line_stays_inside_the_clip(tmp_path):
    script()
    f.clip(f.path().move_to(0, 0).line_to(200, 0).line_to(0, 120).close())
    f.text_size(40)
    f.text("Clipped", 10, 30)
    f.save(str(tmp_path / "a.svg"))
    root, parent = parse(tmp_path / "a.svg")
    t = next(root.iter(f"{SVG}text"))
    clips = []
    el = parent[t]
    while el is not None:
        if el.get("clip-path"):
            clips.append(el.get("clip-path"))
        el = parent.get(el)
    by_id = {c.get("id"): c for c in root.iter(f"{SVG}clipPath")}
    shapes = [by_id[re.search(r"#([^)]+)", c).group(1)][0].get("d") or "" for c in clips]
    assert any("L 0 120" in d for d in shapes), "the triangle clip is above the text"


def test_text_in_pictures_is_live_and_drawn_in_place(tmp_path):
    script(240, 120)
    g = f.create_graphics(200, 80)
    g.fill("purple")
    g.text_size(30)
    g.text("Inside", 10, 10)
    inner = f.create_graphics(100, 40)
    inner.fill("teal")
    inner.text_size(20)
    inner.text("Nested", 0, 0)
    g.image(inner, 100, 40)
    f.image(g, 20, 20)
    f.save(str(tmp_path / "a.svg"))
    root, parent = parse(tmp_path / "a.svg")
    assert [content(t) for t in texts(tmp_path / "a.svg")] == ["Inside", "Nested"]
    assert all(in_body(t, parent) for t in root.iter(f"{SVG}text"))


def test_a_picture_saved_as_svg(tmp_path):
    script()
    g = f.create_graphics(160, 60)
    g.fill("navy")
    g.text_size(24)
    g.text("Picture text", 5, 5)
    g.save(str(tmp_path / "g.svg"))
    assert [content(t) for t in texts(tmp_path / "g.svg")] == ["Picture text"]


# ---------------------------------------------------------------- kept as shapes
def test_shadows_stay_shapes(tmp_path):
    script()
    f.shadow(4, 4, 3, f.color(0, 0, 0, 160))
    f.fill("orange")
    f.text("Shade", 10, 20)
    f.save(str(tmp_path / "a.svg"))
    assert [content(t) for t in texts(tmp_path / "a.svg")] == ["Shade"]     # once
    assert body_paths(tmp_path / "a.svg") > 0                                # the shadow


def test_erased_text_stays_shapes(tmp_path, monkeypatch):
    script()
    f.rect(0, 0, 240, 120)
    f.erase()
    f.text("Gone", 10, 20)
    f.no_erase()
    new, old = save_both(tmp_path, monkeypatch)
    assert texts(new) == []
    assert _normalised(new) == _normalised(old)               # exactly the outlines, as before
    assert "<path" in new.read_text(encoding="utf-8")


# ---------------------------------------------------------------- fonts
def test_two_fonts_give_two_texts(tmp_path):
    script(300, 60)
    fs = f.FormattedString()
    fs.append("Plain ")
    fs.append("ABC", font=str(make_static_font(tmp_path, "Second")))
    f.text(fs, 10, 10)
    f.save(str(tmp_path / "a.svg"))
    found = texts(tmp_path / "a.svg")
    assert [content(t) for t in found] == ["Plain ", "ABC"]
    assert [t.get("font-family") for t in found] == [DEJAVU, "'Second', sans-serif"]


def test_fallback_runs_are_tspans_with_their_own_family(tmp_path):
    script(300, 60)
    f.text("Hi 🙂 नमस्ते", 10, 10)
    f.save(str(tmp_path / "a.svg"))
    found = texts(tmp_path / "a.svg")
    assert len(found) == 1                                    # one line, one <text>
    t = found[0]
    assert content(t) == "Hi 🙂 नमस्ते"
    assert t.get("font-family") == DEJAVU
    spans = list(t)
    assert all(s.tag == f"{SVG}tspan" for s in spans)
    assert {s.text: s.get("font-family") for s in spans if s.text.strip()} == {
        "🙂": "'Noto Emoji', sans-serif", "नमस्ते": "'Noto Sans Devanagari', sans-serif"}
    assert all(s.get("x") is None for s in spans)            # they follow on: easy to edit
    assert body_paths(tmp_path / "a.svg") == 0


def test_fonts_are_embedded_for_browsers(tmp_path):
    script(300, 80)
    f.text("Plain", 10, 10)
    f.text_style("bold")
    f.text("Bold नमस्ते", 10, 40)
    f.save(str(tmp_path / "a.svg"))
    root, _ = parse(tmp_path / "a.svg")
    assert root[0].tag == f"{SVG}style"
    faces = font_faces(tmp_path / "a.svg")
    assert sorted(fam for fam, _ in faces) == ["DejaVu Sans", "DejaVu Sans", "Noto Sans Devanagari"]
    css = root[0].text
    assert "font-weight: bold" in css and "format('truetype')" in css
    for fam, data in faces:
        tt = TTFont(io.BytesIO(data))
        assert tt["name"].getDebugName(1) == fam              # matches the text's font-family
        cmap = tt.getBestCmap()
        assert len(tt.getGlyphOrder()) < 200                  # a subset, not the whole font
        if fam == "Noto Sans Devanagari":
            assert all(ord(c) in cmap for c in "नमस्ते")


def test_a_font_that_forbids_embedding_is_named_but_not_embedded(tmp_path):
    script(300, 60)
    f.text_font(f.load_font(make_static_font(tmp_path, "NoEmbed", fs_type=0x0002)), 30)
    f.text("ABC DE", 10, 10)
    f.save(str(tmp_path / "a.svg"))
    data = (tmp_path / "a.svg").read_text(encoding="utf-8")
    t = texts(tmp_path / "a.svg")[0]
    assert content(t) == "ABC DE" and t.get("font-family") == "'NoEmbed', sans-serif"
    assert "@font-face" not in data and "base64" not in data


def test_the_subset_keeps_shaping_for_devanagari():
    """The embedded subset keeps GSUB/GPOS and the glyph closure, so a browser shapes conjuncts, the
    pre-base vowel and marks from it exactly as from the whole font."""
    text = "क्षत्रिय नमस्ते"
    path = os.path.join(FONT_DIR, BUNDLED_FALLBACKS[2])

    def shaped(data: bytes) -> list[tuple]:
        """Each glyph HarfBuzz picks, as its outline and position: the subset renumbers glyphs and
        drops their names, so they are compared by what they draw."""
        font = hb.Font(hb.Face(data))
        buf = hb.Buffer()
        buf.add_str(text)
        buf.guess_segment_properties()
        hb.shape(font, buf)
        tt = TTFont(io.BytesIO(data))
        order, glyphs = tt.getGlyphOrder(), tt.getGlyphSet()
        out = []
        for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
            pen = RecordingPen()
            glyphs[order[info.codepoint]].draw(pen)
            out.append((tuple(pen.value), info.cluster, pos.x_advance, pos.x_offset, pos.y_offset))
        return out

    with open(path, "rb") as fh:
        full = fh.read()
    small = svg_text.SvgTextCollector._subset(path, set(text))
    assert len(small) < len(full) / 5
    sub = TTFont(io.BytesIO(small))
    assert "GSUB" in sub and "GPOS" in sub
    full_shape = shaped(full)
    assert len(full_shape) < len(text)                        # conjuncts: fewer glyphs than characters
    assert shaped(small) == full_shape


# ---------------------------------------------------------------- layers
def test_text_in_a_layer_stays_in_its_layer_group(tmp_path):
    script()
    f.text("On the canvas", 10, 10)
    with f.layer("words"):
        f.fill(0)
        f.text("In a layer", 10, 60)
    with f.layer("hidden words"):
        f.fill(0)
        f.text("Switched off", 10, 90)
    f.hide_layer("hidden words")
    f.save(str(tmp_path / "a.svg"))
    root, parent = parse(tmp_path / "a.svg")
    groups = {g.get(INKSCAPE + "label"): g for g in root.iter(f"{SVG}g") if g.get(INKSCAPE + "groupmode") == "layer"}
    assert [content(t) for t in groups["words"].iter(f"{SVG}text")] == ["In a layer"]
    assert [content(t) for t in groups["hidden words"].iter(f"{SVG}text")] == ["Switched off"]
    assert groups["hidden words"].get("style") == "display:none"
    canvas = [content(t) for t in root.iter(f"{SVG}text") if not any(t in g.iter() for g in groups.values())]
    assert canvas == ["On the canvas"]
    assert all(in_body(t, parent) for t in root.iter(f"{SVG}text"))


# ---------------------------------------------------------------- nothing else changes
def _normalised(path) -> str:
    """The file with Cairo's process-wide numbering (source-N, clip-N, ...) taken out."""
    data = path.read_text(encoding="utf-8")
    return re.sub(r"\b(source|clip|mask|filter|image|pattern|surface|compositing-group|linear-pattern|"
                  r"radial-pattern)-\d+", r"\1-N", data)


def test_an_svg_without_text_is_unchanged(tmp_path, monkeypatch):
    def draw():
        script()
        f.no_stroke()
        f.fill("gold")
        f.circle(60, 60, 40)
        f.fill(f.linear_gradient(0, 0, 240, 0, ["red", "blue"]))
        f.rect(120, 20, 100, 80)
        f.draw_path(f.text_path("Path", 10, 10))       # text as a shape is a shape (F13)

    draw()
    new = tmp_path / "new.svg"
    f.save(str(new))
    draw()
    with outlines_only(monkeypatch):
        f.save(str(tmp_path / "old.svg"))
    assert texts(new) == []
    assert _normalised(new) == _normalised(tmp_path / "old.svg")


def test_if_the_text_step_fails_the_svg_has_outlines(tmp_path, monkeypatch):
    def broken(self, path):
        raise RuntimeError("boom")

    monkeypatch.setattr(svg_text.SvgTextCollector, "finish", broken)
    script()
    f.text("Still saved", 10, 10)
    with f.layer("top"):
        f.circle(10, 10, 5)
    f.save(str(tmp_path / "a.svg"))
    data = (tmp_path / "a.svg").read_text(encoding="utf-8")
    assert "<text" not in data and "<path" in data
    assert "inkscape:groupmode" in data                  # the layer step still ran


def test_sizes_of_a_text_heavy_page(tmp_path, monkeypatch):
    script(600, 820)
    f.text_size(12)
    line = "The quick brown fox jumps over the lazy dog while it sleeps, 0123456789."
    for i in range(50):
        f.text(line, 10, 10 + i * 16)
    new, old = save_both(tmp_path, monkeypatch)
    embedded = sum(len(data) for _, data in font_faces(new))
    print(f"text-heavy SVG: live text {new.stat().st_size} bytes (font subset {embedded} bytes), "
          f"outlines only {old.stat().st_size} bytes")
    assert len(texts(new)) == 50
    assert new.stat().st_size < old.stat().st_size
