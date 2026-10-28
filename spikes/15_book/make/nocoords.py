"""Spike-only stand-in for proposal D-121 (drawing without coordinates).

install() wraps f.circle, f.square, f.rect, f.ellipse and f.triangle so that a call with no position works:

    f.circle()                       centre of the canvas, size = a third of the smaller side
    f.circle(size=80, at="random")   a random place where the whole shape stays inside the canvas
    f.rect(size=200, height=100)     width = size

A call with the full positional set passes straight through. A mix is a TypeError.
This is a monkeypatch, allowed inside a spike. No product code changes.
"""
import funground as f

_ORIGINAL = {}
_CANVAS = None          # (w, h) override, for drawing a 600 x 600 panel while the page is a different size


class canvas:
    """Context manager: tell the shim which canvas the panel is drawn for."""
    def __init__(self, w, h):
        self.size = (w, h)

    def __enter__(self):
        global _CANVAS
        self.before, _CANVAS = _CANVAS, self.size

    def __exit__(self, *exc):
        global _CANVAS
        _CANVAS = self.before


def _canvas():
    return _CANVAS or (f.width, f.height)


def _place(w, h, at, stroke):
    cw, ch = _canvas()
    if at == "center":
        return cw / 2, ch / 2
    if at == "random":
        if w + stroke >= cw or h + stroke >= ch:
            return cw / 2, ch / 2
        mx, my = (w + stroke) / 2, (h + stroke) / 2
        return f.random(mx, cw - mx), f.random(my, ch - my)
    raise ValueError(f'at= must be "center" or "random", not {at!r}')


def _wrap(name, nargs, shape_size):
    original = _ORIGINAL[name] = getattr(f, name)

    def call(*args, size=None, at=None, height=None, **rest):
        if args:
            if size is not None or at is not None or height is not None:
                raise TypeError(f"f.{name}() takes either no position, or {nargs} numbers")
            return original(*args, **rest)
        cw, ch = _canvas()
        s = min(cw, ch) / 3 if size is None else size
        w, h = shape_size(s, height)
        x, y = _place(w, h, at or "center", 0)
        f.push()
        f.rect_mode("center")
        f.ellipse_mode("center")
        if name == "circle":
            original(x, y, s)
        elif name == "square":
            original(x, y, s)
        elif name == "rect":
            original(x, y, w, h)
        elif name == "ellipse":
            original(x, y, w, h)
        else:                                   # equilateral triangle, point up, s wide
            th = s * 3 ** 0.5 / 2
            original(x - s / 2, y + th / 2, x + s / 2, y + th / 2, x, y - th / 2)
        f.pop()
    call.__name__ = name
    setattr(f, name, call)


def install():
    if _ORIGINAL:
        return
    same = lambda s, h: (s, s)
    _wrap("circle", 3, same)
    _wrap("square", 3, same)
    _wrap("rect", 4, lambda s, h: (s, s if h is None else h))
    _wrap("ellipse", 4, lambda s, h: (s, s if h is None else h))
    _wrap("triangle", 6, lambda s, h: (s, s * 3 ** 0.5 / 2))
