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

from ._core import (
    background,
    circle,
    constrain,
    distance,
    ellipse,
    fill,
    key_down,
    line,
    no_fill,
    no_stroke,
    point,
    random,
    random_seed,
    rect,
    run,
    size,
    stop,
    stroke,
    stroke_width,
    text,
    text_size,
)
from . import _core

__version__ = "0.6.0.dev0"

_LIVE_NAMES = {
    "width",
    "height",
    "mouse_x",
    "mouse_y",
    "mouse_pressed",
    "frame_count",
    "delta_time",
}

__all__ = [
    "background",
    "circle",
    "constrain",
    "distance",
    "ellipse",
    "fill",
    "key_down",
    "line",
    "no_fill",
    "no_stroke",
    "point",
    "random",
    "random_seed",
    "rect",
    "run",
    "size",
    "stop",
    "stroke",
    "stroke_width",
    "text",
    "text_size",
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
    if name in _LIVE_NAMES:
        return _core.live_value(name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
