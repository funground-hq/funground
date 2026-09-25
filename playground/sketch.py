"""The Sketch: one running (or runnable) Playground program.

Owns the lifecycle, live values, graphics state and helpers that v0.5 kept as
module globals in ``_core.py``. Talks to the OS only through a ``Platform`` and
draws only through a ``Renderer`` — never through pygame directly (see
tests/test_boundaries.py). ``api.py`` keeps the learner-facing functions as thin
wrappers over the active Sketch.
"""
from __future__ import annotations

import contextlib
import math
import random as _random
import warnings
from collections.abc import Callable, Iterator
from typing import Any

from . import ir
from .capabilities import Capability, PlaygroundWarning, missing_capability
from .color import WHITE, Color, ColorLike
from .geometry import Path, Transform
from .paths import PathBuilder
from .platform.base import KEY_NAMES, Platform
from .renderers import Renderer
from .state import GraphicsState, StateStack

# What the v0.5 public API needs from any renderer.
REQUIRED_CAPABILITIES: dict[Capability, str] = {Capability.RASTER_2D: "Drawing shapes"}

# Renderer selection (S-023.4). Future optional renderers (e.g. Blend2D, S-036) register here.
RENDERERS = {"cairo": "playground.renderers.cairo2d:CairoRenderer"}
DEFAULT_RENDERER = "cairo"


def default_platform() -> Platform:
    import os

    if os.environ.get("PLAYGROUND_HEADLESS", "").lower() in ("1", "true", "yes"):
        from .platform.headless import HeadlessPlatform

        return HeadlessPlatform()
    from .platform.pygame_platform import PygamePlatform

    return PygamePlatform()


def default_renderer() -> Renderer:
    import importlib
    import os

    name = os.environ.get("PLAYGROUND_RENDERER", DEFAULT_RENDERER).lower()
    if name not in RENDERERS:
        raise ValueError(f"PLAYGROUND_RENDERER must be one of {sorted(RENDERERS)}, not {name!r}")
    module, cls = RENDERERS[name].split(":")
    return getattr(importlib.import_module(module), cls)()

Namespace = dict[str, Any]


class Sketch:
    def __init__(self, platform: Platform | None = None, renderer: Renderer | None = None) -> None:
        if platform is None:
            platform = default_platform()
        if renderer is None:
            renderer = default_renderer()
        self._platform = platform
        self._renderer = renderer
        self._states = StateStack()
        # Ops recorded since the last render; consumed once per loop iteration.
        self.frame = ir.Frame()
        self._pending_saves: list[str] = []
        # The shape between begin_shape() and end_shape(), if one is open (S-028).
        self._shape: PathBuilder | None = None
        # Playground keeps its own generator so random_seed() never disturbs a
        # learner's own `import random`.
        self._rng = _random.Random()

        # Live values (contract R1, R4, R5, I1) and window settings.
        self.width = 640
        self.height = 480
        self.fps = 60
        self.title = "playground"
        self.mouse_x = 0
        self.mouse_y = 0
        self.mouse_pressed = False
        self.frame_count = 0
        self.delta_time = 0.0
        self.running = False
        self._has_window = False
        # ((width, height), RGB bytes) of the final frame when run(max_frames=)
        # stops the sketch; used by the regression suite.
        self.last_frame: tuple[tuple[int, int], bytes] | None = None

    # ------------------------------------------------------------ state
    @property
    def style(self) -> GraphicsState:
        return self._states.current

    def save_state(self) -> None:
        self._states.save()

    def restore_state(self) -> None:
        self._states.restore()

    # One stack for the transform *and* the style (contract F2): a push saves
    # both, a pop restores both - "restore restores everything".
    def push(self) -> None:
        self._emit(ir.Save())
        self._states.save()

    def pop(self) -> None:
        if self._states.depth == 0:
            warnings.warn(
                "p.pop() called without a matching p.push(); ignored.",
                PlaygroundWarning, stacklevel=3,
            )
            return
        self._states.restore()
        self._emit(ir.Restore())

    @contextlib.contextmanager
    def saved_state(self) -> Iterator[None]:
        """``with p.saved_state():`` - push on entry, pop on exit, even when the body raises."""
        self.push()
        depth = self._states.depth
        try:
            yield
        finally:
            # Pop back to where this block started, even if the body left pushes open.
            while self._states.depth >= depth:
                self.pop()

    def _end_draw(self) -> None:
        """End-of-frame safety (S-027.4): unwind pushes draw() left open, with a warning."""
        if self._shape is not None:
            self._shape = None
            warnings.warn(
                "draw() finished inside a shape: p.begin_shape() had no p.end_shape(), "
                "so nothing was drawn for it.",
                PlaygroundWarning, stacklevel=2,
            )
        open_pushes = self._states.unwind()
        if open_pushes:
            for _ in range(open_pushes):
                self.frame.append(ir.Restore())
            warnings.warn(
                f"draw() finished with {open_pushes} p.push() call(s) still open; "
                "Playground popped them for you. Add a matching p.pop(), or use "
                "`with p.saved_state():`.",
                PlaygroundWarning, stacklevel=2,
            )

    # ------------------------------------------------------------ transforms
    def translate(self, dx: float, dy: float) -> None:
        self._emit(ir.Concat(Transform.translation(dx, dy)))

    def rotate(self, degrees: float) -> None:
        """Rotate later drawing by *degrees* (contract F1): +90 turns +x into +y (clockwise on screen)."""
        self._emit(ir.Concat(Transform.rotation(degrees)))

    def scale(self, sx: float, sy: float | None = None) -> None:
        if sy is None:
            sy = sx
        if sx == 0 or sy == 0:
            raise ValueError("scale factor must not be 0 (nothing could be drawn)")
        self._emit(ir.Concat(Transform.scaling(sx, sy)))

    @staticmethod
    def radians(degrees: float) -> float:
        return math.radians(degrees)

    @staticmethod
    def degrees(radians: float) -> float:
        return math.degrees(radians)

    # ------------------------------------------------------------ window
    def size(self, width: int, height: int, *, title: str = "playground", fps: int = 60) -> None:
        if width <= 0 or height <= 0:
            raise ValueError("width and height must be positive")
        if fps <= 0:
            raise ValueError("fps must be positive")
        self.width = int(width)
        self.height = int(height)
        self.fps = int(fps)
        self.title = title
        self._check_capabilities()
        pw, ph = self._platform.open_window(self.width, self.height, self.title)
        self._renderer.attach(pw, ph, self._platform.backing_scale)
        self._has_window = True

    def _check_capabilities(self) -> None:
        """Refuse up front (contract R9) rather than failing on frame 200."""
        for cap, feature in REQUIRED_CAPABILITIES.items():
            if cap not in self._renderer.capabilities:
                raise missing_capability(cap, feature, getattr(self._renderer, "name", "selected"))

    def _require_window(self) -> None:
        if not self._has_window:
            raise RuntimeError("No drawing window yet. Call p.size(...) first.")

    def _emit(self, op: ir.Op) -> None:
        self._require_window()
        self.frame.append(op)

    def _render(self) -> None:
        """Draw everything recorded so far and present it; the frame then starts empty."""
        self._end_draw()
        if self.frame or self._pending_saves:
            self._renderer.render(self.frame)
            self._platform.present(self._renderer.pixels())
            self._flush_saves()
            self.frame.clear()

    # ------------------------------------------------------------ export
    def save(self, path: str) -> None:
        """Write this frame to a .png, .pdf or .svg file when the frame is complete."""
        from .export import format_of

        format_of(path)  # validate early so the learner sees the error at the call site
        self._require_window()
        self._pending_saves.append(path)

    def _flush_saves(self) -> None:
        if not self._pending_saves:
            return
        from .export import save_frame

        paths, self._pending_saves = self._pending_saves, []
        for path in paths:
            save_frame(self.frame, path, self.width, self.height, self._platform.backing_scale)

    # ------------------------------------------------------------ style
    def fill(self, color: ColorLike) -> None:
        self._states.update(fill=Color.parse(color))

    def no_fill(self) -> None:
        self._states.update(fill=None)

    def stroke(self, color: ColorLike) -> None:
        self._states.update(stroke=Color.parse(color))

    def no_stroke(self) -> None:
        self._states.update(stroke=None)

    def stroke_width(self, pixels: int) -> None:
        if pixels < 1:
            raise ValueError("stroke width must be at least 1")
        self._states.update(stroke_width=int(pixels))

    def text_size(self, size: int) -> None:
        if size <= 0:
            raise ValueError("text size must be positive")
        self._states.update(text_size=int(size))

    # ------------------------------------------------------------ drawing
    def background(self, color: ColorLike) -> None:
        self._emit(ir.Clear(Color.parse(color)))

    def circle(self, x: float, y: float, diameter: float) -> None:
        self._emit(ir.Circle(x, y, diameter, self.style))

    def ellipse(self, x: float, y: float, width: float, height: float) -> None:
        self._emit(ir.Ellipse(x, y, width, height, self.style))

    def rect(self, x: float, y: float, width: float, height: float) -> None:
        self._emit(ir.Rect(x, y, width, height, self.style))

    def line(self, x1: float, y1: float, x2: float, y2: float) -> None:
        self._emit(ir.Line(x1, y1, x2, y2, self.style))

    def point(self, x: float, y: float) -> None:
        self._emit(ir.Point(x, y, self.style))

    def text(self, message: object, x: float, y: float, color: ColorLike | None = None) -> None:
        style = self.style
        if color is not None:
            chosen = Color.parse(color)
        else:
            chosen = style.fill or style.stroke or WHITE  # contract T4
        self._emit(ir.Text(str(message), x, y, chosen, style))

    def text_width(self, message: object) -> float:
        """Advance width of *message* in logical pixels at the current text_size (contract T6)."""
        from .typography import text_width

        return text_width(str(message), self.style.text_size)

    # ------------------------------------------------------------ shapes, paths, clipping (S-028)
    def begin_shape(self) -> None:
        if self._shape is not None:
            raise RuntimeError("p.begin_shape() called again before p.end_shape(); finish the first shape.")
        self._shape = PathBuilder()

    def vertex(self, x: float, y: float) -> None:
        shape = self._open_shape("vertex")
        if shape.is_empty:
            shape.move_to(x, y)       # the first corner starts the shape
        else:
            shape.line_to(x, y)

    def curve_vertex(self, cx1: float, cy1: float, cx2: float, cy2: float, x: float, y: float) -> None:
        shape = self._open_shape("curve_vertex")
        if shape.is_empty:
            raise RuntimeError("p.curve_vertex() needs a starting corner: call p.vertex(x, y) first.")
        shape.curve_to(cx1, cy1, cx2, cy2, x, y)

    def end_shape(self, close: bool = False) -> None:
        """Contract F3: closed shapes are filled then stroked; open ones are stroked only."""
        shape = self._open_shape("end_shape")
        self._shape = None
        if close and not shape.is_empty:
            shape.close()
        self._emit_path(shape.geometry)

    def _open_shape(self, name: str) -> PathBuilder:
        if self._shape is None:
            raise RuntimeError(f"p.{name}() called outside a shape: call p.begin_shape() first.")
        return self._shape

    @staticmethod
    def path() -> PathBuilder:
        return PathBuilder()

    def draw_path(self, path: PathBuilder | Path) -> None:
        self._emit_path(_geometry_of(path, "draw_path"))

    def clip(self, path: PathBuilder | Path) -> None:
        """Limit later drawing to *path* (implicitly closed); pop() lifts it, so use it inside push()/pop()."""
        self._emit(ir.ClipPath(_geometry_of(path, "clip")))

    def _emit_path(self, geometry: Path) -> None:
        self._require_window()
        if geometry.is_empty:
            return
        style = self.style
        if style.fill is not None and geometry.is_closed:      # F3: open shapes are never filled
            self._emit(ir.FillPath(geometry, style.fill))
        if style.stroke is not None:                           # S5: stroke on top of the fill
            self._emit(ir.StrokePath(geometry, style.stroke, float(style.stroke_width)))

    # ------------------------------------------------------------ helpers
    def random(self, low: float = 1.0, high: float | None = None) -> float:
        if high is None:
            high = low
            low = 0.0
        return self._rng.uniform(low, high)

    def random_seed(self, seed: int | None = None) -> None:
        self._rng.seed(seed)

    @staticmethod
    def constrain(value: float, low: float, high: float) -> float:
        return max(low, min(high, value))

    @staticmethod
    def distance(x1: float, y1: float, x2: float, y2: float) -> float:
        return math.hypot(x2 - x1, y2 - y1)

    # ------------------------------------------------------------ input
    def key_down(self, key: str | int) -> bool:
        if isinstance(key, str):
            lowered = key.lower()
            if lowered not in KEY_NAMES and len(lowered) != 1:
                raise ValueError(f"unknown key name: {key!r}")
        elif not isinstance(key, int):
            raise ValueError(f"unknown key name: {key!r}")
        return self._platform.key_down(key)

    # ------------------------------------------------------------ lifecycle
    def stop(self) -> None:
        self.running = False

    def run_namespace(
        self, namespace: Namespace, *, fps: int | None = None, max_frames: int | None = None
    ) -> None:
        """Run the setup()/draw() found in *namespace* (the sketch's globals)."""
        setup, draw = _sketch_functions(namespace)
        if max_frames is not None and max_frames <= 0:
            raise ValueError("max_frames must be positive")
        if fps is not None and fps <= 0:
            raise ValueError("fps must be positive")
        self.last_frame = None
        self.last_ops: tuple[ir.Op, ...] | None = None
        self.frame.clear()
        self._states.unwind()
        self._shape = None

        self._platform.start()
        self.running = True
        self.frame_count = 0
        self.delta_time = 0.0
        if fps is not None:
            self.fps = int(fps)

        # setup() usually calls size(). A default canvas keeps setup() optional.
        if setup is not None:
            setup()
        if not self._has_window:
            self.size(self.width, self.height, title=self.title, fps=self.fps)

        try:
            while self.running:
                if not self._platform.poll():
                    self.running = False

                inp = self._platform.input_state()
                self.mouse_x, self.mouse_y, self.mouse_pressed = inp.mouse_x, inp.mouse_y, inp.mouse_pressed

                draw()
                self._end_draw()  # unbalanced push()es never leak into the next frame
                if max_frames is not None and self.frame_count + 1 >= max_frames:
                    self.last_ops = self.frame.ops  # what the final frame asked for (IR snapshot)
                self._render()   # draws, presents, flushes p.save()

                self.frame_count += 1
                if max_frames is not None and self.frame_count >= max_frames:
                    self.last_frame = self._platform.capture()
                    self.running = False
                self.delta_time = self._platform.tick(self.fps)
        finally:
            self.running = False
            self.frame.clear()
            self._pending_saves.clear()
            self._renderer.attach(0, 0)
            self._platform.close()
            self._has_window = False


def _geometry_of(path: PathBuilder | Path, name: str) -> Path:
    if isinstance(path, PathBuilder):
        return path.geometry
    if isinstance(path, Path):
        return path
    raise TypeError(f"p.{name}() needs a path made with p.path(), not {type(path).__name__}")


def _sketch_functions(namespace: Namespace) -> tuple[Callable[[], None] | None, Callable[[], None]]:
    setup = namespace.get("setup")
    draw = namespace.get("draw")

    if setup is not None and not callable(setup):
        raise TypeError("setup must be a function")
    if draw is None:
        raise RuntimeError("Define a draw() function before calling p.run().")
    if not callable(draw):
        raise TypeError("draw must be a function")

    return setup, draw
