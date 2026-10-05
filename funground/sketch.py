"""The Sketch: one running (or runnable) funground program.

Owns the lifecycle, live values, graphics state and helpers that v0.5 kept as
module globals in ``_core.py``. Talks to the OS only through a ``Platform`` and
draws only through a ``Renderer`` — never through pygame directly (see
tests/test_boundaries.py). ``api.py`` keeps the learner-facing functions as thin
wrappers over the active Sketch.
"""
from __future__ import annotations

import contextlib
from collections import namedtuple
import datetime
import math
import time
import random as _random
import warnings
from collections.abc import Callable, Iterator
from typing import Any

from . import ir
from .capabilities import Capability, FungroundWarning, missing_capability
from .controls import Button, Checkbox, ControlPanel, Slider, panel_ops
from .color import COLOR_MODES, WHITE, Color, ColorLike, parse_in_mode
from .paint import Gradient, parse_paint
from .formatted import FormattedString
from .typography import TEXT_STYLES
from .geometry import Path, Transform, rect_radii
from .paths import PathBuilder
from .noise import Noise
from .shapes import ShapeBuilder, catmull_rom_controls
from .platform.base import CURSOR_KINDS, KEY_NAMES, Platform
from .renderers import Renderer
from .state import GraphicsState, StateStack

_Piece = namedtuple("_Piece", "text ri size ascent descent width")   # one measured piece of a line (T14)

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
        self._pending_saves: list[tuple[str, str]] = []     # (path, text mode)
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
        self._graphics_before_run = 0     # pictures made while no run was active: they belong to the next run
        # S-076, contract R13-R15: a script is a top-level f.size() with no sketch running. Its
        # canvas has no window; every op it draws stays in self.frame (show() and PDF/SVG saves
        # replay them) and is drawn onto self._renderer's persistent surface on demand.
        self._script = False
        self._script_scale = 1.0
        self._script_drawn = 0         # how many of self.frame's ops are already on the surface
        self._script_depth = 0         # the persistent surface's open Save depth
        # S-084, contract R16: the pages before the current one, each (width, height, ops, BGRA pixels).
        # The current page is the live canvas (self.frame, self._renderer).
        self._pages: list[tuple[int, int, list, bytes]] = []
        self._pages_full: list[bool] = []      # for each earlier page: made by full_screen() (S-085)
        self._page_durations: list[float] = []  # S-100, contract M1: how long each earlier page is shown, in seconds
        self._frame_duration = 0.1             # the same, for the current page (it carries on to later pages)
        self._motion: list | None = None       # S-100: a recording [path, kind, frames left, frames, size, skip]
        self._page_full = False                # the same, for the current page
        # S-079, contract P7: reading the canvas mid-frame draws the ops recorded so far onto the
        # surface at once. The window frame is then drawn in steps: _frame_open says its Save is
        # open, _frame_drawn how many of self.frame's ops are already on the surface, _frame_depth
        # the Save depth they left. _render() draws only the rest.
        self._frame_open = False
        self._frame_drawn = 0
        self._frame_depth = 0
        # set() calls waiting to become one Pixels op: {(x, y): Color}.
        self._pending_pixels: dict[tuple[int, int], Color] = {}
        self.pixels: bytearray | None = None       # contract P8: None until load_pixels()
        self._render_hook: Callable[[], None] | None = None    # a picture's own flush
        self._name_root: Sketch | None = None      # who numbers the pictures that get() makes
        # S-101, contract U1: the controls, in the order made. The platform shows them in a panel
        # below the canvas; their draw ops go to a renderer of their own, never into self.frame.
        self._panel = ControlPanel()
        self._panel_shown = False                  # the platform has taken the panel
        self._panel_renderer: Renderer | None = None
        self._panel_drawn: tuple | None = None     # (version, width, scale) of the panel pixels it has
        self._in_draw = False
        # S-095, contract F16: the named layers of this canvas, in the order they were first made;
        # each is a canvas-sized Picture. _layer_open is the one a "with f.layer():" block draws on.
        self._layers: dict[str, Picture] = {}
        self._layers_hidden: set[str] = set()
        self._layer_open: Picture | None = None

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

    def _push_layer_block(self) -> None:
        """The implicit push() of a layer block: a Save marked so a picture's history can tell it from a learner's."""
        self._emit(ir.Save(layer_block=True))
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
        self._flush_pixel_patch()
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
                self._append(ir.Restore())
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
        self._pages = []
        self._pages_full = []
        self._page_durations = []
        self._frame_duration = 0.1
        if not self.running:
            self._begin_script()
            return
        self._script = False
        self._give_panel()
        pw, ph = self._platform.open_window(self.width, self.height, self.title)
        self._attach(pw, ph)

    # ---- scripts (S-076, contract R13-R15)
    def _begin_script(self) -> None:
        """A top-level f.size(): a blank canvas with no window (contract R14)."""
        self._start_page()
        self._graphics_counter, self._graphics_before_run = self._graphics_before_run, 0
        self._start_time = time.perf_counter()

    def _start_page(self) -> None:
        """A blank page at self.width x self.height with its own surface (contracts R14, R16)."""
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
        self._page_full = False
        self._reset_pixel_state()
        self._drop_layers()

    # ---- pages (S-084, contract R16, R17, D1)
    def new_page(self, width: Any = None, height: int | None = None) -> None:
        """End the current page and start a blank one (scripts only)."""
        from .pages import page_size

        if self.running:
            raise RuntimeError(
                "f.new_page() is for scripts (a file with no draw()). An animated sketch has one canvas: "
                "to make a document, remove draw() and f.run() and write the drawing at the top level."
            )
        if isinstance(width, str):
            if height is not None:
                raise ValueError("f.new_page(): a page-size name stands alone, e.g. f.new_page(\"A4\"), "
                                 "without a height")
            w, h = page_size(width)
        elif width is None and height is None:
            w, h = self.width, self.height
        elif width is None or height is None:
            raise ValueError("f.new_page() needs both width and height, a size name such as \"A4\", or nothing")
        else:
            w, h = width, height
        if isinstance(w, bool) or isinstance(h, bool) or not isinstance(w, (int, float))                 or not isinstance(h, (int, float)):
            raise TypeError(f"f.new_page() needs numbers for width and height, not ({width!r}, {height!r})")
        if w <= 0 or h <= 0:
            raise ValueError("width and height must be positive")
        if not self._script:                      # the first page, as f.size() would start it
            self.size(w, h)
            return
        self._sync_canvas()
        self._pages.append((self.width, self.height, list(self._with_layers(self.frame, files=True)),
                            bytes(self._view_pixels().data)))
        self._pages_full.append(self._page_full)
        self._page_durations.append(self._frame_duration)
        self.width, self.height = int(w), int(h)
        self._start_page()

    def page_count(self) -> int:
        """How many pages the document has so far (0 before f.size())."""
        if self._script:
            return len(self._pages) + 1
        return 1 if self._has_window else 0

    def _document_pages(self) -> list[tuple[int, int, list, bytes | None]]:
        """Every page, the current one last: (width, height, ops, pixels). The current page's pixels are None."""
        self._flush_pixel_patch()
        return [*self._pages, (self.width, self.height, list(self._with_layers(self.frame, files=True)), None)]

    def _script_flush(self) -> None:
        """Draw the ops added since the last flush onto the script canvas's surface."""
        new = self.frame.ops_since(self._script_drawn)
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
        if self._panel:
            raise RuntimeError(
                "Controls need an animated sketch, and this file is a script (it ends with f.show()). "
                "To use controls, write a draw() function and end the file with f.run()."
            )
        if not self._script:
            raise RuntimeError("No drawing window yet. Call f.size(...) first.")
        self._flush_pixel_patch()
        if isinstance(self._platform, HeadlessPlatform):
            return
        platform = self._platform
        renderer = default_renderer()
        if self._pages:
            self._show_pages(platform, renderer)
            return
        try:
            if self._page_full:
                pw, ph = platform.open_full_screen(self.title)
            else:
                pw, ph = platform.open_window(self.width, self.height, self.title)
            renderer.attach(pw, ph, platform.backing_scale)
            renderer._base_matrix = renderer._ctx.get_matrix()
            renderer.draw_batch(renderer._ctx, self._with_layers(self.frame), 0)   # the kept drawing, at the window's scale
            platform.start()
            platform.set_cursor(self._cursor)
            pixels = renderer.pixels()
            platform.present(pixels)
            while platform.poll():
                platform.present(pixels)           # keeps the picture up if the window is uncovered
                platform.tick(30)
        finally:
            platform.close()

    def _show_pages(self, platform, renderer) -> None:
        """show() for a document: the current page first; Left and Right turn the pages (contract R17)."""
        pages = self._document_pages()
        full = [*self._pages_full, self._page_full]
        total = len(pages)
        index = total - 1
        try:
            def open_page(i: int):
                w, h, ops, _ = pages[i]
                title = f"{self.title} - page {i + 1} of {total}"
                if full[i]:
                    pw, ph = platform.open_full_screen(title)
                else:
                    pw, ph = platform.open_window(w, h, title)
                renderer.attach(pw, ph, platform.backing_scale)
                renderer._base_matrix = renderer._ctx.get_matrix()
                renderer.draw_batch(renderer._ctx, ir.Frame(list(ops)), 0)
                shown = renderer.pixels()
                platform.present(shown)
                return shown

            shown = open_page(index)
            platform.start()
            platform.set_cursor(self._cursor)
            while platform.poll():
                turn = 0
                for event in platform.events():
                    if event.kind == "key_pressed":
                        turn += {"left": -1, "right": 1}.get(event.key, 0)
                if turn and 0 <= index + turn < total:
                    index += turn
                    shown = open_page(index)
                    platform.set_cursor(self._cursor)
                platform.present(shown)           # keeps the picture up if the window is uncovered
                platform.tick(30)
        finally:
            platform.close()

    def _attach(self, pw: int, ph: int) -> None:
        self._renderer.attach(pw, ph, self._platform.backing_scale)
        self._reset_pixel_state()
        self._drop_layers()
        self._has_window = True
        self._platform.set_cursor(self._cursor)

    # ---- window control (S-057, contract R12)
    def resize_canvas(self, width: int, height: int) -> None:
        """A new canvas size while the sketch runs; the canvas starts blank, like p5's resizeCanvas."""
        self.size(width, height, title=self.title, fps=self.fps)

    def full_screen(self) -> None:
        """Make the canvas fill the screen; f.width and f.height become the screen's size."""
        self._check_capabilities()
        if not self.running:                   # a script: the screen's size, no window until show() (R14)
            self.width, self.height = self._platform.display_size()
            self._pages = []
            self._pages_full = []
            self._page_durations = []
            self._frame_duration = 0.1
            self._begin_script()
            self._page_full = True
            return
        self._give_panel()
        pw, ph = self._platform.open_full_screen(self.title)
        scale = self._platform.backing_scale
        self.width, self.height = round(pw / scale), round(ph / scale)
        self._attach(pw, ph)

    # ---- controls (S-101, contract U1, D-047)
    def _new_control(self, control):
        if self._in_draw:
            raise RuntimeError(
                "Controls are made once, in setup() (or at the top of the file), not in draw(): "
                "draw() runs every frame, so it would make a new one each time. "
                "Make the control in setup(), keep it in a variable, and read it in draw()."
            )
        if self._script and (self.frame or self._pages):
            raise RuntimeError(
                "Controls need an animated sketch, and this file is a script (it draws at the top level). "
                "To use controls, write a draw() function and end the file with f.run()."
            )
        self._panel.add(control)
        if self.running and self._has_window:      # the window is open: it grows to hold the panel
            self._give_panel()
        return control

    def create_slider(self, low, high, value=None, step=None, label=None) -> Slider:
        return self._new_control(Slider(low, high, value, step, label))

    def create_checkbox(self, label, checked=False) -> Checkbox:
        return self._new_control(Checkbox(label, checked))

    def create_button(self, label) -> Button:
        return self._new_control(Button(label))

    def _give_panel(self) -> None:
        """Hand the panel to the platform before a window opens (or while it is open)."""
        if self._panel:
            self._panel_shown = self._platform.set_controls(self._panel)
            self._panel_drawn = None

    def _refresh_panel(self) -> None:
        """Draw the panel again when a control changed, and give the platform the pixels."""
        if not (self._panel_shown and self._panel):
            return
        scale = self._platform.backing_scale
        key = (self._panel.version, self.width, scale)
        if key == self._panel_drawn:
            return
        if self._panel_renderer is None:
            self._panel_renderer = default_renderer()
        renderer = self._panel_renderer
        renderer.attach(round(self.width * scale), round(self._panel.height * scale), scale)
        renderer.render(ir.Frame(panel_ops(self._panel, self.width)))
        self._platform.present_panel(renderer.pixels())
        self._panel_drawn = key

    def _end_panel(self) -> None:
        """A run ended: its controls go with it."""
        if self._panel_shown:
            self._platform.set_controls(None)
        self._panel_shown = False
        self._panel.clear()
        self._panel_drawn = None
        if self._panel_renderer is not None:
            self._panel_renderer.attach(0, 0)

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

    # ---- layers (S-095, contract F16, D-053)
    def layer(self, name: str):
        """The layer called *name*, made on first use (a canvas-sized picture); use it in "with"."""
        self._require_window()
        if not isinstance(name, str):
            raise TypeError(f"f.layer() needs a name in quotes, e.g. f.layer(\"sky\"), not {name!r}")
        if not name:
            raise ValueError("f.layer() needs a name that is not empty")
        if self._layer_open is not None:
            raise RuntimeError("f.layer() cannot be used inside another layer block: layers do not nest. "
                               "Finish the first `with f.layer(...)` block, then start the next one.")
        picture = self._layers.get(name)
        if picture is None:
            picture = self.create_graphics(self.width, self.height)
            picture._layer_owner = self
            picture._layer_name = name
            self._layers[name] = picture
        return picture

    def _enter_layer(self, picture) -> None:
        if self._layers.get(picture._layer_name) is not picture:
            raise RuntimeError("this layer belongs to an earlier canvas (f.size() or a new page dropped it). "
                               "Call f.layer(name) again to get the current one.")
        if self._layer_open is not None:
            raise RuntimeError("layers do not nest: a `with f.layer(...)` block cannot start inside another one.")
        self._layer_open = picture

    def _known_layer(self, name: str, call: str) -> None:
        if name not in self._layers:
            known = ", ".join(repr(n) for n in self._layers) or "none yet"
            raise ValueError(f"f.{call}(): there is no layer called {name!r}. Layers so far: {known}")

    def hide_layer(self, name: str) -> None:
        """Stop showing a layer (it keeps its drawing)."""
        self._known_layer(name, "hide_layer")
        self._layers_hidden.add(name)

    def show_layer(self, name: str) -> None:
        """Show a hidden layer again."""
        self._known_layer(name, "show_layer")
        self._layers_hidden.discard(name)

    def _drop_layers(self) -> None:
        """A new canvas (size, page, run): its layers go with the old one."""
        self._layers = {}
        self._layers_hidden = set()
        self._layer_open = None

    def _layer_ops(self, files: bool = False) -> list[ir.Image]:
        """One ir.Image (tagged layer=name) for each visible layer, in first-use order.

        These are never stored in self.frame: they are added on top of a copy of it whenever the
        canvas is drawn for a window, a PNG, a PDF or an SVG, so the canvas's own ops (and IR
        snapshots) stay exactly what the sketch drew. Every layer is flushed, hidden or not.
        With *files* (S-096), hidden layers are included too, tagged layer_hidden: PDF and SVG keep
        them switched off, and every other renderer leaves them out."""
        ops: list[ir.Image] = []
        for name, picture in self._layers.items():
            snap = picture._snapshot()                 # draws what the layer has recorded so far
            hidden = name in self._layers_hidden
            if hidden and not files:
                continue
            ops.append(ir.Image(picture.name, snap.version, 0.0, 0.0, float(picture.width),
                                float(picture.height), snapshot=snap, layer=name, layer_hidden=hidden))
        return ops

    def _with_layers(self, frame: ir.Frame, files: bool = False) -> ir.Frame:
        """*frame* with the layers' ops after it (the same frame when there are none): the visible
        ones, plus the hidden ones with *files* (for PDF and SVG, and for pages kept for them)."""
        if not self._layers:
            return frame
        layers = self._layer_ops(files)
        if not layers:
            return frame
        # Layers sit over the canvas exactly as on screen: close any push() the canvas left open and drop its
        # transform and clip first, or a file would move or clip the layers where the window does not.
        depth = 0
        for op in frame:
            if isinstance(op, ir.Save):
                depth += 1
            elif isinstance(op, ir.Restore) and depth:
                depth -= 1
        top = [ir.Restore()] * depth + [ir.Save(), ir.ResetMatrix(), ir.ResetClip()]
        return ir.Frame([*frame, *top, *layers, ir.Restore()])

    def _view(self):
        """A renderer whose surface is the canvas with the visible layers over it (the canvas's own
        renderer when there are none). Call after the canvas has been drawn up to date."""
        if not self._layers:
            return self._renderer
        layers = self._layer_ops()
        if not layers:
            return self._renderer
        src = self._renderer.pixels()
        view = default_renderer()
        view.attach(src.width, src.height, self._renderer._scale)
        surface = view.surface
        surface.flush()
        surface.get_data()[:] = bytes(src.data)
        surface.mark_dirty()
        view._base_matrix = view._ctx.get_matrix()
        view.draw_batch(view._ctx, ir.Frame(layers), 0)
        return view

    def _view_pixels(self):
        """The pixels of _view(), as a copy when they are not the canvas's own surface."""
        from .platform.base import Pixels

        view = self._view()
        pixels = view.pixels()
        if view is self._renderer:
            return pixels
        return Pixels(bytes(pixels.data), pixels.width, pixels.height, pixels.format)

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
        scale = self._script_scale if self._script else self._platform.backing_scale
        picture = Picture(int(width), int(height), scale, self._next_graphics_name())
        picture._sketch._name_root = self._name_root or self
        return picture

    def load_image(self, path: str, base_dir: str | None = None):
        """A picture made from an image file (contract P4). Needs no window, so it may come first."""
        from . import imaging
        from .picture import Picture
        from .typography import _resolve_path

        resolved = _resolve_path(path, base_dir, "f.load_image()", "image")
        width, height, bgra = imaging.decode(resolved)
        picture = Picture.from_pixels(width, height, bgra, self._next_graphics_name())
        picture._sketch._name_root = self._name_root or self
        return picture

    def load_svg(self, path: str, base_dir: str | None = None):
        """A picture drawn from an SVG file's shapes (contract P11). Needs no window, so it may come first."""
        from . import svg
        from .picture import Picture
        from .typography import _resolve_path

        resolved = _resolve_path(path, base_dir, "f.load_svg()", "SVG")
        doc = svg.read(resolved, "f.load_svg()")
        # The picture is drawn at a finer scale than the window needs, so the raster copy that a
        # window shows stays reasonably sharp when the picture is drawn larger. PDF/SVG replay vectors.
        window = (self._script_scale if self._script else self._platform.backing_scale) if self._has_window else 1.0
        scale = max(float(window), 2.0 if max(doc.width, doc.height) <= 2048 else 1.0)
        picture = Picture(doc.width, doc.height, scale, self._next_graphics_name())
        picture._sketch._name_root = self._name_root or self
        svg.draw(doc, picture)
        return picture

    def _next_graphics_name(self) -> str:
        """The next picture name, numbered in creation order within a run (a picture's get() uses its window's count)."""
        root = self._name_root or self
        root._graphics_counter += 1
        if not (root.running or root._script):       # made before f.size()/f.run(): keep its number in that run
            root._graphics_before_run += 1
        return f"graphics-{root._graphics_counter}"

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
        self._append(op)

    def _append(self, op: ir.Op) -> None:
        """Record an op, after turning any waiting set() calls into their one Pixels op (contract P7)."""
        if self._pending_pixels:
            self._flush_pixel_patch()
        self.frame.append(op)

    def _render(self) -> None:
        """Draw everything recorded so far and present it; the frame then starts empty."""
        self._end_draw()
        # Always present, even a frame that drew nothing: the canvas is still a frame
        # (the headless platform has nothing to capture otherwise).
        if self._frame_open:                 # part of the frame is already on the surface (S-079)
            self._flush_frame()
            self._renderer.end_frame(self._renderer._ctx, self._frame_depth)
            self._frame_open, self._frame_drawn, self._frame_depth = False, 0, 0
        else:
            self._renderer.render(self.frame)
        self._refresh_panel()
        self._platform.present(self._view_pixels())          # the canvas with its visible layers over it (F16)
        self._queue_sequence_frame()
        self._record_motion_frame()
        self._flush_saves()
        self.frame.clear()

    # ------------------------------------------------------------ pixels (S-079, contract P7, P8)
    def _reset_pixel_state(self) -> None:
        """A new canvas (or a new run): nothing is half drawn, nothing is waiting, no pixels loaded."""
        self._frame_open, self._frame_drawn, self._frame_depth = False, 0, 0
        self._pending_pixels = {}
        self.pixels = None

    def _flush_frame(self) -> None:
        """Draw the window frame's ops that are not on the surface yet, and remember how far it got."""
        renderer = self._renderer
        if not self._frame_open:
            renderer.begin_frame(renderer._ctx)
            self._frame_open, self._frame_drawn, self._frame_depth = True, 0, 0
        new = self.frame.ops_since(self._frame_drawn)
        if new:
            self._frame_depth = renderer.draw_batch(renderer._ctx, ir.Frame(list(new)), self._frame_depth)
            self._frame_drawn += len(new)

    def _render_so_far(self) -> None:
        """Draw what is recorded so far onto the canvas's surface, so it can be read (contract P7)."""
        if self._render_hook is not None:
            self._render_hook()                    # a picture flushes itself
        elif self._script:
            self._script_flush()
        else:
            self._flush_frame()

    def _sync_canvas(self) -> None:
        self._flush_pixel_patch()
        self._render_so_far()

    def _flush_pixel_patch(self) -> None:
        """Turn the waiting set() calls into one Pixels op (so many set()s are one op, never one each)."""
        if not self._pending_pixels:
            return
        patch, self._pending_pixels = self._pending_pixels, {}
        self._render_so_far()                      # pixels around the written ones keep what is drawn now
        self.frame.append(self._renderer.patch_op(patch))

    @staticmethod
    def _whole(value: Any, name: str, call: str) -> int:
        """A coordinate rounded down to a whole pixel (contract P7)."""
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise TypeError(f"f.{call}(): {name} must be a number, not {value!r}")
        if isinstance(value, float) and not math.isfinite(value):
            raise ValueError(f"f.{call}(): {name} must be a finite number, not {value!r}")
        return math.floor(value)

    def get(self, x: float, y: float, w: float | None = None, h: float | None = None):
        """The colour at a pixel (a colour object), or the region x, y, w, h as a new picture (contract P7)."""
        from .picture import Picture

        self._require_window()
        x, y = self._whole(x, "x", "get"), self._whole(y, "y", "get")
        if (w is None) != (h is None):
            raise ValueError("f.get(): to copy a region give both w and h, or neither for one pixel")
        if w is not None:
            w, h = self._whole(w, "w", "get"), self._whole(h, "h", "get")
            if w <= 0 or h <= 0:
                raise ValueError("f.get(): w and h must be above 0")
        self._sync_canvas()
        from . import imaging

        if w is None:
            r, g, b, a = imaging.bgra_to_rgba(self._view().read_logical(x, y, 1, 1, self.width, self.height), 1, 1)
            return Color(r, g, b, a)
        bgra = self._view().read_logical(x, y, w, h, self.width, self.height)
        picture = Picture.from_pixels(w, h, bgra, self._next_graphics_name())
        picture._sketch._name_root = self._name_root or self
        return picture

    def set(self, x: float, y: float, color: ColorLike, *more: float) -> None:
        """Make one pixel exactly this colour, whatever the drawing state is (contract P7)."""
        self._require_window()
        x, y = self._whole(x, "x", "set"), self._whole(y, "y", "set")
        c = self.read_color(color, *more)
        if 0 <= x < self.width and 0 <= y < self.height:
            self._pending_pixels[(x, y)] = c

    def load_pixels(self) -> None:
        """Copy the canvas into ``pixels``: red, green, blue, alpha for each pixel, row by row (contract P8)."""
        self._require_window()
        self._sync_canvas()
        from . import imaging

        bgra = self._renderer.read_logical(0, 0, self.width, self.height, self.width, self.height)
        self.pixels = imaging.bgra_to_rgba(bgra, self.width, self.height)

    def update_pixels(self) -> None:
        """Write ``pixels`` back onto the canvas, as a set() of every pixel (contract P8)."""
        self._require_window()
        if self.pixels is None:
            raise RuntimeError("f.update_pixels() needs f.load_pixels() first: it copies the canvas into "
                               "pixels, which you then change")
        try:
            rgba = bytes(self.pixels)
        except (TypeError, ValueError) as exc:
            raise ValueError("f.update_pixels(): pixels must hold numbers from 0 to 255") from exc
        if len(rgba) != self.width * self.height * 4:
            raise ValueError(f"f.update_pixels(): pixels must have {self.width * self.height * 4} values "
                             f"(4 for each of {self.width} x {self.height} pixels), not {len(rgba)}")
        self._flush_pixel_patch()
        from . import imaging

        bgra = imaging.rgba_to_bgra(rgba, self.width, self.height)
        self._append(self._renderer.pixels_op(bgra, 0, 0, self.width, self.height))

    def filter(self, kind: str, value: float | None = None) -> None:
        """Change every pixel drawn so far with a filter, in place (contract P10)."""
        from . import imaging

        self._require_window()
        value = imaging.check_filter(kind, value)
        self._sync_canvas()
        w, h = self.width, self.height
        bgra = self._renderer.read_logical(0, 0, w, h, w, h)
        out = imaging.filter_bgra(bgra, w, h, kind, value)
        self._append(self._renderer.pixels_op(out, 0, 0, w, h))

    # ------------------------------------------------------------ export
    def save(self, path: str, *, text: str = "live") -> None:
        """Write this frame to a .png, .pdf or .svg file when the frame is complete.

        *text* is "live" or "shapes" (contract T20): how a PDF or SVG holds its letters."""
        from .export import check_text_mode, format_of
        check_text_mode(text)
        from .export.motion import MOTION_FORMATS

        if isinstance(path, str) and "." in path and path.lower().rsplit(".", 1)[-1] in MOTION_FORMATS:
            self._save_motion(path)          # S-100, contract M1
            return
        format_of(path)  # validate early so the learner sees the error at the call site
        self._require_window()
        if self._script:                     # contract R14: a script's save writes at once
            self._save_script(path, text)
            return
        self._pending_saves.append((path, text))

    def _save_script(self, path: str, text: str = "live") -> None:
        from .export import format_of, save_frame, save_pixels

        self._flush_pixel_patch()
        fmt = format_of(path)
        if self._pages:                                  # contract R17: several pages
            self._save_pages(path, fmt, text)
            return
        if fmt == "png":
            self._script_flush()
            save_pixels(self._view_pixels(), path)
        else:
            save_frame(self._with_layers(self.frame, files=True), path, self.width, self.height, self._script_scale,
                       text)

    def _save_pages(self, path: str, fmt: str, text: str = "live") -> None:
        import os

        from .export import save_document, save_frame, save_pixels
        from .platform.base import Pixels

        pages = self._document_pages()
        if fmt == "pdf":
            save_document([(w, h, ir.Frame(list(ops))) for w, h, ops, _ in pages], path, text)
            return
        self._script_flush()
        stem, ext = os.path.splitext(path)
        scale = self._script_scale
        for number, (w, h, ops, pixels) in enumerate(pages, 1):
            numbered = f"{stem}_{number}{ext}"
            if fmt == "png":
                shown = self._view_pixels() if pixels is None else Pixels(
                    pixels, round(w * scale), round(h * scale), "BGRA")
                save_pixels(shown, numbered)
            else:
                save_frame(ir.Frame(list(ops)), numbered, w, h, scale, text)

    # ---- GIF and MP4 (S-100, contract M1)
    def frame_duration(self, seconds: float) -> None:
        """Script style: how long this page, and the pages after it, are shown in a GIF or MP4."""
        if self.running:
            raise RuntimeError(
                "f.frame_duration() is for scripts (a file with no draw()). In an animated sketch every frame "
                "lasts 1 / frame rate: use f.save_gif(path, seconds) or f.save_movie(path, seconds)."
            )
        self._require_window()
        if isinstance(seconds, bool) or not isinstance(seconds, (int, float)):
            raise TypeError(f"f.frame_duration() needs a number of seconds, not {seconds!r}")
        if not 0 < seconds < float("inf"):
            raise ValueError(f"f.frame_duration() needs a time above 0 seconds, not {seconds!r}")
        self._frame_duration = float(seconds)

    def _save_motion(self, path: str) -> None:
        """f.save("x.gif") / f.save("x.mp4") in a script: every page is a frame."""
        from .export import motion

        kind = path.lower().rsplit(".", 1)[-1]
        if not self._script:
            self._require_window()
            use = "f.save_gif(path, seconds)" if kind == "gif" else "f.save_movie(path, seconds)"
            raise ValueError(
                f"f.save({path!r}) makes a {kind.upper()} from the pages of a script. This is an animated "
                f"sketch: use {use} to record it."
            )
        pages = self._document_pages()
        first = pages[0][:2]
        for number, (w, h, _, _) in enumerate(pages, 1):
            if (w, h) != first:
                raise ValueError(
                    f"f.save({path!r}): every page of a {kind.upper()} must be the same size. "
                    f"Page 1 is {first[0]} x {first[1]} but page {number} is {w} x {h}."
                )
        motion.require_encoder(kind)
        self._script_flush()
        frames = []
        scale = self._script_scale
        for w, h, _, pixels in pages:
            if pixels is None:
                bgra = self._view().read_logical(0, 0, w, h, w, h)
            else:
                bgra = motion.resample_bgra(pixels, round(w * scale), round(h * scale), w, h)
            frames.append(motion.bgra_to_rgb(bgra, w, h))
        durations = [*self._page_durations, self._frame_duration]
        (motion.write_gif if kind == "gif" else motion.write_mp4)(path, frames, first, durations)

    def save_gif(self, path: str, seconds: float) -> None:
        """Record the next *seconds* of an animated sketch into a GIF."""
        self._start_motion("save_gif", path, "gif", seconds)

    def save_movie(self, path: str, seconds: float) -> None:
        """Record the next *seconds* of an animated sketch into an MP4."""
        self._start_motion("save_movie", path, "mp4", seconds)

    def _start_motion(self, name: str, path: str, kind: str, seconds: float) -> None:
        from .export import motion

        self._only_in_animated(name)
        if not isinstance(path, str) or not path.lower().endswith("." + kind):
            raise ValueError(f"f.{name}() needs a path ending in .{kind}, not {path!r}")
        if isinstance(seconds, bool) or not isinstance(seconds, (int, float)):
            raise TypeError(f"f.{name}() needs a number of seconds, not {seconds!r}")
        if not 0 < seconds < float("inf"):
            raise ValueError(f"f.{name}() needs a time above 0 seconds, not {seconds!r}")
        self._require_window()
        if self._motion is not None:
            raise RuntimeError(f"f.{name}() was called while another recording is still running. "
                               "Wait until it has finished.")
        motion.require_encoder(kind)
        frames = max(1, round(seconds * self.fps))
        # Called from draw(), this frame is already being drawn: the recording starts with the next one.
        self._motion = [path, kind, frames, [], None, bool(self._in_draw)]

    def _record_motion_frame(self) -> None:
        recording = self._motion
        if recording is None:
            return
        if recording[5]:                       # the frame that called save_gif() is not recorded
            recording[5] = False
            return
        from .export import motion

        path, kind, left, frames, size, _ = recording
        w, h = self.width, self.height
        if size is not None and size != (w, h):
            self._motion = None
            raise ValueError(f"the canvas changed size from {size[0]} x {size[1]} to {w} x {h} while "
                             f"{path!r} was being recorded; a GIF or MP4 keeps one size")
        recording[4] = (w, h)
        frames.append(motion.bgra_to_rgb(self._view().read_logical(0, 0, w, h, w, h), w, h))
        recording[2] = left - 1
        if recording[2] > 0:
            return
        self._motion = None
        durations = [1.0 / self.fps] * len(frames)
        (motion.write_gif if kind == "gif" else motion.write_mp4)(path, frames, (w, h), durations)

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
        self._pending_saves.append((path, "live"))
        seq[1] += 1
        if seq[1] > last:
            self._frame_sequence = None

    def _flush_saves(self) -> None:
        if not self._pending_saves:
            return
        from .export import format_of, save_frame, save_pixels

        paths, self._pending_saves = self._pending_saves, []
        for path, text in paths:
            if format_of(path) == "png":
                save_pixels(self._view_pixels(), path)      # what is on screen
            else:
                save_frame(self._with_layers(self.frame, files=True), path, self.width, self.height,
                           self._platform.backing_scale, text)

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

    def tint(self, color: ColorLike, *more: float) -> None:
        """Colour every picture drawn with image() from now on (contract P5). Any colour form but a gradient."""
        if isinstance(color, Gradient):
            raise ValueError("f.tint() takes a colour, not a gradient")
        self._states.update(tint=self.read_color(color, *more))

    def no_tint(self) -> None:
        self._states.update(tint=None)

    def stroke(self, color: ColorLike, *more: float) -> None:
        self._states.update(stroke=self._paint(color, *more))

    def no_stroke(self) -> None:
        self._states.update(stroke=None)

    def stroke_width(self, pixels: float) -> None:
        if pixels < 1:
            raise ValueError("stroke width must be at least 1")
        # S6: whole numbers stay ints (so IR snapshots are unchanged); other floats are kept, not truncated.
        self._states.update(stroke_width=int(pixels) if pixels == int(pixels) else float(pixels))

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
            self._append(ir.SetAntialias(False))

    def smooth(self) -> None:
        """Smooth (anti-aliased) edges again - the default."""
        self._smooth = True
        if self._has_window:
            self._append(ir.SetAntialias(True))

    def text_size(self, size: int) -> None:
        if size <= 0:
            raise ValueError("text size must be positive")
        self._states.update(text_size=int(size))

    # ---- fonts and styles (S-054, contract T11/T12)
    TEXT_STYLES = TEXT_STYLES          # one list, in typography (contract T12)

    def load_font(self, path: str, base_dir: str | None = None, face: int | str = 0):
        """Load a TrueType/OpenType font file (or one face of a .ttc collection); pass the result to f.text_font()."""
        from .typography import load_font as _load_font

        return _load_font(path, base_dir, face)

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

    def text_fallback(self, *fonts) -> None:
        """Fonts to draw letters the current font lacks (contract T18). No arguments: only the bundled
        fallbacks. None: no fallback at all."""
        from .typography import Font

        if fonts == (None,):
            self._states.update(text_fallback=None)
            return
        keys = []
        for font in fonts:
            if isinstance(font, Font):
                key = font.name
            elif isinstance(font, str):
                key = self.load_font(font).name
            else:
                raise TypeError(
                    f"f.text_fallback() needs fonts from f.load_font() or f.system_font(), not {type(font).__name__}"
                )
            if key not in keys:
                keys.append(key)
        self._states.update(text_fallback=tuple(keys))

    def system_font(self, name: str):
        """A font installed on this computer, found by its family name (contract T18)."""
        from .typography import system_font as _system_font

        return _system_font(name)

    def text_style(self, style: str) -> None:
        """Use one of the four built-in styles for later text (ignored once a font is loaded)."""
        if style not in self.TEXT_STYLES:
            raise ValueError(f"f.text_style() takes one of {', '.join(map(repr, self.TEXT_STYLES))}, not {style!r}")
        self._states.update(text_style=style)

    # ---- tracking, OpenType features, font variations (S-090, contract T13)
    @staticmethod
    def _tag(tag: str, who: str) -> str:
        """A four-character OpenType tag; a shorter one is padded with spaces, as OpenType allows."""
        if not isinstance(tag, str) or not 1 <= len(tag) <= 4 or not tag.isascii():
            raise ValueError(f"f.{who}() names things by tags of 1 to 4 plain letters, like 'liga' or 'wght', not {tag!r}")
        return tag.ljust(4)

    def text_tracking(self, pixels: float) -> None:
        """Add *pixels* of space after every letter (negative tightens)."""
        if isinstance(pixels, bool) or not isinstance(pixels, (int, float)):
            raise TypeError(f"f.text_tracking() takes a number of pixels, not {type(pixels).__name__}")
        self._states.update(text_tracking=float(pixels))

    def text_features(self, **features: bool) -> None:
        """Turn OpenType features on or off by tag; no arguments goes back to the font's defaults."""
        if not features:
            self._states.update(text_features=())
            return
        merged = dict(self.style.text_features)
        for tag, value in features.items():
            if not isinstance(value, bool):
                raise TypeError(f"f.text_features() takes True or False for each feature, not {value!r} for {tag!r}")
            merged[self._tag(tag, "text_features")] = value
        self._states.update(text_features=tuple(sorted(merged.items())))

    def font_variations(self, **axes: float) -> None:
        """Set a variable font's axes by tag, like wght=700; no arguments goes back to the font's defaults."""
        if not axes:
            self._states.update(font_variations=())
            return
        merged = dict(self.style.font_variations)
        for tag, value in axes.items():
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise TypeError(f"f.font_variations() takes a number for each axis, not {value!r} for {tag!r}")
            merged[self._tag(tag, "font_variations")] = float(value)
        self._states.update(font_variations=tuple(sorted(merged.items())))

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
        for line, left, line_top in self._line_layout(lines, x, y, style, top):
            self._emit(ir.Text(line, left, line_top, color, style))

    def _line_layout(self, lines: list[str], x: float, y: float, style, top: float | None = None):
        """Yield (line, left, top) for each non-empty line: the one layout `text`, `text_box` and
        `text_path` all share, so they cannot drift apart (contract T7/T9, F13)."""
        from .typography import effective_font, text_metrics, text_settings, text_width

        font = effective_font(style)
        settings = text_settings(style)
        ascent, descent = text_metrics(style.text_size, font)
        leading = self._leading(style)
        if top is None:
            block = ascent + descent + leading * (len(lines) - 1)
            shift = {"top": 0, "baseline": ascent, "bottom": block, "center": block / 2}[style.text_valign]
            top = y - shift if shift else y      # untouched numbers keep old snapshots byte-identical
        for i, line in enumerate(lines):
            left = x
            if style.text_align != "left":
                w = text_width(line, style.text_size, font, **settings)
                left -= w / 2 if style.text_align == "center" else w
            if line:
                yield line, left, top + i * leading if i else top

    def _text_color(self, color: ColorLike | None, style) -> Color:
        if color is not None:
            return self._paint(color)
        return style.fill or style.stroke or WHITE  # contract T4

    def text_box(self, message: object, x: float, y: float, width: float, height: float | None = None,
                 color: ColorLike | None = None) -> str | FormattedString:
        """Wrap *message* inside the box; return the text that did not fit (contract T10, T14)."""
        from .typography import effective_font, text_metrics, text_settings, wrap_lines

        if not width > 0 or (height is not None and not height >= 0):
            raise ValueError("f.text_box() needs a width above 0 and a height of 0 or more (or no height)")
        if isinstance(message, FormattedString):
            return self._fs_text_box(message, x, y, width, height, color)
        style = self.style
        font = effective_font(style)
        lines, rests = wrap_lines(str(message), width, style.text_size, font, **text_settings(style))
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

    # ---- mixed styles in one text (S-091, contract T14)
    def _fs_resolve(self, fs: FormattedString, style, color: ColorLike | None) -> dict:
        """For each run of *fs* (and None, for text with no run): the state to draw it with and its colour.
        A setting the run gave is its own; the rest follows *style*, the drawing state of now."""
        base = self._text_color(color, style)
        out = {None: (style, base)}
        for i, run in enumerate(fs.runs):
            out[i] = (run.apply(style), run.color if run.color is not None else base)
        return out

    def _fs_pieces(self, line, resolved: dict) -> list:
        """Measure the (text, run index) pieces of one line: size, ascent, descent and width of each."""
        from .typography import effective_font, text_metrics, text_settings, text_width

        out = []
        for text, ri in line:
            st = resolved[ri][0]
            font = effective_font(st)
            ascent, descent = text_metrics(st.text_size, font)
            out.append(_Piece(text, ri, st.text_size, ascent, descent,
                              text_width(text, st.text_size, font, **text_settings(st))))
        return out

    def _fs_metrics(self, measured: list, style):
        """For each measured line: its ascent and descent (the tallest piece's), and the distance of its
        baseline from the first line's. The step to a line is its leading: 1.25 x its largest size,
        unless text_leading is set."""
        ascents = [max((p.ascent for p in line), default=0.0) for line in measured]
        descents = [max((p.descent for p in line), default=0.0) for line in measured]
        leadings = [style.text_leading if style.text_leading is not None
                    else max((p.size for p in line), default=style.text_size) * 1.25 for line in measured]
        if len(set(leadings)) <= 1:
            offsets = [i * leadings[0] for i in range(len(leadings))] if leadings else []
        else:
            offsets, total = [0.0], 0.0
            for lead in leadings[1:]:
                total += lead
                offsets.append(total)
        return ascents, descents, offsets

    def _fs_layout(self, lines: list, x: float, y: float, style, resolved: dict, top: float | None = None):
        """Yield (text, left, top, run index) for each non-empty piece: the layout of a FormattedString,
        shared by text, text_box and text_path as `_line_layout` is for plain text (T7, T9, T14).
        The pieces of a line share one baseline, which comes from the tallest ascent on the line."""
        measured = [self._fs_pieces(line, resolved) for line in lines]
        ascents, descents, offsets = self._fs_metrics(measured, style)
        if top is None:
            block = ascents[0] + descents[-1] + offsets[-1]
            shift = {"top": 0, "baseline": ascents[0], "bottom": block, "center": block / 2}[style.text_valign]
            top = y - shift if shift else y
        for i, line in enumerate(measured):
            line_top = top + offsets[i] if i else top
            width = sum(p.width for p in line)
            pen = x
            if style.text_align != "left":
                pen -= width / 2 if style.text_align == "center" else width
            for p in line:
                if p.text:
                    delta = ascents[0] - p.ascent
                    yield p.text, pen, line_top + delta if delta else line_top, p.ri
                pen += p.width

    def _fs_text_box(self, fs: FormattedString, x: float, y: float, width: float, height: float | None,
                     color: ColorLike | None) -> FormattedString:
        style = self.style
        resolved = self._fs_resolve(fs, style, color)

        def fits(pieces) -> bool:
            return sum(p.width for p in self._fs_pieces(pieces, resolved)) <= width

        lines, starts = fs.wrap(fits)
        measured = [self._fs_pieces(line, resolved) for line in lines]
        ascents, descents, offsets = self._fs_metrics(measured, style)
        fitting = len(lines)
        if height is not None:
            fitting = 0
            while fitting < len(lines) and offsets[fitting] + ascents[0] + descents[fitting] <= height + 1e-9:
                fitting += 1
        if fitting:
            block = ascents[0] + descents[fitting - 1] + offsets[fitting - 1]
            room = (height if height is not None else block) - block
            drop = {"top": 0, "baseline": 0, "center": room / 2, "bottom": room}[style.text_valign]
            top = y + drop if drop else y
            anchor = x + {"left": 0, "center": width / 2, "right": width}[style.text_align]
            for piece_text, left, piece_top, ri in self._fs_layout(lines[:fitting], anchor, y, style, resolved, top=top):
                self._emit(ir.Text(piece_text, left, piece_top, resolved[ri][1], resolved[ri][0]))
        return fs._from(starts[fitting]) if fitting < len(lines) else FormattedString()

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

    def _emit_rect(self, name: str, x: float, y: float, w: float, h: float, radii: tuple) -> None:
        r = rect_radii(radii, w, h, name)           # checks the count and signs even for an empty box
        if any(r):
            if w < 0:
                x, w = x + w, -w                    # a negative size: the box spans the same area
            if h < 0:
                y, h = y + h, -h
            r = rect_radii(r, w, h, name)
            if any(r):
                self._emit(ir.Rect(x, y, w, h, self.style, r))
                return
        self._emit(ir.Rect(x, y, w, h, self.style))

    def rect(self, x: float, y: float, width: float, height: float, *radii: float) -> None:
        """A rectangle. Optional corner radii: one for all corners, or four (top-left, top-right, bottom-right, bottom-left)."""
        x, y, width, height = self._rect_box(x, y, width, height)
        self._emit_rect("rect", x, y, width, height, radii)

    def line(self, x1: float, y1: float, x2: float, y2: float) -> None:
        self._emit(ir.Line(x1, y1, x2, y2, self.style))

    def point(self, x: float, y: float) -> None:
        self._emit(ir.Point(x, y, self.style))

    # ---- more shapes (S-041, contract F5-F7)
    def square(self, x: float, y: float, size: float, *radii: float) -> None:
        """A square placed like rect(): by its top-left corner unless rect_mode() says otherwise.

        Optional corner radii work as for rect()."""
        x, y, w, h = self._rect_box(x, y, size, size, one_size=True)
        self._emit_rect("square", x, y, w, h, radii)

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
        if isinstance(message, FormattedString):
            resolved = self._fs_resolve(message, style, color)
            for piece_text, left, top, ri in self._fs_layout(message.lines(), x, y, style, resolved):
                self._emit(ir.Text(piece_text, left, top, resolved[ri][1], resolved[ri][0]))
            return
        self._emit_lines(str(message).split("\n"), x, y, self._text_color(color, style), style)

    def text_path(self, message: object, x: float, y: float) -> PathBuilder:
        """The glyph outlines `text(message, x, y)` would draw now, as a new path (contract F13)."""
        from .typography import effective_font, text_settings

        style = self.style
        if isinstance(message, FormattedString):
            resolved = self._fs_resolve(message, style, None)
            geometry = Path()
            for piece_text, left, top, ri in self._fs_layout(message.lines(), x, y, style, resolved):
                st = resolved[ri][0]
                shaped = effective_font(st).shape(piece_text, st.text_size, **text_settings(st))
                for op in shaped.outline_ops(left, top, WHITE):
                    geometry = Path(geometry.segments + op.path.segments)
            return PathBuilder(geometry)
        font = effective_font(style)
        settings = text_settings(style)
        geometry = Path()
        for line, left, top in self._line_layout(str(message).split("\n"), x, y, style):
            for op in font.shape(line, style.text_size, **settings).outline_ops(left, top, WHITE):
                geometry = Path(geometry.segments + op.path.segments)
        return PathBuilder(geometry)

    def text_to_points(self, message: object, x: float, y: float, spacing: float = 5) -> list[tuple[float, float]]:
        """Points along the outlines of `text_path(message, x, y)`, one every *spacing* pixels (contract T16)."""
        from .geometry import sample_path

        if isinstance(spacing, bool) or not isinstance(spacing, (int, float)):
            raise TypeError(f"f.text_to_points() takes spacing as a number of pixels, not {type(spacing).__name__}")
        if not spacing > 0:
            raise ValueError(f"f.text_to_points() needs a spacing above 0 pixels, not {spacing!r}")
        return [(float(px), float(py)) for px, py in sample_path(self.text_path(message, x, y).geometry, float(spacing))]

    def current_font(self):
        """The font text is set in now, as a font object, the built-in font too (contract T17)."""
        from .typography import STYLE_FILES, Font

        style = self.style
        return Font(STYLE_FILES[style.text_style] if style.font is None else style.font)

    def text_width(self, message: object) -> float:
        """Advance width of *message* in logical pixels at the current text_size (contract T6)."""
        from .typography import effective_font, text_settings, text_width

        if isinstance(message, FormattedString):
            resolved = self._fs_resolve(message, self.style, None)
            return max((sum(p.width for p in self._fs_pieces(line, resolved)) for line in message.lines()),
                       default=0.0)
        font = effective_font(self.style)
        settings = text_settings(self.style)
        return max(text_width(line, self.style.text_size, font, **settings) for line in str(message).split("\n"))

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
        return ir.FillPath(geometry, style.fill, style.blend_mode, style.opacity, style.shadow,
                           None if style.erasing is None else style.erasing[0])

    @staticmethod
    def _stroke_op(geometry: Path, style: GraphicsState) -> ir.StrokePath:
        return ir.StrokePath(geometry, style.stroke, float(style.stroke_width),
                             style.stroke_cap, style.stroke_join, style.miter_limit,
                             style.dash, style.dash_offset,
                             style.blend_mode, style.opacity, style.shadow,
                             None if style.erasing is None else style.erasing[1])

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

    # ---- erasing (S-107, contract F15)
    def erase(self, fill_strength: float = 255, stroke_strength: float = 255) -> None:
        for name, v in (("fill_strength", fill_strength), ("stroke_strength", stroke_strength)):
            if isinstance(v, bool) or not isinstance(v, (int, float)) or not 0 <= v <= 255:
                raise ValueError(f"f.erase() takes {name} from 0 (nothing erased) to 255 (fully erased), not {v!r}")
        self._states.update(erasing=(int(fill_strength), int(stroke_strength)))

    def no_erase(self) -> None:
        self._states.update(erasing=None)

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
        was_script = self._script                 # only f.size() so far: its pictures belong to this run
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
        self._reset_pixel_state()
        self._drop_layers()
        self._states.unwind()
        self._shape = None
        if not was_script:
            self._graphics_counter = self._graphics_before_run
        self._graphics_before_run = 0

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
                self._refresh_panel()                  # a click on a control shows even when draw() does not run

                # draw() runs every frame while looping, once after redraw(), and always on
                # the first frame - even after no_loop() in setup(), as in p5.
                if self._looping or self._redraw_pending or self.frame_count == 0:
                    self._redraw_pending = False
                    if not self._smooth:
                        self.frame.append(ir.SetAntialias(False))   # the renderer resets per frame
                    self._in_draw = True
                    try:
                        draw()
                    finally:
                        self._in_draw = False
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
            self._reset_pixel_state()
            self._drop_layers()
            self._pending_saves.clear()
            self._frame_sequence = None
            self._motion = None                      # a recording the sketch did not live to finish is dropped
            self._renderer.attach(0, 0)
            self._platform.close()
            self._end_panel()
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
