"""funground's own colour type.

Learners keep writing ``"tomato"``, ``(255, 99, 71)`` or ``"#FF6347"`` (contract row S1);
funground parses those once into an RGBA ``Color`` so renderers never see backend types.
"""
from __future__ import annotations

import colorsys
from dataclasses import dataclass
from typing import Any

from ._colornames import NAMED_COLORS

ColorLike = Any  # str | tuple[int, ...] | list[int] | Color


@dataclass(frozen=True, slots=True)
class Color:
    """A colour, as red, green, blue and alpha numbers.

    You get one from f.color(), f.hsb(), f.hsl(), f.lerp_color() and f.get(x, y). You can give it to
    fill(), stroke(), background() and every other command that takes a colour. A colour cannot be
    changed.

    Read its parts as c.red, c.green, c.blue and c.alpha (each a whole number from 0 to 255), c.hue (0 to
    360) and c.saturation, c.brightness and c.lightness (each 0 to 100). The short names c.r, c.g, c.b and
    c.a are the same as red, green, blue and alpha.

    Example:
        c = f.color("tomato")
        print(c.red, c.green, c.blue)    # 255 99 71
        f.fill(c)

    See also: color, hsb, hsl, lerp_color
    """
    r: int
    g: int
    b: int
    a: int = 255

    def __post_init__(self) -> None:
        for name in ("r", "g", "b", "a"):
            v = getattr(self, name)
            if not isinstance(v, int) or not 0 <= v <= 255:
                raise ValueError(f"colour component {name}={v!r} must be an integer from 0 to 255")

    @property
    def rgb(self) -> tuple[int, int, int]:
        """The red, green and blue parts together.

        Returns:
            a tuple (red, green, blue), each a whole number from 0 to 255.

        Example:
            r, g, b = f.color("tomato").rgb

        See also: rgba
        """
        return (self.r, self.g, self.b)

    @property
    def rgba(self) -> tuple[int, int, int, int]:
        """The red, green, blue and alpha parts together.

        Returns:
            a tuple (red, green, blue, alpha), each a whole number from 0 to 255.

        Example:
            print(f.color("tomato").rgba)    # (255, 99, 71, 255)

        See also: rgb
        """
        return (self.r, self.g, self.b, self.a)

    # ---- readable components (S-044, contract S12). RGB and alpha 0-255; hue 0-360;
    # saturation and brightness are HSB, lightness is HSL, all 0-100.
    @property
    def red(self) -> int:
        """How much red the colour has.

        Returns:
            a whole number from 0 to 255.

        Example:
            print(f.color("tomato").red)

        See also: green, blue
        """
        return self.r

    @property
    def green(self) -> int:
        """How much green the colour has.

        Returns:
            a whole number from 0 to 255.

        Example:
            print(f.color("tomato").green)

        See also: red, blue
        """
        return self.g

    @property
    def blue(self) -> int:
        """How much blue the colour has.

        Returns:
            a whole number from 0 to 255.

        Example:
            print(f.color("tomato").blue)

        See also: red, green
        """
        return self.b

    @property
    def alpha(self) -> int:
        """How solid the colour is.

        Returns:
            a whole number from 0 (see-through) to 255 (solid).

        Example:
            print(f.color(255, 0, 0, 128).alpha)    # 128

        See also: rgba
        """
        return self.a

    @property
    def hue(self) -> float:
        """The hue of the colour: its place on the colour wheel.

        Returns:
            a number from 0 to 360. Red is 0, green is 120 and blue is 240.

        Example:
            print(f.color("blue").hue)    # 240.0

        See also: saturation, brightness, lightness
        """
        h, _, _ = colorsys.rgb_to_hsv(self.r / 255, self.g / 255, self.b / 255)
        return h * 360

    @property
    def saturation(self) -> float:
        """How strong the colour is, in the HSB way of measuring.

        Returns:
            a number from 0 (grey) to 100 (the strongest colour).

        Example:
            print(f.color("red").saturation)    # 100.0

        See also: hue, brightness
        """
        _, s, _ = colorsys.rgb_to_hsv(self.r / 255, self.g / 255, self.b / 255)
        return s * 100

    @property
    def brightness(self) -> float:
        """How bright the colour is, in the HSB way of measuring.

        Returns:
            a number from 0 (black) to 100 (full brightness).

        Example:
            print(f.color("red").brightness)    # 100.0

        See also: hue, saturation, lightness
        """
        _, _, v = colorsys.rgb_to_hsv(self.r / 255, self.g / 255, self.b / 255)
        return v * 100

    @property
    def lightness(self) -> float:
        """How light the colour is, in the HSL way of measuring.

        Returns:
            a number from 0 (black) to 100 (white). A pure colour such as red is 50.

        Example:
            print(f.color("red").lightness)    # 50.0

        See also: brightness, hue
        """
        _, l, _ = colorsys.rgb_to_hls(self.r / 255, self.g / 255, self.b / 255)
        return l * 100

    @classmethod
    def from_hsb(cls, h: float, s: float, b: float, a: float = 255) -> "Color":
        """Make a colour from hue, saturation and brightness.

        f.hsb() does the same, and is the one to use in a sketch.

        Arguments:
            h: the hue in degrees. It wraps round, so 370 is the same as 10.
            s: the saturation, from 0 to 100. Numbers outside are cut off.
            b: the brightness, from 0 to 100. Numbers outside are cut off.
            a: the alpha, from 0 to 255. It is 255 at first.

        Returns:
            a new Color.

        Raises:
            ValueError: if a value is not a number.

        See also: from_hsl, hue
        """
        r, g, bl = colorsys.hsv_to_rgb(*_hue_and_percents(h, s, b))
        return cls(round(r * 255), round(g * 255), round(bl * 255), _component(a))

    @classmethod
    def from_hsl(cls, h: float, s: float, l: float, a: float = 255) -> "Color":
        """Make a colour from hue, saturation and lightness.

        f.hsl() does the same, and is the one to use in a sketch.

        Arguments:
            h: the hue in degrees. It wraps round, so 370 is the same as 10.
            s: the saturation, from 0 to 100. Numbers outside are cut off.
            l: the lightness, from 0 to 100. Numbers outside are cut off.
            a: the alpha, from 0 to 255. It is 255 at first.

        Returns:
            a new Color.

        Raises:
            ValueError: if a value is not a number.

        See also: from_hsb, lightness
        """
        hh, ss, ll = _hue_and_percents(h, s, l)
        r, g, b = colorsys.hls_to_rgb(hh, ll, ss)
        return cls(round(r * 255), round(g * 255), round(b * 255), _component(a))

    def lerp(self, other: "Color", amount: float) -> "Color":
        """Make a colour that is part of the way from this colour to another.

        f.lerp_color() does the same. It mixes red, green, blue and alpha.

        Arguments:
            other: the Color to mix towards.
            amount: how much of the way to go, from 0 (this colour) to 1 (the other). Numbers outside are cut off.

        Returns:
            a new Color.

        Example:
            mid = f.color("red").lerp(f.color("blue"), 0.5)

        See also: from_hsb
        """
        t = max(0.0, min(1.0, float(amount)))
        return Color(*(round(x + (y - x) * t) for x, y in zip(self.rgba, other.rgba)))

    @classmethod
    def parse(cls, value: ColorLike) -> "Color":
        """Read a colour from any of the forms that funground accepts.

        Every command that takes a colour uses it. You do not need to call it.

        Arguments:
            value: a name like "tomato", a hex string like "#FF6347", a tuple of 2, 3 or 4 numbers, one grey number, or another Color.

        Returns:
            a Color. If you give a Color, you get the same one back.

        Raises:
            ValueError: if the colour is not understood, or a part is not from 0 to 255.
            TypeError: if the value is True or False.

        See also: from_hsb, from_hsl
        """
        if isinstance(value, Color):
            return value
        if isinstance(value, str):
            return cls._parse_str(value)
        if isinstance(value, bool):
            raise TypeError(f"{value!r} is not a colour: True and False are not numbers here")
        if isinstance(value, (int, float)):
            grey = _component(value)         # one number is a grey, as in p5 (S16)
            return cls(grey, grey, grey)
        if all(hasattr(value, c) for c in "rgb"):
            # Any object exposing r/g/b[/a] - covers pygame.Color without importing pygame.
            return cls(
                _component(value.r), _component(value.g), _component(value.b),
                _component(getattr(value, "a", 255)),
            )
        if isinstance(value, (tuple, list)):
            if len(value) == 2:              # grey and alpha (S16)
                grey, alpha = (_component(c) for c in value)
                return cls(grey, grey, grey, alpha)
            if len(value) == 3:
                return cls(*(_component(c) for c in value))
            if len(value) == 4:
                return cls(*(_component(c) for c in value))
            raise ValueError(
                f"a colour tuple needs 2, 3 or 4 numbers (grey, alpha or red, green, blue[, alpha]), got {len(value)}"
            )
        raise ValueError(
            f"{value!r} is not a colour. Use a name like 'tomato', a tuple like (255, 99, 71) "
            "or a hex string like '#FF6347'."
        )

    @classmethod
    def _parse_str(cls, text: str) -> "Color":
        key = text.strip().lower().replace(" ", "")
        if key in NAMED_COLORS:
            return cls(*NAMED_COLORS[key])
        digits = None
        if key.startswith("#"):
            digits = key[1:]
        elif key.startswith("0x"):
            digits = key[2:]
        if digits is not None and len(digits) in (6, 8) and all(c in "0123456789abcdef" for c in digits):
            parts = [int(digits[i : i + 2], 16) for i in range(0, len(digits), 2)]
            return cls(*parts)
        raise ValueError(
            f"unknown colour {text!r}. Use a name like 'tomato', a tuple like (255, 99, 71) "
            "or a hex string like '#FF6347'."
        )


def _component(c: object) -> int:
    """v0.5 behaviour (pygame-ce): a number is truncated toward zero, then must be 0..255.

    So 211.8 -> 211 and -0.5 -> 0 are accepted, as v0.5 accepted them; NaN is not.
    Computed colours such as f.map_range(...) results therefore just work.
    """
    if isinstance(c, bool) or not isinstance(c, (int, float)):
        raise ValueError(f"colour component {c!r} must be a number from 0 to 255")
    if isinstance(c, float):
        if c != c:
            raise ValueError("colour component nan must be a number from 0 to 255")
        c = int(c)
    return c


def _hue_and_percents(h: float, s: float, v: float) -> tuple[float, float, float]:
    """Hue wraps (370 is 10); the two percentages are clamped to 0..100 (S-044)."""
    for value, name in ((h, "hue"), (s, "saturation"), (v, "brightness/lightness")):
        if isinstance(value, bool) or not isinstance(value, (int, float)) or value != value:
            raise ValueError(f"colour {name} {value!r} must be a number")
    return (h % 360) / 360, max(0.0, min(100.0, s)) / 100, max(0.0, min(100.0, v)) / 100


WHITE = Color(255, 255, 255)
BLACK = Color(0, 0, 0)


# ---- colour mode (S-082, contract S15) -------------------------------------------------
COLOR_MODES = ("rgb", "hsb", "hsl")
# Ranges per mode, in COLOR_MODES order: (first, second, third, alpha). p5's defaults.
DEFAULT_COLOR_RANGES: tuple[tuple[float, float, float, float], ...] = (
    (255, 255, 255, 255),
    (360, 100, 100, 1),
    (360, 100, 100, 1),
)


def parse_in_mode(value: ColorLike, mode: str = "rgb", ranges=DEFAULT_COLOR_RANGES) -> Color:
    """Read *value* as a colour under the colour mode (S15, S16). Only numbers change: a number,
    or a tuple or list of 2, 3 or 4 numbers. Names, hex, colour objects and the like go to
    Color.parse. The default mode is S1 exactly."""
    if isinstance(value, bool):
        raise TypeError(f"{value!r} is not a colour: True and False are not numbers here")
    if mode == "rgb" and ranges[0] == DEFAULT_COLOR_RANGES[0]:
        return Color.parse(value)
    if isinstance(value, (int, float)):
        parts = (value,)
    elif isinstance(value, (tuple, list)) and len(value) in (2, 3, 4):
        parts = tuple(value)
    else:
        return Color.parse(value)                # names, hex, objects; also raises the usual messages
    for part in parts:
        if isinstance(part, bool) or not isinstance(part, (int, float)) or part != part:
            raise ValueError(f"colour component {part!r} must be a number")
    max1, max2, max3, max_a = ranges[COLOR_MODES.index(mode)]
    if len(parts) <= 2:                          # grey, or grey and alpha: on the third range (S16)
        one, two, three = 0, 0, parts[0]
        alpha = parts[1] if len(parts) == 2 else max_a
        if mode == "rgb":
            one = two = three
            max1 = max2 = max3
    else:
        one, two, three = parts[:3]
        alpha = parts[3] if len(parts) == 4 else max_a
    alpha255 = round(max(0.0, min(1.0, alpha / max_a)) * 255)
    if mode == "rgb":
        r, g, b = (round(max(0.0, min(1.0, v / m)) * 255) for v, m in ((one, max1), (two, max2), (three, max3)))
        return Color(r, g, b, alpha255)
    hue = (one % max1) / max1 * 360
    make = Color.from_hsb if mode == "hsb" else Color.from_hsl
    return make(hue, two / max2 * 100, three / max3 * 100, alpha255)
