"""The Sketch: one running (or runnable) Playground program.

Owns the lifecycle, live values, graphics state and helpers that v0.5 kept as
module globals in ``_core.py``. Talks to the OS only through a ``Platform`` and
draws only through a ``Renderer`` — never through pygame directly (see
tests/test_boundaries.py). ``api.py`` keeps the learner-facing functions as thin
wrappers over the active Sketch.
"""
from __future__ import annotations

import math
import random as _random
from collections.abc import Callable
from typing import Any

from . import ir
from .capabilities import Capability, missing_capability
from .color import WHITE, Color, ColorLike
from .platform.base import KEY_NAMES, Platform
from .renderers import Renderer
from .state import GraphicsState, StateStack

# What the v0.5 public API needs from any renderer.
REQUIRED_CAPABILITIES: dict[Capability, str] = {Capability.RASTER_2D: "Drawing shapes"}

Namespace = dict[str, Any]


class Sketch:
    def __init__(self, platform: Platform | None = None, renderer: Renderer | None = None) -> None:
        if platform is None:
            from .platform.pygame_platform import PygamePlatform

            platform = PygamePlatform()
        if renderer is None:
            from .renderers.legacy_pygame import LegacyPygameRenderer

            renderer = LegacyPygameRenderer()
        self._platform = platform
        self._renderer = renderer
        self._states = StateStack()
        # Ops recorded since the last render; consumed once per loop iteration.
        self.frame = ir.Frame()
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
        target = self._platform.open_window(self.width, self.height, self.title)
        self._renderer.attach(target)
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
        """Draw everything recorded so far onto the window; the frame then starts empty."""
        if self.frame:
            self._renderer.render(self.frame)
            self.frame.clear()

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
                if max_frames is not None and self.frame_count + 1 >= max_frames:
                    self.last_ops = self.frame.ops  # what the final frame asked for (IR snapshot)
                self._render()
                self._platform.present()

                self.frame_count += 1
                if max_frames is not None and self.frame_count >= max_frames:
                    self.last_frame = self._platform.capture()
                    self.running = False
                self.delta_time = self._platform.tick(self.fps)
        finally:
            self.running = False
            self.frame.clear()
            self._renderer.attach(None)
            self._platform.close()
            self._has_window = False


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
