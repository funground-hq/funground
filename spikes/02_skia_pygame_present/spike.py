"""Spike 02 - Skia renders the frame, pygame-ce presents it.

Measures the per-frame cost of the "one rasteriser + pygame presentation"
topology recommended in the review (Issue 1), at 640x400 and 1920x1080.

Variants:
  A. skia.Surface -> makeImageSnapshot().tobytes() -> pygame.image.frombuffer -> blit
  B. skia.Surface.MakeRasterDirect on a numpy buffer (Skia draws straight into
     memory) -> frombuffer wraps the same memory -> blit   (fewer copies)

Each variant is timed in three parts: skia draw, buffer->pygame surface, blit+flip.
Runs first on the dummy driver (no real flip), then on a hidden real window if
the platform allows it, so presentation cost is measured for real.
"""
import json
import math
import os
import sys
import time

import numpy as np

RESULTS = {"python": sys.version.split()[0], "runs": []}
OUT = os.path.dirname(os.path.abspath(__file__))


def scene(canvas, w, h, frame):
    """A frame with the kind of content the review says pygame cannot do:
    rotated stroked rects, an ellipse, translucent fills, a bezier, text."""
    import skia
    canvas.clear(skia.ColorWHITE)
    fill = skia.Paint(AntiAlias=True, Color=skia.ColorSetARGB(255, 255, 99, 71))
    stroke = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=6,
                        Color=skia.ColorBLACK, StrokeJoin=skia.Paint.kRound_Join)
    for k in range(50):
        canvas.save()
        canvas.translate(w * 0.1 + k * (w * 0.8 / 50), h / 2)
        canvas.rotate(frame + k * 7)
        r = skia.Rect.MakeLTRB(-w * 0.05, -h * 0.03, w * 0.05, h * 0.03)
        canvas.drawRect(r, fill)
        canvas.drawRect(r, stroke)
        canvas.restore()
    trans = skia.Paint(AntiAlias=True, Color=skia.ColorSetARGB(96, 70, 130, 180))
    canvas.drawOval(skia.Rect.MakeXYWH(w * 0.3, h * 0.2, w * 0.4, h * 0.6), trans)
    path = skia.Path()
    path.moveTo(0, h)
    path.cubicTo(w * 0.3, 0, w * 0.7, h, w, 0)
    canvas.drawPath(path, stroke)
    font = skia.Font(skia.Typeface("Arial"), h * 0.08)
    canvas.drawString(f"frame {frame}", w * 0.05, h * 0.12, font, skia.Paint(AntiAlias=True))


def run(w, h, frames, driver):
    import skia
    import pygame

    os.environ["SDL_VIDEODRIVER"] = driver
    pygame.display.quit()
    pygame.display.init()
    flags = 0 if driver == "dummy" else pygame.HIDDEN
    screen = pygame.display.set_mode((w, h), flags)
    out = {"size": f"{w}x{h}", "driver": driver, "frames": frames}

    # ---- Variant A: snapshot + tobytes + frombuffer
    surf = skia.Surface(w, h)
    canvas = surf.getCanvas()
    t_draw = t_conv = t_blit = 0.0
    for f in range(frames):
        t0 = time.perf_counter()
        scene(canvas, w, h, f)
        t1 = time.perf_counter()
        img = surf.makeImageSnapshot()
        buf = img.tobytes()
        ps = pygame.image.frombuffer(buf, (w, h), "BGRA" if skia.kN32_ColorType == skia.kBGRA_8888_ColorType else "RGBA")
        t2 = time.perf_counter()
        screen.blit(ps, (0, 0))
        pygame.display.flip()
        t3 = time.perf_counter()
        t_draw += t1 - t0; t_conv += t2 - t1; t_blit += t3 - t2
    out["A_snapshot_tobytes"] = {k: round(v / frames * 1000, 3) for k, v in
                                {"skia_draw_ms": t_draw, "to_pygame_ms": t_conv, "blit_flip_ms": t_blit,
                                 "total_ms": t_draw + t_conv + t_blit}.items()}

    # ---- Variant B: Skia draws straight into a numpy buffer that pygame wraps
    arr = np.zeros((h, w, 4), dtype=np.uint8)
    info = skia.ImageInfo.MakeN32Premul(w, h)
    direct = skia.Surface.MakeRasterDirect(info, arr, w * 4)
    dcanvas = direct.getCanvas()
    fmt = "BGRA" if skia.kN32_ColorType == skia.kBGRA_8888_ColorType else "RGBA"
    t_draw = t_conv = t_blit = 0.0
    for f in range(frames):
        t0 = time.perf_counter()
        scene(dcanvas, w, h, f)
        t1 = time.perf_counter()
        ps = pygame.image.frombuffer(arr, (w, h), fmt)   # wraps memory, no copy
        t2 = time.perf_counter()
        screen.blit(ps, (0, 0))
        pygame.display.flip()
        t3 = time.perf_counter()
        t_draw += t1 - t0; t_conv += t2 - t1; t_blit += t3 - t2
    out["B_raster_direct"] = {k: round(v / frames * 1000, 3) for k, v in
                             {"skia_draw_ms": t_draw, "to_pygame_ms": t_conv, "blit_flip_ms": t_blit,
                              "total_ms": t_draw + t_conv + t_blit}.items()}
    out["B_fps_equivalent"] = round(1000 / out["B_raster_direct"]["total_ms"], 1)

    # ---- Baseline: what does an all-pygame frame of comparable (but wrong) content cost?
    t0 = time.perf_counter()
    for f in range(frames):
        screen.fill("white")
        for k in range(50):
            cx, cy = w * 0.1 + k * (w * 0.8 / 50), h / 2
            r = math.radians(f + k * 7)
            c, s = math.cos(r), math.sin(r)
            pts = [(cx + c * x - s * y, cy + s * x + c * y) for x, y in
                   ((-w * 0.05, -h * 0.03), (w * 0.05, -h * 0.03), (w * 0.05, h * 0.03), (-w * 0.05, h * 0.03))]
            pygame.draw.polygon(screen, "tomato", pts)
            pygame.draw.polygon(screen, "black", pts, width=6)
        pygame.display.flip()
    out["pygame_only_baseline_ms"] = round((time.perf_counter() - t0) / frames * 1000, 3)

    if driver != "dummy":
        pygame.image.save(screen, os.path.join(OUT, f"frame_{w}x{h}.png"))
    else:
        pygame.image.save(ps, os.path.join(OUT, f"skia_frame_{w}x{h}.png"))
    RESULTS["runs"].append(out)
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    import skia, pygame
    RESULTS["skia_python"] = skia.__version__
    RESULTS["pygame_ce"] = pygame.version.ver
    RESULTS["numpy"] = np.__version__
    pygame.init()
    for (w, h) in ((640, 400), (1280, 720), (1920, 1080)):
        run(w, h, 120, "dummy")
    try:
        for (w, h) in ((640, 400), (1280, 720), (1920, 1080)):
            run(w, h, 120, "windows")
    except Exception as e:  # no display / headless CI
        RESULTS["real_display_error"] = repr(e)
        print("real display run failed:", e)
    pygame.quit()
    json.dump(RESULTS, open(os.path.join(OUT, "results.json"), "w"), indent=2)
