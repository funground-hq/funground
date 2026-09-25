"""Playground's own colour type.

Learners keep writing ``"tomato"``, ``(255, 99, 71)`` or ``"#FF6347"`` (contract row S1);
Playground parses those once into an RGBA ``Color`` so renderers never see backend types.
"""
from __future__ import annotations

import colorsys
from dataclasses import dataclass
from typing import Any

from ._colornames import NAMED_COLORS

ColorLike = Any  # str | tuple[int, ...] | list[int] | Color


@dataclass(frozen=True, slots=True)
class Color:
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
        return (self.r, self.g, self.b)

    @property
    def rgba(self) -> tuple[int, int, int, int]:
        return (self.r, self.g, self.b, self.a)

    # ---- readable components (S-044, contract S12). RGB and alpha 0-255; hue 0-360;
    # saturation and brightness are HSB, lightness is HSL, all 0-100.
    @property
    def red(self) -> int:
        return self.r

    @property
    def green(self) -> int:
        return self.g

    @property
    def blue(self) -> int:
        return self.b

    @property
    def alpha(self) -> int:
        return self.a

    @property
    def hue(self) -> float:
        h, _, _ = colorsys.rgb_to_hsv(self.r / 255, self.g / 255, self.b / 255)
        return h * 360

    @property
    def saturation(self) -> float:
        _, s, _ = colorsys.rgb_to_hsv(self.r / 255, self.g / 255, self.b / 255)
        return s * 100

    @property
    def brightness(self) -> float:
        _, _, v = colorsys.rgb_to_hsv(self.r / 255, self.g / 255, self.b / 255)
        return v * 100

    @property
    def lightness(self) -> float:
        _, l, _ = colorsys.rgb_to_hls(self.r / 255, self.g / 255, self.b / 255)
        return l * 100

    @classmethod
    def from_hsb(cls, h: float, s: float, b: float, a: float = 255) -> "Color":
        r, g, bl = colorsys.hsv_to_rgb(*_hue_and_percents(h, s, b))
        return cls(round(r * 255), round(g * 255), round(bl * 255), _component(a))

    @classmethod
    def from_hsl(cls, h: float, s: float, l: float, a: float = 255) -> "Color":
        hh, ss, ll = _hue_and_percents(h, s, l)
        r, g, b = colorsys.hls_to_rgb(hh, ll, ss)
        return cls(round(r * 255), round(g * 255), round(b * 255), _component(a))

    def lerp(self, other: "Color", amount: float) -> "Color":
        t = max(0.0, min(1.0, float(amount)))
        return Color(*(round(x + (y - x) * t) for x, y in zip(self.rgba, other.rgba)))

    @classmethod
    def parse(cls, value: ColorLike) -> "Color":
        """Accept every form the v0.5 Quick Reference documents."""
        if isinstance(value, Color):
            return value
        if isinstance(value, str):
            return cls._parse_str(value)
        if isinstance(value, bool):
            raise ValueError(f"{value!r} is not a colour")
        if isinstance(value, int):
            # Backend-compatible packed form 0xRRGGBBAA, as pygame.Color(int) reads it.
            if not 0 <= value <= 0xFFFFFFFF:
                raise ValueError(f"packed colour {value:#x} must fit in 0xRRGGBBAA")
            return cls((value >> 24) & 255, (value >> 16) & 255, (value >> 8) & 255, value & 255)
        if all(hasattr(value, c) for c in "rgb"):
            # Any object exposing r/g/b[/a] - covers pygame.Color without importing pygame.
            return cls(
                _component(value.r), _component(value.g), _component(value.b),
                _component(getattr(value, "a", 255)),
            )
        if isinstance(value, (tuple, list)):
            if len(value) == 3:
                return cls(*(_component(c) for c in value))
            if len(value) == 4:
                return cls(*(_component(c) for c in value))
            raise ValueError(
                f"a colour tuple needs 3 or 4 numbers (red, green, blue[, alpha]), got {len(value)}"
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
    Computed colours such as p.map_range(...) results therefore just work.
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
