"""Prototype for spike S-227: tidy a cut-out, turn it into an editable outline, snap the outline to edges.

Plain Python and pygame-ce only (no numpy). It uses funground's public pictures, nothing private:

    mask  = mask_from_picture(me)          # me.remove_background(empty) was called first
    mask  = tidy(mask)                     # (a) keep the largest part, fill its holes
    pts   = outline_points(mask, 200)      # (b) the border as at most 200 points
    pts   = snap_to_edges(pts, photo, 4)   # (d) move each point to the nearest strong edge
    me2   = cut_out_with_path(photo, pts)  # the path cuts the photo out

A mask here is a pygame.mask.Mask: one bit per pixel, True for "this pixel is the person".
"""
from __future__ import annotations

import math

import pygame

import funground as f

Point = tuple[float, float]


# ------------------------------------------------------------------------------------ pictures and masks
def picture_to_surface(picture) -> pygame.Surface:
    """A funground picture as a pygame surface (a copy of its pixels: red, green, blue, alpha)."""
    picture.load_pixels()
    return pygame.image.frombytes(bytes(picture.pixels), (picture.width, picture.height), "RGBA")


def surface_to_picture(surface: pygame.Surface):
    """A pygame surface as a new funground picture."""
    w, h = surface.get_size()
    picture = f.create_graphics(w, h)
    picture.load_pixels()
    picture.pixels[:] = pygame.image.tobytes(surface, "RGBA")
    picture.update_pixels()
    return picture


def mask_from_picture(picture, threshold: int = 127) -> pygame.mask.Mask:
    """The pixels that are not see-through (alpha above *threshold*): after remove_background, that is you."""
    return pygame.mask.from_surface(picture_to_surface(picture), threshold)


def mask_to_picture(picture, mask: pygame.mask.Mask):
    """A copy of *picture* that is see-through wherever *mask* is not set."""
    pixels = bytearray(pygame.image.tobytes(picture_to_surface(picture), "RGBA"))
    shown = mask.to_surface(setcolor=(255, 255, 255, 255), unsetcolor=(0, 0, 0, 255))
    pixels[3::4] = pygame.image.tobytes(shown, "RGBA")[0::4]
    out = f.create_graphics(picture.width, picture.height)
    out.load_pixels()
    out.pixels[:] = pixels
    out.update_pixels()
    return out


# ------------------------------------------------------------------------------------ (a) tidy the mask
def tidy(mask: pygame.mask.Mask, at: tuple[int, int] | None = None) -> pygame.mask.Mask:
    """Keep one connected part and fill its holes. The input is not changed.

    The part is the largest one, or, when *at* is a pixel (a click on yourself), the part that pixel is in.
    If *at* is not in the mask, the largest part is used.

    The largest part drops the specks (bits of room that look like you). A hole is a piece of the outside that
    does not reach the border, so the outside is found by flooding from a one-pixel frame put round the picture;
    whatever the flood does not reach is you. Everything here runs in C inside pygame-ce."""
    width, height = mask.get_size()
    if mask.count() == 0:
        return mask.copy()
    body = mask.connected_component(at) if at is not None and mask.get_at(at) else mask.connected_component()
    framed = pygame.mask.Mask((width + 2, height + 2), fill=True)
    framed.erase(body, (1, 1))                              # the outside, with a frame of set bits round it
    outside = framed.connected_component((0, 0))            # the part of the outside that touches the frame
    filled = pygame.mask.Mask((width, height), fill=True)
    filled.erase(outside, (-1, -1))                         # everything else: the body and its holes
    return filled


# ------------------------------------------------------------------------------------ (b) the outline
def _deviations(points: list[Point]) -> dict[int, float]:
    """Ramer-Douglas-Peucker without a cut-off: for each point, how far it was from the chord when it was chosen.

    The first and last point are never chosen. A point with a large number is a corner that matters."""
    deviation: dict[int, float] = {}
    stack = [(0, len(points) - 1)]
    while stack:
        a, b = stack.pop()
        if b - a < 2:
            continue
        ax, ay = points[a]
        dx, dy = points[b][0] - ax, points[b][1] - ay
        length = math.hypot(dx, dy)
        far, far_at = -1.0, a
        for i in range(a + 1, b):
            px, py = points[i]
            d = abs(dx * (py - ay) - dy * (px - ax)) / length if length else math.hypot(px - ax, py - ay)
            if d > far:
                far, far_at = d, i
        deviation[far_at] = far
        stack.append((a, far_at))
        stack.append((far_at, b))
    return deviation


def thin(points: list[Point], max_points: int) -> list[Point]:
    """Fewer points for a closed outline: the *max_points* that matter most (Ramer-Douglas-Peucker order)."""
    n = len(points)
    if n <= max_points:
        return list(points)
    ax, ay = points[0]
    opposite = max(range(n), key=lambda i: (points[i][0] - ax) ** 2 + (points[i][1] - ay) ** 2)
    first = points[:opposite + 1]                           # the closed outline, cut in two at its far ends
    second = points[opposite:] + [points[0]]
    scored = [(d, i) for i, d in _deviations(first).items()]
    scored += [(d, opposite + i) for i, d in _deviations(second).items()]
    keep = {0, opposite} | {i for _d, i in sorted(scored, reverse=True)[:max_points - 2]}
    return [points[i] for i in sorted(keep)]


def outline_points(mask: pygame.mask.Mask, max_points: int = 200) -> list[Point]:
    """The border of the (tidied) mask as a closed outline of at most *max_points* points."""
    return thin([(float(x), float(y)) for x, y in mask.outline()], max_points)


def polygon_to_mask(points: list[Point], size: tuple[int, int]) -> pygame.mask.Mask:
    """The pixels inside a polygon (pygame's rasteriser: the edge pixels count as inside)."""
    surface = pygame.Surface(size, pygame.SRCALPHA)
    pygame.draw.polygon(surface, (255, 255, 255, 255), points)
    return pygame.mask.from_surface(surface, 127)


def cut_out_with_path(picture, points: list[Point]):
    """A copy of *picture* cut out by the outline, with funground's own path and Picture.mask (public API only)."""
    stencil = f.create_graphics(picture.width, picture.height)
    stencil.no_stroke()
    stencil.fill("white")
    stencil.draw_path(f.path().polygon(points))
    out = picture.copy()
    out.mask(stencil)
    return out


# ------------------------------------------------------------------------------------ (d) edges
def edge_strength(picture, radius: int = 1) -> pygame.Surface:
    """Brightness of the picture, lightly blurred (noise would otherwise be taken for edges). Grey, one channel used."""
    return pygame.transform.gaussian_blur(pygame.transform.grayscale(picture_to_surface(picture)), radius)


def snap_to_edges(points: list[Point], picture, radius: int = 4, min_edge: int = 6) -> list[Point]:
    """Move each point along the outline's normal, up to *radius* pixels, to where the brightness changes most.

    *picture* is the photo with you in it (not the cut-out). The change is measured over two pixels across the
    outline. A point stays where it is when nothing changes by at least *min_edge* levels nearby. Ties go to the
    nearest place."""
    grey = edge_strength(picture)
    w, h = grey.get_size()

    def level(x: float, y: float) -> int:
        return grey.get_at((min(w - 1, max(0, round(x))), min(h - 1, max(0, round(y)))))[0]

    snapped: list[Point] = []
    n = len(points)
    for i, (x, y) in enumerate(points):
        px, py = points[(i - 1) % n]
        nx, ny = points[(i + 1) % n]
        tx, ty = nx - px, ny - py
        length = math.hypot(tx, ty) or 1.0
        ux, uy = -ty / length, tx / length                  # the normal: the tangent turned a quarter
        best, best_t = 0.0, 0
        for t in range(-radius, radius + 1):
            cx, cy = x + ux * t, y + uy * t
            change = abs(level(cx + ux, cy + uy) - level(cx - ux, cy - uy))
            score = change * (1 - 0.1 * abs(t) / radius)
            if change >= min_edge and score > best:
                best, best_t = score, t
        snapped.append((x + ux * best_t, y + uy * best_t))
    return snapped


# ------------------------------------------------------------------------------------ measuring helpers
def fit(mask: pygame.mask.Mask, truth: pygame.mask.Mask) -> dict:
    """How well *mask* matches the truth: IoU, false positives (specks), false negatives (holes), parts."""
    inside = mask.overlap_area(truth, (0, 0))
    total, wanted = mask.count(), truth.count()
    return {
        "iou": round(inside / (total + wanted - inside), 4) if total + wanted - inside else 1.0,
        "false_positive": total - inside,
        "false_negative": wanted - inside,
        "parts": len(mask.connected_components()) if total else 0,
    }
