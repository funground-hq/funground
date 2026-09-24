"""Spike 06 - deterministic single-line text from a bundled font (story S-031).

Route under test (D-006):
    bundled TTF -> uharfbuzz shaping (glyph ids + positions)
                -> fontTools glyph outlines (cached per glyph id, in font units)
                -> path ops (the future IR) -> Cairo fill

Compared against Cairo's "toy" text API (system font by name) and pygame's
default font. Measures quality (PNGs), anchor correctness, per-frame cost with
and without the outline cache, byte-determinism across runs, and PDF/SVG.
Narrow scope: single line, no wrapping, no layout.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import time

import cairo
import uharfbuzz as hb
from fontTools.pens.basePen import BasePen
from fontTools.ttLib import TTFont

OUT = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(OUT, "fonts")
SIZES = (12, 16, 24, 36, 48)
STRINGS = ["ABC xyz 123", "Hello, Playground!", "AVATAR", "office", "Привет, мир — αβγδ"]
DEVANAGARI = "नमस्ते दुनिया"


# ------------------------------------------------------------------ outlines
class OpsPen(BasePen):
    """Records a glyph outline as backend-neutral ops in font units."""

    def __init__(self, glyph_set):
        super().__init__(glyph_set)
        self.ops: list[tuple] = []

    def _moveTo(self, p):
        self.ops.append(("move", p))

    def _lineTo(self, p):
        self.ops.append(("line", p))

    def _curveToOne(self, c1, c2, p):
        self.ops.append(("cubic", c1, c2, p))

    def _qCurveToOne(self, q, p):          # quadratic -> cubic
        p0 = self._getCurrentPoint()
        c1 = (p0[0] + 2 / 3 * (q[0] - p0[0]), p0[1] + 2 / 3 * (q[1] - p0[1]))
        c2 = (p[0] + 2 / 3 * (q[0] - p[0]), p[1] + 2 / 3 * (q[1] - p[1]))
        self.ops.append(("cubic", c1, c2, p))

    def _closePath(self):
        self.ops.append(("close",))

    def _endPath(self):
        self.ops.append(("close",))


class FontResource:
    """HarfBuzz font + fontTools glyph set + glyph-outline cache (see Text_Subsystem_Note)."""

    def __init__(self, path: str):
        self.path = path
        self.tt = TTFont(path)
        self.upem = self.tt["head"].unitsPerEm
        self.ascent = self.tt["hhea"].ascent
        self.descent = self.tt["hhea"].descent
        self.glyph_order = self.tt.getGlyphOrder()
        self.glyph_set = self.tt.getGlyphSet()
        with open(path, "rb") as f:
            self.hb_font = hb.Font(hb.Face(f.read()))
        self.hb_font.scale = (self.upem, self.upem)
        self._cache: dict[int, tuple] = {}
        self.outline_builds = 0

    def outline(self, gid: int, use_cache: bool = True):
        if use_cache and gid in self._cache:
            return self._cache[gid]
        pen = OpsPen(self.glyph_set)
        self.glyph_set[self.glyph_order[gid]].draw(pen)
        ops = tuple(pen.ops)
        self.outline_builds += 1
        if use_cache:
            self._cache[gid] = ops
        return ops

    def shape(self, text: str):
        buf = hb.Buffer()
        buf.add_str(text)
        buf.guess_segment_properties()
        hb.shape(self.hb_font, buf, {"kern": True, "liga": True})
        return [(i.codepoint, p.x_advance, p.x_offset, p.y_offset) for i, p in zip(buf.glyph_infos, buf.glyph_positions)]


def text_ops(font: FontResource, text: str, x: float, y: float, size: float, use_cache=True):
    """Top-left anchored (contract T1): baseline = y + ascent."""
    s = size / font.upem
    pen_x = x
    baseline = y + font.ascent * s
    ops = []
    for gid, adv, dx, dy in font.shape(text):
        ox, oy = pen_x + dx * s, baseline - dy * s
        for op in font.outline(gid, use_cache):
            if op[0] == "close":
                ops.append(("close",))
            else:
                pts = [(ox + px * s, oy - py * s) for px, py in op[1:]]
                ops.append((op[0], *pts))
        pen_x += adv * s
    return ops


def fill_ops(ctx: cairo.Context, ops, rgb=(0, 0, 0)):
    ctx.new_path()
    for op in ops:
        k = op[0]
        if k == "move": ctx.move_to(*op[1])
        elif k == "line": ctx.line_to(*op[1])
        elif k == "cubic": ctx.curve_to(*op[1], *op[2], *op[3])
        elif k == "close": ctx.close_path()
    ctx.set_source_rgb(*rgb)
    ctx.set_fill_rule(cairo.FILL_RULE_WINDING)
    ctx.fill()


# ------------------------------------------------------------------ harness
def sheet(font: FontResource, strings, title: str):
    """Grid: rows = strings, columns = sizes; outlines only."""
    w, h = 1400, 60 * len(strings) * 2 + 40
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
    ctx = cairo.Context(surf)
    ctx.set_source_rgb(1, 1, 1); ctx.paint()
    y = 10
    for s in strings:
        x = 10
        for size in SIZES:
            # anchor guide: red dot at (x, y) - ink must start at/right-below it
            ctx.set_source_rgb(1, 0, 0); ctx.arc(x, y, 1.5, 0, 6.3); ctx.fill()
            fill_ops(ctx, text_ops(font, s, x, y, size))
            x += 40 + size * 5.5
        y += 56 + 48
    surf.flush()
    path = os.path.join(OUT, f"{title}_outlines.png")
    surf.write_to_png(path)
    return path


def comparison(font: FontResource, size: int, title: str):
    """Three columns at one size: outlines / cairo toy API / pygame default font."""
    import pygame
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    pygame.init(); pygame.font.init()
    strings = STRINGS[:4]
    w, h = 1300, 20 + len(strings) * (size + 16)
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
    ctx = cairo.Context(surf)
    ctx.set_source_rgb(1, 1, 1); ctx.paint()
    pg = pygame.Surface((420, h)); pg.fill((255, 255, 255))
    pf = pygame.font.Font(None, int(size * 1.4))  # pygame's size unit is not px; scale roughly
    y = 10
    for s in strings:
        fill_ops(ctx, text_ops(font, s, 10, y, size))
        ctx.select_font_face("Arial"); ctx.set_font_size(size)
        ctx.move_to(440, y + ctx.font_extents()[0]); ctx.set_source_rgb(0, 0, 0); ctx.show_text(s)
        pg.blit(pf.render(s, True, (0, 0, 0)), (10, y))
        y += size + 16
    surf.flush()
    # paste pygame column into the cairo sheet
    data = pygame.image.tobytes(pg, "BGRA")
    pgs = cairo.ImageSurface.create_for_data(bytearray(data), cairo.FORMAT_ARGB32, 420, h, 420 * 4)
    ctx.set_source_surface(pgs, 870, 0); ctx.paint()
    ctx.set_source_rgb(0.5, 0.5, 0.5); ctx.select_font_face("Arial"); ctx.set_font_size(11)
    for label, x in (("outlines (bundled font)", 10), ("cairo toy API (system Arial)", 440), ("pygame default font", 880)):
        ctx.move_to(x, h - 4); ctx.show_text(label)
    path = os.path.join(OUT, f"{title}_compare_{size}px.png")
    surf.write_to_png(path)
    pygame.quit()
    return path


def timing(font: FontResource, text: str, size: int, frames=200):
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, 640, 100)
    ctx = cairo.Context(surf)
    out = {}
    for label, cache in (("no_cache", False), ("cache", True)):
        font._cache.clear(); font.outline_builds = 0
        t0 = time.perf_counter()
        for _ in range(frames):
            ctx.set_source_rgb(1, 1, 1); ctx.paint()
            fill_ops(ctx, text_ops(font, text, 10, 10, size, use_cache=cache))
        dt = (time.perf_counter() - t0) / frames * 1000
        out[label] = {"ms_per_frame": round(dt, 3), "outline_builds": font.outline_builds}
    # split the cached cost: shaping vs geometry+fill
    t0 = time.perf_counter()
    for _ in range(frames): font.shape(text)
    out["shape_only_ms"] = round((time.perf_counter() - t0) / frames * 1000, 3)
    return out


def determinism(font: FontResource):
    def render():
        surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, 800, 200)
        ctx = cairo.Context(surf); ctx.set_source_rgb(1, 1, 1); ctx.paint()
        y = 5
        for s in STRINGS[:4]:
            fill_ops(ctx, text_ops(font, s, 5, y, 24)); y += 40
        surf.flush()
        return hashlib.sha256(bytes(surf.get_data())).hexdigest()
    a, b = render(), render()
    return {"identical_across_runs": a == b, "sha256": a[:16]}


def exports(font: FontResource, title: str):
    res = {}
    for kind, cls in (("pdf", cairo.PDFSurface), ("svg", cairo.SVGSurface)):
        path = os.path.join(OUT, f"{title}.{kind}")
        surf = cls(path, 640, 200)
        ctx = cairo.Context(surf)
        y = 10
        for s in STRINGS[:4]:
            fill_ops(ctx, text_ops(font, s, 10, y, 24)); y += 40
        surf.finish()
        res[kind] = os.path.getsize(path)
    return res


def anchor_check(font: FontResource):
    """Ink of 'H' at (40, 20) must start at x>=40 and y>=20, within a few px (contract T1)."""
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, 200, 100)
    ctx = cairo.Context(surf); ctx.set_source_rgb(1, 1, 1); ctx.paint()
    fill_ops(ctx, text_ops(font, "H", 40, 20, 30)); surf.flush()
    data, stride = surf.get_data(), surf.get_stride()
    xs, ys = [], []
    for y in range(100):
        for x in range(200):
            if data[y * stride + x * 4 + 1] < 128:  # green channel dark = ink
                xs.append(x); ys.append(y)
    return {"ink_x0": min(xs), "ink_y0": min(ys), "anchor": (40, 20)}


if __name__ == "__main__":
    results = {"python": sys.version.split()[0], "pycairo": cairo.version, "fonts": {}}
    candidates = [f for f in sorted(os.listdir(FONTS)) if f.endswith(".ttf")]
    for fname in candidates:
        path = os.path.join(FONTS, fname)
        title = fname.split("[")[0].replace("-Regular", "").replace(".ttf", "")
        font = FontResource(path)
        r = {"file_bytes": os.path.getsize(path), "upem": font.upem, "glyphs": len(font.glyph_order)}
        strings = list(STRINGS)
        if "Devanagari" in fname:
            strings = [DEVANAGARI, "नमस्ते"]
        try:
            r["sheet"] = os.path.basename(sheet(font, strings, title))
            if "Devanagari" not in fname:
                r["compare_12"] = os.path.basename(comparison(font, 12, title))
                r["compare_24"] = os.path.basename(comparison(font, 24, title))
                r["timing_hello_24px"] = timing(font, "Hello, Playground!", 24)
                r["timing_hello_48px"] = timing(font, "Hello, Playground!", 48)
                r["anchor"] = anchor_check(font)
            r["determinism"] = determinism(font) if "Devanagari" not in fname else None
            r["exports"] = exports(font, title)
            # shaping evidence: kerning (AVATAR narrower than sum of advances?) and ligature (office -> fewer glyphs)
            if "Devanagari" not in fname:
                av = font.shape("AVATAR"); r["AVATAR_glyphs"] = len(av)
                naive = sum(font.hb_font.get_glyph_h_advance(g) for g, *_ in av)
                r["AVATAR_kerned_narrower"] = sum(a for _, a, _, _ in av) < naive
                r["office_glyph_count"] = len(font.shape("office"))
            else:
                r["devanagari_glyph_count"] = len(font.shape(DEVANAGARI))
                r["devanagari_codepoints"] = len(DEVANAGARI)
        except Exception as e:
            r["error"] = repr(e)
        results["fonts"][fname] = r
        print(fname, json.dumps(r, indent=1, default=str))
    json.dump(results, open(os.path.join(OUT, "results.json"), "w"), indent=2, default=str)
