"""Learner-facing functions: thin wrappers over the active Sketch.

Signatures here are the public contract (tests/test_api_contract.py); keep
them stable and keep this module free of any backend import.
"""
from __future__ import annotations

import atexit
import inspect
import sys
from contextlib import AbstractContextManager

from .color import ColorLike as Color
from .paths import PathBuilder
from .picture import Picture, draw_image  # noqa: F401  (Picture: public via f.create_graphics, S-052)
from .sketch import Sketch
from .vector import Vector  # noqa: F401  (public: f.Vector, S-055)

_active: Sketch | None = None

LIVE_NAMES = frozenset(
    {"width", "height", "mouse_x", "mouse_y", "is_mouse_pressed", "pmouse_x", "pmouse_y", "mouse_button",
     "key", "key_code", "is_key_pressed", "frame_count", "delta_time"}
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


HINT = "Your sketch has a draw() function but never started. Add f.run() as the last line."


def exit_hint() -> None:
    """At exit, remind the learner who wrote draw() but forgot f.run() (contract R13).

    Only for a program run from a terminal that ended without an error: never in an
    interactive session, never when f.run() was called, and never for a script.
    """
    from . import sketch as _sketch_module

    if _crashed or _sketch_module._run_started or hasattr(sys, "ps1") or sys.flags.interactive:
        return
    if _active is not None and _active._script:
        return
    main = sys.modules.get("__main__")
    if callable(getattr(main, "draw", None)):
        print(HINT, file=sys.stderr)


_crashed = False
_previous_excepthook = sys.excepthook


def _note_crash(exc_type, exc, tb) -> None:
    """Remember that the program ended with an error, so the exit hint stays quiet: the error is
    the thing to fix, and a hint about f.run() below it would point the wrong way."""
    global _crashed
    _crashed = True
    _previous_excepthook(exc_type, exc, tb)


sys.excepthook = _note_crash
atexit.register(exit_hint)


# ---- window / lifecycle
def size(width: int, height: int, *, title: str = "funground", fps: int = 60) -> None:
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
        raise RuntimeError("Could not find the sketch that called f.run().")
    active_sketch().run_namespace(caller.f_back.f_globals, fps=fps, max_frames=max_frames)


def show() -> None:
    """Script style: open a window on what has been drawn and wait until it is closed (or Escape)."""
    active_sketch().show()


def stop() -> None:
    active_sketch().stop()


def exit() -> None:  # noqa: A001 - p5/Processing name; shadows the REPL helper only inside funground
    """End the sketch after this frame (the same as f.stop())."""
    active_sketch().exit()


def no_loop() -> None:
    """Stop calling draw() every frame; the window stays open. loop() or redraw() bring it back."""
    active_sketch().no_loop()


def loop() -> None:
    """Call draw() every frame again after no_loop()."""
    active_sketch().loop()


def redraw() -> None:
    """Call draw() once more, e.g. after a key press while not looping."""
    active_sketch().redraw()


def is_looping() -> bool:
    """True while draw() is called every frame."""
    return active_sketch().is_looping()


def millis() -> int:
    """Milliseconds since the sketch started running."""
    return active_sketch().millis()


def frame_rate() -> float:
    """Frames per second actually achieved (smoothed); 0.0 until the second frame."""
    return active_sketch().frame_rate()


def second() -> int:
    """The clock's seconds, 0-59."""
    return Sketch.second()


def minute() -> int:
    """The clock's minutes, 0-59."""
    return Sketch.minute()


def hour() -> int:
    """The clock's hour, 0-23."""
    return Sketch.hour()


def day() -> int:
    """The day of the month, 1-31."""
    return Sketch.day()


def month() -> int:
    """The month, 1-12."""
    return Sketch.month()


def year() -> int:
    """The year, e.g. 2026."""
    return Sketch.year()


def save(path: str) -> None:
    """Save this frame to a .png, .pdf or .svg file (written when the frame is complete)."""
    active_sketch().save(path)


def resize_canvas(width: int, height: int) -> None:
    """Change the canvas size while the sketch runs; f.width and f.height follow."""
    active_sketch().resize_canvas(width, height)


def full_screen() -> None:
    """Fill the whole screen (use it instead of f.size in setup); Escape still ends the sketch."""
    active_sketch().full_screen()


def cursor(kind: str = "arrow") -> None:
    """The mouse pointer over the canvas: "arrow", "cross", "hand", "move", "text" or "wait"."""
    active_sketch().cursor(kind)


def no_cursor() -> None:
    """Hide the mouse pointer over the canvas."""
    active_sketch().no_cursor()


def save_frames(pattern: str, count: int) -> None:
    """Save this frame and the next ones, *count* in all: "frames/####.png" gives frames/0001.png, 0002.png, ..."""
    active_sketch().save_frames(pattern, count)


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


def square(x: float, y: float, size: float) -> None:
    """A square placed by its top-left corner, like rect()."""
    active_sketch().square(x, y, size)


def triangle(x1: float, y1: float, x2: float, y2: float, x3: float, y3: float) -> None:
    """A filled triangle through three corners."""
    active_sketch().triangle(x1, y1, x2, y2, x3, y3)


def quad(x1: float, y1: float, x2: float, y2: float, x3: float, y3: float, x4: float, y4: float) -> None:
    """A four-sided shape through four corners, in order."""
    active_sketch().quad(x1, y1, x2, y2, x3, y3, x4, y4)


def polygon(points: list[tuple[float, float]]) -> None:
    """A closed shape through a list of (x, y) points."""
    active_sketch().polygon(points)


def arc(x: float, y: float, width: float, height: float, start: float, stop: float, mode: str = "open") -> None:
    """Part of an ellipse centred at (x, y), from start to stop degrees clockwise; mode "open", "chord" or "pie"."""
    active_sketch().arc(x, y, width, height, start, stop, mode)


def clear() -> None:
    """Make the whole canvas transparent; a PNG saved afterwards keeps the transparency."""
    active_sketch().clear()


def text(message: object, x: float, y: float, color: Color | None = None) -> None:
    active_sketch().text(message, x, y, color)


def text_align(horizontal: str, vertical: str | None = None) -> None:
    """Which point of the text (x, y) means: "left"/"center"/"right", then "top"/"center"/"baseline"/"bottom"."""
    active_sketch().text_align(horizontal, vertical)


def text_ascent() -> float:
    """How far letters reach above the baseline at the current text_size, in pixels."""
    return active_sketch().text_ascent()


def text_descent() -> float:
    """How far letters like g and y reach below the baseline at the current text_size, in pixels."""
    return active_sketch().text_descent()


def text_leading(leading: float | None) -> None:
    """The distance from one line's baseline to the next, in pixels; None = automatic (1.25 x text_size)."""
    active_sketch().text_leading(leading)


def text_box(message: object, x: float, y: float, width: float, height: float | None = None,
             color: Color | None = None) -> str:
    """Draw *message* wrapped inside a box; return whatever did not fit ("" if it all did)."""
    return active_sketch().text_box(message, x, y, width, height, color)


def text_width(message: object) -> float:
    """How wide *message* will be at the current text_size, e.g. to centre it: f.text(msg, (f.width - f.text_width(msg)) / 2, y)."""
    return active_sketch().text_width(message)


# ---- style
def color(*values):
    """A colour you can read and reuse: f.color("tomato"), f.color(255, 99, 71) or f.color((255, 99, 71, 128)).

    Its parts are .red .green .blue .alpha (0-255), .hue (0-360), .saturation .brightness
    .lightness (0-100). Tuples always mean red, green, blue - use f.hsb() or f.hsl() for hue.
    """
    from .color import Color as _Color

    if len(values) == 1:
        return _Color.parse(values[0])
    if len(values) in (3, 4):
        return _Color.parse(tuple(values))
    raise ValueError("f.color() takes one colour, or 3 or 4 numbers (red, green, blue[, alpha])")


def hsb(hue: float, saturation: float, brightness: float, alpha: float = 255):
    """A colour from hue (0-360), saturation and brightness (0-100); alpha 0-255."""
    from .color import Color as _Color

    return _Color.from_hsb(hue, saturation, brightness, alpha)


def hsl(hue: float, saturation: float, lightness: float, alpha: float = 255):
    """A colour from hue (0-360), saturation and lightness (0-100); alpha 0-255."""
    from .color import Color as _Color

    return _Color.from_hsl(hue, saturation, lightness, alpha)


def linear_gradient(x1: float, y1: float, x2: float, y2: float, colors, stops=None):
    """Colours blended along the line from (x1, y1) to (x2, y2); use it like a colour in fill/stroke/background."""
    from .paint import linear_gradient as make

    return make(x1, y1, x2, y2, colors, stops)


def radial_gradient(x: float, y: float, radius: float, colors, stops=None):
    """Colours blended outward from (x, y) to *radius*; the first colour is at the centre."""
    from .paint import radial_gradient as make

    return make(x, y, radius, colors, stops)


def blend_mode(mode: str) -> None:
    """How what you draw next mixes with what is already there: "normal", "multiply", "screen", "add", ..."""
    active_sketch().blend_mode(mode)


def opacity(amount: float) -> None:
    """Make everything drawn after this see-through: 0 invisible, 255 solid (the default)."""
    active_sketch().opacity(amount)


def shadow(x_offset: float, y_offset: float, blur: float = 5, color: Color = (0, 0, 0, 128)) -> None:
    """Give everything drawn after this a shadow, moved by (x_offset, y_offset) and softened by *blur* pixels."""
    active_sketch().shadow(x_offset, y_offset, blur, color)


def no_shadow() -> None:
    """Stop drawing shadows."""
    active_sketch().no_shadow()


def lerp_color(c1: Color, c2: Color, amount: float):
    """The colour *amount* of the way from c1 to c2 (0 to 1), mixing red, green, blue and alpha."""
    from .color import Color as _Color

    return _Color.parse(c1).lerp(_Color.parse(c2), amount)


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


def stroke_cap(cap: str) -> None:
    """How line ends look: "round" (default), "square" (extends past the end) or "butt" (stops flat)."""
    active_sketch().stroke_cap(cap)


def stroke_join(join: str) -> None:
    """How corners look: "round" (default), "miter" (sharp) or "bevel" (cut off)."""
    active_sketch().stroke_join(join)


def miter_limit(limit: float) -> None:
    """How far a sharp "miter" corner may stick out before it is bevelled (default 10)."""
    active_sketch().miter_limit(limit)


def stroke_dash(pattern: float | list[float], offset: float = 0) -> None:
    """Dashed outlines: stroke_dash(10) or stroke_dash([12, 4, 2, 4]); offset shifts the pattern."""
    active_sketch().stroke_dash(pattern, offset)


def no_dash() -> None:
    """Solid outlines again."""
    active_sketch().no_dash()


def no_smooth() -> None:
    """Hard, pixel-sharp edges from now on (no anti-aliasing) - for pixel art."""
    active_sketch().no_smooth()


def smooth() -> None:
    """Smooth edges again (the default)."""
    active_sketch().smooth()


def text_size(size: int) -> None:
    active_sketch().text_size(size)


# ---- fonts and styles (S-054, contract T11/T12)
def load_font(path: str):
    """Load a TrueType/OpenType font file; pass the result to f.text_font(). A relative path is
    looked for next to the sketch file first, then in the current folder."""
    caller = inspect.currentframe()
    base_dir = None
    if caller is not None and caller.f_back is not None:
        sketch_file = caller.f_back.f_globals.get("__file__")
        if sketch_file:
            import os

            base_dir = os.path.dirname(os.path.abspath(sketch_file))
    return active_sketch().load_font(path, base_dir=base_dir)


def text_font(font, size: float | None = None) -> None:
    """Use *font* (from f.load_font(), a path, or None for the built-in family) for later text."""
    caller = inspect.currentframe()
    base_dir = None
    if isinstance(font, str) and caller is not None and caller.f_back is not None:
        sketch_file = caller.f_back.f_globals.get("__file__")
        if sketch_file:
            import os

            base_dir = os.path.dirname(os.path.abspath(sketch_file))
    active_sketch().text_font(font, size, base_dir=base_dir)


def text_style(style: str) -> None:
    """Use one of the four built-in styles for later text: "normal", "bold", "italic", "bold_italic"."""
    active_sketch().text_style(style)


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


def shear_x(degrees: float) -> None:
    """Slant later drawing sideways by *degrees* (x moves by tan(degrees) * y)."""
    active_sketch().shear_x(degrees)


def shear_y(degrees: float) -> None:
    """Slant later drawing up or down by *degrees* (y moves by tan(degrees) * x)."""
    active_sketch().shear_y(degrees)


def apply_matrix(a: float, b: float, c: float, d: float, e: float, f: float) -> None:
    """Multiply in a whole transform: x' = a*x + c*y + e, y' = b*x + d*y + f."""
    active_sketch().apply_matrix(a, b, c, d, e, f)


def reset_matrix() -> None:
    """Forget every translate/rotate/scale/shear so far, until the enclosing pop()."""
    active_sketch().reset_matrix()


def push() -> None:
    """Save the current transform and style; pop() brings them back."""
    active_sketch().push()


def pop() -> None:
    """Restore the transform and style saved by the last push()."""
    active_sketch().pop()


def saved_state() -> AbstractContextManager[None]:
    """``with f.saved_state():`` - push() on entry, pop() on exit, even after an error."""
    return active_sketch().saved_state()


# ---- shapes, paths and clipping (S-028)
def begin_shape() -> None:
    """Start a shape: list its corners with vertex(), then call end_shape()."""
    active_sketch().begin_shape()


def vertex(x: float, y: float) -> None:
    """Add a corner to the shape begun by begin_shape()."""
    active_sketch().vertex(x, y)


def bezier_vertex(cx1: float, cy1: float, cx2: float, cy2: float, x: float, y: float) -> None:
    """Add a Bezier curve segment: two control points (cx1, cy1), (cx2, cy2), then the end point (x, y)."""
    active_sketch().bezier_vertex(cx1, cy1, cx2, cy2, x, y)


def quadratic_vertex(cx: float, cy: float, x: float, y: float) -> None:
    """Add a quadratic curve segment: one control point, then the end point."""
    active_sketch().quadratic_vertex(cx, cy, x, y)


def curve_vertex(x: float, y: float) -> None:
    """Add a point for a smooth curve through the points (the first and last only steer it)."""
    active_sketch().curve_vertex(x, y)


def curve_tightness(tightness: float) -> None:
    """How tight curve_vertex()/curve() curves are: 0 smooth (default), 1 straight lines."""
    active_sketch().curve_tightness(tightness)


def begin_contour() -> None:
    """Start a hole inside the shape being built; list its corners, then end_contour()."""
    active_sketch().begin_contour()


def end_contour() -> None:
    """Finish the hole started by begin_contour()."""
    active_sketch().end_contour()


def bezier(x1: float, y1: float, cx1: float, cy1: float, cx2: float, cy2: float, x2: float, y2: float) -> None:
    """A Bezier curve from (x1, y1) to (x2, y2) with two control points; stroked only."""
    active_sketch().bezier(x1, y1, cx1, cy1, cx2, cy2, x2, y2)


def curve(x1: float, y1: float, x2: float, y2: float, x3: float, y3: float, x4: float, y4: float) -> None:
    """A smooth curve from (x2, y2) to (x3, y3), steered by (x1, y1) and (x4, y4); stroked only."""
    active_sketch().curve(x1, y1, x2, y2, x3, y3, x4, y4)


def bezier_point(a: float, b: float, c: float, d: float, t: float) -> float:
    """One coordinate of the Bezier curve at t (0 to 1); call it for x and for y."""
    from .shapes import bezier_point as _bp

    return _bp(a, b, c, d, t)


def bezier_tangent(a: float, b: float, c: float, d: float, t: float) -> float:
    """The slope of one coordinate of the Bezier curve at t, e.g. for math.atan2."""
    from .shapes import bezier_tangent as _bt

    return _bt(a, b, c, d, t)


def curve_point(a: float, b: float, c: float, d: float, t: float) -> float:
    """One coordinate of the curve() segment at t (0 to 1), with the current curve_tightness."""
    return active_sketch().curve_point(a, b, c, d, t)


def curve_tangent(a: float, b: float, c: float, d: float, t: float) -> float:
    """The slope of one coordinate of the curve() segment at t."""
    return active_sketch().curve_tangent(a, b, c, d, t)


def end_shape(close: bool = False) -> None:
    """Draw the shape. close=True joins the last corner to the first and fills it; open shapes are only stroked."""
    active_sketch().end_shape(close)


def path() -> PathBuilder:
    """A reusable path: f.path().move_to(0, 0).line_to(40, 0).curve_to(...).close(); draw it with draw_path()."""
    return active_sketch().path()


def draw_path(path: PathBuilder) -> None:
    """Fill (if closed) and stroke a path made with f.path(), using the current style."""
    active_sketch().draw_path(path)


def no_clip() -> None:
    """Remove clipping until the enclosing pop() / end of the saved_state block."""
    active_sketch().no_clip()


def clip(path: PathBuilder) -> None:
    """Limit later drawing to the inside of *path* until the enclosing pop() / end of the saved_state() block."""
    active_sketch().clip(path)


# ---- off-screen graphics (S-052, contract P1-P3)
def create_graphics(width: int, height: int) -> Picture:
    """A picture: an off-screen canvas width x height, transparent to start, with its own
    drawing commands (fill, circle, push/pop, ...) and its own state and transform."""
    return active_sketch().create_graphics(width, height)


def load_image(path: str) -> Picture:
    """Read an image file (PNG, JPEG, GIF, BMP, TGA...) and return a picture; draw it with f.image().
    A relative path is looked for next to the sketch file first, then in the current folder.
    Phone photos are turned the right way up."""
    caller = inspect.currentframe()
    base_dir = None
    if caller is not None and caller.f_back is not None:
        sketch_file = caller.f_back.f_globals.get("__file__")
        if sketch_file:
            import os

            base_dir = os.path.dirname(os.path.abspath(sketch_file))
    return active_sketch().load_image(path, base_dir=base_dir)


def image(picture, x: float, y: float, width: float | None = None, height: float | None = None) -> None:
    """Draw *picture* at (x, y), stretched to width x height (default: its own size), as it
    is at this moment - later drawing on it does not change what was placed."""
    draw_image(active_sketch(), picture, x, y, width, height)


# ---- input
def key_down(key: str | int) -> bool:
    """Return whether a key is held, e.g. key_down('left') or key_down('a')."""
    return active_sketch().key_down(key)


# ---- helpers
def random(low: float = 1.0, high: float | None = None) -> float:
    """random(10) -> 0..10; random(5, 10) -> 5..10."""
    return active_sketch().random(low, high)


def random_seed(seed: int | None = None) -> None:
    """Make f.random() repeatable: the same seed gives the same sequence."""
    active_sketch().random_seed(seed)


def noise(x: float, y: float = 0.0, z: float = 0.0) -> float:
    """Smooth random values from 0 to 1: nearby inputs give nearby outputs (p5's noise)."""
    return active_sketch().noise(x, y, z)


def noise_seed(seed: int) -> None:
    """Make noise() repeatable; the same seed gives the same values as p5's noiseSeed."""
    active_sketch().noise_seed(seed)


def noise_detail(octaves: int, falloff: float | None = None) -> None:
    """How many layers of detail noise() adds (default 4) and how much each fades (default 0.5)."""
    active_sketch().noise_detail(octaves, falloff)


def random_gaussian(mean: float = 0.0, sd: float = 1.0) -> float:
    """A random number from a bell curve: most near *mean*, about 2/3 within *sd* of it."""
    return active_sketch().random_gaussian(mean, sd)


def random_choice(items):
    """One item picked at random from a list, tuple or string (repeatable with random_seed)."""
    return active_sketch().random_choice(items)


def map_range(value: float, start1: float, stop1: float, start2: float, stop2: float, clamp: bool = False) -> float:
    """Re-scale *value* from one range to another, e.g. map_range(f.mouse_x, 0, f.width, 0, 255)."""
    return Sketch.map_range(value, start1, stop1, start2, stop2, clamp)


def lerp(start: float, stop: float, amount: float) -> float:
    """The number *amount* of the way from start to stop: 0 gives start, 1 gives stop, 0.5 halfway."""
    return Sketch.lerp(start, stop, amount)


def norm(value: float, start: float, stop: float) -> float:
    """Where *value* sits between start and stop, as 0 to 1."""
    return Sketch.norm(value, start, stop)


def mag(x: float, y: float) -> float:
    """The length of the arrow (x, y): distance from (0, 0)."""
    return Sketch.mag(x, y)


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
