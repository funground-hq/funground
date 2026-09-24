"""Spike 01 - Can pygame.draw alone implement Playground's core model
(transform stack + stroked paths + clipping)?

Question from the review (Issue 1): if pygame-ce is a peer *renderer* that must
satisfy draw_path(path, state) with an affine transform in the state, how much of
that work does pygame.draw do for us?

Runs headless (SDL dummy driver) and writes PNGs + results.json.
"""
import json
import math
import os
import sys
import time

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
import pygame  # noqa: E402

OUT = os.path.dirname(os.path.abspath(__file__))
W, H = 640, 400
results = {"pygame_ce": pygame.version.ver, "python": sys.version.split()[0], "cases": {}}


def affine(tx, ty, deg, sx=1.0, sy=1.0):
    """Minimal affine matrix (a, b, c, d, e, f) - Playground would own this."""
    r = math.radians(deg)
    cos, sin = math.cos(r), math.sin(r)
    return (cos * sx, sin * sx, -sin * sy, cos * sy, tx, ty)


def apply(m, x, y):
    a, b, c, d, e, f = m
    return (a * x + c * y + e, b * x + d * y + f)


def save(surf, name):
    path = os.path.join(OUT, name)
    pygame.image.save(surf, path)
    return name


pygame.init()
screen = pygame.display.set_mode((W, H))
api = {n: hasattr(pygame.draw, n) for n in ("polygon", "aapolygon", "aaline", "aacircle", "aaellipse", "lines", "aalines")}
results["pygame_draw_api"] = api

# ---------------------------------------------------------------- case 1
# Rotated *filled* rectangle: doable - transform 4 corners ourselves, draw.polygon.
screen.fill("white")
m = affine(320, 200, 30)
corners = [apply(m, x, y) for x, y in ((-100, -40), (100, -40), (100, 40), (-100, 40))]
pygame.draw.polygon(screen, "tomato", corners)
results["cases"]["rotated_filled_rect"] = {
    "possible": True,
    "how": "Playground computes the affine and transforms corners; pygame.draw.polygon fills.",
    "cost": "Transform math lives entirely in Playground - pygame contributes nothing here.",
    "png": save(screen, "01_rotated_filled_rect.png"),
}

# ---------------------------------------------------------------- case 2
# Rotated *stroked* rectangle with stroke_width=12: polygon(width=n) strokes
# each edge as an independent thick line -> no proper joins, and the stroke is
# not centred on the path the way Skia/cairo/p5 define it.
screen.fill("white")
pygame.draw.polygon(screen, "black", corners, width=12)
# zoom the corner so the join defect is visible in the PNG
crop = screen.subsurface(pygame.Rect(int(corners[0][0]) - 30, int(corners[0][1]) - 30, 60, 60)).copy()
zoom = pygame.transform.scale(crop, (240, 240))
results["cases"]["rotated_stroked_rect"] = {
    "possible": "partially",
    "how": "pygame.draw.polygon(width=12) on transformed corners.",
    "defect": "Edges are drawn as separate thick segments: joins are notched/gapped, "
              "no miter/round/bevel control, stroke alignment differs from every vector model.",
    "png": save(screen, "02_rotated_stroked_rect.png"),
    "png_join_zoom": save(zoom, "02b_join_zoom.png"),
}

# ---------------------------------------------------------------- case 3
# Rotated ellipse: pygame.draw.ellipse takes an axis-aligned Rect only.
# Only route: polygonise the ellipse ourselves and use polygon -> we are now
# writing the curve flattener the architecture says is a non-goal.
screen.fill("white")
pts = [apply(m, 100 * math.cos(t), 40 * math.sin(t)) for t in (i / 64 * 2 * math.pi for i in range(64))]
pygame.draw.polygon(screen, "steelblue", pts)
pygame.draw.polygon(screen, "black", pts, width=4)
results["cases"]["rotated_ellipse"] = {
    "possible": "only by flattening to a polygon in Playground",
    "how": "64-segment polygonisation done in Python; pygame.draw.ellipse cannot rotate.",
    "png": save(screen, "03_rotated_ellipse.png"),
}

# ---------------------------------------------------------------- case 4
# Anti-aliasing: does pygame-ce give us AA for the shapes above?
screen.fill("white")
aa_note = {}
if api.get("aapolygon"):
    pygame.draw.aapolygon(screen, "tomato", corners)
    aa_note["fill"] = "pygame.draw.aapolygon available (fill only)"
else:
    pygame.draw.polygon(screen, "tomato", corners)
    aa_note["fill"] = "no aapolygon in this pygame-ce"
# there is no anti-aliased *thick* stroke primitive at all
pygame.draw.aalines(screen, "black", True, corners)
aa_note["stroke"] = "aalines is 1px only - no anti-aliased thick stroke exists"
results["cases"]["antialiasing"] = {"possible": "partially", **aa_note, "png": save(screen, "04_antialiasing.png")}

# ---------------------------------------------------------------- case 5
# Clipping to a rotated shape: Surface.set_clip is an axis-aligned Rect.
screen.fill("white")
screen.set_clip(pygame.Rect(220, 120, 200, 160))
for i in range(0, W, 20):
    pygame.draw.line(screen, "gray", (i, 0), (i, H), 2)
screen.set_clip(None)
pygame.draw.polygon(screen, "black", corners, width=2)  # the shape we *wanted* to clip to
results["cases"]["clip_to_rotated_shape"] = {
    "possible": False,
    "how": "set_clip accepts only a Rect; arbitrary-path clipping needs a mask + per-pixel blend "
           "(pygame.mask / surfarray) - i.e. a rasteriser written in Playground.",
    "png": save(screen, "05_clip_rect_only.png"),
}

# ---------------------------------------------------------------- case 6
# Rotated text: pygame.font renders axis-aligned; rotation = raster resample of
# the rendered bitmap (pygame.transform.rotate), not glyph outlines under a transform.
screen.fill("white")
font = pygame.font.Font(None, 48)
txt = font.render("rotated text", True, "black")
rot = pygame.transform.rotate(txt, -30)
screen.blit(rot, rot.get_rect(center=(320, 200)))
results["cases"]["rotated_text"] = {
    "possible": "raster approximation only",
    "how": "render bitmap then pygame.transform.rotate -> resampled, blurry at small sizes, "
           "no outline access, no hinting under transform.",
    "png": save(screen, "06_rotated_text.png"),
}

# ---------------------------------------------------------------- case 7
# Alpha fill on a shape: pygame.draw ignores alpha on the target surface's blend;
# needs a temp SRCALPHA surface + blit per shape.
screen.fill("white")
pygame.draw.polygon(screen, (255, 99, 71, 96), corners)          # alpha silently ignored -> opaque
tmp = pygame.Surface((W, H), pygame.SRCALPHA)
pygame.draw.polygon(tmp, (70, 130, 180, 96), [(x + 60, y + 40) for x, y in corners])
screen.blit(tmp, (0, 0))                                          # translucent only via temp surface
results["cases"]["translucent_fill"] = {
    "possible": "only via a temporary SRCALPHA surface per shape",
    "how": "Direct draw ignores alpha (left/red shape opaque); right/blue shape used a temp surface.",
    "png": save(screen, "07_alpha_fill.png"),
}

# ---------------------------------------------------------------- case 8
# Bezier curve path: no bezier primitive in pygame.draw at all.
results["cases"]["bezier_path"] = {
    "possible": False,
    "how": "No curve primitive; Playground would flatten cubic/quadratic curves itself.",
}

# ---------------------------------------------------------------- timing
# What does the manual-transform polygon route cost per frame?
t0 = time.perf_counter()
N = 300
for i in range(N):
    screen.fill("white")
    for k in range(50):
        mm = affine(100 + k * 8, 200, i + k * 7)
        cs = [apply(mm, x, y) for x, y in ((-30, -12), (30, -12), (30, 12), (-30, 12))]
        pygame.draw.polygon(screen, "tomato", cs)
        pygame.draw.polygon(screen, "black", cs, width=3)
dt = (time.perf_counter() - t0) / N * 1000
results["timing_ms_per_frame_50_rotated_stroked_rects_640x400"] = round(dt, 3)

pygame.quit()
json.dump(results, open(os.path.join(OUT, "results.json"), "w"), indent=2)
print(json.dumps(results, indent=2))
