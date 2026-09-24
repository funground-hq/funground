"""Playground's own colour type.

Learners keep writing ``"tomato"``, ``(255, 99, 71)`` or ``"#FF6347"`` (contract row S1);
Playground parses those once into an RGBA ``Color`` so renderers never see backend types.
"""
from __future__ import annotations

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

    @classmethod
    def parse(cls, value: ColorLike) -> "Color":
        """Accept every form the v0.5 Quick Reference documents."""
        if isinstance(value, Color):
            return value
        if isinstance(value, str):
            return cls._parse_str(value)
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
    if isinstance(c, bool) or not isinstance(c, (int, float)):
        raise ValueError(f"colour component {c!r} must be a number from 0 to 255")
    if isinstance(c, float):
        if not c.is_integer():
            raise ValueError(f"colour component {c!r} must be a whole number from 0 to 255")
        c = int(c)
    return c


WHITE = Color(255, 255, 255)
BLACK = Color(0, 0, 0)
