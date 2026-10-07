"""Learner-facing functions: thin wrappers over the active Sketch.

Signatures here are the public contract (tests/test_api_contract.py); keep
them stable and keep this module free of any backend import.
"""
from __future__ import annotations

import atexit
import inspect
import sys
from contextlib import AbstractContextManager

from . import exploring as _exploring  # S-132 Play: variations and keep (the Play section at the end)
from .color import ColorLike as Color
from .controls import Button, Checkbox, Slider  # noqa: F401  (public through f.create_slider and friends, S-101)
from .marks import NOT_GIVEN, Mark, mark_from_path, mark_from_svg, refuse_in_mark  # S-132: marks (the Marks section at the end)
from .paths import PathBuilder
from .typography import Font
from .picture import Picture, draw_image  # noqa: F401  (Picture: public via f.create_graphics, S-052)
from .sketch import DEFAULT_SHADOW_COLOR, Sketch
from .surface import Area, Grid  # noqa: F401  (S-132 part 4: returned by f.area and f.grid, contract G1)
from .formatted import FormattedString  # noqa: F401  (public: f.FormattedString, S-091)
from .vector import Vector  # noqa: F401  (public: f.Vector, S-055)

_active: Sketch | None = None

LIVE_NAMES = frozenset(
    {"width", "height", "mouse_x", "mouse_y", "is_mouse_pressed", "pmouse_x", "pmouse_y", "mouse_button",
     "key", "key_code", "is_key_pressed", "frame_count", "delta_time", "pixels", "ground"}
)

# What each live value is, in the same format as the function docstrings (S-125).
# A test checks that this covers LIVE_NAMES exactly. docs/reference/API.md is built from it.
LIVE_DOCS: dict[str, str] = {
    "width": """The width of the canvas, in pixels.

    It is a whole number, exactly what you gave to size(). It is 640 until you call size(). It changes with resize_canvas() and full_screen(). On a high-resolution screen it is still the number you asked for.

    Example:
        f.circle(f.width / 2, f.height / 2, 80)
    """,
    "height": """The height of the canvas, in pixels.

    It is a whole number, exactly what you gave to size(). It is 480 until you call size(). It changes with resize_canvas() and full_screen().

    Example:
        f.line(0, f.height, f.width, 0)
    """,
    "mouse_x": """The mouse's x position over the canvas, in pixels from the left edge.

    It is a number. It is updated before every call to draw(). It is 0 with no window.

    Example:
        f.circle(f.mouse_x, f.mouse_y, 30)
    """,
    "mouse_y": """The mouse's y position over the canvas, in pixels from the top edge.

    It is a number. It is updated before every call to draw(). It is 0 with no window. The panel of controls below the canvas is not counted.

    Example:
        f.circle(f.mouse_x, f.mouse_y, 30)
    """,
    "pmouse_x": """Where the mouse's x was in the previous frame, in pixels.

    It is a number. It is updated before every call to draw(), together with mouse_x. Use it with mouse_x to draw a line that follows the mouse.

    Example:
        f.line(f.pmouse_x, f.pmouse_y, f.mouse_x, f.mouse_y)
    """,
    "pmouse_y": """Where the mouse's y was in the previous frame, in pixels.

    It is a number. It is updated before every call to draw(), together with mouse_y.

    Example:
        f.line(f.pmouse_x, f.pmouse_y, f.mouse_x, f.mouse_y)
    """,
    "is_mouse_pressed": """Whether a mouse button is held down now.

    It is True or False. It is True while any of the first three mouse buttons is held. It is updated before every call to draw(). To act once when a click starts, define a mouse_pressed() function instead.

    Example:
        if f.is_mouse_pressed:
            f.fill("tomato")
    """,
    "mouse_button": """The last mouse button that was pressed or released.

    It is the word "left", "center" or "right", or None before any button has been used. It changes when a button goes down or up, and it stays after the button is let go.

    Example:
        if f.mouse_button == "right":
            f.background("white")
    """,
    "key": """The last key that was pressed or released.

    It is a one-character string such as "a" or " ", or a name such as "left", "right", "up", "down", "enter" or "escape". It is None before any key has been used. It changes when a key goes down or up, and it stays after the key is let go. To ask whether a key is held right now, use key_down().

    Example:
        if f.key == "r":
            f.background("white")
    """,
    "key_code": """The code of the last key that was pressed or released.

    It is a whole number, or None before any key has been used. It changes at the same time as key. Most programs use key instead, which is easier to read.

    Example:
        print(f.key_code)
    """,
    "is_key_pressed": """Whether any key is held down now.

    It is True or False. It is updated before every call to draw(). It is always False with no window.

    Example:
        if f.is_key_pressed:
            f.fill("gold")
    """,
    "frame_count": """How many frames have been completed since the sketch started.

    It is a whole number. It is 0 during the first draw(), 1 during the second, and so on. It goes up by one after each draw().

    Example:
        f.rotate(f.frame_count * 3)
    """,
    "delta_time": """The seconds that the previous frame took.

    It is a number, such as 0.016 at 60 frames a second. It is 0.0 in the first frame. It is updated once a frame. Use it to move at the same speed on any computer.

    Example:
        x += 120 * f.delta_time
    """,
    "ground": """The canvas as an area, with its margins.

    It is a read-only value, always up to date, like width. It is an Area, so it has left, top, right, bottom, width, height, cx and cy (the centre), and inset() and grid(). It also has margin, a tuple (top, right, bottom, left) from size(). It starts at (0, 0), so left and top are 0, and right and bottom are the canvas width and height. Its content is the area inside the margins: a value of the same kind, whose own margin is (0, 0, 0, 0) and whose own content is itself. With no margin, ground.content is ground. It follows size(), resize_canvas() and new_page(). The margin stays when the canvas changes size. Margins are a guide: drawing outside them is allowed. Inside a ``with f.layer(...)`` block it is still the canvas.

    Example:
        f.size(400, 300, margin=20)
        f.rect(f.ground.content.left, f.ground.content.top, f.ground.content.width, f.ground.content.height)
    """,
    "pixels": """The canvas pixels, after load_pixels().

    It is a bytearray with red, green, blue and alpha (0 to 255, not premultiplied) for every pixel, row by row from the top left. The pixel at (x, y) starts at index (y * f.width + x) * 4. It is None until you call load_pixels(). Change the numbers in place, then call update_pixels(). Inside a ``with f.layer(...)`` block it holds the layer's pixels.

    Example:
        f.load_pixels()
        f.pixels[0] = 255
        f.update_pixels()
    """,
}


def canvas_sketch() -> Sketch:
    """Return the sketch that owns the window or script canvas.

    It is the same sketch even inside a ``with f.layer(...)`` block. It is made the first time it is needed. Most learners never call this.

    Returns:
        The Sketch object that the public functions talk to.

    """
    global _active
    if _active is None:
        _active = Sketch()
    return _active


def active_sketch() -> Sketch:
    """Return the sketch that the drawing functions talk to.

    Normally this is the canvas's sketch. Inside ``with f.layer(...)`` it is the open layer's own sketch. Everything that is not drawing (width, mouse_x, random, save, size and so on) uses the canvas sketch, so it keeps its canvas meaning inside the block. Most learners never call this.

    Returns:
        The Sketch object that drawing calls go to.

    """
    canvas = canvas_sketch()
    layer = canvas._layer_open
    return canvas if layer is None else layer._sketch


def use_sketch(sketch: Sketch | None) -> Sketch:
    """Make a given sketch the one that the public functions talk to.

    This is for tests and for programs that keep more than one sketch. Most learners never call this.

    Arguments:
        sketch: the Sketch to use, or None to start again with a fresh one.

    Returns:
        The Sketch now in use.

    """
    global _active
    _active = sketch
    return canvas_sketch()


def live_value(name: str) -> object:
    """Return the current value of a live name such as "width" or "mouse_x".

    This is what ``f.width``, ``f.mouse_x`` and the other live values call behind the scenes. Inside a ``with f.layer(...)`` block, "pixels" is the layer's pixels. Most learners never call this.

    Arguments:
        name: one of "width", "height", "mouse_x", "mouse_y", "pmouse_x", "pmouse_y", "is_mouse_pressed", "mouse_button", "key", "key_code", "is_key_pressed", "frame_count", "delta_time", "pixels" or "ground".

    Returns:
        The value that name has now.

    Raises:
        AttributeError: the name is not a live value.

    Example:
        print(f.live_value("width"))
    """
    if name not in LIVE_NAMES:
        raise AttributeError(name)
    sketch = canvas_sketch()
    if name == "pixels" and sketch._layer_open is not None:
        return sketch._layer_open._sketch.pixels         # f.load_pixels() inside a layer block loaded the layer
    return getattr(sketch, name)


HINT = "Your sketch has a draw() function but never started. Add f.run() as the last line."


def exit_hint() -> None:
    """Remind a learner who wrote draw() but forgot f.run().

    It runs by itself when the program ends. It only prints a hint for a program run from a terminal that ended without an error. It stays quiet in an interactive session, when f.run() was called, and for a script. Most learners never call this.
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
def size(width: int | str, height: int | None = None, *, title: str = "funground", fps: int = 60,
         margin: float | tuple = 0, landscape: bool = False) -> None:
    """Create the canvas, or change its size.

    Call it once, at the start of setup(). In an animated sketch it opens the window. In a script (a file with no draw()) it makes a canvas with no window; use show() to look at it. If setup() never calls size(), run() opens a 640 by 480 window for you. Instead of numbers you can give a page name, such as size("A4") (see page_size). The margin is a guide for your drawing: read it back with f.ground.content, or use grid(). It does not clip anything.

    Arguments:
        width: the canvas width in pixels (above 0), or a page name such as "A4".
        height: the canvas height in pixels (above 0). Leave it out when width is a page name.
        title: the text in the window's title bar. The default is "funground".
        fps: the target frames per second. The default is 60. It must be above 0.
        margin: the space kept free around the edge. One number is used on all four sides. A tuple of four numbers is (top, right, bottom, left). The default is 0. It stays when the canvas changes size or a new page starts.
        landscape: True turns a named page on its side, as in size("A4", landscape=True). The default is False. It only goes with a page name.

    Raises:
        ValueError: the width, height or fps is 0 or less, a page name has a height, the name is unknown, a margin is negative, or the margins leave no room.

    Example:
        f.size("A4", margin=f.mm(15))

    See also: ground, grid, run, resize_canvas, full_screen, page_size
    """
    refuse_in_mark("f.size()")
    canvas_sketch().size(width, height, title=title, fps=fps, margin=margin, landscape=landscape)


def run(*, fps: int | None = None, max_frames: int | None = None) -> None:
    """Start the sketch: call setup() once, then draw() again and again.

    Put it as the last line of your file. It finds the functions called setup() and draw() in your file, so you do not pass them in. setup() is optional. draw() is required. The window closes with its close button, the Escape key or stop().

    Arguments:
        fps: the frames per second, replacing the one given to size(). The default None keeps it.
        max_frames: stop by itself after this many frames. The default None runs until the window closes. It is mostly for tests and for runs with no window.

    Raises:
        RuntimeError: f.run() cannot find the file that called it, or the file mixes the script style with run().

    Example:
        f.run(max_frames=300)

    See also: size, stop, no_loop
    """
    caller = inspect.currentframe()
    if caller is None or caller.f_back is None:
        raise RuntimeError("Could not find the sketch that called f.run().")
    canvas_sketch().run_namespace(caller.f_back.f_globals, fps=fps, max_frames=max_frames)


def show() -> None:
    """Open a window on what a script has drawn, and wait until it is closed.

    This is for the script style (a file with no draw()). Call size() first. The window also closes with the Escape key. With a document of several pages, the arrow keys turn the pages. With no window (FUNGROUND_HEADLESS=1) it returns at once.

    Example:
        f.size(400, 300)
        f.circle(200, 150, 100)
        f.show()

    See also: size, new_page, save
    """
    refuse_in_mark("f.show()")
    canvas_sketch().show()


def new_page(width: int | str | None = None, height: int | None = None) -> None:
    """End this page and start a blank one.

    This is for scripts (a file with no draw()). Colours, text settings and other styles carry over. The transform starts afresh. After a few pages, save("x.pdf") writes every page. PNG and SVG write x_1.png, x_2.png and so on. In a window, the arrow keys turn the pages.

    Arguments:
        width: a page width in points, or a page name such as "A4" (see page_size). Leave it out to keep the size.
        height: the page height in points. Leave it out when width is a name or None.

    Raises:
        RuntimeError: an animated sketch has one canvas, so it cannot start a new page.
        ValueError: a page name was given together with a height, or the name is unknown.

    Example:
        f.new_page("A5")

    See also: page_count, page_size, save
    """
    refuse_in_mark("f.new_page()")
    canvas_sketch().new_page(width, height)


def page_count() -> int:
    """Return how many pages the document has so far.

    Returns:
        A whole number, 1 or more.

    Example:
        print(f.page_count())

    See also: new_page
    """
    return canvas_sketch().page_count()


def page_size(name: str, landscape: bool = False) -> tuple[int, int]:
    """Return the size of a named page, in points.

    Add "Landscape" to the name, or give landscape=True, to turn the page on its side.

    Arguments:
        name: "A3", "A4", "A5", "B5", "Letter", "Legal", "Tabloid" or "Square". Capitals do not matter. "A4Landscape" is also allowed.
        landscape: True turns the page on its side. The default False keeps it upright.

    Returns:
        A (width, height) tuple of whole numbers. page_size("A4") is (595, 842).

    Raises:
        ValueError: the name is not one of the page names.

    Example:
        f.size(*f.page_size("A4"))

    See also: new_page, size
    """
    from .pages import page_size as _page_size

    return _page_size(name, landscape)


def area(x: float, y: float, w: float, h: float) -> Area:
    """Make an area: a rectangle kept as a value.

    An area has left, top, right, bottom, width, height, cx and cy (its centre). inset() gives a smaller area inside it, and grid() divides it into cells. f.ground, f.ground.content and every grid cell are areas too. An area may be 0 wide or 0 high, but not less. It draws nothing by itself.

    Arguments:
        x: the left edge.
        y: the top edge.
        w: the width, 0 or more.
        h: the height, 0 or more.

    Returns:
        A new Area.

    Raises:
        TypeError: a value is not a number.
        ValueError: w or h is negative, or a value is not finite.

    Example:
        panel = f.area(40, 40, 320, 200)
        f.rect(panel.left, panel.top, panel.width, panel.height)
        for cell in panel.inset(10).grid(4, 2, gutter=6):
            f.circle(cell.cx, cell.cy, 20)

    See also: grid, ground
    """
    return Area(x, y, w, h)


def grid(cols: int, rows: int, *, gutter: float | tuple = 0, area: object = None) -> Grid:
    """Divide an area into a grid of equal cells.

    The cells cover f.ground.content (the canvas inside the margins), or the area you give. The grid works like a list of its cells, row by row, left to right: a for loop goes through them, len() counts them, g[0] is the top-left cell, g[-1] the last, and g[1:3] gives a list. Each cell is an area (left, top, right, bottom, width, height, cx, cy) with col, row and index, all counted from 0, so a cell can be the area of another grid.

    The grid also has g.cell(col, row), g.span(col, row, cols, rows) for one area over several cells and the gutters between them, g.column_count and g.row_count, g.columns and g.rows as lists of areas, and g.show() to draw guide lines in the window.

    Arguments:
        cols: how many columns. A whole number above 0.
        rows: how many rows. A whole number above 0.
        gutter: the gap between cells. One number is used both across and down. A tuple (column_gutter, row_gutter) sets them apart. The default is 0.
        area: what to divide: an area such as f.ground, a cell or f.area(...), or any object with left, top, width and height. The default None is f.ground.content.

    Returns:
        A Grid of cols times rows cells.

    Raises:
        TypeError: cols or rows is not a whole number, a gutter is not a number, or area has no edges.
        ValueError: cols or rows is 0 or less, a gutter is negative, or the gutters leave no room for the cells.

    Example:
        g = f.grid(3, 2, gutter=10)
        for cell in g:
            f.circle(cell.cx, cell.cy, cell.width * 0.8)
        g.show()

    See also: area, ground, size, mm
    """
    from .surface import make_grid

    if area is None:
        area = canvas_sketch().ground.content
    return make_grid(cols, rows, gutter, area)


def mm(n: float) -> float:
    """Convert millimetres to funground units.

    One unit is one point, as in a PDF: 72 to the inch, so 1 mm is about 2.83 units. It is a plain conversion. It does not change the canvas.

    Arguments:
        n: a length in millimetres.

    Returns:
        The length in funground units, as a float.

    Example:
        f.size("A4", margin=f.mm(15))

    See also: inch, size, grid
    """
    from .surface import mm as _mm

    return _mm(n)


def inch(n: float) -> float:
    """Convert inches to funground units.

    One unit is one point, as in a PDF: 72 to the inch. It is a plain conversion. It does not change the canvas.

    Arguments:
        n: a length in inches.

    Returns:
        The length in funground units, as a float. inch(1) is 72.0.

    Example:
        f.size(f.inch(6), f.inch(4))

    See also: mm, size, grid
    """
    from .surface import inch as _inch

    return _inch(n)


def stop() -> None:
    """Ask the sketch to stop.

    The sketch ends after the current frame. It is the same as exit().

    Example:
        if f.frame_count > 600:
            f.stop()

    See also: exit, run, no_loop
    """
    canvas_sketch().stop()


def exit() -> None:  # noqa: A001 - p5/Processing name; shadows the REPL helper only inside funground
    """End the sketch after this frame.

    It is the same as stop(). It shadows Python's own exit() only inside funground.

    Example:
        f.exit()

    See also: stop
    """
    canvas_sketch().exit()


def no_loop() -> None:
    """Stop calling draw() every frame. The window stays open.

    draw() still runs once at the start, and after redraw(). Use loop() to start again.

    Example:
        f.no_loop()

    See also: loop, redraw, is_looping
    """
    canvas_sketch().no_loop()


def loop() -> None:
    """Call draw() every frame again, after no_loop().

    See also: no_loop, redraw
    """
    canvas_sketch().loop()


def redraw() -> None:
    """Call draw() once more.

    Use it, for example, after a key press when the sketch is not looping.

    Example:
        def key_pressed():
            f.redraw()

    See also: no_loop, loop
    """
    canvas_sketch().redraw()


def is_looping() -> bool:
    """Return whether draw() is called every frame.

    Returns:
        True while the sketch is looping. False after no_loop().

    See also: no_loop, loop
    """
    return canvas_sketch().is_looping()


def millis() -> int:
    """Return the milliseconds since the sketch started running.

    Returns:
        A whole number of thousandths of a second.

    Example:
        seconds = f.millis() / 1000

    See also: frame_rate
    """
    return canvas_sketch().millis()


def frame_rate() -> float:
    """Return the frames per second that the sketch is really achieving.

    The number is smoothed over a few frames. It is 0.0 until the second frame.

    Returns:
        A number of frames a second.

    Example:
        f.text(round(f.frame_rate()), 10, 10)

    See also: size, millis
    """
    return canvas_sketch().frame_rate()


def second() -> int:
    """Return the clock's seconds, from 0 to 59.

    See also: minute, hour
    """
    return Sketch.second()


def minute() -> int:
    """Return the clock's minutes, from 0 to 59.

    See also: second, hour
    """
    return Sketch.minute()


def hour() -> int:
    """Return the clock's hour, from 0 to 23.

    Example:
        print(f.hour(), f.minute(), f.second())

    See also: minute, second
    """
    return Sketch.hour()


def day() -> int:
    """Return the day of the month, from 1 to 31.

    See also: month, year
    """
    return Sketch.day()


def month() -> int:
    """Return the month, from 1 to 12.

    See also: day, year
    """
    return Sketch.month()


def year() -> int:
    """Return the year, for example 2026.

    See also: month, day
    """
    return Sketch.year()


def save(path: str, *, text: str = "live") -> None:
    """Save this frame to a picture or document file.

    The file is written when the frame is complete, and it holds everything that frame drew, including what comes after the call. In a script, it writes at once. A .png holds pixels. A .pdf or .svg holds a true vector drawing. A .gif or .mp4 records an animation (see save_gif and save_movie). Any other extension is an error that names the choices. In a document of several pages, a PDF holds every page.

    A PNG is written at the screen's real resolution, so on a 2x display a 640 by 400 window gives a 1280 by 800 file.

    Arguments:
        path: the file name. Its ending decides the kind: ".png", ".pdf" or ".svg".
        text: for a PDF or SVG only. "live" (the default) keeps text real and editable. "shapes" draws every letter as a shape, so the file looks right without the font. A PNG ignores it.

    Raises:
        ValueError: the file ending is not one that save() knows, or text is not "live" or "shapes".

    Example:
        if f.key_down("s"):
            f.save("my_sketch.png")

    See also: save_frames, save_gif, save_movie, new_page
    """
    refuse_in_mark("f.save()")
    canvas_sketch().save(path, text=text)


def resize_canvas(width: int, height: int) -> None:
    """Change the canvas size while the sketch runs.

    f.width and f.height follow the new size.

    Arguments:
        width, height: the new size in pixels.

    Example:
        f.resize_canvas(800, 600)

    See also: size, full_screen
    """
    canvas_sketch().resize_canvas(width, height)


def full_screen() -> None:
    """Fill the whole screen with the canvas.

    Use it instead of size(), in setup(). f.width and f.height become the screen's size. Escape still ends the sketch. In a script it makes the canvas the screen's size, and show() then shows it full screen.

    Example:
        def setup():
            f.full_screen()

    See also: size, resize_canvas
    """
    canvas_sketch().full_screen()


def cursor(kind: str = "arrow") -> None:
    """Choose the shape of the mouse pointer over the canvas.

    Arguments:
        kind: "arrow" (the default), "cross", "hand", "move", "text" or "wait".

    Raises:
        ValueError: the kind is not one of those names.

    Example:
        f.cursor("hand")

    See also: no_cursor
    """
    canvas_sketch().cursor(kind)


def no_cursor() -> None:
    """Hide the mouse pointer over the canvas.

    Use cursor() to show it again.

    See also: cursor
    """
    canvas_sketch().no_cursor()


def save_frames(pattern: str, count: int) -> None:
    """Save this frame and the next ones as numbered picture files.

    Arguments:
        pattern: the file name with a run of # signs, which becomes the frame number. "frames/####.png" gives frames/0001.png, frames/0002.png and so on.
        count: how many frames to save in all, this one included.

    Example:
        f.save_frames("frames/####.png", 60)

    See also: save, save_gif, save_movie
    """
    refuse_in_mark("f.save_frames()")
    canvas_sketch().save_frames(pattern, count)


def save_gif(path: str, seconds: float) -> None:
    """Record the next few seconds of an animated sketch into a GIF.

    The GIF loops for ever. Each frame lasts 1 divided by the frame rate. It needs Pillow (install funground[extras]) or ffmpeg. It is an error to call it again while recording, or in a script (use frame_duration() and save() for a script).

    Arguments:
        path: the file name. It must end in ".gif".
        seconds: how long to record, starting from the next frame.

    Example:
        f.save_gif("spin.gif", 2)

    See also: save_movie, save_frames, frame_duration
    """
    refuse_in_mark("f.save_gif()")
    canvas_sketch().save_gif(path, seconds)


def save_movie(path: str, seconds: float) -> None:
    """Record the next few seconds of an animated sketch into an MP4 movie.

    It needs ffmpeg on your PATH. A canvas with an odd width or height is padded by one pixel.

    Arguments:
        path: the file name. It must end in ".mp4".
        seconds: how long to record, starting from the next frame.

    Example:
        f.save_movie("spin.mp4", 2)

    See also: save_gif, save_frames, frame_duration
    """
    refuse_in_mark("f.save_movie()")
    canvas_sketch().save_movie(path, seconds)


def frame_duration(seconds: float) -> None:
    """Set how long each page is shown in a saved GIF or MP4.

    This is for scripts. It applies to this page and the pages after it, until you call it again. The start is 0.1 seconds. Then save("x.gif") or save("x.mp4") writes every page as a frame, all of the same size.

    Arguments:
        seconds: how long to show the page. It must be above 0.

    Raises:
        ValueError: seconds is 0 or less.

    Example:
        f.frame_duration(0.2)

    See also: new_page, save, save_gif
    """
    canvas_sketch().frame_duration(seconds)


# ---- drawing
def background(color: Color, *more: float) -> None:
    """Fill the whole canvas with one colour.

    It ignores the fill, the stroke, the transform and any clip. Call it near the start of draw() to clear the last frame. Leave it out when you want trails. Inside a ``with f.layer(...)`` block it clears that layer. Inside a function drawn by variations(), it paints that version's whole picture.

    Arguments:
        color: a colour name such as "white", a hex string such as "#F05A45", an (r, g, b) or (r, g, b, a) tuple, a colour from f.color(), or a gradient. One number is a grey.
        *more: extra numbers, so that background(30, 30, 60) works like background((30, 30, 60)). They follow the colour mode. A name, hex string or gradient takes no extra numbers.

    Raises:
        ValueError: the colour is not understood, or numbers follow a name or gradient.

    Example:
        f.background("white")
        f.background(30, 30, 60)

    See also: clear, fill, color_mode
    """
    if _exploring.in_cell():                      # S-132 Play: in a variations cell it paints the cell's ground
        _exploring.cell_background(color, more)
        return
    refuse_in_mark("f.background()")
    active_sketch().background(color, *more)


def circle(x: float, y: float, diameter: float) -> None:
    """Draw a circle.

    The circle uses the current fill and stroke. By default (x, y) is the centre. ellipse_mode() can change that. The last number is the diameter, not the radius.

    Arguments:
        x, y: the centre, in pixels from the top-left corner.
        diameter: the width across, in pixels.

    Example:
        f.circle(200, 150, 80)

    See also: ellipse, ellipse_mode, fill, stroke
    """
    active_sketch().circle(x, y, diameter)


def ellipse(x: float, y: float, width: float, height: float) -> None:
    """Draw an ellipse.

    It uses the current fill and stroke. By default (x, y) is the centre. ellipse_mode() can change that.

    Arguments:
        x, y: the centre, in pixels from the top-left corner.
        width: the width across, in pixels.
        height: the height, in pixels.

    Example:
        f.ellipse(220, 80, 100, 50)

    See also: circle, ellipse_mode, arc
    """
    active_sketch().ellipse(x, y, width, height)


def rect(x: float, y: float, width: float, height: float, *radii: float) -> None:
    """Draw a rectangle.

    It uses the current fill and stroke. By default (x, y) is the top-left corner. rect_mode() can change that. Corner radii cannot be negative, and big ones are cut to half the shorter side.

    Arguments:
        x, y: the corner, in pixels from the top-left of the canvas.
        width: the width, in pixels.
        height: the height, in pixels.
        *radii: optional corner rounding. Give one number to round all four corners, or four numbers (top-left, top-right, bottom-right, bottom-left).

    Example:
        f.rect(40, 160, 120, 60)
        f.rect(40, 240, 120, 60, 12)

    See also: square, rect_mode, fill, stroke
    """
    active_sketch().rect(x, y, width, height, *radii)


def rect_mode(mode: str) -> None:
    """Choose how rect() and square() read their numbers.

    The choice is saved by push() and brought back by pop().

    Arguments:
        mode: "corner" (the default: x, y is the top-left corner, then the size), "corners" (two opposite corners), "center" (x, y is the middle, then the size) or "radius" (x, y is the middle, then half-sizes).

    Raises:
        ValueError: the mode is not one of those words.

    Example:
        f.rect_mode("center")
        f.rect(200, 150, 80, 40)

    See also: rect, square, ellipse_mode, image_mode
    """
    active_sketch().rect_mode(mode)


def ellipse_mode(mode: str) -> None:
    """Choose how ellipse(), circle() and arc() read their numbers.

    The choice is saved by push() and brought back by pop().

    Arguments:
        mode: "center" (the default: x, y is the middle), "radius" (x, y is the middle, then half-sizes), "corner" (x, y is the top-left of the box around the shape) or "corners" (two opposite corners of that box).

    Raises:
        ValueError: the mode is not one of those words.

    Example:
        f.ellipse_mode("corner")
        f.ellipse(20, 20, 100, 60)

    See also: ellipse, circle, arc, rect_mode
    """
    active_sketch().ellipse_mode(mode)


def image_mode(mode: str) -> None:
    """Choose how image() reads its numbers.

    The choice is saved by push() and brought back by pop().

    Arguments:
        mode: "corner" (the default: x, y is the top-left corner), "center" (x, y is the middle) or "corners" (x, y and the opposite corner; it needs a width and height).

    Raises:
        ValueError: the mode is not one of those words.

    Example:
        f.image_mode("center")

    See also: image, rect_mode
    """
    active_sketch().image_mode(mode)


def line(x1: float, y1: float, x2: float, y2: float) -> None:
    """Draw a straight line between two points.

    A line uses the stroke only. The fill does not matter.

    Arguments:
        x1, y1: where the line starts.
        x2, y2: where the line ends.

    Example:
        f.line(220, 160, 340, 220)

    See also: stroke, stroke_width, point
    """
    active_sketch().line(x1, y1, x2, y2)


def point(x: float, y: float) -> None:
    """Draw a dot.

    The dot has the stroke colour and is about stroke_width pixels across.

    Arguments:
        x, y: the position, in pixels.

    Example:
        f.stroke_width(6)
        f.point(400, 100)

    See also: line, stroke, stroke_width
    """
    active_sketch().point(x, y)


def square(x: float, y: float, size: float, *radii: float) -> None:
    """Draw a square.

    It is placed like rect(): by its top-left corner, unless rect_mode() says otherwise.

    Arguments:
        x, y: the corner, in pixels.
        size: the length of each side, in pixels.
        *radii: optional corner rounding, as for rect(): one number, or four.

    Example:
        f.square(40, 40, 60, 10)

    See also: rect, rect_mode
    """
    active_sketch().square(x, y, size, *radii)


def triangle(x1: float, y1: float, x2: float, y2: float, x3: float, y3: float) -> None:
    """Draw a triangle through three corners.

    It uses the current fill and stroke.

    Arguments:
        x1, y1: the first corner.
        x2, y2: the second corner.
        x3, y3: the third corner.

    Example:
        f.triangle(10, 90, 90, 90, 50, 10)

    See also: quad, polygon
    """
    active_sketch().triangle(x1, y1, x2, y2, x3, y3)


def quad(x1: float, y1: float, x2: float, y2: float, x3: float, y3: float, x4: float, y4: float) -> None:
    """Draw a four-sided shape through four corners.

    The corners are joined in the order you give them. It uses the current fill and stroke.

    Arguments:
        x1, y1: the first corner.
        x2, y2: the second corner.
        x3, y3: the third corner.
        x4, y4: the fourth corner.

    Example:
        f.quad(20, 20, 80, 20, 80, 80, 20, 80)

    See also: triangle, polygon
    """
    active_sketch().quad(x1, y1, x2, y2, x3, y3, x4, y4)


def polygon(points: list[tuple[float, float]]) -> None:
    """Draw a closed shape through a list of points.

    It uses the current fill and stroke. The last point is joined back to the first.

    Arguments:
        points: a list of (x, y) pairs, at least two.

    Raises:
        ValueError: an item is not an (x, y) pair, or there are fewer than two points.

    Example:
        f.polygon([(0, 0), (50, 20), (20, 60)])

    See also: triangle, quad, begin_shape
    """
    active_sketch().polygon(points)


def arc(x: float, y: float, width: float, height: float, start: float, stop: float, mode: str = "open") -> None:
    """Draw part of an ellipse.

    Angles are in degrees and go clockwise, starting from the right (3 o'clock). If stop is less than start, 360 is added to it. An arc is never more than one full turn. ellipse_mode() changes how x, y, width and height are read.

    Arguments:
        x, y: the centre of the whole ellipse.
        width, height: the size of the whole ellipse, in pixels.
        start, stop: the first and last angle, in degrees.
        mode: "open" (the default: the area is filled, but only the curve is outlined), "chord" (closed by a straight line) or "pie" (closed through the centre, like a slice).

    Raises:
        ValueError: the mode is not one of those words.

    Example:
        f.arc(100, 100, 80, 80, 0, 270, "pie")

    See also: ellipse, ellipse_mode
    """
    active_sketch().arc(x, y, width, height, start, stop, mode)


def clear() -> None:
    """Make the whole canvas transparent.

    A PNG saved afterwards keeps the transparency. The window shows it as black.

    See also: background, erase, save
    """
    refuse_in_mark("f.clear()")
    active_sketch().clear()


def text(message: object, x: float, y: float, color: Color | None = None) -> None:
    """Draw text.

    By default (x, y) is the top-left corner of the text; text_align() can change that. The text uses the fill colour. If there is no fill it uses the stroke colour, and if there is neither it is white. A new line in the message starts a new line of text. The default size is 20 (see text_size).

    Arguments:
        message: what to write. Any value works: str() is applied. A FormattedString gives each part its own look.
        x, y: the position, in pixels.
        color: a colour for this text only, in any form that fill() takes. The default None uses the fill.

    Example:
        f.fill("black")
        f.text("Hello", 30, 40)
        f.text(f.frame_count, 30, 80, color="navy")

    See also: text_size, text_align, text_width, text_box, text_font, FormattedString
    """
    active_sketch().text(message, x, y, color)


def text_path(message: object, x: float, y: float) -> PathBuilder:
    """Return the outlines of some text as a path.

    It is set with the current font, style, size, alignment and leading, just like text(). The path has no colour, and it is not moved by the current transform until you draw it. You can cut it, outline it, fill it, or clip with it.

    Arguments:
        message: what to write. Any value works, or a FormattedString.
        x, y: the position, as for text().

    Returns:
        A path (like f.path()). Draw it with draw_path(), or use union(), intersection(), expand_stroke() and so on.

    Example:
        f.draw_path(f.text_path("Hi", 20, 20))

    See also: text, text_to_points, draw_path, clip
    """
    return active_sketch().text_path(message, x, y)


def text_to_points(message: object, x: float, y: float, spacing: float = 5) -> list[tuple[float, float]]:
    """Return points along the outlines of some text.

    It draws nothing. Each outline starts at its first point, and curves are measured along the curve. An empty message gives an empty list.

    Arguments:
        message: what to write, as for text().
        x, y: the position, as for text().
        spacing: the distance between points, in pixels. The default is 5. It must be above 0.

    Returns:
        A list of (x, y) tuples.

    Raises:
        ValueError: spacing is 0 or less.
        TypeError: spacing is not a number.

    Example:
        for x, y in f.text_to_points("hi", 20, 20, 6):
            f.circle(x, y, 3)

    See also: text_path, text
    """
    return canvas_sketch().text_to_points(message, x, y, spacing)


def current_font() -> Font:
    """Return the font that text is set in now.

    It works for the built-in font too.

    Returns:
        A Font. Ask it font.family(), font.style(), font.variations() (axis tag to (minimum, default, maximum); empty if the font is not variable), font.features() (a sorted list of OpenType tags) and font.contains(text) (True when every character has a glyph).

    Example:
        print(f.current_font().contains("e"))

    See also: text_font, load_font, system_font
    """
    return canvas_sketch().current_font()


def text_align(horizontal: str, vertical: str | None = None) -> None:
    """Choose which point of the text (x, y) means.

    The default is left and top. The choice is saved by push() and brought back by pop().

    Arguments:
        horizontal: "left" (the default), "center" or "right".
        vertical: "top" (the default), "center", "baseline" or "bottom". Leave it out to keep the current choice.

    Raises:
        ValueError: a word is not one of those.

    Example:
        f.text_align("center", "center")
        f.text("Middle", f.width / 2, f.height / 2)

    See also: text, text_width
    """
    active_sketch().text_align(horizontal, vertical)


def text_ascent() -> float:
    """Return how far letters reach above the baseline, in pixels.

    It is measured at the current text size and font.

    See also: text_descent, text_size
    """
    return active_sketch().text_ascent()


def text_descent() -> float:
    """Return how far letters such as g and y reach below the baseline, in pixels.

    It is measured at the current text size and font.

    See also: text_ascent, text_size
    """
    return active_sketch().text_descent()


def text_leading(leading: float | None) -> None:
    """Set the distance from one line's baseline to the next.

    It matters when a message has several lines, and in text_box().

    Arguments:
        leading: the distance in pixels, 0 or more. None (the default behaviour) means automatic: 1.25 times the text size.

    Raises:
        ValueError: leading is negative.

    Example:
        f.text_leading(30)

    See also: text_size, text, text_box
    """
    active_sketch().text_leading(leading)


def text_box(message: object, x: float, y: float, width: float, height: float | None = None,
             color: Color | None = None) -> str | FormattedString:
    """Draw text wrapped inside a box, and return whatever did not fit.

    Words are moved to a new line when they would pass the right edge. With a height, only the lines that fit are drawn. Give the returned text to another box to flow a story across columns.

    Arguments:
        message: the text, a string or a FormattedString.
        x, y: the top-left corner of the box.
        width: the width of the box, in pixels. It must be above 0.
        height: the height of the box, in pixels, 0 or more. None (the default) means no limit.
        color: a colour for this text only. The default None uses the fill, as text() does.

    Returns:
        The text that did not fit: a string, or a FormattedString if you gave one. It is "" when everything fitted.

    Raises:
        ValueError: the width is not above 0, or the height is negative.

    Example:
        rest = f.text_box("A long story that wraps inside a box.", 20, 60, 280, 100)

    See also: text, text_width, text_leading, FormattedString
    """
    return active_sketch().text_box(message, x, y, width, height, color)


def text_width(message: object) -> float:
    """Return how wide some text will be, in pixels.

    It is measured at the current text size and font, and it is the exact distance text() advances. Use it to centre or right-align text.

    Arguments:
        message: what to measure. Any value works, or a FormattedString.

    Returns:
        The width in pixels.

    Example:
        msg = "Hello"
        f.text(msg, (f.width - f.text_width(msg)) / 2, 100)

    See also: text, text_size, text_align
    """
    return active_sketch().text_width(message)


# ---- style
def color(*values):
    """Make a colour that you can read and reuse.

    You can pass it to fill(), stroke(), background() and so on. It has these parts: red, green, blue and alpha (each 0 to 255), hue (0 to 360), and saturation, brightness and lightness (each 0 to 100). Numbers follow the colour mode. A tuple always means red, green, blue. Use hsb() or hsl() to give a hue.

    Arguments:
        *values: one colour (a name, a hex string, a tuple or another colour), or one grey number, or a grey and alpha, or three or four numbers (red, green, blue and optional alpha).

    Returns:
        A colour with parts such as .red, .green, .blue, .alpha, .hue, .saturation, .brightness and .lightness.

    Raises:
        ValueError: there are no values, or more than four, or the colour is not understood.

    Example:
        c = f.color("tomato")
        print(c.red, c.hue)

    See also: hsb, hsl, lerp_color, color_mode
    """
    from .color import Color as _Color

    if len(values) == 1:
        return canvas_sketch().read_color(values[0])         # numbers follow color_mode (S15, S16)
    if len(values) in (2, 3, 4):
        return canvas_sketch().read_color(*values)           # follows color_mode (S15, S16)
    raise ValueError("f.color() takes one colour, a grey and alpha, or 3 or 4 numbers (red, green, blue[, alpha])")


def hsb(hue: float, saturation: float, brightness: float, alpha: float = 255):
    """Make a colour from hue, saturation and brightness.

    The ranges are always these, whatever the colour mode is.

    Arguments:
        hue: the colour wheel position, 0 to 360. It wraps round.
        saturation: how strong the colour is, 0 to 100.
        brightness: how light it is, 0 to 100.
        alpha: the opacity, 0 (invisible) to 255 (solid). The default is 255.

    Returns:
        A colour, as from color().

    Example:
        f.fill(f.hsb(200, 80, 90))

    See also: hsl, color, color_mode
    """
    from .color import Color as _Color

    return _Color.from_hsb(hue, saturation, brightness, alpha)


def hsl(hue: float, saturation: float, lightness: float, alpha: float = 255):
    """Make a colour from hue, saturation and lightness.

    The ranges are always these, whatever the colour mode is.

    Arguments:
        hue: the colour wheel position, 0 to 360. It wraps round.
        saturation: how strong the colour is, 0 to 100.
        lightness: how light it is, 0 to 100.
        alpha: the opacity, 0 (invisible) to 255 (solid). The default is 255.

    Returns:
        A colour, as from color().

    Example:
        f.fill(f.hsl(30, 90, 60))

    See also: hsb, color, color_mode
    """
    from .color import Color as _Color

    return _Color.from_hsl(hue, saturation, lightness, alpha)


def linear_gradient(x1: float, y1: float, x2: float, y2: float, colors, stops=None):
    """Make a gradient: colours blended along a line.

    Use it like a colour in fill(), stroke() or background().

    Arguments:
        x1, y1: where the line starts (the first colour).
        x2, y2: where the line ends (the last colour).
        colors: a list of colours, in any form that fill() takes.
        stops: where each colour sits along the line, from 0 to 1. The default None spaces them evenly.

    Returns:
        A gradient. Give it to fill(), stroke() or background().

    Example:
        f.fill(f.linear_gradient(0, 0, 200, 0, ["red", "blue"]))
        f.rect(0, 0, 200, 100)

    See also: radial_gradient, fill, lerp_color
    """
    from .paint import linear_gradient as make

    return make(x1, y1, x2, y2, colors, stops, canvas_sketch().read_color)


def radial_gradient(x: float, y: float, radius: float, colors, stops=None):
    """Make a gradient: colours blended outward from a point.

    The first colour is at the centre. Use it like a colour in fill(), stroke() or background().

    Arguments:
        x, y: the centre.
        radius: the distance where the last colour is reached, in pixels.
        colors: a list of colours, in any form that fill() takes.
        stops: where each colour sits, from 0 (centre) to 1 (the radius). The default None spaces them evenly.

    Returns:
        A gradient. Give it to fill(), stroke() or background().

    Example:
        f.background(f.radial_gradient(320, 200, 300, ["white", "navy"]))

    See also: linear_gradient, fill
    """
    from .paint import radial_gradient as make

    return make(x, y, radius, colors, stops, canvas_sketch().read_color)


def color_mode(mode: str, max1: float | None = None, max2: float | None = None,
               max3: float | None = None, max_alpha: float | None = None) -> None:
    """Choose how numbers become a colour.

    It affects colours given as numbers. Names, hex strings and colour objects are not affected. Each mode remembers its own ranges. The choice is saved by push() and brought back by pop().

    Arguments:
        mode: "rgb" (the default; ranges 255), "hsb" or "hsl" (ranges 360, 100, 100, and opacity 0 to 1).
        max1: with only this one, it sets the top of all four ranges. With max2 and max3 as well, it is the top of the first (red or hue).
        max2: the top of the second range (green or saturation).
        max3: the top of the third range (blue, brightness or lightness).
        max_alpha: the top of the opacity range. Leave it out to keep the opacity range.

    Raises:
        ValueError: the mode is unknown, a range is not a number above 0, or exactly two ranges are given.

    Example:
        f.color_mode("hsb", 360, 100, 100)
        f.fill(200, 80, 90)

    See also: color, hsb, hsl, fill
    """
    active_sketch().color_mode(mode, max1, max2, max3, max_alpha)


def blend_mode(mode: str) -> None:
    """Choose how what you draw next mixes with what is already there.

    The choice is saved by push() and brought back by pop().

    Arguments:
        mode: "normal" (the default), "multiply", "screen", "overlay", "darken", "lighten", "add", "difference", "exclusion", "dodge", "burn", "hard_light", "soft_light", "hue", "saturation", "color" or "luminosity".

    Raises:
        ValueError: the mode is not one of those words.

    Example:
        f.blend_mode("multiply")

    See also: opacity, tint, erase
    """
    active_sketch().blend_mode(mode)


def opacity(amount: float) -> None:
    """Make everything drawn after this see-through.

    The choice is saved by push() and brought back by pop().

    Arguments:
        amount: from 0 (invisible) to 255 (solid, the default).

    Raises:
        ValueError: amount is not a number from 0 to 255.

    Example:
        f.opacity(128)

    See also: blend_mode, fill, tint
    """
    active_sketch().opacity(amount)


def shadow(x_offset: float, y_offset: float, blur: float = 5, color: Color = DEFAULT_SHADOW_COLOR) -> None:
    """Give everything drawn after this a soft shadow.

    Stop it with no_shadow(). The choice is saved by push() and brought back by pop().

    Arguments:
        x_offset, y_offset: how far the shadow moves from the shape, in pixels.
        blur: how soft the edge is, in pixels, 0 or more. The default is 5.
        color: the shadow colour. The default is black at half strength.

    Raises:
        ValueError: blur is negative.

    Example:
        f.shadow(4, 6, blur=8)

    See also: no_shadow, opacity
    """
    active_sketch().shadow(x_offset, y_offset, blur, color)


def no_shadow() -> None:
    """Stop drawing shadows.

    See also: shadow
    """
    active_sketch().no_shadow()


def lerp_color(c1: Color, c2: Color, amount: float):
    """Return a colour part of the way between two colours.

    It mixes red, green, blue and alpha.

    Arguments:
        c1: the first colour, in any form that fill() takes.
        c2: the second colour.
        amount: from 0 to 1. 0 gives c1, 1 gives c2 and 0.5 is halfway.

    Returns:
        A colour, as from color().

    Example:
        f.fill(f.lerp_color("red", "blue", 0.5))

    See also: color, lerp, linear_gradient
    """
    from .color import Color as _Color

    return _Color.parse(c1).lerp(_Color.parse(c2), amount)


def fill(color: Color, *more: float) -> None:
    """Set the colour that shapes are filled with.

    It applies to the shapes you draw after the call. The start is white. The choice is saved by push() and brought back by pop().

    Arguments:
        color: a colour name such as "gold", a hex string such as "#F05A45", an (r, g, b) or (r, g, b, a) tuple, a colour from f.color(), or a gradient. One number is a grey.
        *more: extra numbers, so that fill(255, 99, 71) works like fill((255, 99, 71)). They follow the colour mode. A name, hex string or gradient takes no extra numbers.

    Raises:
        ValueError: the colour is not understood, or numbers follow a name or gradient.

    Example:
        f.fill("gold")
        f.fill(255, 99, 71, 128)

    See also: no_fill, stroke, color_mode, linear_gradient
    """
    active_sketch().fill(color, *more)


def no_fill() -> None:
    """Do not fill shapes drawn after this.

    Only their outlines are drawn. Use fill() to start filling again.

    Example:
        f.no_fill()
        f.circle(100, 100, 50)

    See also: fill, no_stroke
    """
    active_sketch().no_fill()


def stroke(color: Color, *more: float) -> None:
    """Set the colour of outlines and lines.

    It applies to what you draw after the call. The start is black. The choice is saved by push() and brought back by pop().

    Arguments:
        color: a colour name such as "black", a hex string, an (r, g, b) or (r, g, b, a) tuple, a colour from f.color(), or a gradient. One number is a grey.
        *more: extra numbers, so that stroke(0, 0, 255) works like stroke((0, 0, 255)). They follow the colour mode. A name, hex string or gradient takes no extra numbers.

    Raises:
        ValueError: the colour is not understood, or numbers follow a name or gradient.

    Example:
        f.stroke("navy")

    See also: no_stroke, stroke_width, fill
    """
    active_sketch().stroke(color, *more)


def no_stroke() -> None:
    """Do not draw outlines or lines after this.

    Use stroke() to start again.

    Example:
        f.no_stroke()
        f.circle(100, 100, 50)

    See also: stroke, no_fill
    """
    active_sketch().no_stroke()


def stroke_width(pixels: int) -> None:
    """Set how thick outlines and lines are.

    The stroke is centred on the edge of the shape: half of it lies outside and half inside. The start is 1. The choice is saved by push() and brought back by pop().

    Arguments:
        pixels: the thickness, in pixels. It must be 1 or more. Fractions such as 2.5 are kept.

    Raises:
        ValueError: pixels is less than 1.

    Example:
        f.stroke_width(3)

    See also: stroke, stroke_cap, stroke_join, stroke_dash
    """
    active_sketch().stroke_width(pixels)


def stroke_cap(cap: str) -> None:
    """Choose how the ends of lines look.

    Arguments:
        cap: "round" (the default), "square" (extends past the end by half the width) or "butt" (stops flat at the end).

    Raises:
        ValueError: the cap is not one of those words.

    Example:
        f.stroke_cap("butt")

    See also: stroke_join, stroke_width
    """
    active_sketch().stroke_cap(cap)


def stroke_join(join: str) -> None:
    """Choose how corners of outlines look.

    Arguments:
        join: "round" (the default), "miter" (sharp) or "bevel" (cut off).

    Raises:
        ValueError: the join is not one of those words.

    Example:
        f.stroke_join("miter")

    See also: miter_limit, stroke_cap, stroke_width
    """
    active_sketch().stroke_join(join)


def miter_limit(limit: float) -> None:
    """Set how far a sharp "miter" corner may stick out.

    Past that limit the corner is cut off (bevelled). It matters only when stroke_join is "miter".

    Arguments:
        limit: the ratio of the point's length to the stroke width. The default is 10. It must be 1 or more.

    Raises:
        ValueError: limit is less than 1.

    Example:
        f.miter_limit(4)

    See also: stroke_join
    """
    active_sketch().miter_limit(limit)


def stroke_dash(pattern: float | list[float], offset: float = 0) -> None:
    """Draw outlines and lines as dashes.

    Use no_dash() for solid lines again.

    Arguments:
        pattern: one length, or a list of lengths that alternate dash, gap, dash, gap and so on. Lengths are in pixels, 0 or more, and not all 0.
        offset: how far into the pattern to start, in pixels. The default is 0.

    Raises:
        ValueError: the pattern is empty, has a negative length, or is all zeros.

    Example:
        f.stroke_dash([12, 4])
        f.line(20, 50, 300, 50)

    See also: no_dash, stroke_width
    """
    active_sketch().stroke_dash(pattern, offset)


def no_dash() -> None:
    """Draw solid outlines and lines again.

    See also: stroke_dash
    """
    active_sketch().no_dash()


def no_smooth() -> None:
    """Draw hard, pixel-sharp edges from now on.

    There is no anti-aliasing, which suits pixel art. It is a setting of the sketch, so pop() does not undo it. Use smooth() to go back.

    Example:
        f.no_smooth()

    See also: smooth
    """
    active_sketch().no_smooth()


def smooth() -> None:
    """Draw smooth (anti-aliased) edges again.

    This is the start. Use it after no_smooth().

    See also: no_smooth
    """
    active_sketch().smooth()


def text_size(size: int) -> None:
    """Set the size of text.

    The size is an em of that many pixels, as in CSS. Capital letters come out about three-quarters of it. The start is 20. The choice is saved by push() and brought back by pop().

    Arguments:
        size: the size in pixels, above 0. A fraction is cut to a whole number.

    Raises:
        ValueError: size is 0 or less.

    Example:
        f.text_size(28)

    See also: text, text_width, text_font, text_leading
    """
    active_sketch().text_size(size)


# ---- fonts and styles (S-054, contract T11/T12)
def load_font(path: str, face: int | str = 0):
    """Load a font file.

    Pass the result to text_font(), text_fallback() and so on. A relative path is looked for next to your sketch file first, then in the current folder.

    Arguments:
        path: a .ttf or .otf font file, or a .ttc collection.
        face: for a .ttc collection, which font to use: its number (0 is the first) or its style as a word, such as "Bold". The default is 0.

    Returns:
        A Font. Ask it font.family(), font.style(), font.variations(), font.features() and font.contains(text).

    Raises:
        FileNotFoundError: the file is not found in either place.

    Example:
        mono = f.load_font("fonts/DejaVuSansMono.ttf")
        f.text_font(mono)

    See also: text_font, system_font, current_font
    """
    caller = inspect.currentframe()
    base_dir = None
    if caller is not None and caller.f_back is not None:
        sketch_file = caller.f_back.f_globals.get("__file__")
        if sketch_file:
            import os

            base_dir = os.path.dirname(os.path.abspath(sketch_file))
    return active_sketch().load_font(path, base_dir=base_dir, face=face)


def text_font(font, size: float | None = None) -> None:
    """Choose the font for the text you draw after this.

    The choice is saved by push() and brought back by pop().

    Arguments:
        font: a font from load_font() or system_font(), a path to a font file, or None for the built-in family.
        size: a text size to set at the same time. The default None keeps the size.

    Raises:
        TypeError: font is not a Font, a path or None.

    Example:
        f.text_font(f.load_font("fonts/MyFont.ttf"), 24)
        f.text_font(None)

    See also: load_font, system_font, text_size, text_style
    """
    caller = inspect.currentframe()
    base_dir = None
    if isinstance(font, str) and caller is not None and caller.f_back is not None:
        sketch_file = caller.f_back.f_globals.get("__file__")
        if sketch_file:
            import os

            base_dir = os.path.dirname(os.path.abspath(sketch_file))
    active_sketch().text_font(font, size, base_dir=base_dir)


def text_style(style: str) -> None:
    """Choose one of the four styles of the built-in font.

    It is ignored once you have chosen a font with text_font(), but remembered for when you go back to the built-in one.

    Arguments:
        style: "normal", "bold", "italic" or "bold_italic".

    Raises:
        ValueError: the style is not one of those words.

    Example:
        f.text_style("bold")

    See also: text_font, text_size
    """
    active_sketch().text_style(style)


# ---- tracking, OpenType features, font variations (S-090)
def text_fallback(*fonts) -> None:
    """Choose fonts to use for letters that the current font does not have.

    They are tried before funground's built-in fallbacks (emoji, symbols and Devanagari). Emoji are drawn in one colour, the fill. Part of the drawing state, so push() and pop() keep it.

    Arguments:
        *fonts: fonts from load_font() or system_font(). Give none to use only the built-in fallbacks. Give None on its own to turn fallback off, so a missing letter is an empty box.

    Example:
        f.text_fallback(f.system_font("Arial"))

    See also: system_font, load_font, text_font
    """
    active_sketch().text_fallback(*fonts)


def system_font(name: str):
    """Find a font installed on this computer.

    A sketch that uses it can look different on another computer. Font collections (.ttc files) are read too.

    Arguments:
        name: the family name, such as "Arial" (capitals do not matter; the Regular face is used when there are several), or a family with a style, such as "Nirmala UI Bold".

    Returns:
        A Font, for text_font() or text_fallback().

    Raises:
        FileNotFoundError: no installed font has that name.

    Example:
        f.text_font(f.system_font("Arial"))

    See also: load_font, text_font, text_fallback
    """
    return active_sketch().system_font(name)


def text_tracking(pixels: float) -> None:
    """Add space after every letter.

    The space is added after the last letter too. It changes text_width(), alignment, text_box() and text_path(). The start is 0. The choice is saved by push() and brought back by pop().

    Arguments:
        pixels: the extra space in pixels. A negative number tightens the text.

    Example:
        f.text_tracking(4)

    See also: text_width, text_size
    """
    active_sketch().text_tracking(pixels)


def text_features(**features: bool) -> None:
    """Turn OpenType features of the font on or off.

    Calls add to each other. With no arguments it goes back to the font's defaults.

    Arguments:
        **features: each name is a four-letter feature tag, and each value is True or False. For example liga=False turns ligatures off.

    Raises:
        TypeError: a value is not True or False.

    Example:
        f.text_features(liga=False)

    See also: font_variations, current_font
    """
    active_sketch().text_features(**features)


def font_variations(**axes: float) -> None:
    """Set the axes of a variable font.

    An axis that the font does not have is ignored, so it is harmless with an ordinary font. With no arguments it goes back to the font's defaults.

    Arguments:
        **axes: each name is an axis tag, and each value is a number. For example wght=700 is bold.

    Raises:
        TypeError: a value is not a number.

    Example:
        f.font_variations(wght=700)

    See also: text_features, current_font
    """
    active_sketch().font_variations(**axes)


# ---- transforms and the state stack (S-027)
def translate(dx: float, dy: float) -> None:
    """Move the origin.

    Everything drawn after this is shifted by (dx, dy). Transforms add up, and they apply to shapes, text, paths and clips. Order matters: translate then rotate turns about the new origin. The stack is reset at the start of every draw().

    Arguments:
        dx: how far to move to the right, in pixels.
        dy: how far to move down, in pixels.

    Example:
        f.translate(f.width / 2, f.height / 2)

    See also: rotate, scale, push, pop
    """
    active_sketch().translate(dx, dy)


def rotate(degrees: float) -> None:
    """Turn later drawing about the current origin.

    Degrees are used. 90 is a quarter turn clockwise on the screen. Each call adds to the turns before it.

    Arguments:
        degrees: the angle, in degrees. Use radians() or degrees() to convert if you work in radians.

    Example:
        f.translate(200, 150)
        f.rotate(45)
        f.rect(-40, -25, 80, 50)

    See also: translate, scale, radians, push
    """
    active_sketch().rotate(degrees)


def scale(sx: float, sy: float | None = None) -> None:
    """Grow or shrink later drawing about the origin.

    Each call multiplies the scale already in force.

    Arguments:
        sx: the factor sideways. 2 doubles, 0.5 halves. If sy is left out it is used both ways.
        sy: the factor up and down. The default None means the same as sx.

    Raises:
        ValueError: a factor is 0.

    Example:
        f.scale(2)
        f.scale(2, 1)

    See also: translate, rotate, push
    """
    active_sketch().scale(sx, sy)


def shear_x(degrees: float) -> None:
    """Slant later drawing sideways.

    Each point moves along x by tan(degrees) times its y.

    Arguments:
        degrees: the slant, in degrees.

    Example:
        f.shear_x(20)

    See also: shear_y, apply_matrix
    """
    active_sketch().shear_x(degrees)


def shear_y(degrees: float) -> None:
    """Slant later drawing up or down.

    Each point moves along y by tan(degrees) times its x.

    Arguments:
        degrees: the slant, in degrees.

    See also: shear_x, apply_matrix
    """
    active_sketch().shear_y(degrees)


def apply_matrix(a: float, b: float, c: float, d: float, e: float, f: float) -> None:
    """Multiply a whole transform into later drawing.

    A point (x, y) goes to x' = a*x + c*y + e and y' = b*x + d*y + f.

    Arguments:
        a, b, c, d: the four numbers that stretch, turn and slant. a and d are the sideways and up-and-down scale.
        e, f: how far to move along x and y, in pixels.

    Example:
        f.apply_matrix(1, 0, 0.5, 1, 0, 0)

    See also: translate, rotate, scale, shear_x, reset_matrix
    """
    active_sketch().apply_matrix(a, b, c, d, e, f)


def reset_matrix() -> None:
    """Forget every translate, rotate, scale and shear so far.

    It lasts until the enclosing pop().

    See also: translate, push, pop
    """
    active_sketch().reset_matrix()


def push() -> None:
    """Save the current transform and style.

    pop() brings them back. The style includes fill, stroke, stroke width, text settings, modes and clip. If you forget a pop(), funground pops for you at the end of draw() and prints a warning.

    Example:
        f.push()
        f.rotate(30)
        f.rect(0, 0, 80, 40)
        f.pop()

    See also: pop, saved_state
    """
    active_sketch().push()


def pop() -> None:
    """Restore the transform and style saved by the last push().

    A pop() with nothing to restore prints a warning and is ignored.

    See also: push, saved_state
    """
    active_sketch().pop()


def saved_state() -> AbstractContextManager[None]:
    """Return a ``with`` block that saves and restores the transform and style.

    It does push() on entry and pop() on exit, even if the block raises an error.

    Returns:
        A context manager. Use it as ``with f.saved_state():``.

    Example:
        with f.saved_state():
            f.rotate(30)
            f.rect(0, 0, 80, 40)

    See also: push, pop
    """
    return active_sketch().saved_state()


# ---- shapes, paths and clipping (S-028)
def begin_shape() -> None:
    """Start a shape that you build from its corners.

    Call vertex() for each corner, then end_shape(). Calling it twice without end_shape() is an error. A shape still open when draw() ends is dropped with a warning.

    Raises:
        RuntimeError: a shape is already being built.

    Example:
        f.begin_shape()
        f.vertex(100, 20)
        f.vertex(180, 80)
        f.vertex(60, 90)
        f.end_shape(close=True)

    See also: vertex, end_shape, begin_contour
    """
    active_sketch().begin_shape()


def vertex(x: float, y: float) -> None:
    """Add a corner to the shape begun by begin_shape().

    Arguments:
        x, y: the corner, in pixels.

    Raises:
        RuntimeError: there is no begin_shape() before it.

    See also: begin_shape, end_shape, bezier_vertex
    """
    active_sketch().vertex(x, y)


def bezier_vertex(cx1: float, cy1: float, cx2: float, cy2: float, x: float, y: float) -> None:
    """Add a Bezier curve segment to the shape being built.

    It goes from the last point to (x, y). It needs a vertex() before it.

    Arguments:
        cx1, cy1: the first control point, which pulls the start of the curve.
        cx2, cy2: the second control point, which pulls the end of the curve.
        x, y: where the curve ends.

    Raises:
        RuntimeError: there is no begin_shape() or no earlier vertex().

    Example:
        f.begin_shape()
        f.vertex(20, 80)
        f.bezier_vertex(20, 0, 180, 0, 180, 80)
        f.end_shape()

    See also: quadratic_vertex, curve_vertex, bezier
    """
    active_sketch().bezier_vertex(cx1, cy1, cx2, cy2, x, y)


def quadratic_vertex(cx: float, cy: float, x: float, y: float) -> None:
    """Add a quadratic curve segment to the shape being built.

    It goes from the last point to (x, y), pulled by one control point.

    Arguments:
        cx, cy: the control point.
        x, y: where the curve ends.

    Raises:
        RuntimeError: there is no begin_shape() or no earlier vertex().

    Example:
        f.quadratic_vertex(100, 0, 180, 80)

    See also: bezier_vertex, curve_vertex
    """
    active_sketch().quadratic_vertex(cx, cy, x, y)


def curve_vertex(x: float, y: float) -> None:
    """Add a point for a smooth curve that passes through the points.

    Give at least four in a row. The first and last only steer the curve. curve_tightness() changes how tight it is.

    Arguments:
        x, y: the point, in pixels.

    Example:
        f.begin_shape()
        f.curve_vertex(0, 100)
        f.curve_vertex(40, 40)
        f.curve_vertex(160, 40)
        f.curve_vertex(200, 100)
        f.end_shape()

    See also: curve, curve_tightness, bezier_vertex
    """
    active_sketch().curve_vertex(x, y)


def curve_tightness(tightness: float) -> None:
    """Set how tight curve_vertex() and curve() curves are.

    Arguments:
        tightness: 0 is smooth (the default). 1 gives straight lines.

    Example:
        f.curve_tightness(0.5)

    See also: curve_vertex, curve
    """
    active_sketch().curve_tightness(tightness)


def begin_contour() -> None:
    """Start a hole inside the shape being built.

    List the hole's corners with vertex(), then call end_contour().

    See also: end_contour, begin_shape
    """
    active_sketch().begin_contour()


def end_contour() -> None:
    """Finish the hole started by begin_contour().

    See also: begin_contour, end_shape
    """
    active_sketch().end_contour()


def bezier(x1: float, y1: float, cx1: float, cy1: float, cx2: float, cy2: float, x2: float, y2: float) -> None:
    """Draw a Bezier curve from one point to another.

    Two control points pull the curve. It is stroked only, never filled.

    Arguments:
        x1, y1: where the curve starts.
        cx1, cy1: the first control point.
        cx2, cy2: the second control point.
        x2, y2: where the curve ends.

    Example:
        f.bezier(20, 80, 20, 0, 180, 0, 180, 80)

    See also: curve, bezier_vertex, bezier_point
    """
    active_sketch().bezier(x1, y1, cx1, cy1, cx2, cy2, x2, y2)


def curve(x1: float, y1: float, x2: float, y2: float, x3: float, y3: float, x4: float, y4: float) -> None:
    """Draw a smooth curve from point 2 to point 3.

    Points 1 and 4 only steer it. It is stroked only, never filled. curve_tightness() changes how tight it is.

    Arguments:
        x1, y1: the first steering point.
        x2, y2: where the curve starts.
        x3, y3: where the curve ends.
        x4, y4: the last steering point.

    Example:
        f.curve(0, 100, 40, 40, 160, 40, 200, 100)

    See also: bezier, curve_vertex, curve_tightness
    """
    active_sketch().curve(x1, y1, x2, y2, x3, y3, x4, y4)


def bezier_point(a: float, b: float, c: float, d: float, t: float) -> float:
    """Return one coordinate of a Bezier curve at a place along it.

    Call it once for x and once for y.

    Arguments:
        a: the start coordinate.
        b: the first control coordinate.
        c: the second control coordinate.
        d: the end coordinate.
        t: the place along the curve, 0 (start) to 1 (end).

    Returns:
        The coordinate at t.

    Example:
        x = f.bezier_point(20, 20, 180, 180, 0.5)
        y = f.bezier_point(80, 0, 0, 80, 0.5)

    See also: bezier, bezier_tangent
    """
    from .shapes import bezier_point as _bp

    return _bp(a, b, c, d, t)


def bezier_tangent(a: float, b: float, c: float, d: float, t: float) -> float:
    """Return the slope of one coordinate of a Bezier curve at a place along it.

    Call it once for x and once for y, then use math.atan2 to get the direction.

    Arguments:
        a: the start coordinate.
        b: the first control coordinate.
        c: the second control coordinate.
        d: the end coordinate.
        t: the place along the curve, 0 (start) to 1 (end).

    Returns:
        The rate of change of the coordinate at t.

    See also: bezier, bezier_point
    """
    from .shapes import bezier_tangent as _bt

    return _bt(a, b, c, d, t)


def curve_point(a: float, b: float, c: float, d: float, t: float) -> float:
    """Return one coordinate of a curve() segment at a place along it.

    It uses the current curve_tightness(). Call it once for x and once for y.

    Arguments:
        a, b, c, d: the four coordinates, as for curve(): the first and last steer, and the curve runs from b to c.
        t: the place along the segment, 0 (at b) to 1 (at c).

    Returns:
        The coordinate at t.

    See also: curve, curve_tangent, curve_tightness
    """
    return active_sketch().curve_point(a, b, c, d, t)


def curve_tangent(a: float, b: float, c: float, d: float, t: float) -> float:
    """Return the slope of one coordinate of a curve() segment at a place along it.

    Arguments:
        a, b, c, d: the four coordinates, as for curve().
        t: the place along the segment, 0 to 1.

    Returns:
        The rate of change of the coordinate at t.

    See also: curve, curve_point
    """
    return active_sketch().curve_tangent(a, b, c, d, t)


def end_shape(close: bool = False) -> None:
    """Draw the shape that you built from corners.

    It uses the current fill and stroke. An open shape is only stroked, never filled. A shape that crosses itself, like a five-pointed star, is filled right through its centre.

    Arguments:
        close: True joins the last corner to the first, then fills and strokes it. The default False leaves the shape open.

    Raises:
        RuntimeError: there is no begin_shape() before it.

    Example:
        f.end_shape(close=True)

    See also: begin_shape, vertex
    """
    active_sketch().end_shape(close)


def path() -> PathBuilder:
    """Make a new, empty path that you can reuse.

    Chain its methods, each of which returns the builder: move_to(x, y), line_to(x, y), curve_to(cx1, cy1, cx2, cy2, x, y), quad_to(cx, cy, x, y), close(), rect(), ellipse(), circle() and polygon(). Draw it with draw_path(), or use it with clip(). Only closed paths are filled.

    Returns:
        A path builder. It also has union(), intersection(), difference(), xor(), expand_stroke(), bounds(), contains(), translate(), scale(), rotate() and copy().

    Example:
        tri = f.path().move_to(0, 0).line_to(40, 0).line_to(20, -30).close()
        f.draw_path(tri)

    See also: draw_path, clip, text_path, svg_paths
    """
    return active_sketch().path()


def draw_path(path: PathBuilder) -> None:
    """Draw a path made with path().

    It is filled (if it is closed) and then stroked, with the current style and transform.

    Arguments:
        path: the path to draw.

    Example:
        f.draw_path(f.path().circle(50, 50, 40))

    See also: path, clip, text_path
    """
    active_sketch().draw_path(path)


def no_clip() -> None:
    """Remove clipping.

    It lasts until the enclosing pop() or the end of the saved_state() block, which brings the previous clip back.

    See also: clip, saved_state
    """
    active_sketch().no_clip()


def clip(path: PathBuilder) -> None:
    """Limit later drawing to the inside of a path.

    The path is treated as closed and follows the current transform. The clip lasts until the enclosing pop() or the end of the saved_state() block, so put it inside one. background() ignores the clip.

    Arguments:
        path: a path made with path() or text_path().

    Example:
        with f.saved_state():
            f.clip(f.path().circle(100, 100, 80))
            f.background("gold")

    See also: no_clip, path, saved_state
    """
    active_sketch().clip(path)


# ---- off-screen graphics (S-052, contract P1-P3)
def create_graphics(width: int, height: int) -> Picture:
    """Make a picture: an off-screen canvas.

    It starts transparent. It has the same drawing commands as f (fill, circle, text, push, pop, transforms, clip and more) but its own state, transform and pixels. Nothing about it resets between frames. Draw it on the canvas with image().

    Arguments:
        width, height: the size in pixels.

    Returns:
        A Picture, with width and height, the drawing commands, get(), set(), copy(), resize(w, h), mask(other), filter(), load_pixels(), pixels, update_pixels() and save(path).

    Example:
        g = f.create_graphics(200, 100)
        g.fill("tomato")
        g.circle(100, 50, 80)
        f.image(g, 20, 20)

    See also: image, layer, load_image
    """
    return canvas_sketch().create_graphics(width, height)


# ---- layers (S-095, contract F16, D-053)
def layer(name: str) -> Picture:
    """Return the layer with a given name, and make it if it is new.

    A layer is a see-through picture the size of the canvas. Use it with ``with``: everything drawn inside the block goes to the layer. Layers are put over the canvas in the order they were first made. A layer keeps its drawing from frame to frame until you call background() or clear() inside it. Inside the block, f.width, f.mouse_x, random() and the like keep their canvas meaning. Layers do not nest. In a saved PDF or SVG each layer is a real, named layer.

    Arguments:
        name: a name in quotes. It must not be empty.

    Returns:
        A Picture, so ``with f.layer("sky") as sky:`` gives you sky.get(), sky.filter() and sky.save().

    Raises:
        RuntimeError: a layer block is already open.
        ValueError: the name is empty.

    Example:
        with f.layer("sky"):
            f.background("skyblue")

    See also: hide_layer, show_layer, create_graphics
    """
    refuse_in_mark("f.layer()")
    return canvas_sketch().layer(name)


def hide_layer(name: str) -> None:
    """Stop showing a layer.

    It keeps its drawing, and show_layer() brings it back. A hidden layer is left out of the window, a PNG and get(). It is kept in a PDF or SVG, switched off.

    Arguments:
        name: the layer's name.

    Raises:
        ValueError: there is no layer with that name.

    See also: show_layer, layer
    """
    canvas_sketch().hide_layer(name)


def show_layer(name: str) -> None:
    """Show a layer that hide_layer() hid.

    Arguments:
        name: the layer's name.

    Raises:
        ValueError: there is no layer with that name.

    See also: hide_layer, layer
    """
    canvas_sketch().show_layer(name)


# ---- controls (S-101, contract U1)
def create_slider(low: float, high: float, value: float | None = None, step: float | None = None,
                  label: str | None = None) -> Slider:
    """Make a slider in a panel below the canvas.

    Make it in setup() (or at the top of the file) and keep it in a variable. Read it in draw(). The panel is not part of the picture: it is not in f.width or f.height, saves, or get(). Making a control inside draw(), or in a script, is a RuntimeError. Without a window the slider keeps its value.

    Arguments:
        low, high: the smallest and largest value. low must be below high.
        value: where the slider starts. The default None starts at low.
        step: the size of each move. The default None moves smoothly. It must be above 0.
        label: the text beside the slider. The default None has no label.

    Returns:
        A Slider. slider.value() reads the value. slider.value(v) sets it.

    Raises:
        ValueError: low is not below high, or step is 0 or less.

    Example:
        size = f.create_slider(10, 100, 40, step=5, label="size")
        f.circle(200, 150, size.value())

    See also: create_checkbox, create_button
    """
    refuse_in_mark("f.create_slider()")
    return canvas_sketch().create_slider(low, high, value, step, label)


def create_checkbox(label: str, checked: bool = False) -> Checkbox:
    """Make a tick box in the panel below the canvas.

    Make it in setup(), and read it in draw().

    Arguments:
        label: the text beside the box.
        checked: whether it starts ticked. The default is False.

    Returns:
        A Checkbox. box.checked() reads it. box.checked(True) sets it.

    Example:
        grid = f.create_checkbox("grid")
        if grid.checked():
            f.line(0, 0, f.width, f.height)

    See also: create_slider, create_button
    """
    refuse_in_mark("f.create_checkbox()")
    return canvas_sketch().create_checkbox(label, checked)


def create_button(label: str) -> Button:
    """Make a button in the panel below the canvas.

    Make it in setup(), and read it in draw().

    Arguments:
        label: the text on the button.

    Returns:
        A Button. button.clicked() is True once for each click since it was last asked.

    Example:
        reset = f.create_button("reset")
        if reset.clicked():
            f.background("white")

    See also: create_slider, create_checkbox
    """
    refuse_in_mark("f.create_button()")
    return canvas_sketch().create_button(label)


def load_image(path: str) -> Picture:
    """Read an image file and return it as a picture.

    Draw it with image(). A relative path is looked for next to your sketch file first, then in the current folder. Photos from phones are turned the right way up. Transparency is kept. You can draw on the picture like any other.

    Arguments:
        path: the file name: PNG, JPEG, GIF, BMP, TGA and others.

    Returns:
        A Picture, with width and height in pixels.

    Raises:
        FileNotFoundError: the file is not found in either place.
        ValueError: the file is not an image.

    Example:
        photo = f.load_image("photo.jpg")
        f.image(photo, 0, 0)

    See also: image, load_svg, create_graphics
    """
    caller = inspect.currentframe()
    base_dir = None
    if caller is not None and caller.f_back is not None:
        sketch_file = caller.f_back.f_globals.get("__file__")
        if sketch_file:
            import os

            base_dir = os.path.dirname(os.path.abspath(sketch_file))
    return canvas_sketch().load_image(path, base_dir=base_dir)


def _sketch_folder() -> str | None:
    """The folder of the script that called the public function two frames up, or None."""
    import os

    caller = inspect.currentframe()
    for _ in range(2):
        caller = caller.f_back if caller is not None else None
    if caller is not None:
        sketch_file = caller.f_globals.get("__file__")
        if sketch_file:
            return os.path.dirname(os.path.abspath(sketch_file))
    return None


def load_svg(path: str) -> Picture:
    """Read an SVG file and return a picture of its shapes.

    It stays sharp at any size, and stays vector in a saved PDF or SVG. The size is the file's width and height (96 to the inch), or its viewBox. It reads paths, rect, circle, ellipse, line, polyline, polygon, groups, use, transforms, fill and stroke colours, stroke width, caps, joins, dashes and fill-rule. A gradient or pattern uses its first colour. Text, images, filters, masks and animation are ignored. A relative path is looked for next to your sketch file first, then in the current folder.

    Arguments:
        path: the SVG file name.

    Returns:
        A Picture. Draw it with image().

    Raises:
        FileNotFoundError: the file is not found.
        ValueError: the file is not an SVG.

    Example:
        badge = f.load_svg("badge.svg")
        f.image(badge, 20, 20)

    See also: svg_paths, load_image, image
    """
    return canvas_sketch().load_svg(path, base_dir=_sketch_folder())


def load_sound(path: str):
    """Read a sound file and return a sound.

    A relative path is looked for next to your sketch file first, then in the current folder. With no sound device (or FUNGROUND_HEADLESS=1) it plays silently and keeps time.

    Arguments:
        path: a WAV, OGG or MP3 file.

    Returns:
        A Sound: play(), loop(), stop(), pause(), set_volume(v), is_playing(), duration(), current_time(), level(), spectrum(bands), pitch(), pan(p), reverb(amount), samples() and save(path).

    Raises:
        FileNotFoundError: the file is not found in either place.
        ValueError: the file is not sound.

    Example:
        beep = f.load_sound("beep.wav")
        beep.play()

    See also: create_sound, tone, note, draw_wave
    """
    from . import sound

    return sound.load(path, _sketch_folder(), lambda: canvas_sketch().frame_count)


def _sound_frame() -> int:
    return canvas_sketch().frame_count


def create_sound(samples, rate: int = 44100):
    """Make a sound from a list of numbers.

    It is an ordinary sound. sound.samples() gives the numbers back.

    Arguments:
        samples: a list of numbers from -1 to 1, one channel. Numbers outside that range are clipped.
        rate: how many numbers make one second. The default is 44100.

    Returns:
        A Sound: play(), loop(), stop(), level(), spectrum(bands), samples() and so on.

    Raises:
        ValueError: the list is empty or has things that are not numbers.

    Example:
        import math
        s = f.create_sound([math.sin(i / 9) for i in range(44100)])
        s.play()

    See also: tone, load_sound, mix
    """
    from . import sound

    return sound.create(samples, rate, _sound_frame)


def tone(frequency: float, seconds: float, wave: str = "sine", volume: float = 0.5,
         attack: float = 0.01, release: float = 0.15, decay: float = 0.15, sustain: float = 0.7):
    """Make a sound that is one steady tone.

    The loudness follows an envelope. It rises to full over the attack, falls to the sustain level over the decay, holds, and fades out over the last release seconds. If attack and release do not fit, they are made shorter. Noise repeats after random_seed().

    Arguments:
        frequency: the pitch, in hertz.
        seconds: how long the sound lasts.
        wave: "sine" (the default), "soft", "triangle", "square", "saw" or "noise".
        volume: from 0 to 1. The default 0.5 is half, so sounds can play together without clipping.
        attack: seconds to rise to full. The default is 0.01.
        release: seconds to fade out at the end. The default is 0.15.
        decay: seconds to fall to the sustain level. The default is 0.15.
        sustain: the level held after the decay, 0 to 1. The default is 0.7.

    Returns:
        A Sound: play(), loop(), stop(), level() and so on.

    Example:
        f.tone(440, 1, "square").play()

    See also: note, pluck, melody, create_sound
    """
    from . import sound, synth

    rng = canvas_sketch()._rng
    return sound.make(synth.tone(frequency, seconds, wave, volume, attack, release, rng, "f.tone()",
                                 decay, sustain), _sound_frame, "f.tone()")


def note(name: str, seconds: float, wave: str = "sine", volume: float = 0.5,
         attack: float = 0.01, release: float = 0.15, decay: float = 0.15, sustain: float = 0.7):
    """Make a sound that is one named note.

    It takes the same options as tone().

    Arguments:
        name: a note name such as "A4" (440 hertz), "C#5" or "Bb3".
        seconds: how long the sound lasts.
        wave: "sine" (the default), "soft", "triangle", "square", "saw" or "noise".
        volume: from 0 to 1. The default is 0.5.
        attack: seconds to rise to full. The default is 0.01.
        release: seconds to fade out at the end. The default is 0.15.
        decay: seconds to fall to the sustain level. The default is 0.15.
        sustain: the level held after the decay, 0 to 1. The default is 0.7.

    Returns:
        A Sound: play(), loop(), stop(), level() and so on.

    Raises:
        ValueError: the note name is not understood.

    Example:
        f.note("C4", 2, attack=0.5, sustain=1).play()

    See also: tone, melody, note_to_frequency
    """
    from . import sound, synth

    rng = canvas_sketch()._rng
    hz = synth.note_to_frequency(name, who="f.note()")
    return sound.make(synth.tone(hz, seconds, wave, volume, attack, release, rng, "f.note()",
                                 decay, sustain), _sound_frame, "f.note()")


def pluck(name_or_frequency, seconds: float, volume: float = 0.5):
    """Make a sound like a plucked string.

    It dies away by itself. It repeats after random_seed().

    Arguments:
        name_or_frequency: a note name such as "E3", or a frequency in hertz.
        seconds: how long the sound lasts.
        volume: from 0 to 1. The default is 0.5.

    Returns:
        A Sound: play(), loop(), stop(), reverb() and so on.

    Example:
        f.pluck("E3", 2).play()

    See also: tone, note, drone
    """
    from . import sound, synth

    values = synth.pluck(name_or_frequency, seconds, volume, canvas_sketch()._rng, "f.pluck()")
    return sound.make(values, _sound_frame, "f.pluck()")


def melody(text: str, tempo: float = 120, wave: str = "soft", sa: str | None = None,
           tuning: str = "equal", volume: float = 0.5):
    """Make a sound from a string of notes.

    Separate the tokens with spaces. A token is a note name, "-" for a rest, or "[C4 E4 G4]" for a chord. Add ":2" after a token for how many beats it lasts (1 if left off). Notes are smooth: each one fades out over 0.15 seconds while the next begins, so the sound lasts that much longer than its beats when it ends on a note. With sa given, the notes are sargam: S r R g G m M P d D n N, with ' for the octave above and a comma for the octave below. In sargam, "S~G" glides from S to G over the token's beats, and "(R)G" touches R for about 60 milliseconds and then plays G.

    Arguments:
        text: the notes, such as "C4 E4 G4:2 - [C4 E4 G4]:4".
        tempo: beats a minute. The default is 120.
        wave: the tone, as for tone(). The default is "soft".
        sa: a note name such as "C4" that makes the notes sargam, with that note as Sa. The default None reads note names.
        tuning: "equal" (the default) or "just". "just" uses just-intonation ratios from Sa, and needs sa.
        volume: from 0 to 1. The default is 0.5.

    Returns:
        A Sound: play(), loop(), stop() and so on.

    Raises:
        ValueError: a token cannot be read. The message names it.

    Example:
        f.melody("C4 E4 G4:2 -", tempo=100).play()

    See also: note, sequence, mix, raga
    """
    from . import sound, synth

    values = synth.melody_samples(text, tempo, wave, sa, tuning, canvas_sketch()._rng, "f.melody()", volume)
    return sound.make(values, _sound_frame, "f.melody()")


def sequence(*sounds):
    """Make a new sound that plays the given sounds one after another.

    Arguments:
        *sounds: the sounds to join, in order.

    Returns:
        A Sound that lasts as long as all of them together.

    Example:
        f.sequence(f.note("C4", 1), f.note("E4", 1)).play()

    See also: mix, melody
    """
    from . import sound

    return sound.sequence(sounds, _sound_frame)


def mix(*sounds):
    """Make a new sound that plays the given sounds together.

    A soft limiter keeps the loudest moments at or below 0.9, so the sum never clips. Quiet sums are not changed.

    Arguments:
        *sounds: the sounds to play together.

    Returns:
        A Sound as long as the longest of them.

    Example:
        f.mix(f.note("C4", 2), f.note("E4", 2), f.note("G4", 2)).play()

    See also: sequence, chord_notes
    """
    from . import sound

    return sound.mix(sounds, _sound_frame)


def note_to_frequency(name: str, sa: str | None = None) -> float:
    """Return the frequency of a note, in hertz.

    Arguments:
        name: a note name such as "A4". With sa given, a swara such as "G" or "N,".
        sa: a note name such as "C4" that the swara is counted from. The default None reads an ordinary note name.

    Returns:
        The frequency in hertz. note_to_frequency("A4") is 440.

    Raises:
        ValueError: the name is not understood.

    Example:
        print(f.note_to_frequency("A4"))

    See also: frequency_to_note, note, tone
    """
    from . import synth

    return synth.note_to_frequency(name, sa)


def frequency_to_note(hz: float, sa: str | None = None) -> str:
    """Return the name of the note nearest to a frequency.

    Sharps are used, such as "C#5".

    Arguments:
        hz: the frequency, in hertz.
        sa: a note name such as "C4". With it, the answer is the nearest swara, such as "G'". The default None gives an ordinary note name.

    Returns:
        A note name, such as "A4".

    Example:
        print(f.frequency_to_note(440))

    See also: note_to_frequency
    """
    from . import synth

    return synth.frequency_to_note(hz, sa)


def chord_notes(name: str) -> list[str]:
    """Return the note names in a chord.

    Arguments:
        name: a note (with # or b), followed by nothing, m, dim, aug, 7, maj7 or m7. For example "C", "Am" or "Bdim".

    Returns:
        A list of note names, with sharps. chord_notes("C") is ["C", "E", "G"], and chord_notes("Am") is ["A", "C", "E"].

    Raises:
        ValueError: the chord name is not understood.

    Example:
        print(f.chord_notes("Am"))

    See also: mix, note
    """
    from . import analysis

    return analysis.chord_notes(name)


# ---- ragas and talas (S-115, contract A8)
def ragas() -> list[str]:
    """Return the names of the ragas in funground's small built-in table.

    For example "Yaman" and "Bhupali".

    Returns:
        A list of names.

    See also: raga, match_ragas, talas
    """
    from . import hindustani as _ragas

    return _ragas.raga_names()


def raga(name: str):
    """Return one raga from the built-in table.

    Arguments:
        name: the raga's name. Capitals do not matter.

    Returns:
        A read-only record with name, thaat, swaras, aroha, avaroha and pakad (sargam strings for melody(sa=...)), vadi, samvadi, time, notes and sources.

    Raises:
        ValueError: the name is not in the table. The message lists the table.

    Example:
        f.melody(f.raga("Yaman").aroha, sa="D4").play()

    See also: ragas, melody, match_ragas
    """
    from . import hindustani as _ragas

    return _ragas.find_raga(name, "f.raga()")


def talas() -> list[str]:
    """Return the names of the talas in the built-in table.

    They are Teentaal, Ektaal, Jhaptaal, Rupak, Dadra and Keherwa.

    Returns:
        A list of names.

    See also: tala_info, tala, ragas
    """
    from . import hindustani as _ragas

    return _ragas.tala_names()


def tala_info(name: str):
    """Return one tala from the built-in table.

    Arguments:
        name: the tala's name. Capitals do not matter.

    Returns:
        A read-only record with name, beats, vibhag (the divisions), tali (claps) and khali (waves) as beat numbers, sam (beat 1), bols (the theka, one bol a beat), notes and sources.

    Raises:
        ValueError: the name is not in the table.

    Example:
        print(f.tala_info("Rupak").khali)

    See also: talas, tala
    """
    from . import hindustani as _ragas

    return _ragas.find_tala(name, "f.tala_info()")


def tala(name: str, tempo: float = 80, cycles: int = 1):
    """Make a sound of a tala's theka played with simple drum sounds.

    The sam is accented, and the khali part is softer. The sound is exactly beats * 60 / tempo * cycles seconds long.

    Arguments:
        name: the tala's name, such as "Teentaal". See talas().
        tempo: beats a minute. The default is 80.
        cycles: how many times round the tala. The default is 1.

    Returns:
        A Sound: play(), loop() and so on.

    Raises:
        ValueError: the name is not in the table.

    Example:
        f.tala("Teentaal", tempo=100).loop()

    See also: talas, tala_info, drone
    """
    from . import hindustani as _ragas, sound

    return sound.make(_ragas.tala(name, tempo, cycles, None, "f.tala()"), _sound_frame, "f.tala()")


def drone(sa, seconds: float, pattern: str = "P S' S' S", volume: float = 0.5):
    """Make a tanpura-like drone.

    It is plucked strings that ring on, played in turn over and over. It loops smoothly with sound.loop(). It repeats after random_seed().

    Arguments:
        sa: the base note: a note name such as "D3", or a frequency in hertz.
        seconds: how long the sound lasts.
        pattern: the strings to pluck, as swaras. The default is "P S' S' S". It may start with m or N instead of P.
        volume: its loudest point, 0 to 1. The default is 0.5.

    Returns:
        A Sound: loop(), play(), reverb() and so on.

    Example:
        f.drone("D3", 8).loop()

    See also: pluck, tala, raga
    """
    from . import hindustani as _ragas, sound

    values = _ragas.drone(sa, seconds, pattern, canvas_sketch()._rng, "f.drone()", volume)
    return sound.make(values, _sound_frame, "f.drone()")


def match_ragas(histogram) -> list[tuple[str, float]]:
    """Rank the table's ragas by how well their swaras fit a histogram.

    It compares note sets only, so ragas with the same swaras score almost the same (for example Bhupali and Deshkar). It is a learning aid, not a judge.

    Arguments:
        histogram: twelve numbers, as from sound.swara_histogram(sa).

    Returns:
        A list of (name, score) pairs, best first, with scores from 0 to 1.

    Example:
        h = song.swara_histogram("C#4")
        print(f.match_ragas(h)[0])

    See also: ragas, raga
    """
    from . import hindustani as _ragas

    return _ragas.match(histogram, "f.match_ragas()")


def microphone(name: str | None = None):
    """Make a microphone object for the computer's default input.

    Call mic.start() to listen. While it listens, mic.level(), mic.spectrum(bands) and mic.pitch() work as they do on a sound. mic.capture(seconds) returns the last few seconds as a sound. It is never played back. With FUNGROUND_HEADLESS=1 it is silent and hears nothing. On a Mac, allow microphone access in System Settings.

    Arguments:
        name: part of the name of the input to use. The default None uses the default input. See microphones().

    Returns:
        A Microphone: start(), stop(), is_listening(), level(), spectrum(bands), pitch(), capture(seconds), is_onset(), chroma() and chord().

    Raises:
        RuntimeError: there is no microphone, or access is refused.

    Example:
        mic = f.microphone()
        mic.start()

    See also: microphones, draw_wave, draw_spectrum, draw_pitch_line
    """
    from . import microphone_input as mic

    return mic.make(name, _sound_frame)


def microphones() -> list[str]:
    """Return the names of the computer's microphones (inputs).

    Returns:
        A list of names. Give part of one to microphone().

    Example:
        print(f.microphones())

    See also: microphone
    """
    from . import microphone_input as mic

    return mic.microphones()


# ---- drawing sound (S-111, contract A7, D-061)
def draw_wave(source, x: float, y: float, w: float, h: float) -> None:
    """Draw the wave of a sound, a microphone or a list of numbers.

    It is drawn inside a box, with the current fill, stroke and transform. For a sound it shows the whole sound, with a line at the place it is playing. For a microphone it shows the last half second. A sound's shape is worked out once for each width, so it is quick.

    Arguments:
        source: a Sound, a Microphone or a list of numbers.
        x, y: the top-left corner of the box.
        w, h: the width and height of the box, in pixels.

    Example:
        f.draw_wave(song, 20, 20, 400, 80)

    See also: draw_spectrum, spectrogram, draw_pitch_line
    """
    from . import sound_views

    sound_views.draw_wave(active_sketch(), source, x, y, w, h)


def draw_spectrum(source, x: float, y: float, w: float, h: float, bands: int = 32) -> None:
    """Draw bars for a spectrum, as it is now.

    The bars stand on the bottom of a box, in the current style.

    Arguments:
        source: a Sound or a Microphone.
        x, y: the top-left corner of the box.
        w, h: the width and height of the box, in pixels.
        bands: how many bars. The default is 32.

    Example:
        f.draw_spectrum(mic, 20, 120, 400, 80)

    See also: draw_wave, spectrogram
    """
    from . import sound_views

    sound_views.draw_spectrum(active_sketch(), source, x, y, w, h, bands)


def spectrogram(sound, width: int, height: int) -> Picture:
    """Make a picture of a whole sound.

    Time goes across. Pitch goes up (about 40 hertz to 16 kilohertz, spaced like notes). Louder is brighter. The brightest colour is the current fill. It takes a moment (about a second for 10 seconds of sound at 400 by 200), so make it once, in setup().

    Arguments:
        sound: the Sound to look at.
        width, height: the size of the picture, in pixels.

    Returns:
        A Picture. Draw it with image(), or save it.

    Example:
        pic = f.spectrogram(song, 400, 200)
        f.image(pic, 20, 20)

    See also: draw_wave, draw_spectrum, image
    """
    from . import sound_views

    return sound_views.spectrogram(canvas_sketch(), active_sketch(), sound, width, height)


def draw_pitch_line(source, x: float, y: float, w: float, h: float, seconds: float = 5,
                    low: str = "C3", high: str = "C6", sa: str | None = None) -> None:
    """Draw the pitch of a sound or microphone as a scrolling line.

    Call it once in every frame, because it reads source.pitch() each time. The line scrolls left. Faint guide lines are labelled with note names, or with swaras when sa is given. The line has a gap where pitch() is None.

    Arguments:
        source: a Sound or a Microphone.
        x, y: the top-left corner of the box.
        w, h: the width and height of the box, in pixels.
        seconds: how much time the box shows. The default is 5.
        low: the note at the bottom. The default is "C3".
        high: the note at the top. The default is "C6".
        sa: a note name such as "C4". With it the guide lines are swaras. The default None uses note names.

    Example:
        f.draw_pitch_line(mic, 20, 20, 400, 150)

    See also: draw_wave, microphone, frequency_to_note
    """
    from . import sound_views

    sound_views.draw_pitch_line(active_sketch(), canvas_sketch().frame_count, source,
                                x, y, w, h, seconds, low, high, sa)


def svg_paths(path: str) -> list[PathBuilder]:
    """Read an SVG file and return its shapes as paths.

    There is one path for each shape, in the file's own coordinates. Use them for booleans, clips or your own colours.

    Arguments:
        path: the SVG file name. A relative path is looked for next to your sketch file first, then in the current folder.

    Returns:
        A list of path builders, as from path().

    Raises:
        FileNotFoundError: the file is not found.
        ValueError: the file is not an SVG.

    Example:
        shapes = f.svg_paths("badge.svg")
        f.draw_path(shapes[0])

    See also: load_svg, path, draw_path
    """
    from . import svg
    from .typography import _resolve_path

    resolved = _resolve_path(path, _sketch_folder(), "f.svg_paths()", "SVG")
    return [PathBuilder(geometry) for geometry in svg.shapes_as_paths(svg.read(resolved, "f.svg_paths()"))]


def image(picture, x: float, y: float, width: float | None = None, height: float | None = None,
          sx: float | None = None, sy: float | None = None,
          sw: float | None = None, sh: float | None = None) -> None:
    """Draw a picture.

    It is drawn as it is at this moment: later drawing on the picture does not change what was placed. image_mode() changes how x, y, width and height are read. tint() colours it.

    Arguments:
        picture: a Picture, from load_image(), load_svg(), create_graphics(), get() or spectrogram().
        x, y: where to put it, by default the top-left corner.
        width, height: the size to stretch it to. The default None uses the picture's own size.
        sx, sy, sw, sh: give all four to draw only that part of the picture (in its own pixels) into the box. A part that reaches outside the picture is clipped and keeps its place. sw and sh must be above 0.

    Raises:
        ValueError: only some of sx, sy, sw and sh were given, or sw or sh is not above 0.

    Example:
        f.image(photo, 0, 0)
        f.image(photo, 0, 0, 200, 150, 40, 30, 100, 75)

    See also: load_image, create_graphics, image_mode, tint
    """
    draw_image(active_sketch(), picture, x, y, width, height, sx, sy, sw, sh)


def tint(color, *more: float) -> None:
    """Colour every picture drawn with image() from now on.

    Red, green and blue of each pixel are multiplied by the tint's, and the alpha is multiplied in. Shapes and text are not tinted. The choice is saved by push() and brought back by pop().

    Arguments:
        color: any colour that fill() takes, except a gradient. One number is a grey.
        *more: extra numbers, as for fill(). tint(255, 128) draws pictures half see-through.

    Example:
        f.tint("gold")
        f.image(photo, 0, 0)

    See also: no_tint, image, opacity
    """
    active_sketch().tint(color, *more)


def no_tint() -> None:
    """Stop tinting pictures.

    See also: tint
    """
    active_sketch().no_tint()


def erase(fill_strength: float = 255, stroke_strength: float = 255) -> None:
    """Make everything drawn after this remove what is under it, instead of painting.

    Colours, gradients, tint, blend mode, opacity and shadow are ignored. Use it to cut holes in a picture from create_graphics(). Stop it with no_erase().

    Arguments:
        fill_strength: how much shape fills remove. 255 (the default) removes completely, making it see-through. 128 removes about half. 0 removes nothing.
        stroke_strength: the same for outlines.

    Raises:
        ValueError: a strength is not a number from 0 to 255.

    Example:
        f.erase()
        f.circle(50, 50, 40)
        f.no_erase()

    See also: no_erase, clear, create_graphics
    """
    active_sketch().erase(fill_strength, stroke_strength)


def no_erase() -> None:
    """Go back to painting.

    See also: erase
    """
    active_sketch().no_erase()


# ---- pixels (S-079, contract P7, P8)
def get(x: float, y: float, w: float | None = None, h: float | None = None):
    """Read a pixel, or copy a region of the canvas.

    It sees what has been drawn so far, this frame included. Outside the canvas is transparent. Coordinates are rounded down. On a high-resolution screen it reads the top-left real pixel of a logical one.

    Arguments:
        x, y: the pixel, or the top-left corner of the region.
        w, h: the size of the region. Give both to copy a region. Leave them out (None) to read one pixel.

    Returns:
        With no w and h: a colour with .red, .green, .blue and .alpha. With w and h: a new Picture copied from that region.

    Example:
        c = f.get(10, 20)
        part = f.get(0, 0, 50, 50)

    See also: set, load_pixels, image
    """
    refuse_in_mark("f.get()")
    return active_sketch().get(x, y, w, h)


def set(x: float, y: float, color, *more: float) -> None:  # noqa: A001  (p5's name)
    """Make one pixel exactly one colour.

    Fill, stroke, transform, clip, tint, opacity and blend mode do not apply. Outside the canvas, nothing happens.

    Arguments:
        x, y: the pixel.
        color: any colour that fill() takes.
        *more: extra numbers, as for fill().

    Example:
        f.set(10, 20, "red")

    See also: get, update_pixels
    """
    refuse_in_mark("f.set()")
    active_sketch().set(x, y, color, *more)


def load_pixels() -> None:
    """Copy the canvas into f.pixels.

    f.pixels is then a bytearray with red, green, blue and alpha (0 to 255, not premultiplied) for every pixel, row by row from the top left. The pixel at (x, y) starts at index (y * f.width + x) * 4. Change the numbers in place, then call update_pixels(). A Python loop over a whole 640 by 400 canvas takes seconds.

    Example:
        f.load_pixels()
        f.pixels[(10 * f.width + 20) * 4] = 255
        f.update_pixels()

    See also: update_pixels, get, set
    """
    refuse_in_mark("f.load_pixels()")
    active_sketch().load_pixels()


def update_pixels() -> None:
    """Write f.pixels back onto the canvas.

    It works like a set() of every pixel.

    Raises:
        RuntimeError: load_pixels() was not called first.

    See also: load_pixels, set
    """
    refuse_in_mark("f.update_pixels()")
    active_sketch().update_pixels()


def filter(kind: str, value: float | None = None) -> None:  # noqa: A001  (p5's name)
    """Change everything drawn so far, in place.

    Alpha is kept, except by "opaque". "posterize", "erode" and "dilate" are faster with funground[extras] installed, but the result is the same.

    Arguments:
        kind: "threshold", "gray", "opaque", "invert", "blur", "posterize", "erode" or "dilate".
        value: for "threshold", a level from 0 to 1 (default 0.5). For "blur", a radius in pixels (default 1). For "posterize", the number of levels, 2 to 255 (required). The others take none.

    Raises:
        ValueError: the kind is unknown, or the value is out of range.

    Example:
        f.filter("blur", 3)

    See also: get, create_graphics
    """
    refuse_in_mark("f.filter()")
    active_sketch().filter(kind, value)


# ---- input
def key_down(key: str | int) -> bool:
    """Return whether a key is held down right now.

    Escape also closes the sketch. With no window, no key is ever down.

    Arguments:
        key: "left", "right", "up", "down", "space", "enter", "escape", or a single character such as "a" or "7". Capitals do not matter.

    Returns:
        True while the key is held.

    Raises:
        ValueError: the name is not one of those.

    Example:
        if f.key_down("left"):
            x -= 3

    See also: is_key_pressed, key, key_code
    """
    return canvas_sketch().key_down(key)


# ---- helpers
def random(low: float = 1.0, high: float | None = None) -> float:
    """Return a random number.

    random(10) gives a number from 0 up to 10. random(5, 10) gives a number from 5 up to 10. random() gives a number from 0 up to 1. It uses its own generator and never touches Python's own random module.

    Arguments:
        low: with one argument, the top of the range (it starts at 0). With high as well, the bottom.
        high: the top of the range. The default None means low is the top.

    Returns:
        A floating-point number.

    Example:
        x = f.random(f.width)
        d = f.random(10, 40)

    See also: random_seed, random_choice, random_gaussian, noise
    """
    return canvas_sketch().random(low, high)


def random_seed(seed: int | None = None) -> None:
    """Make random() repeatable.

    The same seed gives the same sequence. It also covers random_gaussian(), random_choice() and the random parts of sounds. Any whole number works, however large or negative, and f.keep() records it exactly as you gave it.

    When you do not call random_seed(), funground picks a seed at the start of the run (a number below 1,000,000) and f.keep() records it, so f.random_seed(that number) gives the same random numbers again. A recorded seed makes funground's randomness repeatable; it does not make every sketch reproducible, because a sketch can also depend on the mouse, the clock, files or Python's own random module.

    Arguments:
        seed: a whole number. The default None starts from a different, unpredictable place each time, and records where.

    Example:
        f.random_seed(7)

    See also: random, noise_seed
    """
    canvas_sketch().random_seed(seed)


def noise(x: float, y: float = 0.0, z: float = 0.0) -> float:
    """Return a smooth random number from 0 to 1.

    Nearby inputs give nearby outputs, so it makes gentle wandering. Take small steps through the input, such as x * 0.01. noise_detail() changes how bumpy it is.

    Arguments:
        x: the place along a line.
        y: a second direction. The default is 0.0.
        z: a third direction, often used for time. The default is 0.0.

    Returns:
        A number from 0 to 1.

    Example:
        y = f.height * f.noise(f.frame_count * 0.01)

    See also: noise_seed, noise_detail, random
    """
    return canvas_sketch().noise(x, y, z)


def noise_seed(seed: int) -> None:
    """Make noise() repeatable.

    The same seed gives the same values as p5.js's noiseSeed. Any whole number works, and f.keep() records it exactly as you gave it. Without noise_seed(), funground picks one the first time noise() is used, and f.keep() records that.

    Arguments:
        seed: a whole number.

    Example:
        f.noise_seed(1)

    See also: noise, random_seed
    """
    canvas_sketch().noise_seed(seed)


def noise_detail(octaves: int, falloff: float | None = None) -> None:
    """Choose how much detail noise() has.

    Arguments:
        octaves: how many layers of detail to add. The default is 4. It must be 1 or more. Fewer is smoother and faster.
        falloff: how much each layer fades, above 0 and below 1. The default None keeps the current one (0.5 at the start).

    Raises:
        ValueError: octaves is less than 1, or falloff is not between 0 and 1.

    Example:
        f.noise_detail(2)

    See also: noise, noise_seed
    """
    canvas_sketch().noise_detail(octaves, falloff)


def random_gaussian(mean: float = 0.0, sd: float = 1.0) -> float:
    """Return a random number from a bell curve.

    Most values are near the mean. About two thirds are within one sd of it.

    Arguments:
        mean: the middle of the bell. The default is 0.0.
        sd: the spread. The default is 1.0. It cannot be negative.

    Returns:
        A floating-point number.

    Raises:
        ValueError: sd is negative.

    Example:
        f.random_gaussian(200, 30)

    See also: random, random_seed
    """
    return canvas_sketch().random_gaussian(mean, sd)


def random_choice(items):
    """Return one item picked at random.

    It can be repeated with random_seed().

    Arguments:
        items: a list, a tuple or a string. It must not be empty.

    Returns:
        One of the items. For a string, one letter.

    Raises:
        ValueError: there are no items.

    Example:
        f.fill(f.random_choice(["red", "gold", "skyblue"]))

    See also: random, random_seed
    """
    return canvas_sketch().random_choice(items)


def map_range(value: float, start1: float, stop1: float, start2: float, stop2: float, clamp: bool = False) -> float:
    """Re-scale a number from one range to another.

    Arguments:
        value: the number to convert.
        start1, stop1: the range it is in now.
        start2, stop2: the range to convert it to.
        clamp: True keeps the answer inside the second range. The default False lets it go beyond.

    Returns:
        The converted number.

    Raises:
        ValueError: start1 and stop1 are the same.

    Example:
        grey = f.map_range(f.mouse_x, 0, f.width, 0, 255)

    See also: lerp, norm, constrain
    """
    return Sketch.map_range(value, start1, stop1, start2, stop2, clamp)


def lerp(start: float, stop: float, amount: float) -> float:
    """Return the number that is part of the way from start to stop.

    Arguments:
        start: the first number.
        stop: the second number.
        amount: how far to go. 0 gives start, 1 gives stop, and 0.5 is halfway. It may go beyond 0 and 1.

    Returns:
        start + (stop - start) * amount.

    Example:
        print(f.lerp(0, 100, 0.25))

    See also: norm, map_range, lerp_color
    """
    return Sketch.lerp(start, stop, amount)


def norm(value: float, start: float, stop: float) -> float:
    """Return where a number sits between two others, as 0 to 1.

    Arguments:
        value: the number to place.
        start: the number that gives 0.
        stop: the number that gives 1.

    Returns:
        (value - start) / (stop - start).

    Raises:
        ValueError: start and stop are the same.

    Example:
        print(f.norm(25, 0, 100))

    See also: lerp, map_range
    """
    return Sketch.norm(value, start, stop)


def mag(x: float, y: float) -> float:
    """Return the length of the arrow (x, y).

    That is the distance from (0, 0).

    Arguments:
        x, y: the sideways and up-and-down parts.

    Returns:
        The length. mag(3, 4) is 5.

    Example:
        print(f.mag(3, 4))

    See also: distance
    """
    return Sketch.mag(x, y)


def constrain(value: float, low: float, high: float) -> float:
    """Keep a number inside a minimum and a maximum.

    Arguments:
        value: the number to limit.
        low: the smallest answer.
        high: the largest answer.

    Returns:
        low if value is below it, high if value is above it, otherwise value.

    Example:
        x = f.constrain(x, 20, f.width - 20)

    See also: map_range, lerp
    """
    return Sketch.constrain(value, low, high)


def radians(degrees: float) -> float:
    """Convert degrees to radians.

    Use it with math.sin and math.cos. rotate() itself takes degrees.

    Arguments:
        degrees: an angle in degrees.

    Returns:
        The angle in radians.

    Example:
        import math
        y = math.sin(f.radians(45))

    See also: degrees, rotate
    """
    return Sketch.radians(degrees)


def degrees(radians: float) -> float:
    """Convert radians to degrees.

    Use it, for example, to give rotate() an angle from math.atan2.

    Arguments:
        radians: an angle in radians.

    Returns:
        The angle in degrees.

    Example:
        import math
        f.rotate(f.degrees(math.atan2(1, 1)))

    See also: radians, rotate
    """
    return Sketch.degrees(radians)


def distance(x1: float, y1: float, x2: float, y2: float) -> float:
    """Return the straight-line distance between two points.

    Arguments:
        x1, y1: the first point.
        x2, y2: the second point.

    Returns:
        The distance, in the same units as the points.

    Example:
        d = f.distance(x, y, f.mouse_x, f.mouse_y)

    See also: mag, constrain
    """
    return Sketch.distance(x1, y1, x2, y2)



# ---- marks (S-132, contract K1-K3, D-069, D-070)
def mark(path: PathBuilder | str | None = None, *, fill: Color | None = NOT_GIVEN, stroke: Color | None = NOT_GIVEN,
         stroke_width: float | None = None) -> Mark:
    """Make a mark: a drawing kept as a value, to place as often as you like.

    Use it with ``with``: ``with f.mark() as m:`` records the drawing calls in the block instead of drawing them. Each part keeps the fill, stroke and font it was drawn with. The block starts with the current style and no transform, so (0, 0) is the mark's own origin. When it ends, the transform, style and clip are exactly as before, even after an error. Then m.place(x, y) draws the mark. Inside the block you cannot open a layer, make controls, save files, or read or change pixels.

    Give a path instead to make a mark from it at once. It is filled (if closed) and stroked with the current style, changed by fill, stroke and stroke_width when you give them.

    Give the name of an SVG file to make a mark of its shapes, each with the file's own colours. A name that is not a full path is looked for next to the sketch first, as load_svg() does. The mark's origin is the file's top-left corner.

    A mark stays sharp at any size, and stays real shapes and text in a saved PDF or SVG. It cannot be changed once it is made.

    Arguments:
        path: a path made with f.path(), or the name of an .svg file. Leave it out to record a block.
        fill: the fill for a path, as fill() takes it. None means no fill. Left out, it is the current fill.
        stroke: the stroke for a path, as stroke() takes it. None means no stroke. Left out, it is the current stroke.
        stroke_width: the stroke width for a path. Left out (None), it is the current width.

    Returns:
        A Mark, with place(), bounds(), width, height and is_empty.

    Raises:
        TypeError: path is not a path or a file name, or fill, stroke or stroke_width is given without a path.
        ValueError: the file name does not end in ".svg", or the file is not an SVG file.
        FileNotFoundError: the SVG file is not there.

    Example:
        leaf = f.mark(f.path().ellipse(0, 0, 40, 16), fill="olive", stroke=None)
        badge = f.mark("badge.svg")
        with f.mark() as flower:
            f.fill("gold")
            f.circle(0, 0, 24)
        flower.place(100, 100)

    See also: path, load_svg, saved_state, layer
    """
    styled = fill is not NOT_GIVEN or stroke is not NOT_GIVEN or stroke_width is not None
    if path is None:
        if styled:
            raise TypeError("f.mark(): fill, stroke and stroke_width go with a path, as f.mark(path, fill=...). "
                            "In a `with f.mark() as m:` block, call f.fill() and f.stroke() inside it.")
        return Mark()
    if isinstance(path, str):
        if not path.lower().endswith(".svg"):
            raise ValueError(f"f.mark() reads only SVG files, whose names end in \".svg\", not {path!r}")
        if styled:
            raise TypeError("f.mark(): an SVG file keeps its own colours, so fill, stroke and stroke_width do not go "
                            "with it. To recolour it, use place(..., style=\"current\").")
        return mark_from_svg(path, _sketch_folder())
    return mark_from_path(path, fill, stroke, stroke_width)


# ---- play: variations and keep (S-132 parts 3 and 4, contracts E1 and E2, D-071, D-073)
def variations(fn, *, columns: int | None = None, **values) -> list:
    """Draw several versions of a drawing side by side, as a labelled contact sheet.

    Write the drawing as a function with a parameter, then give a list of values to try. variations() calls the function once for each value, and draws each result in its own cell over f.ground.content, with a thin frame and a label such as "gap = 35".

    With one parameter the versions go in one row while every cell stays readable: each picture at least 100 units wide, with its label fitting on one line under it. When they do not fit, they wrap into the grid that makes the cells largest (near-square on a square canvas). columns= chooses the number of columns yourself. With two parameters it tries every pair: one row for each value of the first, one column for each value of the second, so columns= is not allowed.

    Each version is drawn as if on the whole canvas, then made smaller to fit its cell. Every cell is made smaller by the same amount and keeps the canvas's coordinates, so a change of size or position shows. Each cell shows only the canvas's rectangle: drawing outside the canvas is cut off in the sheet, but kept in the returned mark. Each version starts from the style you have when you call variations() and no transform, so one version's fill() cannot change the next. Each version also starts from the same random seed, so the versions differ only in the parameter. background() in the function paints only that version's cell; in the returned mark it is a rectangle the size of the canvas.

    It works in a script, in setup(), and in draw(), where it draws the sheet again every frame.

    Arguments:
        fn: the function that draws one version. It is called with the parameters by name, such as fn(gap=35).
        columns: with one parameter, how many columns the sheet has, a whole number above 0. The default None chooses: one row while it stays readable, otherwise a grid. A parameter of your function cannot be called columns.
        **values: one or two parameters, each with a list of values to try, such as gap=[10, 20, 35].

    Returns:
        A list with one (values, mark) pair for each version, in order. values is a dictionary such as {"gap": 35}; mark is that version as a Mark, without its frame or label, so chosen.place(0, 0) draws it full size.

    Raises:
        TypeError: fn cannot be called, a parameter is given one value instead of a list, or columns is not a whole number.
        ValueError: there is no parameter, more than two, a list is empty, columns is 0 or less or given with two parameters, or the cells do not fit in the canvas.

    Example:
        def study(gap):
            for i in range(12):
                f.circle(f.ground.content.left + i * gap, f.ground.content.cy, 20)

        f.variations(study, gap=[10, 20, 35, 60])

    See also: keep, mark, random_seed
    """
    return _exploring.variations(fn, values, columns)


def keep(note: str = "", *, pdf: bool = False, **settings) -> str:
    """Save this version of your picture in a studio folder, with what made it.

    The files go in a folder called studio next to your sketch file (or in the current folder when there is no file). They are numbered in order, after any already there: 001.png, 002.png and so on. Each kept version has a picture (.png), a copy of your sketch (.py), and a record (.json). The record holds your note, the settings you give, every control's value, the random and noise seeds, the size and margin, the page or frame, the date, the versions of funground and Python, the fonts used and the files read. It also lists what it could not keep, such as fonts installed on this computer. It prints one line saying where it saved. Grid guides from show() are not in the picture.

    In a script it keeps the canvas as drawn so far, at once. In an animated sketch it keeps the next frame that is drawn: the frame being drawn when you call it from draw(), or the next one when you call it from key_pressed() or another event. The picture, the copy and the record are all written when that frame is complete, so the frame number, the controls, the seeds and the fonts in the record are that frame's. If no frame is drawn (after no_loop()), it keeps the frame on the screen.

    The seeds make funground's random() and noise() repeatable: f.random_seed(n) and f.noise_seed(n) with the recorded numbers give the same values again. A recorded seed makes funground's randomness repeatable; it does not make every sketch reproducible. The record's lists of fonts, files read and what it could not keep say what else the picture depends on.

    Arguments:
        note: a few words about this version, such as "gap 35 reads as a rhythm".
        pdf: True also saves a .pdf, a vector drawing that stays sharp when printed. The default is False.
        **settings: any values you want to remember with it, such as gap=35.

    Returns:
        The path of the files without their ending, such as "studio/007". In an animated sketch the files appear there when the frame is complete.

    Raises:
        RuntimeError: it is used inside a ``with f.mark()`` block, or before f.size().
        TypeError: the note is not text.

    Example:
        f.keep("gap 35 reads as a rhythm", gap=35)
        f.keep("for printing", pdf=True)

    See also: variations, save, random_seed
    """
    return _exploring.keep(note, pdf, settings, inspect.currentframe().f_back)
