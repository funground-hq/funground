"""Spike 08, Part 1 -- runs INSIDE Pyodide (see feasibility.mjs).

Imports the pure-Python core, drives a Session-1-scale sketch through a
rAF-style stub platform and a Canvas-2D-call-counting stub renderer, then
times fontTools outline extraction in wasm and Frame.to_jsonable().
Evaluates to one JSON string (the last expression).
"""
import json
import os
import sys
import time

# /playground inside Pyodide; SPIKE_ROOT=<repo> runs this same file under native CPython
ROOT = os.environ.get("SPIKE_ROOT", "/playground")
sys.path.insert(0, ROOT)
R = {}
perf = time.perf_counter

# ---- (d) import the core ------------------------------------------------
t0 = perf()
import playground                                    # noqa: E402
from playground import api, color, geometry, ir, sketch, state  # noqa: E402,F401
R["import_ms"] = round((perf() - t0) * 1000, 2)
R["python"] = sys.version.split()[0]
R["playground_version"] = playground.__version__

from playground.capabilities import Capability       # noqa: E402
from playground.platform.base import InputState, Pixels  # noqa: E402


class BrowserPlatform:
    """rAF-style stub: the host drives frames, so tick() never waits."""

    backing_scale = 1.0

    def __init__(self):
        self._t = perf()
        self.frames_presented = 0

    def open_window(self, width, height, title):
        return (width, height)

    def start(self):
        self._t = perf()

    def poll(self):
        return True

    def input_state(self):
        return InputState()

    def key_down(self, key):
        return False

    def present(self, pixels):
        self.frames_presented += 1

    def tick(self, fps):
        now = perf()
        dt, self._t = now - self._t, now
        return dt

    def capture(self):
        return ((0, 0), b"")

    def close(self):
        pass


class Canvas2DStubRenderer:
    """Walks the IR exactly as a Canvas2DRenderer would, counting the
    Canvas 2D calls it would make instead of making them (no DOM in Node)."""

    name = "canvas2d-stub"
    capabilities = frozenset({
        Capability.RASTER_2D, Capability.ALPHA, Capability.ANTIALIAS, Capability.TRANSFORMS,
        Capability.VECTOR_PATHS, Capability.CLIP_PATH, Capability.TEXT_OUTLINES,
    })

    def __init__(self):
        self.calls = 0
        self.ops = 0
        self.render_s = 0.0
        self.w = self.h = 0

    def attach(self, width, height, scale=1.0):
        self.w, self.h = width, height

    def _paint(self, style):
        n = 0
        if style.fill is not None:
            n += 2                                   # fillStyle=, fill()
        if style.stroke is not None:
            n += 3                                   # strokeStyle=, lineWidth=, stroke()
        return n

    def _path(self, path):
        return 1 + len(path)                         # beginPath + one call per segment

    def render(self, frame):
        t0 = perf()
        calls = 0
        for op in frame:
            t = type(op)
            self.ops += 1
            if t is ir.Clear:
                calls += 2                           # fillStyle=, fillRect
            elif t is ir.Circle or t is ir.Ellipse:
                calls += 2 + self._paint(op.style)   # beginPath, arc/ellipse
            elif t is ir.Rect:
                calls += 2 + self._paint(op.style)   # beginPath, rect
            elif t is ir.Line:
                calls += (3 + 3) if op.style.stroke is not None else 0
            elif t is ir.Point:
                calls += (2 + 2) if op.style.stroke is not None else 0
            elif t is ir.Text:
                calls += 3                           # font=, fillStyle=, fillText
            elif t is ir.Save or t is ir.Restore or t is ir.Concat:
                calls += 1
            elif t is ir.ClipPath:
                calls += self._path(op.path) + 1
            elif t is ir.FillPath:
                calls += self._path(op.path) + 2
            elif t is ir.StrokePath:
                calls += self._path(op.path) + 3
        self.calls += calls
        self.render_s += perf() - t0

    def pixels(self):
        return Pixels(b"", self.w, self.h, "RGBA")


# ---- Session-1-scale sketch: 50 circles + text, 60 frames ---------------
plat = BrowserPlatform()
rend = Canvas2DStubRenderer()
s = api.use_sketch(sketch.Sketch(plat, rend))
p = playground


def setup():
    p.size(640, 400)


def draw():
    p.background("white")
    p.stroke("black")
    for i in range(50):
        p.fill((255, 99, 71, 200) if i % 2 else "steelblue")
        p.circle(40 + (i % 10) * 60, 60 + (i // 10) * 70, 40 + (p.frame_count % 20))
    p.fill("black")
    p.text_size(28)
    p.text("Hello, Playground!", 30, 340)
    p.text(p.frame_count, 500, 340, color="navy")


FRAMES = 60
ns = {"setup": setup, "draw": draw}
t0 = perf()
s.run_namespace(ns, max_frames=FRAMES)
total_s = perf() - t0
R["frames"] = FRAMES
R["ops_per_frame"] = rend.ops // FRAMES
R["canvas_calls_per_frame"] = rend.calls // FRAMES
R["frame_ms"] = round(total_s / FRAMES * 1000, 3)          # api + IR build + stub render
R["render_walk_ms"] = round(rend.render_s / FRAMES * 1000, 3)
R["api_and_ir_ms"] = round((total_s - rend.render_s) / FRAMES * 1000, 3)
last_ops = s.last_ops
assert last_ops is not None and plat.frames_presented == FRAMES

# ---- (f) Frame.to_jsonable() for that frame ------------------------------
frame = ir.Frame(list(last_ops))
REPS = 20
t0 = perf()
for _ in range(REPS):
    data = frame.to_jsonable()
R["to_jsonable_ms"] = round((perf() - t0) / REPS * 1000, 3)
t0 = perf()
for _ in range(REPS):
    js = json.dumps(data)
R["json_dumps_ms"] = round((perf() - t0) / REPS * 1000, 3)
R["json_bytes"] = len(js)
t0 = perf()
for _ in range(REPS):
    ir.Frame.from_jsonable(data)
R["from_jsonable_ms"] = round((perf() - t0) / REPS * 1000, 3)

# ---- (e) fontTools outlines in wasm --------------------------------------
from fontTools.pens.basePen import BasePen   # noqa: E402
from fontTools.ttLib import TTFont           # noqa: E402
from playground.geometry import Path, Transform  # noqa: E402

t0 = perf()
tt = TTFont(os.path.join(ROOT, "playground", "fonts", "DejaVuSans.ttf"))
upem = tt["head"].unitsPerEm
ascent = tt["hhea"].ascent
cmap = tt.getBestCmap()
glyph_set = tt.getGlyphSet()
hmtx = tt["hmtx"]
R["font_load_ms"] = round((perf() - t0) * 1000, 2)


class PathPen(BasePen):
    def __init__(self, gs):
        super().__init__(gs)
        self.path = Path()

    def _moveTo(self, p): self.path = self.path.move_to(*p)
    def _lineTo(self, p): self.path = self.path.line_to(*p)
    def _curveToOne(self, c1, c2, p): self.path = self.path.cubic_to(*c1, *c2, *p)
    def _qCurveToOne(self, q, p): self.path = self.path.quad_to(*q, *p)
    def _closePath(self): self.path = self.path.close()
    def _endPath(self): self.path = self.path.close()


_cache = {}


def outline(name):
    p = _cache.get(name)
    if p is None:
        pen = PathPen(glyph_set)
        glyph_set[name].draw(pen)
        p = _cache[name] = pen.path
    return p


TEXT = "Hello, Playground!"
names = [cmap[ord(ch)] for ch in TEXT]
t0 = perf()
for n in names:
    outline(n)
R["outline_ms_uncached"] = round((perf() - t0) * 1000, 3)     # cache cold: 18 glyphs
t0 = perf()
for _ in range(REPS):
    for n in names:
        outline(n)
R["outline_ms_cached"] = round((perf() - t0) / REPS * 1000, 4)  # cache warm: 18 lookups

# per-frame cost the real typography module pays: cached outline -> transformed FillPath
size = 28
sc = size / upem
t0 = perf()
for _ in range(REPS):
    pen_x, ops = 30.0, []
    for n in names:
        o = outline(n)
        if not o.is_empty:
            t = Transform.scaling(sc, -sc).then(Transform.translation(pen_x, 340 + ascent * sc))
            ops.append(ir.FillPath(o.transformed(t), color.Color(0, 0, 0)))
        pen_x += hmtx[n][0] * sc
R["text_fillpath_ops_ms"] = round((perf() - t0) / REPS * 1000, 3)
R["text_fillpath_segments"] = sum(len(o.path) for o in ops)
R["text_glyphs"] = len(names)
R["upem"] = upem
R["hhea_ascent"] = ascent

if __name__ == "__main__":          # native CPython comparison run
    print(json.dumps(R))
json.dumps(R)                       # the value Pyodide's runPython returns
