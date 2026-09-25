"""A tiny teaching-friendly visual programming wrapper around pygame-ce.

Typical use::

    import playground as p

    x = 50

    def setup():
        p.size(640, 400)

    def draw():
        global x
        p.background("white")
        p.circle(x, p.height / 2, 40)
        x += 2

    p.run()
"""

from . import api as _api
from .api import (
    background,
    begin_shape,
    circle,
    clip,
    constrain,
    curve_vertex,
    degrees,
    distance,
    draw_path,
    ellipse,
    end_shape,
    fill,
    key_down,
    line,
    no_fill,
    no_stroke,
    path,
    point,
    pop,
    push,
    radians,
    random,
    random_seed,
    rect,
    rotate,
    run,
    save,
    saved_state,
    scale,
    size,
    stop,
    stroke,
    stroke_width,
    text,
    text_size,
    text_width,
    translate,
    vertex,
)

__version__ = "0.7.0.dev0"

__all__ = [
    "background",
    "begin_shape",
    "circle",
    "clip",
    "constrain",
    "curve_vertex",
    "degrees",
    "distance",
    "draw_path",
    "ellipse",
    "end_shape",
    "fill",
    "key_down",
    "line",
    "no_fill",
    "no_stroke",
    "path",
    "point",
    "pop",
    "push",
    "radians",
    "random",
    "random_seed",
    "rect",
    "rotate",
    "run",
    "save",
    "saved_state",
    "scale",
    "size",
    "stop",
    "stroke",
    "stroke_width",
    "text",
    "text_size",
    "text_width",
    "translate",
    "vertex",
    "width",
    "height",
    "mouse_x",
    "mouse_y",
    "mouse_pressed",
    "frame_count",
    "delta_time",
]


def __getattr__(name: str):
    """Expose live values without copying stale integers into this module."""
    if name in _api.LIVE_NAMES:
        return _api.live_value(name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
