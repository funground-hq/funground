"""Text subsystem v1: outline route (S-029). Module is `typography`, not `text`, so it cannot shadow the public p.text()."""
from __future__ import annotations

import hashlib
import os

import pytest

from playground import ir
from playground.color import BLACK
from playground.typography import DEFAULT_FONT, FontResource, TextRun, default_font


def test_bundled_font_and_licence_ship_with_the_package():
    assert os.path.exists(DEFAULT_FONT)
    assert os.path.exists(os.path.join(os.path.dirname(DEFAULT_FONT), "DejaVu-LICENSE.txt"))
    assert default_font().family == "DejaVu Sans"


def test_shape_returns_glyphs_and_outline_ops_anchor_top_left():
    run = default_font().shape("H", 30)
    assert isinstance(run, TextRun) and len(run.glyphs) == 1
    ops = run.outline_ops(40, 20, BLACK)
    assert len(ops) == 1 and isinstance(ops[0], ir.FillPath)
    x0, y0, x1, y1 = ops[0].path.bounds()
    assert 40 <= x0 < 46 and 20 <= y0 < 32          # ink starts just right/below the anchor
    assert y1 <= 20 + 30                             # and stays inside the em box height


def test_kerning_and_ligature_come_from_harfbuzz():
    f = default_font()
    av = f.shape("AVATAR", 24)
    naive = sum(f._hb.get_glyph_h_advance(g.gid) for g in av.glyphs) * av.scale
    assert av.advance < naive                        # kerned
    assert len(f.shape("office", 24).glyphs) == 4    # 'fi' ligature


def test_outline_cache_is_per_glyph():
    f = FontResource(DEFAULT_FONT)
    f.shape("aaa", 12).outline_ops(0, 0, BLACK)
    assert len(f._outlines) == 1


def test_outlines_are_deterministic_across_runs():
    def digest():
        ops = default_font().shape("Hello, Playground!", 24).outline_ops(5, 5, BLACK)
        return hashlib.sha256(repr([o.path.segments for o in ops]).encode()).hexdigest()
    assert digest() == digest()


def test_space_produces_no_path_but_advances():
    run = default_font().shape("a b", 20)
    ops = run.outline_ops(0, 0, BLACK)
    assert len(ops) == 2 and run.advance > 2 * run.outline_ops(0, 0, BLACK)[0].path.bounds()[2]


def test_unicode_shaping_is_not_latin_only():
    run = default_font().shape("Привет αβγ", 20)
    assert len(run.outline_ops(0, 0, BLACK)) == 9  # 6 Cyrillic + 3 Greek glyphs, space skipped


# ---------------------------------------------------------------- S-037: text polish
def test_renderer_text_run_cache_is_an_lru_capped_at_256():
    """S-037.1: `p.text(p.frame_count, ...)` must not grow the per-window cache without bound."""
    from playground.renderers.cairo2d import TEXT_RUN_CACHE_SIZE, CairoRenderer
    from playground.state import GraphicsState

    assert TEXT_RUN_CACHE_SIZE == 256
    r = CairoRenderer()
    r.attach(200, 100)
    style = GraphicsState()
    for frame in range(1000):
        r.render(ir.Frame([ir.Clear(BLACK), ir.Text(str(frame), 10, 10, BLACK, style)]))
        assert len(r._text_runs) <= 256
    assert len(r._text_runs) == 256
    # The most recent runs survive, the oldest were evicted.
    assert ("999", 20) in r._text_runs and ("0", 20) not in r._text_runs


def test_text_run_cache_evicts_least_recently_used_not_oldest_inserted():
    from playground.renderers.cairo2d import CairoRenderer
    from playground.state import GraphicsState

    r = CairoRenderer()
    r.attach(50, 50)
    style = GraphicsState()
    for i in range(256):
        r.render(ir.Frame([ir.Text(str(i), 0, 0, BLACK, style)]))
    r.render(ir.Frame([ir.Text("0", 0, 0, BLACK, style)]))       # touch "0": now most recently used
    r.render(ir.Frame([ir.Text("new", 0, 0, BLACK, style)]))     # evicts "1", not "0"
    assert ("0", 20) in r._text_runs and ("1", 20) not in r._text_runs and len(r._text_runs) == 256


def test_text_width_is_the_shaped_advance_in_logical_pixels():
    import playground as p
    from playground.typography import text_width

    p.text_size(20)
    assert p.text_width("") == 0.0
    assert p.text_width("Hello") == default_font().shape("Hello", 20).advance
    assert p.text_width("Hello") == text_width("Hello", 20)
    w20 = p.text_width("Hello")
    p.text_size(40)
    assert p.text_width("Hello") == pytest.approx(2 * w20)       # grows linearly with size (T3: n-pixel em)
    assert p.text_width(3.5) == p.text_width("3.5")              # T5: str() is applied
    assert isinstance(p.text_width("x"), float)


def test_text_width_is_kerned_like_the_rendered_text():
    import playground as p

    p.text_size(24)
    f = default_font()
    unkerned = sum(f._hb.get_glyph_h_advance(g.gid) for g in f.shape("AVATAR", 24).glyphs) * (24 / f.units_per_em)
    assert p.text_width("AVATAR") < unkerned


def test_text_width_ignores_transforms(canvas):
    import playground as p

    p.text_size(20)
    w = p.text_width("scaled?")
    with p.saved_state():
        p.scale(3)
        assert p.text_width("scaled?") == w


def test_text_width_centres_text(canvas):
    """The learner recipe: p.text(msg, (p.width - p.text_width(msg)) / 2, y)."""
    import playground as p
    from tests.test_semantics import _ink_bbox

    msg = "Centred"
    p.background("white")
    p.fill("black")
    p.text_size(24)
    x = (p.width - p.text_width(msg)) / 2
    p.text(msg, x, 30)
    x0, y0, x1, y1 = _ink_bbox(canvas, (255, 255, 255))
    left_gap, right_gap = x0, canvas.get_size()[0] - 1 - x1
    assert abs(left_gap - right_gap) <= 3                          # side bearings differ by a pixel or two
