"""Controls: sliders, checkboxes and buttons (story S-101, contract U1, D-047).

This module is plain Python. It never imports pygame. It holds three things:

* the control objects a sketch gets back from `f.create_slider()` and friends;
* `ControlPanel`, the list of controls a sketch owns, with the panel's layout and the
  mouse rules (press, drag, release) in *panel coordinates*;
* `panel_ops()`, which turns the panel into draw ops for a renderer.

The panel is chrome. It sits below the canvas, it is drawn by its own renderer, and its ops
never join the canvas's frame, so they are never in `width`/`height`, saves, `get`, pixels
or the IR snapshots. A platform with a window routes the mouse to `ControlPanel` and shows
the finished panel pixels; a platform with no window ignores the panel and the controls
simply keep their values.
"""
from __future__ import annotations

import math

from . import ir
from .color import Color
from .state import GraphicsState

ROW_HEIGHT = 30            # logical pixels for each control
TEXT_SIZE = 14
PAD = 8                    # space at the left and right edges
BOX = 16                   # the checkbox's square
BUTTON_PAD = 12            # space either side of a button's label
TRACK_MIN = 24             # the slider track is never shorter than this

_UNSET = object()

BACKGROUND = Color(238, 238, 238)
EDGE = Color(200, 200, 200)
INK = Color(40, 40, 40)
TRACK = Color(200, 200, 200)
ACCENT = Color(60, 120, 200)
BOX_FILL = Color(255, 255, 255)
BUTTON_FILL = Color(250, 250, 250)
BUTTON_DOWN = Color(205, 215, 230)


def _is_number(v: object) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _number(v: object, what: str) -> float | int:
    if not _is_number(v):
        raise TypeError(f"{what} must be a number, not {type(v).__name__}")
    if isinstance(v, float) and not math.isfinite(v):
        raise ValueError(f"{what} must be a finite number, not {v!r}")
    return v


class Control:
    """What a slider, a checkbox and a button share: a label.

    You do not make a Control yourself. Use f.create_slider(), f.create_checkbox() and f.create_button().
    They sit in a panel below the canvas, in the order you made them. Make them in setup() and read them
    in draw().

    See also: Slider, Checkbox, Button
    """

    def __init__(self, label: str | None) -> None:
        if label is not None and not isinstance(label, str):
            raise TypeError(f"a control's label must be text, not {type(label).__name__}")
        self._label = label or ""
        self._panel: ControlPanel | None = None
        self._visible = True

    @property
    def label(self) -> str:
        """The text shown beside the control.

        Returns:
            the label, or "" when it has none.

        Example:
            box = f.create_checkbox("Show grid")
            print(box.label)    # Show grid

        See also: create_slider, create_checkbox, create_button
        """
        return self._label

    def visible(self, flag=_UNSET):
        """Read whether the control is shown, or hide or show it.

        A hidden control is not drawn and cannot be pressed, dragged or clicked. Its space in the panel stays
        blank, so the panel keeps its height and nothing moves when you show it again. It keeps its value.
        value(), checked() and clicked() still work while it is hidden. You can call visible() in draw().

        Arguments:
            flag: True to show the control, False to hide it. Leave it out to read.

        Returns:
            True or False when you leave flag out. None when you set it.

        Example:
            size = f.create_slider(10, 100, 50)
            size.visible(False)
            print(size.visible())    # False

        See also: value, checked, create_slider
        """
        if flag is _UNSET:
            return self._visible
        flag = bool(flag)
        if flag != self._visible:
            self._visible = flag
            if not flag and self._panel is not None:
                self._panel._let_go(self)
            self._touch()
        return None

    def _touch(self) -> None:
        """Tell the panel something changed, so it is drawn again."""
        if self._panel is not None:
            self._panel.version += 1


class Slider(Control):
    """A control that holds a number between a low and a high end. You drag it in the panel below the canvas.

    You get one from f.create_slider(low, high, value, step, label). Make it in setup(). In draw(), read
    it with slider.value(). It starts at value, or at low if you give none. If you give a step, the value
    moves in jumps of that size from low. Whole numbers in give whole numbers out, when low and step are
    both whole.

    Example:
        size_slider = f.create_slider(10, 200, 50, label="size")

        def draw():
            f.circle(200, 200, size_slider.value())

    See also: create_slider, value, Checkbox, Button
    """

    def __init__(self, low, high, value=None, step=None, label=None) -> None:
        super().__init__(label)
        _number(low, "a slider's low value")
        _number(high, "a slider's high value")
        if low >= high:
            raise ValueError(f"a slider needs low below high, not low={low!r}, high={high!r}")
        if step is not None:
            _number(step, "a slider's step")
            if step <= 0:
                raise ValueError(f"a slider's step must be more than 0, not {step!r}")
        self._low, self._high, self._step = low, high, step
        # Whole numbers in, whole numbers out: only when every value the slider can have is whole.
        self._whole = isinstance(low, int) and isinstance(step, int)
        self._value = low
        self._set(low if value is None else _number(value, "a slider's value"))

    @property
    def low(self):
        """The smallest value the slider can have.

        Returns:
            the low end, as given.

        See also: high, step
        """
        return self._low

    @property
    def high(self):
        """The largest value the slider can have.

        Returns:
            the high end, as given.

        See also: low, step
        """
        return self._high

    @property
    def step(self):
        """The size of each jump of the slider.

        Returns:
            the step as given, or None when the slider moves smoothly.

        See also: low, high
        """
        return self._step

    def _set(self, v) -> None:
        v = min(max(v, self._low), self._high)
        if self._step is not None:
            v = self._low + round((v - self._low) / self._step) * self._step
            v = min(max(v, self._low), self._high)
            if not self._whole:
                v = round(v, 12)             # 0.1 + 0.2 style noise never reaches the learner
        if self._whole:
            v = int(v)
        elif isinstance(v, int):
            v = float(v)
        if v != self._value:
            self._value = v
            self._touch()

    def value(self, v=_UNSET):
        """Read the slider's number, or set it.

        With no argument it reads the value. With a number it sets the value, which is kept between low and
        high and rounded to the step. It changes in the panel too.

        Arguments:
            v: the new value. Leave it out to read the value.

        Returns:
            the value when you leave v out. None when you set it.

        Raises:
            TypeError: if v is not a number.
            ValueError: if v is infinity or nan.

        Example:
            s = f.create_slider(0, 1, 0.5)
            print(s.value())    # 0.5
            s.value(0.8)

        See also: text, low, high
        """
        if v is _UNSET:
            return self._value
        self._set(_number(v, "a slider's value"))
        return None

    def text(self) -> str:
        """The value as the panel shows it.

        Returns:
            the value as text. A step of 0.1 gives one decimal place.

        Example:
            s = f.create_slider(0, 1, 0.5, 0.1)
            print(s.text())    # 0.5

        See also: value
        """
        return _format(self._value, self._step)


def _format(v, step) -> str:
    if isinstance(v, int):
        return str(v)
    decimals = 2
    if step is not None:
        decimals = 0
        while decimals < 6 and abs(round(step, decimals) - step) > 1e-9:
            decimals += 1
    text = f"{v:.{decimals}f}"
    if "." in text and step is None:
        text = text.rstrip("0").rstrip(".")
    return text


class Checkbox(Control):
    """A box that is ticked or not. You click it in the panel below the canvas.

    You get one from f.create_checkbox(label, checked). Make it in setup(). In draw(), read it with
    box.checked().

    Example:
        grid = f.create_checkbox("Show grid", True)

        def draw():
            if grid.checked():
                f.line(0, 200, 400, 200)

    See also: create_checkbox, checked, Slider, Button
    """

    def __init__(self, label, checked=False) -> None:
        super().__init__(label)
        self._checked = bool(checked)

    def checked(self, b=_UNSET):
        """Read whether the box is ticked, or tick or untick it.

        Arguments:
            b: True to tick it, False to untick it. Leave it out to read.

        Returns:
            True or False when you leave b out. None when you set it.

        Example:
            box = f.create_checkbox("Fill", True)
            if box.checked():
                box.checked(False)

        See also: create_checkbox
        """
        if b is _UNSET:
            return self._checked
        b = bool(b)
        if b != self._checked:
            self._checked = b
            self._touch()
        return None


class Button(Control):
    """A button that you click in the panel below the canvas.

    You get one from f.create_button(label). Make it in setup(). In draw(), ask button.clicked(). It is True
    once for each click.

    Example:
        again = f.create_button("Again")

        def draw():
            if again.clicked():
                f.background("white")

    See also: create_button, clicked, Slider, Checkbox
    """

    def __init__(self, label) -> None:
        super().__init__(label)
        self._clicks = False
        self._down = False

    def clicked(self) -> bool:
        """Whether the button was clicked since you last asked.

        It is True once for each click. Asking again straight away gives False.

        Returns:
            True if there was a click since the last time you asked, otherwise False.

        Example:
            if again.clicked():
                f.background("white")

        See also: create_button
        """
        was, self._clicks = self._clicks, False
        return was


# ---------------------------------------------------------------- the panel

class ControlPanel:
    """The controls of one sketch, in the order they were made, and the panel they sit in.

    Coordinates here are *panel coordinates* in logical pixels: x across, y down from the
    panel's top edge. `version` goes up whenever the panel needs to be drawn again.
    """

    def __init__(self) -> None:
        self.controls: list[Control] = []
        self.version = 0
        self._drag: Control | None = None      # the control a pressed mouse is holding
        self._width = -1
        self._rects: list[dict] = []

    def add(self, control: Control) -> Control:
        control._panel = self
        self.controls.append(control)
        self._width = -1
        self.version += 1
        return control

    def clear(self) -> None:
        for c in self.controls:
            c._panel = None
        self.controls.clear()
        self._drag = None
        self._width = -1
        self.version += 1

    def __len__(self) -> int:
        return len(self.controls)

    def __bool__(self) -> bool:
        return bool(self.controls)

    @property
    def height(self) -> int:
        """The panel's height in logical pixels (0 with no controls)."""
        return ROW_HEIGHT * len(self.controls)

    # ---- layout
    def layout(self, width: int) -> list[dict]:
        """One dict of rectangles per control, for a panel *width* logical pixels wide."""
        if width == self._width:
            return self._rects
        from .typography import default_font, text_width

        font = default_font()

        def tw(s: str) -> float:
            return text_width(s, TEXT_SIZE, font)

        sliders = [c for c in self.controls if isinstance(c, Slider)]
        label_col = max((tw(s.label) for s in sliders if s.label), default=0.0)
        label_col = label_col + PAD if label_col else 0.0
        value_col = max((tw(_format(v, s.step)) for s in sliders for v in (s.low, s.high)), default=0.0)
        rects = []
        for i, c in enumerate(self.controls):
            top = i * ROW_HEIGHT
            mid = top + ROW_HEIGHT / 2
            r: dict = {"top": top, "mid": mid}
            if isinstance(c, Slider):
                x0 = PAD + label_col
                x1 = width - PAD - value_col - PAD
                if x1 - x0 < TRACK_MIN:
                    x1 = x0 + TRACK_MIN
                r.update(x0=x0, x1=x1, label_x=PAD, value_x=width - PAD)
            elif isinstance(c, Checkbox):
                r.update(box=(PAD, mid - BOX / 2, BOX, BOX), label_x=PAD + BOX + 8,
                         hit_x1=PAD + BOX + 8 + tw(c.label) + PAD)
            else:
                w = tw(c.label) + 2 * BUTTON_PAD
                r.update(button=(PAD, top + 4, w, ROW_HEIGHT - 8), label_x=PAD + BUTTON_PAD)
            rects.append(r)
        self._rects, self._width = rects, width
        return rects

    # ---- the mouse, in panel coordinates (the platform calls these; width is the canvas's)
    def press(self, x: float, y: float, width: int) -> None:
        """The left button went down in the panel."""
        row = int(y // ROW_HEIGHT)
        if not 0 <= row < len(self.controls):
            return
        c, r = self.controls[row], self.layout(width)[row]
        if not c._visible:
            return
        if isinstance(c, Slider):
            if r["x0"] - 8 <= x <= r["x1"] + 8:
                self._drag = c
                self._slide(c, r, x)
        elif isinstance(c, Checkbox):
            if x <= r["hit_x1"]:
                c.checked(not c.checked())
        else:
            bx, by, bw, bh = r["button"]
            if bx <= x <= bx + bw and by <= y <= by + bh:
                self._drag = c
                c._down = True
                self.version += 1

    def drag(self, x: float, y: float, width: int) -> None:
        """The mouse moved with the left button held, after a press in the panel."""
        c = self._drag
        if isinstance(c, Slider):
            self._slide(c, self.layout(width)[self.controls.index(c)], x)

    def release(self, x: float, y: float, width: int) -> None:
        """The left button came up."""
        c, self._drag = self._drag, None
        if isinstance(c, Button):
            c._down = False
            row = self.controls.index(c) if c in self.controls else -1
            if row >= 0:
                bx, by, bw, bh = self.layout(width)[row]["button"]
                if bx <= x <= bx + bw and by <= y <= by + bh:
                    c._clicks = True
            self.version += 1

    def _let_go(self, c: Control) -> None:
        """A control was hidden: a drag it was holding ends, and a pressed button pops up."""
        if self._drag is c:
            self._drag = None
        if isinstance(c, Button):
            c._down = False

    @property
    def holding(self) -> bool:
        """True while a press that began in the panel is still held."""
        return self._drag is not None

    def _slide(self, s: Slider, r: dict, x: float) -> None:
        t = (x - r["x0"]) / (r["x1"] - r["x0"])
        s.value(s.low + min(max(t, 0.0), 1.0) * (s.high - s.low))


# ---------------------------------------------------------------- drawing

def panel_ops(panel: ControlPanel, width: int) -> list[ir.Op]:
    """The draw ops for the panel, for a surface *width* x `panel.height` logical pixels."""
    style = GraphicsState(fill=INK, stroke=None, stroke_width=0, text_size=TEXT_SIZE)
    plain = style.with_(fill=BOX_FILL, stroke=EDGE, stroke_width=1)

    def box(x, y, w, h, fill, stroke=None):
        st = style.with_(fill=fill, stroke=stroke, stroke_width=1 if stroke else 0)
        return ir.Rect(x, y, w, h, st)

    def label(text, x, mid):
        top = mid - TEXT_SIZE * 0.62          # a line's box is about 1.25 x the size, centred on mid
        return ir.Text(text, x, top, INK, style)

    ops: list[ir.Op] = [ir.Clear(BACKGROUND), ir.Line(0, 0.5, width, 0.5, plain)]
    from .typography import default_font, text_width

    font = default_font()
    for c, r in zip(panel.controls, panel.layout(width)):
        if not c._visible:
            continue                          # its row stays blank
        mid = r["mid"]
        if isinstance(c, Slider):
            if c.label:
                ops.append(label(c.label, r["label_x"], mid))
            x0, x1 = r["x0"], r["x1"]
            t = (c.value() - c.low) / (c.high - c.low)
            ops.append(box(x0, mid - 2, x1 - x0, 4, TRACK))
            ops.append(box(x0, mid - 2, (x1 - x0) * t, 4, ACCENT))
            ops.append(ir.Circle(x0 + (x1 - x0) * t, mid, 14, plain.with_(fill=BOX_FILL, stroke=ACCENT, stroke_width=2)))
            shown = c.text()
            ops.append(label(shown, r["value_x"] - text_width(shown, TEXT_SIZE, font), mid))
        elif isinstance(c, Checkbox):
            bx, by, bw, bh = r["box"]
            ops.append(box(bx, by, bw, bh, BOX_FILL, EDGE))
            if c.checked():
                ops.append(box(bx + 4, by + 4, bw - 8, bh - 8, ACCENT))
            ops.append(label(c.label, r["label_x"], mid))
        else:
            bx, by, bw, bh = r["button"]
            ops.append(ir.Rect(bx, by, bw, bh, style.with_(fill=BUTTON_DOWN if c._down else BUTTON_FILL,
                                                           stroke=EDGE, stroke_width=1), (4, 4, 4, 4)))
            ops.append(label(c.label, r["label_x"], mid))
    return ops
