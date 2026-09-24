"""Spike 05 - Skia vs Cairo bake-off behind one tiny draw-op IR.

The same scene is described once as a list of backend-neutral ops (the review's
"draw-op IR" idea) and rendered by two thin adapters: CairoRenderer and
SkiaRenderer. Both must do: rect, circle, bezier path, fill, stroke, translate,
rotate, scale, clip, linear gradient, text, PNG, PDF, SVG, pygame presentation.

Outputs: <backend>_<WxH>.png, <backend>.pdf, <backend>.svg, results.json.
"""
import json
import math
import os
import sys
import time

import numpy as np

OUT = os.path.dirname(os.path.abspath(__file__))
RESULTS = {"python": sys.version.split()[0], "backends": {}, "timing": []}

# ----------------------------------------------------------------- the IR
# (op, *args). Colours are (r, g, b, a) 0-255. Angles in degrees.
def scene_ops(w, h, frame):
    ops = [("clear", (255, 255, 255, 255))]
    for k in range(50):
        ops += [("save",),
                ("translate", w * 0.1 + k * (w * 0.8 / 50), h / 2),
                ("rotate", frame + k * 7),
                ("scale", 1.0, 1.0),
                ("fill", (255, 99, 71, 255)),
                ("stroke", (0, 0, 0, 255), 6),
                ("rect", -w * 0.05, -h * 0.03, w * 0.1, h * 0.06),
                ("restore",)]
    ops += [("save",),
            ("clip_circle", w / 2, h / 2, min(w, h) * 0.35),
            ("gradient", (0, 0), (w, h), (70, 130, 180, 200), (255, 215, 0, 200)),
            ("no_stroke",),
            ("circle", w / 2, h / 2, min(w, h) * 0.35),
            ("restore",),
            ("no_fill",),
            ("stroke", (0, 0, 0, 255), 6),
            ("bezier", (0, h), (w * 0.3, 0), (w * 0.7, h), (w, 0)),
            ("fill", (0, 0, 0, 255)),
            ("text", f"frame {frame}", w * 0.05, h * 0.12, h * 0.08)]
    return ops


# ----------------------------------------------------------------- Cairo
class CairoRenderer:
    name = "cairo"

    def __init__(self, w, h, target="raster"):
        import cairo
        self.cairo, self.w, self.h = cairo, w, h
        if target == "raster":
            self.surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
        elif target == "pdf":
            self.surface = cairo.PDFSurface(os.path.join(OUT, "cairo.pdf"), w, h)
        elif target == "svg":
            self.surface = cairo.SVGSurface(os.path.join(OUT, "cairo.svg"), w, h)
        self.ctx = cairo.Context(self.surface)
        self._fill = (0, 0, 0, 255); self._stroke = None; self._grad = None

    def _rgba(self, c):
        return (c[0] / 255, c[1] / 255, c[2] / 255, c[3] / 255)

    def _paint(self):
        c = self.ctx
        if self._grad is not None:
            c.set_source(self._grad); c.fill_preserve()
        elif self._fill is not None:
            c.set_source_rgba(*self._rgba(self._fill)); c.fill_preserve()
        if self._stroke is not None:
            col, wdt = self._stroke
            c.set_source_rgba(*self._rgba(col)); c.set_line_width(wdt)
            c.set_line_join(self.cairo.LINE_JOIN_ROUND); c.stroke_preserve()
        c.new_path()

    def run(self, ops):
        c = self.ctx
        for op in ops:
            k = op[0]
            if k == "clear":
                c.save(); c.identity_matrix(); c.set_source_rgba(*self._rgba(op[1])); c.paint(); c.restore()
            elif k == "save": c.save()
            elif k == "restore": c.restore()
            elif k == "translate": c.translate(op[1], op[2])
            elif k == "rotate": c.rotate(math.radians(op[1]))
            elif k == "scale": c.scale(op[1], op[2])
            elif k == "fill": self._fill = op[1]; self._grad = None
            elif k == "no_fill": self._fill = None; self._grad = None
            elif k == "stroke": self._stroke = (op[1], op[2])
            elif k == "no_stroke": self._stroke = None
            elif k == "gradient":
                g = self.cairo.LinearGradient(op[1][0], op[1][1], op[2][0], op[2][1])
                g.add_color_stop_rgba(0, *self._rgba(op[3])); g.add_color_stop_rgba(1, *self._rgba(op[4]))
                self._grad = g
            elif k == "rect": c.rectangle(op[1], op[2], op[3], op[4]); self._paint()
            elif k == "circle": c.arc(op[1], op[2], op[3], 0, 2 * math.pi); self._paint()
            elif k == "clip_circle": c.arc(op[1], op[2], op[3], 0, 2 * math.pi); c.clip()
            elif k == "bezier":
                c.move_to(*op[1]); c.curve_to(*op[2], *op[3], *op[4]); self._paint()
            elif k == "text":
                c.select_font_face("Arial"); c.set_font_size(op[4])
                asc = c.font_extents()[0]
                c.move_to(op[2], op[3] + asc)        # top-left anchoring per proposed contract
                c.set_source_rgba(*self._rgba(self._fill)); c.show_text(op[1]); c.new_path()

    # presentation / export
    def buffer(self):
        self.surface.flush()
        return self.surface.get_data()           # premultiplied BGRA (little-endian ARGB32)

    def save_png(self, path):
        self.surface.write_to_png(path)

    def finish(self):
        self.surface.finish()


# ----------------------------------------------------------------- Skia
class SkiaRenderer:
    name = "skia"

    def __init__(self, w, h, target="raster"):
        import skia
        self.skia, self.w, self.h = skia, w, h
        self.doc = self.stream = None
        if target == "raster":
            self.arr = np.zeros((h, w, 4), dtype=np.uint8)
            self.surface = skia.Surface.MakeRasterDirect(skia.ImageInfo.MakeN32Premul(w, h), self.arr, w * 4)
            self.canvas = self.surface.getCanvas()
        elif target == "pdf":
            self.stream = skia.FILEWStream(os.path.join(OUT, "skia.pdf"))
            self.doc = skia.PDF.MakeDocument(self.stream)
            self.canvas = self.doc.beginPage(w, h)
        elif target == "svg":
            self.stream = skia.FILEWStream(os.path.join(OUT, "skia.svg"))
            self.canvas = skia.SVGCanvas.Make(skia.Rect.MakeWH(w, h), self.stream)
        self._fill = (0, 0, 0, 255); self._stroke = None; self._grad = None
        try:
            self.typeface = skia.Typeface("Arial")
        except Exception:
            self.typeface = skia.Typeface.MakeDefault()

    def _color(self, c):
        return self.skia.ColorSetARGB(c[3], c[0], c[1], c[2])

    def _paint(self, path):
        sk = self.skia
        if self._grad is not None or self._fill is not None:
            p = sk.Paint(AntiAlias=True)
            if self._grad is not None: p.setShader(self._grad)
            else: p.setColor(self._color(self._fill))
            self.canvas.drawPath(path, p)
        if self._stroke is not None:
            col, wdt = self._stroke
            p = sk.Paint(AntiAlias=True, Style=sk.Paint.kStroke_Style, StrokeWidth=wdt,
                         StrokeJoin=sk.Paint.kRound_Join, Color=self._color(col))
            self.canvas.drawPath(path, p)

    def run(self, ops):
        sk, c = self.skia, self.canvas
        for op in ops:
            k = op[0]
            if k == "clear": c.clear(self._color(op[1]))
            elif k == "save": c.save()
            elif k == "restore": c.restore()
            elif k == "translate": c.translate(op[1], op[2])
            elif k == "rotate": c.rotate(op[1])
            elif k == "scale": c.scale(op[1], op[2])
            elif k == "fill": self._fill = op[1]; self._grad = None
            elif k == "no_fill": self._fill = None; self._grad = None
            elif k == "stroke": self._stroke = (op[1], op[2])
            elif k == "no_stroke": self._stroke = None
            elif k == "gradient":
                self._grad = sk.GradientShader.MakeLinear(
                    points=[sk.Point(*op[1]), sk.Point(*op[2])],
                    colors=[self._color(op[3]), self._color(op[4])])
            elif k == "rect":
                path = sk.Path(); path.addRect(sk.Rect.MakeXYWH(op[1], op[2], op[3], op[4])); self._paint(path)
            elif k == "circle":
                path = sk.Path(); path.addCircle(op[1], op[2], op[3]); self._paint(path)
            elif k == "clip_circle":
                path = sk.Path(); path.addCircle(op[1], op[2], op[3]); c.clipPath(path, doAntiAlias=True)
            elif k == "bezier":
                path = sk.Path(); path.moveTo(*op[1]); path.cubicTo(*op[2], *op[3], *op[4]); self._paint(path)
            elif k == "text":
                font = sk.Font(self.typeface, op[4])
                asc = -font.getMetrics().fAscent
                c.drawString(op[1], op[2], op[3] + asc, font, sk.Paint(AntiAlias=True, Color=self._color(self._fill)))

    def buffer(self):
        return self.arr

    def save_png(self, path):
        self.surface.makeImageSnapshot().save(path, self.skia.kPNG)

    def finish(self):
        if self.doc is not None:
            self.doc.endPage(); self.doc.close()
        elif self.stream is not None:
            del self.canvas; self.stream.flush()


# ----------------------------------------------------------------- harness
def time_backend(cls, w, h, frames, screen, pygame):
    r = cls(w, h)
    fmt = "BGRA"
    t_draw = t_present = 0.0
    for f in range(frames):
        t0 = time.perf_counter()
        r.run(scene_ops(w, h, f))
        t1 = time.perf_counter()
        ps = pygame.image.frombuffer(r.buffer(), (w, h), fmt)
        screen.blit(ps, (0, 0)); pygame.display.flip()
        t2 = time.perf_counter()
        t_draw += t1 - t0; t_present += t2 - t1
    r.save_png(os.path.join(OUT, f"{cls.name}_{w}x{h}.png"))
    return {"backend": cls.name, "size": f"{w}x{h}", "draw_ms": round(t_draw / frames * 1000, 3),
            "present_ms": round(t_present / frames * 1000, 3),
            "fps_equivalent": round(frames / (t_draw + t_present), 1)}


def export_checks(cls):
    out = {}
    for target in ("pdf", "svg"):
        try:
            r = cls(640, 400, target); r.run(scene_ops(640, 400, 7)); r.finish()
            path = os.path.join(OUT, f"{cls.name}.{target}")
            out[target] = {"ok": True, "bytes": os.path.getsize(path)}
        except Exception as e:
            out[target] = {"ok": False, "error": repr(e)}
    return out


if __name__ == "__main__":
    import cairo, skia, pygame
    RESULTS["versions"] = {"pycairo": cairo.version, "cairo": cairo.cairo_version_string(),
                           "skia_python": skia.__version__, "pygame_ce": pygame.version.ver}
    os.environ["SDL_VIDEODRIVER"] = "windows"
    pygame.init()
    try:
        screen = pygame.display.set_mode((640, 400), pygame.HIDDEN)
    except Exception:
        os.environ["SDL_VIDEODRIVER"] = "dummy"; pygame.display.quit(); pygame.display.init()
        screen = pygame.display.set_mode((640, 400))
    for (w, h) in ((640, 400), (1280, 720), (1920, 1080)):
        screen = pygame.display.set_mode((w, h), pygame.HIDDEN if os.environ["SDL_VIDEODRIVER"] != "dummy" else 0)
        for cls in (CairoRenderer, SkiaRenderer):
            res = time_backend(cls, w, h, 60, screen, pygame)
            RESULTS["timing"].append(res); print(res)
    for cls in (CairoRenderer, SkiaRenderer):
        RESULTS["backends"][cls.name] = {"export": export_checks(cls)}
        print(cls.name, RESULTS["backends"][cls.name])
    pygame.quit()
    json.dump(RESULTS, open(os.path.join(OUT, "results.json"), "w"), indent=2)
