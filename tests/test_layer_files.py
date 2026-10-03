"""Layers in PDF and SVG files (S-096, contract F16, decision D-053).

Each layer (S-095) is a real layer in the file: an optional content group (OCG) in a PDF, an
Inkscape layer group in an SVG. A hidden layer is in the file, switched off. PDFs are read back
with pypdf and drawn with pdfium (pypdfium2, the engine in Chrome and Edge), which honours the
default OFF state; SVGs are parsed with ElementTree.
"""
from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from contextlib import contextmanager

import cairo
import pytest
from fontTools.ttLib.tables import _h_e_a_d as head_table

pypdfium2 = pytest.importorskip("pypdfium2")
from PIL import Image, ImageChops, ImageStat  # noqa: E402
from pypdf import PdfReader  # noqa: E402

import funground as f  # noqa: E402
from funground import api, export, ir  # noqa: E402
from funground.export import layers as file_layers  # noqa: E402
from funground.export.pdf_text import PdfTextCollector  # noqa: E402
from funground.export.svg_text import SvgTextCollector  # noqa: E402
from funground.platform.headless import HeadlessPlatform  # noqa: E402
from funground.renderers.cairo2d import CairoRenderer  # noqa: E402
from funground.sketch import Sketch  # noqa: E402

SVG = "{http://www.w3.org/2000/svg}"
XLINK = "{http://www.w3.org/1999/xlink}"
INKSCAPE = "{http://www.inkscape.org/namespaces/inkscape}"
NCNAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_.-]*$")


def script(w=120, h=80) -> Sketch:
    s = api.use_sketch(Sketch(platform=HeadlessPlatform()))
    s.size(w, h)
    return s


def three_layers():
    """White canvas; "sky" (blue band), "sun" (yellow disc), "ghost" (red disc, hidden)."""
    f.background(255, 255, 255)
    f.no_stroke()
    with f.layer("sky"):
        f.no_stroke()
        f.fill(0, 0, 255)
        f.rect(0, 0, 120, 30)
    with f.layer("sun"):
        f.no_stroke()
        f.fill(255, 220, 0)
        f.circle(60, 55, 30)
    with f.layer("ghost"):
        f.no_stroke()
        f.fill(255, 0, 0)
        f.circle(100, 60, 20)
    f.hide_layer("ghost")


# ---------------------------------------------------------------- PDF helpers
def ocprops(path):
    reader = PdfReader(str(path))
    props = reader.trailer["/Root"]["/OCProperties"]
    ocgs = [ref.get_object() for ref in props["/OCGs"]]
    order = [ref.get_object()["/Name"] for ref in props["/D"]["/Order"]]
    off = [ref.get_object()["/Name"] for ref in props["/D"].get("/OFF", [])]
    return [o["/Name"] for o in ocgs], order, off


def layer_xobjects(path, page=0) -> list[tuple[str, object]]:
    """(OCG name, Form XObject) for each XObject the page draws directly, in drawing order."""
    reader = PdfReader(str(path))
    p = reader.pages[page]
    xobjects = p["/Resources"].get_object()["/XObject"].get_object()
    names = re.findall(rb"/(\w+) Do", p.get_contents().get_data())
    out = []
    for name in names:
        obj = xobjects["/" + name.decode()].get_object()
        oc = obj.get("/OC")
        out.append((oc.get_object()["/Name"] if oc is not None else None, obj))
    return out


def all_streams(path) -> list[bytes]:
    reader = PdfReader(str(path))
    found, seen = [], set()

    def walk(resources):
        if resources is None:
            return
        for ref in (resources.get_object().get("/XObject") or {}).values():
            if ref.idnum in seen:
                continue
            seen.add(ref.idnum)
            obj = ref.get_object()
            if obj.get("/Subtype") == "/Form":
                found.append(obj.get_data())
            walk(obj.get("/Resources"))

    for page in reader.pages:
        found.append(page.get_contents().get_data())
        walk(page.get("/Resources"))
    return found


def has_image_under(xobject) -> bool:
    for ref in (xobject.get("/Resources", {}).get("/XObject") or {}).values():
        obj = ref.get_object()
        if obj.get("/Subtype") == "/Image" or (obj.get("/Subtype") == "/Form" and has_image_under(obj)):
            return True
    return False


def render(path, page=0, scale=1) -> Image.Image:
    doc = pypdfium2.PdfDocument(str(path))
    image = doc[page].render(scale=scale).to_pil().convert("RGB")
    doc.close()
    return image


def mean_difference(a: Image.Image, b: Image.Image) -> float:
    return sum(ImageStat.Stat(ImageChops.difference(a, b)).mean) / 3


def no_marker_left(path) -> bool:
    """No stream still holds a layer marker (a four-cornered clip thousands of units across)."""
    for data in all_streams(path):
        for m in file_layers._PDF_MARKER.finditer(data):
            if max(abs(float(v)) for v in m.groups()) > 1000:
                return False
    return True


class _NoFileLayers(file_layers.LayerMarkers):
    """Layers drawn as S-095 drew them: plain drawing, hidden layers left out."""

    def add(self, name, hidden, box, matrix):
        return None


@contextmanager
def plain_layers(monkeypatch):
    with monkeypatch.context() as m:
        m.setattr(export, "LayerMarkers", _NoFileLayers)
        yield


# ---------------------------------------------------------------- PDF
def test_pdf_lists_each_layer_as_an_optional_content_group(tmp_path):
    script()
    three_layers()
    f.save(str(tmp_path / "a.pdf"))
    names, order, off = ocprops(tmp_path / "a.pdf")
    assert names == ["sky", "sun", "ghost"]
    assert order == ["sky", "sun", "ghost"]                 # first-use order
    assert off == ["ghost"]                                 # the hidden layer is in the file, switched off
    assert PdfReader(str(tmp_path / "a.pdf")).pdf_header >= "%PDF-1.5"


def test_each_layer_is_one_form_xobject_carrying_its_ocg(tmp_path):
    script()
    f.background(255, 255, 255)
    f.fill(0, 128, 0)
    f.rect(5, 5, 10, 10)                                   # canvas drawing: no OCG
    with f.layer("b"):
        f.circle(30, 30, 10)
    with f.layer("a"):
        f.circle(60, 30, 10)
    f.save(str(tmp_path / "a.pdf"))
    drawn = layer_xobjects(tmp_path / "a.pdf")
    assert [name for name, _ in drawn] == ["b", "a"]        # stacked in first-use order, over the canvas
    ocgs = PdfReader(str(tmp_path / "a.pdf")).trailer["/Root"]["/OCProperties"]["/OCGs"]
    for (name, obj), ref in zip(drawn, ocgs):
        assert obj["/Subtype"] == "/Form" and obj.raw_get("/OC").idnum == ref.idnum
    assert no_marker_left(tmp_path / "a.pdf")


def test_text_in_a_layer_is_still_real_text(tmp_path):
    script(240, 80)
    f.background(255, 255, 255)
    with f.layer("words"):
        f.fill(0)
        f.text_size(20)
        f.text("Layered words", 10, 40)
    f.save(str(tmp_path / "t.pdf"))
    reader = PdfReader(str(tmp_path / "t.pdf"))
    assert "Layered words" in reader.pages[0].extract_text()
    doc = pypdfium2.PdfDocument(str(tmp_path / "t.pdf"))
    assert "Layered words" in doc[0].get_textpage().get_text_range()
    doc.close()
    assert [name for name, _ in layer_xobjects(tmp_path / "t.pdf")] == ["words"]
    assert no_marker_left(tmp_path / "t.pdf")


def test_pdf_looks_like_the_png_and_a_hidden_layer_is_off(tmp_path, monkeypatch):
    script()
    three_layers()
    f.save(str(tmp_path / "a.pdf"))
    f.save(str(tmp_path / "a.png"))
    with plain_layers(monkeypatch):
        f.save(str(tmp_path / "plain.pdf"))                # S-095's file: no OCGs, hidden left out
    page = render(tmp_path / "a.pdf")
    png = Image.open(tmp_path / "a.png").convert("RGB")
    assert mean_difference(page, png) < 0.5
    assert page.getpixel((100, 60)) == (255, 255, 255)      # pdfium keeps the OFF layer switched off
    assert page.getpixel((60, 55)) == (255, 220, 0)
    assert page.getpixel((10, 10)) == (0, 0, 255)
    assert mean_difference(render(tmp_path / "a.pdf", scale=4), render(tmp_path / "plain.pdf", scale=4)) < 0.05
    assert "/OCProperties" not in PdfReader(str(tmp_path / "plain.pdf")).trailer["/Root"]


def test_a_name_used_on_several_pages_is_one_ocg(tmp_path):
    script(60, 40)
    for colour in ((255, 0, 0), (0, 0, 255)):
        if colour == (0, 0, 255):
            f.new_page()
            with f.layer("notes"):
                f.circle(10, 10, 5)
        f.background(255, 255, 255)
        with f.layer("art"):
            f.no_stroke()
            f.fill(*colour)
            f.rect(0, 0, 30, 40)
    f.save(str(tmp_path / "doc.pdf"))
    names, order, off = ocprops(tmp_path / "doc.pdf")
    assert names == ["art", "notes"] and order == ["art", "notes"] and off == []
    first = dict((n, o) for n, o in layer_xobjects(tmp_path / "doc.pdf", 0))
    second = dict((n, o) for n, o in layer_xobjects(tmp_path / "doc.pdf", 1))
    assert set(first) == {"art"} and set(second) == {"art", "notes"}
    ref = PdfReader(str(tmp_path / "doc.pdf")).trailer["/Root"]["/OCProperties"]["/OCGs"][0]
    assert first["art"].raw_get("/OC").idnum == second["art"].raw_get("/OC").idnum == ref.idnum
    assert render(tmp_path / "doc.pdf", 0).getpixel((5, 20)) == (255, 0, 0)
    assert render(tmp_path / "doc.pdf", 1).getpixel((5, 20)) == (0, 0, 255)


def test_a_name_hidden_on_one_page_only_keeps_each_page_s_look(tmp_path):
    """One OCG cannot be both on and off: a name hidden on one page and shown on another is two
    OCGs with that name, the hidden one switched off."""
    script(60, 40)
    f.background(255, 255, 255)
    with f.layer("art"):
        f.no_stroke()
        f.fill(255, 0, 0)
        f.rect(0, 0, 30, 40)
    f.new_page()
    f.background(255, 255, 255)
    with f.layer("art"):
        f.no_stroke()
        f.fill(0, 0, 255)
        f.rect(0, 0, 30, 40)
    f.hide_layer("art")
    f.save(str(tmp_path / "doc.pdf"))
    names, order, off = ocprops(tmp_path / "doc.pdf")
    assert names == ["art", "art"] and off == ["art"]
    assert render(tmp_path / "doc.pdf", 0).getpixel((5, 20)) == (255, 0, 0)
    assert render(tmp_path / "doc.pdf", 1).getpixel((5, 20)) == (255, 255, 255)


def test_a_layer_past_the_history_limit_goes_in_its_ocg_as_pixels(tmp_path):
    script(60, 40)
    f.background(255, 255, 255)
    with f.layer("dense"):
        f.no_stroke()
        f.fill(0, 0, 255)
        for i in range(10_001):                           # past P3's limit: the layer keeps only pixels
            f.rect(0, 0, 30, 20)
    with f.layer("light"):
        f.no_stroke()
        f.fill(255, 0, 0)
        f.rect(40, 0, 20, 40)
    f.save(str(tmp_path / "p.pdf"))
    f.save(str(tmp_path / "p.svg"))
    drawn = dict(layer_xobjects(tmp_path / "p.pdf"))
    assert set(drawn) == {"dense", "light"}
    assert has_image_under(drawn["dense"]) and not has_image_under(drawn["light"])
    page = render(tmp_path / "p.pdf")
    assert page.getpixel((10, 10)) == (0, 0, 255) and page.getpixel((50, 20)) == (255, 0, 0)
    groups = layer_groups(tmp_path / "p.svg")
    assert [g.get(INKSCAPE + "label") for g in groups] == ["dense", "light"]
    assert groups[0].find(f".//{SVG}image") is not None
    assert groups[0].find(f".//{SVG}use") is None                        # the image itself, not a link
    assert groups[1].find(f".//{SVG}image") is None


def test_an_animated_sketch_saves_pdf_layers(tmp_path):
    s = Sketch(platform=HeadlessPlatform())
    api.use_sketch(s)

    def draw():
        f.background(255, 255, 255)
        with f.layer("a"):
            f.circle(10, 10, 8)
        with f.layer("b"):
            f.circle(10, 10, 4)
        f.hide_layer("b")
        f.save(str(tmp_path / "anim.pdf"))

    s.run_namespace({"setup": lambda: f.size(20, 20), "draw": draw}, max_frames=1)
    assert ocprops(tmp_path / "anim.pdf") == (["a", "b"], ["a", "b"], ["b"])


def test_if_the_layer_step_fails_the_pdf_is_saved_as_before(tmp_path, monkeypatch):
    def broken(self, path):
        raise RuntimeError("boom")

    monkeypatch.setattr(file_layers.LayerMarkers, "finish_pdf", broken)
    script(240, 80)
    three_layers()
    with f.layer("sky"):
        f.fill(0)
        f.text("Still text", 10, 40)
    f.save(str(tmp_path / "a.pdf"))
    reader = PdfReader(str(tmp_path / "a.pdf"))
    assert "/OCProperties" not in reader.trailer["/Root"]
    assert "Still text" in reader.pages[0].extract_text()   # the text step still ran
    page = render(tmp_path / "a.pdf")
    assert page.getpixel((100, 60)) == (255, 255, 255)      # the hidden layer is left out, as in S-095
    assert no_marker_left(tmp_path / "a.pdf")


# ---------------------------------------------------------------- SVG helpers
def layer_groups(path) -> list[ET.Element]:
    root = ET.parse(str(path)).getroot()
    return [g for g in root.iter(f"{SVG}g") if g.get(INKSCAPE + "groupmode") == "layer"]


def drawn_leaves(path, skip_hidden=True) -> list[tuple]:
    """What the SVG draws, in order: every shape and image as (tag, its look) with the transforms
    above it, following <use> links. Ids and clip paths are left out (Cairo numbers them)."""
    root = ET.parse(str(path)).getroot()
    by_id = {el.get("id"): el for el in root.iter() if el.get("id")}
    out: list[tuple] = []
    skip = {f"{SVG}{t}" for t in ("defs", "clipPath", "mask", "filter", "pattern", "symbol")}

    def visit(el, transforms):
        if el.tag in skip:
            return
        if skip_hidden and "display:none" in (el.get("style") or ""):
            return
        if el.get("transform"):
            transforms = transforms + (el.get("transform"),)
        tag = el.tag[len(SVG):]
        if tag == "use":
            x, y = el.get("x", "0"), el.get("y", "0")
            if (x, y) != ("0", "0"):
                transforms = transforms + (f"translate({x}, {y})",)
            visit(by_id[(el.get(XLINK + "href") or el.get("href"))[1:]], transforms)
            return
        if tag in ("path", "rect", "image", "circle", "ellipse", "line", "polygon", "polyline"):
            look = tuple(sorted((k, re.sub(r"url\(#[^)]*\)", "url()", v)) for k, v in el.attrib.items()
                                if k not in ("id", "clip-path")))
            out.append((tag, look, tuple(t for t in transforms if not re.fullmatch(
                r"matrix\(1, 0, 0, 1, -?0(\.0+\d*)?, -?0(\.0+\d*)?\)", t))))
        for child in el:
            visit(child, transforms)

    visit(root, ())
    return out


# ---------------------------------------------------------------- SVG
def test_svg_layers_are_inkscape_layer_groups(tmp_path):
    script()
    three_layers()
    f.save(str(tmp_path / "a.svg"))
    text = (tmp_path / "a.svg").read_text(encoding="utf-8")
    assert 'xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape"' in text
    groups = layer_groups(tmp_path / "a.svg")
    assert [g.get(INKSCAPE + "label") for g in groups] == ["sky", "sun", "ghost"]
    assert [g.get("id") for g in groups] == ["sky", "sun", "ghost"]
    assert [g.get("style") for g in groups] == [None, None, "display:none"]
    root = ET.parse(str(tmp_path / "a.svg")).getroot()
    top = [child.get(INKSCAPE + "label") for child in root if child.get(INKSCAPE + "groupmode") == "layer"]
    assert top == ["sky", "sun", "ghost"]                               # top-level, in first-use order
    assert not any(g.find(f".//{SVG}use") is not None for g in groups)  # the drawing itself, not a link


def test_svg_content_is_inside_its_layer_group(tmp_path):
    script()
    three_layers()
    f.fill(0, 255, 0)
    f.rect(0, 70, 10, 10)                                  # the canvas's own drawing
    f.save(str(tmp_path / "a.svg"))
    groups = {g.get(INKSCAPE + "label"): g for g in layer_groups(tmp_path / "a.svg")}

    def fills(el):
        return {p.get("fill") for p in el.iter(f"{SVG}path")} | {r.get("fill") for r in el.iter(f"{SVG}rect")}

    assert "rgb(0%, 0%, 100%)" in fills(groups["sky"])
    assert "rgb(100%, 86.27451%, 0%)" in fills(groups["sun"])
    assert "rgb(100%, 0%, 0%)" in fills(groups["ghost"])
    for g in groups.values():
        assert "rgb(0%, 100%, 0%)" not in fills(g)
    root = ET.parse(str(tmp_path / "a.svg")).getroot()
    clips = [p.get("d") for c in root.iter(f"{SVG}clipPath") for p in c.iter(f"{SVG}path")]
    assert not any(max(abs(float(v)) for v in re.findall(r"-?\d+\.?\d*", d)) > 1000 for d in clips)  # markers gone


def test_svg_looks_the_same_as_without_file_layers(tmp_path, monkeypatch):
    script()
    three_layers()
    with f.layer("sky"):
        f.fill(0)
        f.text_size(12)
        f.text("words", 5, 20)
    f.save(str(tmp_path / "a.svg"))
    with plain_layers(monkeypatch):
        f.save(str(tmp_path / "plain.svg"))                 # S-095's file: hidden layer left out
    assert "inkscape" not in (tmp_path / "plain.svg").read_text(encoding="utf-8")
    new = drawn_leaves(tmp_path / "a.svg")
    assert new == drawn_leaves(tmp_path / "plain.svg")
    assert len(drawn_leaves(tmp_path / "a.svg", skip_hidden=False)) > len(new)   # the hidden layer is there


def test_svg_ids_are_valid_unique_and_labels_verbatim(tmp_path):
    script()
    names = ["a b", "a_b", "clip-0", "3 trees", "café & <tea>", "source-1"]
    for name in names:
        with f.layer(name):
            f.circle(10, 10, 5)
    f.save(str(tmp_path / "a.svg"))
    root = ET.parse(str(tmp_path / "a.svg")).getroot()
    groups = layer_groups(tmp_path / "a.svg")
    assert [g.get(INKSCAPE + "label") for g in groups] == names
    ids = [el.get("id") for el in root.iter() if el.get("id")]
    assert len(ids) == len(set(ids))
    layer_ids = [g.get("id") for g in groups]
    assert all(NCNAME.match(i) for i in layer_ids)
    assert layer_ids[:2] == ["a_b", "a_b-2"] and layer_ids[3] == "layer-3_trees"


def test_an_empty_layer_still_has_its_group_in_order(tmp_path):
    script()
    with f.layer("first"):
        f.circle(10, 10, 5)
    f.layer("empty")
    with f.layer("last"):
        f.circle(30, 10, 5)
    f.save(str(tmp_path / "a.svg"))
    f.save(str(tmp_path / "a.pdf"))
    assert [g.get(INKSCAPE + "label") for g in layer_groups(tmp_path / "a.svg")] == ["first", "empty", "last"]
    assert ocprops(tmp_path / "a.pdf")[1] == ["first", "empty", "last"]


def test_if_the_layer_step_fails_the_svg_is_saved_as_before(tmp_path, monkeypatch):
    def broken(self, path):
        raise RuntimeError("boom")

    monkeypatch.setattr(file_layers.LayerMarkers, "finish_svg", broken)
    script()
    three_layers()
    f.save(str(tmp_path / "a.svg"))
    text = (tmp_path / "a.svg").read_text(encoding="utf-8")
    assert "inkscape" not in text
    assert "rgb(0%, 0%, 100%)" in text and "rgb(100%, 0%, 0%)" not in text   # hidden layer left out


def test_svg_pages_each_get_their_layers(tmp_path):
    script(40, 40)
    with f.layer("a"):
        f.circle(10, 10, 5)
    f.new_page()
    with f.layer("b"):
        f.circle(10, 10, 5)
    f.save(str(tmp_path / "doc.svg"))
    assert [g.get(INKSCAPE + "label") for g in layer_groups(tmp_path / "doc_1.svg")] == ["a"]
    assert [g.get(INKSCAPE + "label") for g in layer_groups(tmp_path / "doc_2.svg")] == ["b"]


# ---------------------------------------------------------------- no layers: the same bytes as before
@contextmanager
def fixed_pdf_date(monkeypatch):
    """Cairo writes the time into every PDF, and fontTools into every font subset; pin both so two
    saves can be compared byte for byte."""
    real = cairo.PDFSurface

    def surface(*args):
        s = real(*args)
        s.set_metadata(cairo.PDFMetadata.CREATE_DATE, "2026-01-01T00:00:00")
        return s

    with monkeypatch.context() as m:
        m.setattr(cairo, "PDFSurface", surface)
        m.setattr(head_table, "timestampNow", lambda: 0)   # fontTools stamps each font subset too
        yield


def before_s096(frame, path, w, h) -> None:
    """How funground wrote a one-page PDF or SVG before S-096 (with the SVG text step of S-097,
    which came later and runs whether or not there are layers)."""
    renderer = CairoRenderer()
    pdf = path.suffix == ".pdf"
    if pdf:
        renderer.pdf_text = PdfTextCollector()
    else:
        renderer.svg_text = SvgTextCollector()
    surface = (cairo.PDFSurface if pdf else cairo.SVGSurface)(str(path), w, h)
    renderer.draw(renderer.context_for(surface, 1.0), frame)
    surface.finish()
    if pdf:
        renderer.pdf_text.finish(str(path))
    else:
        renderer.svg_text.finish(str(path))


def same_bytes(a, b) -> bool:
    """Byte for byte, except the number Cairo gives each SVG source group: it counts them for the
    whole process, so two saves of the same frame differ there (old code against old code too)."""
    def numbered(path):
        return re.sub(rb"source-\d+", b"source-N", path.read_bytes())

    return numbered(a) == numbered(b)


@pytest.mark.parametrize("with_text", [False, True])
def test_a_sketch_without_layers_writes_the_same_bytes_as_before(tmp_path, monkeypatch, with_text):
    s = script()
    f.background(255, 255, 255)
    f.fill(255, 0, 0)
    f.circle(40, 40, 30)
    g = f.create_graphics(20, 20)
    g.background(0, 0, 255)
    f.image(g, 70, 10)
    if with_text:
        f.text("Hello", 10, 70)
    with fixed_pdf_date(monkeypatch):
        for ext in ("pdf", "svg"):
            f.save(str(tmp_path / f"new.{ext}"))
            before_s096(s.frame, tmp_path / f"old.{ext}", 120, 80)
            assert same_bytes(tmp_path / f"new.{ext}", tmp_path / f"old.{ext}"), ext
    assert b"inkscape" not in (tmp_path / "new.svg").read_bytes()


# ---------------------------------------------------------------- never on screen, in a PNG or by get()
def test_hidden_layers_are_only_in_the_file_ops(tmp_path):
    s = script(20, 20)
    f.background(255, 255, 255)
    with f.layer("h"):
        f.background(255, 0, 0)
    f.hide_layer("h")
    assert [op.layer for op in s._layer_ops()] == []
    ops = s._layer_ops(files=True)
    assert [(op.layer, op.layer_hidden) for op in ops] == [("h", True)]
    assert f.get(5, 5).rgba == (255, 255, 255, 255)
    page_ops = s._document_pages()[-1][2]                  # pages keep the hidden layer for their files
    assert any(isinstance(op, ir.Image) and op.layer_hidden for op in page_ops)
    renderer = CairoRenderer()                             # ... and a screen or PNG renderer skips it
    renderer.attach(20, 20)
    renderer.render(ir.Frame(list(page_ops)))
    assert bytes(renderer.pixels().data)[(5 * 20 + 5) * 4:(5 * 20 + 5) * 4 + 4] == b"\xff\xff\xff\xff"
    f.save(str(tmp_path / "a.png"))
    assert Image.open(tmp_path / "a.png").convert("RGB").getpixel((5, 5)) == (255, 255, 255)
    # the hidden flag is left out of serialised ops when False
    assert "layer_hidden" not in ir.op_to_jsonable(ir.Image("g", 1, 0, 0, 1, 1, layer="x"))


# ---------------------------------------------------------------- the markers
def test_layer_and_text_markers_never_read_as_each_other():
    layers = file_layers.LayerMarkers()
    identity = (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)
    corners = layers.add("a", False, (0, 0, 100, 50), identity)
    p0, p1, q, p2 = corners
    assert layers._decode(p0, p1, q, p2) == 0
    # a text marker's (a, b) are in [0.55, 0.95): not a layer number
    side = p1[0] - p0[0]
    text_q = (p0[0] + side * 0.6, p0[1] + side * 0.6)
    assert layers._decode(p0, p1, text_q, p2) is None
    # and a layer marker is off the text grid
    import funground.export.pdf_text as pt
    a = (q[0] - p0[0]) / side
    assert round((a - pt._LOW) / pt._STEP) >= pt._GRID
    # the marker is convex and holds the layer's whole box
    assert p0[0] <= 0 and p0[1] <= 0 and p0[0] + side / 2 >= 100 and p0[1] + side / 2 >= 50


def test_a_marker_under_a_transform_it_was_not_drawn_with_is_refused():
    layers = file_layers.LayerMarkers()
    p0, p1, q, p2 = layers.add("a", False, (0, 0, 10, 10), (1.0, 0.0, 0.0, 1.0, 0.0, 0.0))
    scaled = [(2 * x, 2 * y) for x, y in (p0, p1, q, p2)]
    with pytest.raises(RuntimeError, match="unexpected transform"):
        layers._decode(*scaled)


def test_svg_id():
    used = {"sky"}
    assert file_layers.svg_id("sky", used) == "sky-2"
    assert file_layers.svg_id("", set()) == "layer"
    assert file_layers.svg_id("-x", set()) == "layer--x"
    assert file_layers.svg_id("über", set()) == "_ber"


def test_a_push_left_open_on_the_canvas_does_not_move_the_layers_in_files(tmp_path):
    """Review fix: layers in PDF/SVG sit where the window shows them, whatever transform or clip the
    canvas left open at the end of the script."""
    import pypdfium2 as pdfium
    import funground as f
    from funground import api
    from funground.platform.headless import HeadlessPlatform
    from funground.sketch import Sketch

    api.use_sketch(Sketch(platform=HeadlessPlatform()))
    f.size(60, 40)
    f.background(255, 255, 255)
    with f.layer("dot"):
        f.no_stroke()
        f.fill(255, 0, 0)
        f.rect(5, 5, 10, 10)
    f.push()
    f.translate(30, 20)                    # left open at the end
    out = tmp_path / "open.pdf"
    f.save(str(out))
    page = pdfium.PdfDocument(str(out))[0]
    img = page.render(scale=1).to_pil().convert("RGB")
    assert img.getpixel((10, 10)) == (255, 0, 0)        # the dot is where the window shows it
