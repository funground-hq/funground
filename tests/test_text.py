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
