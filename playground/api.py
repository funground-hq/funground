"""Learner-facing functions: thin wrappers over the active Sketch.

Signatures here are the public contract (tests/test_api_contract.py); keep
them stable and keep this module free of any backend import.
"""
from __future__ import annotations

import inspect
from contextlib import AbstractContextManager

from .color import ColorLike as Color
from .paths import PathBuilder
from .sketch import Sketch

_active: Sketch | None = None

LIVE_NAMES = frozenset(
    {"width", "height", "mouse_x", "mouse_y", "mouse_pressed", "frame_count", "delta_time"}
)


def active_sketch() -> Sketch:
    global _active
    if _active is None:
        _active = Sketch()
    return _active


def use_sketch(sketch: Sketch | None) -> Sketch:
    """Make *sketch* the one the public functions talk to (tests, multi-sketch)."""
    global _active
    _active = sketch
    return active_sketch()


def live_value(name: str) -> object:
    if name not in LIVE_NAMES:
        raise AttributeError(name)
    return getattr(active_sketch(), name)


# ---- window / lifecycle
def size(width: int, height: int, *, title: str = "playground", fps: int = 60) -> None:
    """Create or resize the sketch window."""
    active_sketch().size(width, height, title=title, fps=fps)


def run(*, fps: int | None = None, max_frames: int | None = None) -> None:
    """Run standardized setup() and draw() functions from the calling script.

    setup() is optional; draw() is required. Neither is passed as an argument.
    max_frames stops the sketch automatically after that many frames; it is
    mainly for tests and headless runs.
    """
    caller = inspect.currentframe()
    if caller is None or caller.f_back is None:
        raise RuntimeError("Could not find the sketch that called p.run().")
    active_sketch().run_namespace(caller.f_back.f_globals, fps=fps, max_frames=max_frames)


def stop() -> None:
    active_sketch().stop()


def save(path: str) -> None:
    """Save this frame to a .png, .pdf or .svg file (written when the frame is complete)."""
    active_sketch().save(path)


# ---- drawing
def background(color: Color) -> None:
    active_sketch().background(color)


def circle(x: float, y: float, diameter: float) -> None:
    active_sketch().circle(x, y, diameter)


def ellipse(x: float, y: float, width: float, height: float) -> None:
    """Draw an ellipse centered at (x, y)."""
    active_sketch().ellipse(x, y, width, height)


def rect(x: float, y: float, width: float, height: float) -> None:
    """Draw a rectangle from its top-left corner."""
    active_sketch().rect(x, y, width, height)


def line(x1: float, y1: float, x2: float, y2: float) -> None:
    active_sketch().line(x1, y1, x2, y2)


def point(x: float, y: float) -> None:
    active_sketch().point(x, y)


def text(message: object, x: float, y: float, color: Color | None = None) -> None:
    active_sketch().text(message, x, y, color)


def text_width(message: object) -> float:
    """How wide *message* will be at the current text_size, e.g. to centre it: p.text(msg, (p.width - p.text_width(msg)) / 2, y)."""
    return active_sketch().text_width(message)


# ---- style
def fill(color: Color) -> None:
    active_sketch().fill(color)


def no_fill() -> None:
    active_sketch().no_fill()


def stroke(color: Color) -> None:
    active_sketch().stroke(color)


def no_stroke() -> None:
    active_sketch().no_stroke()


def stroke_width(pixels: int) -> None:
    active_sketch().stroke_width(pixels)


def text_size(size: int) -> None:
    active_sketch().text_size(size)


# ---- transforms and the state stack (S-027)
def translate(dx: float, dy: float) -> None:
    """Move the origin: everything drawn afterwards is shifted by (dx, dy)."""
    active_sketch().translate(dx, dy)


def rotate(degrees: float) -> None:
    """Turn later drawing by *degrees* about the current origin (90 = a quarter turn clockwise)."""
    active_sketch().rotate(degrees)


def scale(sx: float, sy: float | None = None) -> None:
    """Grow or shrink later drawing: scale(2) doubles, scale(2, 1) stretches sideways."""
    active_sketch().scale(sx, sy)


def push() -> None:
    """Save the current transform and style; pop() brings them back."""
    active_sketch().push()


def pop() -> None:
    """Restore the transform and style saved by the last push()."""
    active_sketch().pop()


def saved_state() -> AbstractContextManager[None]:
    """``with p.saved_state():`` - push() on entry, pop() on exit, even after an error."""
    return active_sketch().saved_state()


# ---- shapes, paths and clipping (S-028)
def begin_shape() -> None:
    """Start a shape: list its corners with vertex(), then call end_shape()."""
    active_sketch().begin_shape()


def vertex(x: float, y: float) -> None:
    """Add a corner to the shape begun by begin_shape()."""
    active_sketch().vertex(x, y)


def curve_vertex(cx1: float, cy1: float, cx2: float, cy2: float, x: float, y: float) -> None:
    """Add a curved segment: two control points (cx1, cy1), (cx2, cy2), then the end point (x, y)."""
    active_sketch().curve_vertex(cx1, cy1, cx2, cy2, x, y)


def end_shape(close: bool = False) -> None:
    """Draw the shape. close=True joins the last corner to the first and fills it; open shapes are only stroked."""
    active_sketch().end_shape(close)


def path() -> PathBuilder:
    """A reusable path: p.path().move_to(0, 0).line_to(40, 0).curve_to(...).close(); draw it with draw_path()."""
    return active_sketch().path()


def draw_path(path: PathBuilder) -> None:
    """Fill (if closed) and stroke a path made with p.path(), using the current style."""
    active_sketch().draw_path(path)


def clip(path: PathBuilder) -> None:
    """Limit later drawing to the inside of *path* until the enclosing pop() / end of the saved_state() block."""
    active_sketch().clip(path)


# ---- input
def key_down(key: str | int) -> bool:
    """Return whether a key is held, e.g. key_down('left') or key_down('a')."""
    return active_sketch().key_down(key)


# ---- helpers
def random(low: float = 1.0, high: float | None = None) -> float:
    """random(10) -> 0..10; random(5, 10) -> 5..10."""
    return active_sketch().random(low, high)


def random_seed(seed: int | None = None) -> None:
    """Make p.random() repeatable: the same seed gives the same sequence."""
    active_sketch().random_seed(seed)


def constrain(value: float, low: float, high: float) -> float:
    return Sketch.constrain(value, low, high)


def radians(degrees: float) -> float:
    """Degrees to radians, for math.sin/cos (rotate() itself takes degrees)."""
    return Sketch.radians(degrees)


def degrees(radians: float) -> float:
    """Radians to degrees, e.g. degrees(math.atan2(dy, dx)) for rotate()."""
    return Sketch.degrees(radians)


def distance(x1: float, y1: float, x2: float, y2: float) -> float:
    return Sketch.distance(x1, y1, x2, y2)
