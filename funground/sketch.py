"""The Sketch: one running (or runnable) funground program.

Owns the lifecycle, live values, graphics state and helpers that v0.5 kept as
module globals in ``_core.py``. Talks to the OS only through a ``Platform`` and
draws only through a ``Renderer`` — never through pygame directly (see
tests/test_boundaries.py). ``api.py`` keeps the learner-facing functions as thin
wrappers over the active Sketch.
"""
from __future__ import annotations

import contextlib
import datetime
import math
import time
import random as _random
import warnings
from collections.abc import Callable, Iterator
from typing import Any

from . import ir
from .capabilities import Capability, FungroundWarning, missing_capability
from .color import COLOR_MODES, WHITE, Color, ColorLike, parse_in_mode
from .paint import Gradient, parse_paint
from .typography import TEXT_STYLES
from .geometry import Path, Transform
from .paths import PathBuilder
from .noise import Noise
from .shapes import ShapeBuilder, catmull_rom_controls
from .platform.base import CURSOR_KINDS, KEY_NAMES, Platform
from .renderers import Renderer
from .state import GraphicsState, StateStack

DEFAULT_SHADOW_COLOR = (0, 0, 0, 128)       # not read through the colour mode (S15)

# What the v0.5 public API needs from any renderer.
REQUIRED_CAPABILITIES: dict[Capability, str] = {Capability.RASTER_2D: "Drawing shapes"}

# Renderer selection (S-023.4). Future optional renderers (e.g. Blend2D, S-036) register here.
RENDERERS = {"cairo": "funground.renderers.cairo2d:CairoRenderer"}
DEFAULT_RENDERER = "cairo"


def default_platform() -> Platform:
    import os

    if os.environ.get("FUNGROUND_HEADLESS", "").lower() in ("1", "true", "yes"):
        from .platform.headless import HeadlessPlatform

        return HeadlessPlatform()
    from .platform.pygame_platform import PygamePlatform

    return PygamePlatform()


def default_renderer() -> Renderer:
    import importlib
    import os

    name = os.environ.get("FUNGROUND_RENDERER", DEFAULT_RENDERER).lower()
    if name not in RENDERERS:
        raise ValueError(f"FUNGROUND_RENDERER must be one of {sorted(RENDERERS)}, not {name!r}")
    module, cls = RENDERERS[name].split(":")
    return getattr(importlib.import_module(module), cls)()

Namespace = dict[str, Any]

_run_started = False          # set once any sketch has been run; the exit hint reads it (S-076)


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
        self._frame_sequence: list | None = None      # S-056: [pattern, next number, last number]
        self._cursor: str | None = "arrow"              # S-057: applied whenever a window opens
        # no_smooth() is a sketch setting, re-applied at the start of every frame (S-042).
        self._smooth = True
        # The shape between begin_shape() and end_shape(), if one is open (S-028).
        self._shape: ShapeBuilder | None = None
        # funground keeps its own generator so random_seed() never disturbs a
        # learner's own `import random`.
        self._rng = _random.Random()
        # Smooth noise, ported from p5.js (S-047); seeded separately, as in p5.
        self._noise = Noise()

        # Live values (contract R1, R4, R5, I1) and window settings.
        self.width = 640
        self.height = 480
        self.fps = 60
        self.title = "funground"
        self.mouse_x = 0
        self.mouse_y = 0
        self.is_mouse_pressed = False       # D-016 (was mouse_pressed in v0.5)
        # Input events (S-045, contract I3).
        self.pmouse_x = 0
        self.pmouse_y = 0
        self.mouse_button: str | None = None
        self.key: str | None = None
        self.key_code: int | None = None
        self.is_key_pressed = False
        self._callbacks: dict[str, Callable] = {}
        self.frame_count = 0
        self.delta_time = 0.0
        self.running = False
        # Loop control and clock (S-048, contract R10).
        self._looping = True
        self._redraw_pending = False
        self._start_time = time.perf_counter()
        self._fps_measured = 0.0
        self._has_window = False
        # ((width, height), RGB bytes) of the final frame when run(max_frames=)
        # stops the sketch; used by the regression suite.
        self.last_frame: tuple[tuple[int, int], bytes] | None = None
        # S-052: create_graphics() names pictures "graphics-N" in creation order per run.
        self._graphics_counter = 0
        # S-076, contract R13-R15: a script is a top-level f.size() with no sketch running. Its
        # canvas has no window; every op it draws stays in self.frame (show() and PDF/SVG saves
        # replay them) and is drawn onto self._renderer's persistent surface on demand.
        self._script = False
        self._script_scale = 1.0
        self._script_drawn = 0         # how many of self.frame's ops are already on the surface
        self._script_depth = 0         # the persistent surface's open Save depth

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
                "f.pop() called without a matching f.push(); ignored.",
                FungroundWarning, stacklevel=3,
            )
            return
        self._states.restore()
        self._emit(ir.Restore())

    @contextlib.contextmanager
    def saved_state(self) -> Iterator[None]:
        """``with f.saved_state():`` - push on entry, pop on exit, even when the body raises."""
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
                "draw() finished inside a shape: f.begin_shape() had no f.end_shape(), "
                "so nothing was drawn for it.",
                FungroundWarning, stacklevel=2,
            )
        open_pushes = self._states.unwind()
        if open_pushes:
            for _ in range(open_pushes):
                self.frame.append(ir.Restore())
            warnings.warn(
                f"draw() finished with {open_pushes} f.push() call(s) still open; "
                "funground popped them for you. Add a matching f.pop(), or use "
                "`with f.saved_state():`.",
                FungroundWarning, stacklevel=2,
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

    def shear_x(self, degrees: float) -> None:
        """Slant later drawing sideways: x moves by tan(degrees) * y."""
        self._shear(degrees, 0.0)

    def shear_y(self, degrees: float) -> None:
        """Slant later drawing up/down: y moves by tan(degrees) * x."""
        self._shear(0.0, degrees)

    def _shear(self, x_degrees: float, y_degrees: float) -> None:
        for d in (x_degrees, y_degrees):
            if abs(math.cos(math.radians(d))) < 1e-9:
                raise ValueError("a shear of 90 degrees (or 270) would be infinitely slanted")
        self._emit(ir.Concat(Transform.shearing(x_degrees, y_degrees)))

    def apply_matrix(self, a: float, b: float, c: float, d: float, e: float, f: float) -> None:
        """Multiply in x' = a*x + c*y + e, y' = b*x + d*y + f (the p5 / Canvas order)."""
        t = Transform(float(a), float(b), float(c), float(d), float(e), float(f))
        if t.determinant() == 0:
            raise ValueError("f.apply_matrix(): this matrix squashes everything flat (its determinant is 0)")
        self._emit(ir.Concat(t))

    def reset_matrix(self) -> None:
        """Forget every translate/rotate/scale/shear so far (until the enclosing pop())."""
        self._emit(ir.ResetMatrix())

    @staticmethod
    def radians(degrees: float) -> float:
        return math.radians(degrees)

    @staticmethod
    def degrees(radians: float) -> float:
        return math.degrees(radians)

    # ------------------------------------------------------------ window
    def size(self, width: int, height: int, *, title: str = "funground", fps: int = 60) -> None:
        if width <= 0 or height <= 0:
            raise ValueError("width and height must be positive")
        if fps <= 0:
            raise ValueError("fps must be positive")
        self.width = int(width)
        self.height = int(height)
        self.fps = int(fps)
        self.title = title
        self._check_capabilities()
        if not self.running:
            self._begin_script()
            return
        self._script = False
        pw, ph = self._platform.open_window(self.width, self.height, self.title)
        self._attach(pw, ph)

    # ---- scripts (S-076, contract R13-R15)
    def _begin_script(self) -> None:
        """A top-level f.size(): a blank canvas with no window (contract R14)."""
        import os

        forced = os.environ.get("FUNGROUND_BACKING_SCALE")
        self._script_scale = max(0.5, float(forced)) if forced else 1.0
        self._renderer.attach(round(self.width * self._script_scale), round(self.height * self._script_scale),
                              self._script_scale)
        self._renderer._base_matrix = self._renderer._ctx.get_matrix()   # what reset_matrix() returns to
        self.frame.clear()
        self._states.unwind()          # the old canvas's open pushes went with it
        self._shape = None
        self._script = True
        self._has_window = True
        self._script_drawn = 0
        self._script_depth = 0
        self._graphics_counter = 0
        self._start_time = time.perf_counter()

    def _script_flush(self) -> None:
        """Draw the ops added since the last flush onto the script canvas's surface."""
        new = self.frame.ops[self._script_drawn:]
        if new:
            self._script_depth = self._renderer.draw_batch(self._renderer._ctx, ir.Frame(list(new)),
                                                           self._script_depth)
            self._script_drawn += len(new)

    def _only_in_animated(self, name: str) -> None:
        if self._script:
            raise RuntimeError(
                f"f.{name}() is for animated sketches, and this file is a script (it has no draw()). "
                "To animate, write a draw() function and end the file with f.run()."
            )

    def show(self) -> None:
        """Open a window on the script's drawing and wait until it is closed (contract R15)."""
        from .platform.headless import HeadlessPlatform

        if self.running:
            raise RuntimeError(
                "f.show() is for scripts. An animated sketch already has its window: "
                "remove f.show() and end the file with f.run()."
            )
        if not self._script:
            raise RuntimeError("No drawing window yet. Call f.size(...) first.")
        if isinstance(self._platform, HeadlessPlatform):
            return
        platform = self._platform
        renderer = default_renderer()
        try:
            pw, ph = platform.open_window(self.width, self.height, self.title)
            renderer.attach(pw, ph, platform.backing_scale)
            renderer._base_matrix = renderer._ctx.get_matrix()
            renderer.draw_batch(renderer._ctx, self.frame, 0)      # the kept drawing, at the window's scale
            platform.start()
            platform.set_cursor(self._cursor)
            pixels = renderer.pixels()
            platform.present(pixels)
            while platform.poll():
                platform.present(pixels)           # keeps the picture up if the window is uncovered
                platform.tick(30)
        finally:
            platform.close()

    def _attach(self, pw: int, ph: int) -> None:
        self._renderer.attach(pw, ph, self._platform.backing_scale)
        self._has_window = True
        self._platform.set_cursor(self._cursor)

    # ---- window control (S-057, contract R12)
    def resize_canvas(self, width: int, height: int) -> None:
        """A new canvas size while the sketch runs; the canvas starts blank, like p5's resizeCanvas."""
        self.size(width, height, title=self.title, fps=self.fps)

    def full_screen(self) -> None:
        """Make the canvas fill the screen; f.width and f.height become the screen's size."""
        self._check_capabilities()
        pw, ph = self._platform.open_full_screen(self.title)
        scale = self._platform.backing_scale
        self.width, self.height = round(pw / scale), round(ph / scale)
        self._attach(pw, ph)

    CURSOR_KINDS = CURSOR_KINDS          # the names every platform understands (platform.base)

    def cursor(self, kind: str = "arrow") -> None:
        if kind not in self.CURSOR_KINDS:
            raise ValueError(f"f.cursor() takes one of {', '.join(map(repr, self.CURSOR_KINDS))}, not {kind!r}")
        self._cursor = kind
        if self._has_window and not self._script:
            self._platform.set_cursor(kind)

    def no_cursor(self) -> None:
        self._cursor = None
        if self._has_window and not self._script:
            self._platform.set_cursor(None)

    # ---- pictures (S-052, contract P1)
    def create_graphics(self, width: int, height: int):
        """An off-screen picture width x height, transparent to start; needs the window first."""
        from .picture import Picture

        self._require_window()
        if not _is_positive_whole(width) or not _is_positive_whole(height):
            raise ValueError(
                f"f.create_graphics() needs positive whole numbers for width and height, "
                f"not ({width!r}, {height!r})"
            )
        self._graphics_counter += 1
        scale = self._script_scale if self._script else self._platform.backing_scale
        return Picture(int(width), int(height), scale,
                       f"graphics-{self._graphics_counter}")

    def load_image(self, path: str, base_dir: str | None = None):
        """A picture made from an image file (contract P4). Needs no window, so it may come first."""
        from . import imaging
        from .picture import Picture
        from .typography import _resolve_path

        resolved = _resolve_path(path, base_dir, "f.load_image()", "image")
        width, height, bgra = imaging.decode(resolved)
        self._graphics_counter += 1
        return Picture.from_pixels(width, height, bgra, f"graphics-{self._graphics_counter}")

    def _check_capabilities(self) -> None:
        """Refuse up front (contract R9) rather than failing on frame 200."""
        for cap, feature in REQUIRED_CAPABILITIES.items():
            if cap not in self._renderer.capabilities:
                raise missing_capability(cap, feature, getattr(self._renderer, "name", "selected"))

    def _require_window(self) -> None:
        if not self._has_window:
            raise RuntimeError("No drawing window yet. Call f.size(...) first.")

    def _emit(self, op: ir.Op) -> None:
        self._require_window()
        self.frame.append(op)

    def _render(self) -> None:
        """Draw everything recorded so far and present it; the frame then starts empty."""
        self._end_draw()
        # Always present, even a frame that drew nothing: the canvas is still a frame
        # (the headless platform has nothing to capture otherwise).
        self._renderer.render(self.frame)
        self._platform.present(self._renderer.pixels())
        self._queue_sequence_frame()
        self._flush_saves()
        self.frame.clear()

    # ------------------------------------------------------------ export
    def save(self, path: str) -> None:
        """Write this frame to a .png, .pdf or .svg file when the frame is complete."""
        from .export import format_of

        format_of(path)  # validate early so the learner sees the error at the call site
        self._require_window()
        if self._script:                     # contract R14: a script's save writes at once
            self._save_script(path)
            return
        self._pending_saves.append(path)

    def _save_script(self, path: str) -> None:
        from .export import format_of, save_frame, save_pixels

        if format_of(path) == "png":
            self._script_flush()
            save_pixels(self._renderer.pixels(), path)
        else:
            save_frame(self.frame, path, self.width, self.height, self._script_scale)

    def save_frames(self, pattern: str, count: int) -> None:
        """Save this frame and the ones after it, *count* in all, numbered into *pattern* (S-056)."""
        import re

        from .export import format_of

        self._only_in_animated("save_frames")
        runs = re.findall(r"#+", pattern)
        if len(runs) != 1:
            raise ValueError(f"f.save_frames() needs one run of # in the name for the number, "
                             f"e.g. \"frames/####.png\", not {pattern!r}")
        format_of(pattern)
        if isinstance(count, bool) or not isinstance(count, int) or count < 1:
            raise ValueError(f"f.save_frames() needs a whole number of frames, 1 or more, not {count!r}")
        self._require_window()
        self._frame_sequence = [pattern, 1, count]

    def _queue_sequence_frame(self) -> None:
        seq = self._frame_sequence
        if seq is None:
            return
        import os
        import re

        pattern, number, last = seq
        path = re.sub(r"#+", lambda m: str(number).zfill(len(m.group())), pattern)
        folder = os.path.dirname(path)
        if folder:
            os.makedirs(folder, exist_ok=True)
        self._pending_saves.append(path)
        seq[1] += 1
        if seq[1] > last:
            self._frame_sequence = None

    def _flush_saves(self) -> None:
        if not self._pending_saves:
            return
        from .export import format_of, save_frame, save_pixels

        paths, self._pending_saves = self._pending_saves, []
        for path in paths:
            if format_of(path) == "png":
                save_pixels(self._renderer.pixels(), path)      # what is on screen
            else:
                save_frame(self.frame, path, self.width, self.height, self._platform.backing_scale)

    # ------------------------------------------------------------ style
    def read_color(self, value: ColorLike, *more: float) -> Color:
        """A colour form read under the current colour mode (S-082, contract S15, S16).

        ``read_color(255, 0, 0)`` is the same as ``read_color((255, 0, 0))``: 2 to 4 separate numbers.
        """
        if more:
            if any(isinstance(v, bool) for v in (value, *more)):
                raise TypeError("True and False are not numbers here: give numbers, e.g. fill(255, 0, 0)")
            if not isinstance(value, (int, float)):
                raise ValueError(f"f.fill() and friends take more than one argument only for numbers, not {value!r}: "
                                 "give a name, hex string, colour or gradient on its own")
            if len(more) > 3:
                raise ValueError("a colour takes at most 4 numbers (red, green, blue, alpha)")
            value = (value, *more)
        state = self._states.current
        return parse_in_mode(value, state.color_mode, state.color_ranges)

    def _paint(self, value, *more):
        if more and isinstance(value, Gradient):
            raise ValueError("a gradient is given on its own, without more numbers")
        return parse_paint(value, lambda v: self.read_color(v, *more))

    def color_mode(self, mode: str, max1: float | None = None, max2: float | None = None,
                   max3: float | None = None, max_alpha: float | None = None) -> None:
        """Choose how numbers are read as a colour: "rgb", "hsb" or "hsl", with optional ranges."""
        if mode not in COLOR_MODES:
            raise ValueError(f"f.color_mode() takes one of {', '.join(map(repr, COLOR_MODES))}, not {mode!r}")
        for m in (max1, max2, max3, max_alpha):
            if m is not None and (isinstance(m, bool) or not isinstance(m, (int, float)) or not m > 0):
                raise ValueError(f"f.color_mode() ranges must be numbers above 0, not {m!r}")
        state = self._states.current
        index = COLOR_MODES.index(mode)
        old = state.color_ranges[index]
        if max1 is None:
            new = old
        elif max2 is None:
            new = (max1, max1, max1, max1)
        elif max3 is None:
            raise ValueError("f.color_mode() takes one range, three ranges or four, not two")
        elif max_alpha is None:
            new = (max1, max2, max3, old[3])
        else:
            new = (max1, max2, max3, max_alpha)
        ranges = state.color_ranges[:index] + (tuple(new),) + state.color_ranges[index + 1:]
        self._states.update(color_mode=mode, color_ranges=ranges)

    def fill(self, color: ColorLike, *more: float) -> None:
        self._states.update(fill=self._paint(color, *more))      # a colour or a gradient (S-050)

    def no_fill(self) -> None:
        self._states.update(fill=None)

    def stroke(self, color: ColorLike, *more: float) -> None:
        self._states.update(stroke=self._paint(color, *more))

    def no_stroke(self) -> None:
        self._states.update(stroke=None)

    def stroke_width(self, pixels: int) -> None:
        if pixels < 1:
            raise ValueError("stroke width must be at least 1")
        self._states.update(stroke_width=int(pixels))

    # ---- stroke styles and smoothing (S-042, contract S11/C6)
    STROKE_CAPS = ("round", "square", "butt")
    STROKE_JOINS = ("round", "miter", "bevel")

    def stroke_cap(self, cap: str) -> None:
        if cap not in self.STROKE_CAPS:
            raise ValueError(f"f.stroke_cap() takes one of {', '.join(map(repr, self.STROKE_CAPS))}, not {cap!r}")
        self._states.update(stroke_cap=cap)

    def stroke_join(self, join: str) -> None:
        if join not in self.STROKE_JOINS:
            raise ValueError(f"f.stroke_join() takes one of {', '.join(map(repr, self.STROKE_JOINS))}, not {join!r}")
        self._states.update(stroke_join=join)

    def miter_limit(self, limit: float) -> None:
        if limit < 1:
            raise ValueError("f.miter_limit() must be at least 1")
        self._states.update(miter_limit=float(limit))

    def stroke_dash(self, pattern, offset: float = 0) -> None:
        """Dashed strokes: stroke_dash(10) or stroke_dash([12, 4, 2, 4]); offset shifts the pattern."""
        values = (pattern,) if isinstance(pattern, (int, float)) else tuple(pattern)
        if not values or any((not isinstance(v, (int, float))) or v < 0 for v in values) or sum(values) == 0:
            raise ValueError("f.stroke_dash() needs one or more lengths of 0 or more, not all 0, e.g. f.stroke_dash([10, 5])")
        self._states.update(dash=tuple(float(v) for v in values), dash_offset=float(offset))

    def no_dash(self) -> None:
        self._states.update(dash=(), dash_offset=0.0)

    def no_smooth(self) -> None:
        """Hard, pixel-sharp edges (no anti-aliasing) from now on - for pixel art."""
        self._smooth = False
        if self._has_window:
            self.frame.append(ir.SetAntialias(False))

    def smooth(self) -> None:
        """Smooth (anti-aliased) edges again - the default."""
        self._smooth = True
        if self._has_window:
            self.frame.append(ir.SetAntialias(True))

    def text_size(self, size: int) -> None:
        if size <= 0:
            raise ValueError("text size must be positive")
        self._states.update(text_size=int(size))

    # ---- fonts and styles (S-054, contract T11/T12)
    TEXT_STYLES = TEXT_STYLES          # one list, in typography (contract T12)

    def load_font(self, path: str, base_dir: str | None = None):
        """Load a TrueType/OpenType font file; pass the result to f.text_font()."""
        from .typography import load_font as _load_font

        return _load_font(path, base_dir)

    def text_font(self, font, size: float | None = None, *, base_dir: str | None = None) -> None:
        """Use *font* (from f.load_font(), a path, or None for the built-in family) for later text."""
        from .typography import Font

        if font is None:
            key = None
        elif isinstance(font, Font):
            key = font.name
        elif isinstance(font, str):
            key = self.load_font(font, base_dir=base_dir).name
        else:
            raise TypeError(
                f"f.text_font() needs a font from f.load_font(), a path, or None, not {type(font).__name__}"
            )
        changes = {"font": key}
        if size is not None:
            changes["text_size"] = int(size)
        self._states.update(**changes)

    def text_style(self, style: str) -> None:
        """Use one of the four built-in styles for later text (ignored once a font is loaded)."""
        if style not in self.TEXT_STYLES:
            raise ValueError(f"f.text_style() takes one of {', '.join(map(repr, self.TEXT_STYLES))}, not {style!r}")
        self._states.update(text_style=style)

    # ---- text alignment and metrics (S-049, contract T7/T8)
    TEXT_ALIGNS = ("left", "center", "right")
    TEXT_VALIGNS = ("top", "center", "baseline", "bottom")

    def text_align(self, horizontal: str, vertical: str | None = None) -> None:
        if horizontal not in self.TEXT_ALIGNS:
            raise ValueError(f"f.text_align() takes one of {', '.join(map(repr, self.TEXT_ALIGNS))} first, not {horizontal!r}")
        if vertical is not None and vertical not in self.TEXT_VALIGNS:
            raise ValueError(f"f.text_align()'s second value is one of {', '.join(map(repr, self.TEXT_VALIGNS))}, not {vertical!r}")
        changes = {"text_align": horizontal}
        if vertical is not None:
            changes["text_valign"] = vertical
        self._states.update(**changes)

    def text_ascent(self) -> float:
        from .typography import effective_font, text_metrics

        return text_metrics(self.style.text_size, effective_font(self.style))[0]

    def text_descent(self) -> float:
        from .typography import effective_font, text_metrics

        return text_metrics(self.style.text_size, effective_font(self.style))[1]

    def text_leading(self, leading: float | None) -> None:
        if leading is not None and not leading >= 0:
            raise ValueError("f.text_leading() takes a distance of 0 or more pixels, or None for automatic")
        self._states.update(text_leading=None if leading is None else float(leading))

    @staticmethod
    def _leading(style) -> float:
        return style.text_leading if style.text_leading is not None else style.text_size * 1.25

    def _emit_lines(self, lines: list[str], x: float, y: float, color: Color, style, top: float | None = None) -> None:
        """Emit one Text op per line, top-left anchored, so that (x, y) is the block's alignment point
        (contract T7/T9). *top*, when given, is the block's top edge (text boxes place it themselves)."""
        from .typography import effective_font, text_metrics, text_width

        font = effective_font(style)
        ascent, descent = text_metrics(style.text_size, font)
        leading = self._leading(style)
        if top is None:
            block = ascent + descent + leading * (len(lines) - 1)
            shift = {"top": 0, "baseline": ascent, "bottom": block, "center": block / 2}[style.text_valign]
            top = y - shift if shift else y      # untouched numbers keep old snapshots byte-identical
        for i, line in enumerate(lines):
            left = x
            if style.text_align != "left":
                w = text_width(line, style.text_size, font)
                left -= w / 2 if style.text_align == "center" else w
            if line:
                self._emit(ir.Text(line, left, top + i * leading if i else top, color, style))

    def _text_color(self, color: ColorLike | None, style) -> Color:
        if color is not None:
            return self._paint(color)
        return style.fill or style.stroke or WHITE  # contract T4

    def text_box(self, message: object, x: float, y: float, width: float, height: float | None = None,
                 color: ColorLike | None = None) -> str:
        """Wrap *message* inside the box; return the text that did not fit (contract T10)."""
        from .typography import effective_font, text_metrics, wrap_lines

        if not width > 0 or (height is not None and not height >= 0):
            raise ValueError("f.text_box() needs a width above 0 and a height of 0 or more (or no height)")
        style = self.style
        font = effective_font(style)
        lines, rests = wrap_lines(str(message), width, style.text_size, font)
        ascent, descent = text_metrics(style.text_size, font)
        leading = self._leading(style)
        fitting = len(lines)
        if height is not None:
            fitting = 0
            while fitting < len(lines) and fitting * leading + ascent + descent <= height + 1e-9:
                fitting += 1
        shown = lines[:fitting]
        if shown:
            block = ascent + descent + leading * (len(shown) - 1)
            room = (height if height is not None else block) - block
            drop = {"top": 0, "baseline": 0, "center": room / 2, "bottom": room}[style.text_valign]
            top = y + drop if drop else y
            anchor = x + {"left": 0, "center": width / 2, "right": width}[style.text_align]
            self._emit_lines(shown, anchor, y, self._text_color(color, style), style, top=top)
        return rests[fitting] if fitting < len(lines) else ""

    # ------------------------------------------------------------ drawing
    def background(self, color: ColorLike, *more: float) -> None:
        self._emit(ir.Clear(self._paint(color, *more)))

    # ---- drawing modes (S-081, contract F10). Resolved before an op is recorded, so the IR
    # always holds top-left geometry for rectangles and centre geometry for ellipses.
    RECT_MODES = ("corner", "corners", "center", "radius")
    ELLIPSE_MODES = ("center", "radius", "corner", "corners")
    IMAGE_MODES = ("corner", "corners", "center")

    def rect_mode(self, mode: str) -> None:
        """Choose how rect() and square() read their numbers: corner, corners, center or radius."""
        self._set_mode("rect_mode", mode, self.RECT_MODES)

    def ellipse_mode(self, mode: str) -> None:
        """Choose how ellipse(), circle() and arc() read their numbers: center, radius, corner or corners."""
        self._set_mode("ellipse_mode", mode, self.ELLIPSE_MODES)

    def image_mode(self, mode: str) -> None:
        """Choose how image() reads its numbers: corner, corners or center."""
        self._set_mode("image_mode", mode, self.IMAGE_MODES)

    def _set_mode(self, name: str, mode: str, valid: tuple[str, ...]) -> None:
        if mode not in valid:
            raise ValueError(f"f.{name}() takes one of {', '.join(map(repr, valid))}, not {mode!r}")
        self._states.update(**{name: mode})

    @staticmethod
    def _box_from_corners(x1: float, y1: float, x2: float, y2: float) -> tuple[float, float, float, float]:
        return min(x1, x2), min(y1, y2), abs(x2 - x1), abs(y2 - y1)

    def _rect_box(self, x: float, y: float, w: float, h: float, one_size: bool = False) -> tuple[float, float, float, float]:
        """Top-left x, y, width, height for the current rect_mode."""
        mode = self.style.rect_mode
        if mode == "corners" and not one_size:
            return self._box_from_corners(x, y, w, h)
        if mode == "center":
            return x - w / 2, y - h / 2, w, h
        if mode == "radius":
            return x - w, y - h, w * 2, h * 2
        return x, y, w, h                       # "corner" (and "corners" for square): numbers untouched

    def _ellipse_box(self, x: float, y: float, w: float, h: float, one_size: bool = False) -> tuple[float, float, float, float]:
        """Centre x, y, width, height for the current ellipse_mode."""
        mode = self.style.ellipse_mode
        if mode == "corners" and not one_size:
            left, top, w, h = self._box_from_corners(x, y, w, h)
            return left + w / 2, top + h / 2, w, h
        if mode in ("corner", "corners"):
            return x + w / 2, y + h / 2, w, h
        if mode == "radius":
            return x, y, w * 2, h * 2
        return x, y, w, h                       # "center": numbers untouched

    def circle(self, x: float, y: float, diameter: float) -> None:
        x, y, w, _ = self._ellipse_box(x, y, diameter, diameter, one_size=True)
        self._emit(ir.Circle(x, y, w, self.style))

    def ellipse(self, x: float, y: float, width: float, height: float) -> None:
        x, y, width, height = self._ellipse_box(x, y, width, height)
        self._emit(ir.Ellipse(x, y, width, height, self.style))

    def rect(self, x: float, y: float, width: float, height: float) -> None:
        x, y, width, height = self._rect_box(x, y, width, height)
        self._emit(ir.Rect(x, y, width, height, self.style))

    def line(self, x1: float, y1: float, x2: float, y2: float) -> None:
        self._emit(ir.Line(x1, y1, x2, y2, self.style))

    def point(self, x: float, y: float) -> None:
        self._emit(ir.Point(x, y, self.style))

    # ---- more shapes (S-041, contract F5-F7)
    def square(self, x: float, y: float, size: float) -> None:
        """A square placed like rect(): by its top-left corner unless rect_mode() says otherwise."""
        x, y, w, h = self._rect_box(x, y, size, size, one_size=True)
        self._emit(ir.Rect(x, y, w, h, self.style))

    def triangle(self, x1: float, y1: float, x2: float, y2: float, x3: float, y3: float) -> None:
        self._emit_path(Path().move_to(x1, y1).line_to(x2, y2).line_to(x3, y3).close())

    def quad(self, x1: float, y1: float, x2: float, y2: float,
             x3: float, y3: float, x4: float, y4: float) -> None:
        self._emit_path(Path().move_to(x1, y1).line_to(x2, y2).line_to(x3, y3).line_to(x4, y4).close())

    def polygon(self, points) -> None:
        """A closed shape through a list of (x, y) points."""
        pts = [tuple(pt) for pt in points]
        if any(len(pt) != 2 for pt in pts):
            raise ValueError("f.polygon() needs a list of (x, y) points")
        if len(pts) < 2:
            raise ValueError("f.polygon() needs at least two points")
        path = Path().move_to(*pts[0])
        for pt in pts[1:]:
            path = path.line_to(*pt)
        self._emit_path(path.close())

    ARC_MODES = ("open", "chord", "pie")

    def arc(self, x: float, y: float, width: float, height: float,
            start: float, stop: float, mode: str = "open") -> None:
        """Part of an ellipse centred at (x, y), from *start* to *stop* degrees, clockwise.

        mode "open": the region is filled but the outline is not closed (as in p5);
        "chord": closed by a straight line; "pie": closed through the centre.
        """
        if mode not in self.ARC_MODES:
            raise ValueError(f"f.arc() mode must be one of {', '.join(self.ARC_MODES)}, not {mode!r}")
        while stop < start:
            stop += 360
        stop = min(stop, start + 360)
        x, y, width, height = self._ellipse_box(x, y, width, height)
        rx, ry = width / 2, height / 2
        if mode == "pie":
            self._emit_path(Path().move_to(x, y).arc_to(x, y, rx, ry, start, stop).close())
            return
        outline = Path().arc_to(x, y, rx, ry, start, stop)
        closed = outline.close()
        if mode == "chord":
            self._emit_path(closed)
            return
        style = self.style                      # "open": fill the chord area, stroke only the curve
        self._require_window()
        if style.fill is not None:
            self._emit(self._fill_op(closed, style))
        if style.stroke is not None:
            self._emit(self._stroke_op(outline, style))

    def clear(self) -> None:
        """Make the whole canvas transparent (saved PNGs keep the transparency)."""
        self._emit(ir.Clear(Color(0, 0, 0, 0)))

    def text(self, message: object, x: float, y: float, color: ColorLike | None = None) -> None:
        style = self.style
        self._emit_lines(str(message).split("\n"), x, y, self._text_color(color, style), style)

    def text_width(self, message: object) -> float:
        """Advance width of *message* in logical pixels at the current text_size (contract T6)."""
        from .typography import effective_font, text_width

        font = effective_font(self.style)
        return max(text_width(line, self.style.text_size, font) for line in str(message).split("\n"))

    # ------------------------------------------------------------ shapes, paths, clipping (S-028)
    def begin_shape(self) -> None:
        if self._shape is not None:
            raise RuntimeError("f.begin_shape() called again before f.end_shape(); finish the first shape.")
        self._shape = ShapeBuilder()

    def vertex(self, x: float, y: float) -> None:
        self._open_shape("vertex").vertex(x, y)

    def bezier_vertex(self, cx1: float, cy1: float, cx2: float, cy2: float, x: float, y: float) -> None:
        self._open_shape("bezier_vertex").bezier_vertex(cx1, cy1, cx2, cy2, x, y)

    def quadratic_vertex(self, cx: float, cy: float, x: float, y: float) -> None:
        self._open_shape("quadratic_vertex").quadratic_vertex(cx, cy, x, y)

    def curve_vertex(self, x: float, y: float) -> None:
        self._open_shape("curve_vertex").curve_vertex(x, y)

    def begin_contour(self) -> None:
        self._open_shape("begin_contour").begin_contour()

    def end_contour(self) -> None:
        self._open_shape("end_contour").end_contour()

    def curve_tightness(self, tightness: float) -> None:
        self._states.update(curve_tightness=float(tightness))

    def end_shape(self, close: bool = False) -> None:
        """Contract F3: closed shapes are filled then stroked; open ones are stroked only."""
        shape = self._open_shape("end_shape")
        path = shape.build(close, self.style.curve_tightness)
        self._shape = None
        self._emit_path(path)

    def bezier(self, x1, y1, cx1, cy1, cx2, cy2, x2, y2) -> None:
        """A single cubic Bezier curve: open, so stroked only (F3)."""
        self._emit_path(Path().move_to(x1, y1).cubic_to(cx1, cy1, cx2, cy2, x2, y2))

    def curve(self, x1, y1, x2, y2, x3, y3, x4, y4) -> None:
        """The Catmull-Rom curve from (x2, y2) to (x3, y3), steered by (x1, y1) and (x4, y4)."""
        c1, c2 = catmull_rom_controls((x1, y1), (x2, y2), (x3, y3), (x4, y4), self.style.curve_tightness)
        self._emit_path(Path().move_to(x2, y2).cubic_to(*c1, *c2, x3, y3))

    def curve_point(self, a, b, c, d, t) -> float:
        from .shapes import curve_point

        return curve_point(a, b, c, d, t, self.style.curve_tightness)

    def curve_tangent(self, a, b, c, d, t) -> float:
        from .shapes import curve_tangent

        return curve_tangent(a, b, c, d, t, self.style.curve_tightness)

    def _open_shape(self, name: str) -> ShapeBuilder:
        if self._shape is None:
            raise RuntimeError(f"f.{name}() called outside a shape: call f.begin_shape() first.")
        return self._shape

    @staticmethod
    def path() -> PathBuilder:
        return PathBuilder()

    def draw_path(self, path: PathBuilder | Path) -> None:
        self._emit_path(_geometry_of(path, "draw_path"))

    def clip(self, path: PathBuilder | Path) -> None:
        """Limit later drawing to *path* (implicitly closed); pop() lifts it, so use it inside push()/pop()."""
        geometry = _geometry_of(path, "clip")
        if geometry.is_empty:
            # Clipping to nothing would silently hide everything drawn afterwards (S-067).
            warnings.warn(
                "f.clip() was given an empty path, so it was ignored. "
                "Add points with move_to()/line_to() before clipping.",
                FungroundWarning,
                stacklevel=3,
            )
            return
        self._emit(ir.ClipPath(geometry))

    def no_clip(self) -> None:
        """Remove clipping until the enclosing pop() / end of the saved_state block."""
        self._emit(ir.ResetClip())

    def _emit_path(self, geometry: Path) -> None:
        self._require_window()
        if geometry.is_empty:
            return
        style = self.style
        if style.fill is not None and geometry.is_closed:      # F3: open shapes are never filled
            self._emit(self._fill_op(geometry, style))
        if style.stroke is not None:                           # S5: stroke on top of the fill
            self._emit(self._stroke_op(geometry, style))

    @staticmethod
    def _fill_op(geometry: Path, style: GraphicsState) -> ir.FillPath:
        return ir.FillPath(geometry, style.fill, style.blend_mode, style.opacity, style.shadow)

    @staticmethod
    def _stroke_op(geometry: Path, style: GraphicsState) -> ir.StrokePath:
        return ir.StrokePath(geometry, style.stroke, float(style.stroke_width),
                             style.stroke_cap, style.stroke_join, style.miter_limit,
                             style.dash, style.dash_offset,
                             style.blend_mode, style.opacity, style.shadow)

    # ---- compositing (S-051, contract S14)
    BLEND_MODES = ("normal", "multiply", "screen", "overlay", "darken", "lighten", "add", "difference",
                   "exclusion", "dodge", "burn", "hard_light", "soft_light", "hue", "saturation", "color",
                   "luminosity")

    def blend_mode(self, mode: str) -> None:
        if mode not in self.BLEND_MODES:
            raise ValueError(f"f.blend_mode() takes one of {', '.join(map(repr, self.BLEND_MODES))}, not {mode!r}")
        self._states.update(blend_mode=mode)

    def opacity(self, amount: float) -> None:
        if isinstance(amount, bool) or not isinstance(amount, (int, float)) or not 0 <= amount <= 255:
            raise ValueError(f"f.opacity() takes a number from 0 (invisible) to 255 (solid), not {amount!r}")
        self._states.update(opacity=int(amount))

    def shadow(self, x_offset: float, y_offset: float, blur: float = 5, color: ColorLike = DEFAULT_SHADOW_COLOR) -> None:
        if not blur >= 0:
            raise ValueError("f.shadow() needs a blur of 0 or more")
        self._states.update(shadow=(float(x_offset), float(y_offset), float(blur),
                                       Color(*DEFAULT_SHADOW_COLOR) if color is DEFAULT_SHADOW_COLOR
                                       else self.read_color(color)))   # the default is black at half strength in any mode

    def no_shadow(self) -> None:
        self._states.update(shadow=None)

    # ------------------------------------------------------------ helpers
    def random(self, low: float = 1.0, high: float | None = None) -> float:
        if high is None:
            high = low
            low = 0.0
        return self._rng.uniform(low, high)

    def random_seed(self, seed: int | None = None) -> None:
        self._rng.seed(seed)

    def noise(self, x: float, y: float = 0.0, z: float = 0.0) -> float:
        return self._noise(x, y, z)

    def noise_seed(self, seed: int) -> None:
        self._noise.seed(seed)

    def noise_detail(self, octaves: int, falloff: float | None = None) -> None:
        if octaves < 1:
            raise ValueError("f.noise_detail(): octaves must be at least 1")
        if falloff is not None and not 0 < falloff < 1:
            raise ValueError("f.noise_detail(): falloff must be between 0 and 1, e.g. 0.5")
        self._noise.detail(octaves, falloff)

    def random_gaussian(self, mean: float = 0.0, sd: float = 1.0) -> float:
        """A normally distributed random number: most values near *mean*, spread *sd*."""
        if sd < 0:
            raise ValueError("f.random_gaussian(): the spread (sd) cannot be negative")
        return self._rng.gauss(mean, sd)

    def random_choice(self, items):
        """One item picked at random from a list, tuple or string."""
        if len(items) == 0:
            raise ValueError("f.random_choice() needs at least one item to choose from")
        return self._rng.choice(items)

    @staticmethod
    def map_range(value: float, start1: float, stop1: float, start2: float, stop2: float,
                  clamp: bool = False) -> float:
        if start1 == stop1:
            raise ValueError("f.map_range(): the first range is empty (start1 == stop1)")
        result = start2 + (value - start1) * (stop2 - start2) / (stop1 - start1)
        if clamp:
            low, high = min(start2, stop2), max(start2, stop2)
            result = max(low, min(high, result))
        return result

    @staticmethod
    def lerp(start: float, stop: float, amount: float) -> float:
        return start + (stop - start) * amount

    @staticmethod
    def norm(value: float, start: float, stop: float) -> float:
        if start == stop:
            raise ValueError("f.norm(): the range is empty (start == stop)")
        return (value - start) / (stop - start)

    @staticmethod
    def mag(x: float, y: float) -> float:
        return math.hypot(x, y)

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

    # ---- input events (S-045, contract I3, D-016)
    def _dispatch_events(self) -> None:
        """Update the input live values and call the learner's callbacks, in event order."""
        for ev in self._platform.events():
            if ev.kind in ("mouse_pressed", "mouse_released") and ev.button:
                self.mouse_button = ev.button
            if ev.kind in ("key_pressed", "key_released"):
                self.key, self.key_code = ev.key, ev.key_code
            self._call(ev.kind, ev)
            if ev.kind == "mouse_released":
                self._call("mouse_clicked", ev)
            if ev.kind == "key_pressed" and ev.key and len(ev.key) == 1:
                self._call("key_typed", ev)

    def _call(self, name: str, ev) -> None:
        fn = self._callbacks.get(name)
        if fn is None:
            return
        if name == "mouse_wheel" and _takes_an_argument(fn):
            fn(ev.delta)
        else:
            fn()

    # ---- loop control and clock (S-048, contract R10)
    def exit(self) -> None:
        """Same as stop(): the sketch ends after the current frame."""
        self._only_in_animated("exit")
        self.stop()

    def no_loop(self) -> None:
        self._only_in_animated("no_loop")
        self._looping = False

    def loop(self) -> None:
        self._only_in_animated("loop")
        self._looping = True

    def redraw(self) -> None:
        self._only_in_animated("redraw")
        self._redraw_pending = True

    def is_looping(self) -> bool:
        return self._looping

    def millis(self) -> int:
        return int((time.perf_counter() - self._start_time) * 1000)

    def frame_rate(self) -> float:
        return self._fps_measured

    @staticmethod
    def second() -> int:
        return datetime.datetime.now().second

    @staticmethod
    def minute() -> int:
        return datetime.datetime.now().minute

    @staticmethod
    def hour() -> int:
        return datetime.datetime.now().hour

    @staticmethod
    def day() -> int:
        return datetime.datetime.now().day

    @staticmethod
    def month() -> int:
        return datetime.datetime.now().month

    @staticmethod
    def year() -> int:
        return datetime.datetime.now().year

    def run_namespace(
        self, namespace: Namespace, *, fps: int | None = None, max_frames: int | None = None
    ) -> None:
        """Run the setup()/draw() found in *namespace* (the sketch's globals)."""
        global _run_started
        if self._script:
            if self.frame:
                raise RuntimeError(
                    "This file mixes the two styles: it draws at the top level (a script) and also calls "
                    "f.run() (an animated sketch). Pick one. For an animation, move the drawing into draw(). "
                    "For a script, remove f.run() and end with f.show()."
                )
            self._script = False               # only f.size() so far: it sets the sketch's canvas size
            self._has_window = False
            self._renderer.attach(0, 0)
        _run_started = True
        setup, draw = _sketch_functions(namespace)
        self._callbacks = _event_callbacks(namespace)
        if max_frames is not None and max_frames <= 0:
            raise ValueError("max_frames must be positive")
        if fps is not None and fps <= 0:
            raise ValueError("fps must be positive")
        self.last_frame = None
        self.last_ops: tuple[ir.Op, ...] | None = None
        self.frame.clear()
        self._states.unwind()
        self._shape = None
        self._graphics_counter = 0

        self._platform.start()
        self.running = True
        self.frame_count = 0
        self.delta_time = 0.0
        self._looping = True
        self._redraw_pending = False
        self._start_time = time.perf_counter()
        self._fps_measured = 0.0
        iterations = 0          # run(max_frames=n) counts loop iterations, so no_loop() sketches end too
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

                self.pmouse_x, self.pmouse_y = self.mouse_x, self.mouse_y
                inp = self._platform.input_state()
                self.mouse_x, self.mouse_y = inp.mouse_x, inp.mouse_y
                self.is_mouse_pressed, self.is_key_pressed = inp.mouse_pressed, inp.key_pressed
                self._dispatch_events()

                # draw() runs every frame while looping, once after redraw(), and always on
                # the first frame - even after no_loop() in setup(), as in p5.
                if self._looping or self._redraw_pending or self.frame_count == 0:
                    self._redraw_pending = False
                    if not self._smooth:
                        self.frame.append(ir.SetAntialias(False))   # the renderer resets per frame
                    draw()
                    self._end_draw()  # unbalanced push()es never leak into the next frame
                    self.last_ops = self.frame.ops  # what the latest drawn frame asked for (IR snapshot)
                    self._render()   # draws, presents, flushes f.save()
                    self.frame_count += 1

                iterations += 1
                if max_frames is not None and iterations >= max_frames:
                    self.last_frame = self._platform.capture()
                    self.running = False
                self.delta_time = self._platform.tick(self.fps)
                if self.delta_time > 0:
                    now = 1.0 / self.delta_time
                    self._fps_measured = now if self._fps_measured == 0 else self._fps_measured * 0.9 + now * 0.1
        finally:
            self.running = False
            self.frame.clear()
            self._pending_saves.clear()
            self._frame_sequence = None
            self._renderer.attach(0, 0)
            self._platform.close()
            self._has_window = False


def _is_positive_whole(n: object) -> bool:
    return isinstance(n, int) and not isinstance(n, bool) and n > 0


def _geometry_of(path: PathBuilder | Path, name: str) -> Path:
    if isinstance(path, PathBuilder):
        return path.geometry
    if isinstance(path, Path):
        return path
    raise TypeError(f"f.{name}() needs a path made with f.path(), not {type(path).__name__}")


CALLBACK_NAMES = ("mouse_pressed", "mouse_released", "mouse_moved", "mouse_dragged", "mouse_clicked",
                  "mouse_wheel", "key_pressed", "key_released", "key_typed")


def _event_callbacks(namespace: Namespace) -> dict[str, Callable]:
    """Input callbacks are found by name, like setup() and draw() (D-016)."""
    found = {}
    for name in CALLBACK_NAMES:
        fn = namespace.get(name)
        if fn is None:
            continue
        if not callable(fn):
            raise TypeError(f"{name} must be a function (it is called when that input happens)")
        found[name] = fn
    return found


def _takes_an_argument(fn: Callable) -> bool:
    import inspect

    try:
        params = [p for p in inspect.signature(fn).parameters.values()
                  if p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD, p.VAR_POSITIONAL)]
    except (TypeError, ValueError):
        return True
    return bool(params)


def _sketch_functions(namespace: Namespace) -> tuple[Callable[[], None] | None, Callable[[], None]]:
    setup = namespace.get("setup")
    draw = namespace.get("draw")

    if setup is not None and not callable(setup):
        raise TypeError("setup must be a function")
    if draw is None and setup is not None:
        raise RuntimeError(
            "f.run() found a setup() but no draw(). To animate, add a draw() function. "
            "To draw once, remove setup() and f.run(), write the drawing at the top level "
            "and end with f.show() (a script)."
        )
    if draw is None:
        raise RuntimeError("Define a draw() function before calling f.run().")
    if not callable(draw):
        raise TypeError("draw must be a function")

    return setup, draw
