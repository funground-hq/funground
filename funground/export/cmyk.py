"""CMYK stand-ins: how a PDF gets exact ink colours out of a renderer that only knows RGB (story S-170, D-087).

Cairo draws in red, green and blue. A colour from ``f.cmyk()`` has to come out of a PDF as ``k``/``K``
operators holding its exact ink amounts. So the PDF renderer draws each distinct set of inks in a
*stand-in* RGB value, and a step after Cairo (``pdf_colour``) swaps each stand-in for its inks. This
module makes the stand-ins and reads them back. See `Colour_For_Print_Note.md`.

Why a stand-in can never be mistaken for a real colour. Every RGB colour in funground is whole numbers
from 0 to 255, so Cairo writes it as ``n / 255``. A stand-in is ``k / 65535`` with ``k`` from 1 to 255.
``n / 255`` is ``257 n / 65535``, so it is 0 or at least 257 in those units: it can never be a ``k``
from 1 to 255. The stand-ins therefore need no search through the document for a free value; they
are free by construction.

The code ``k`` carries the number of the colour, in three digits: red and green count from 1 to 250 and
blue is from 251 to 255 (so a stand-in is never a grey, which Cairo might write another way).
"""
from __future__ import annotations

SCALE = 65535.0                       # Cairo's 16-bit colour: one part in 65535
LOW, HIGH = 1, 250                    # red and green digits
BLUE_LOW, BLUE_HIGH = 251, 255        # blue digit
ROOM = (HIGH - LOW + 1) ** 2 * (BLUE_HIGH - BLUE_LOW + 1)      # 312 500 distinct inks in one document
TOLERANCE = 0.02                      # Cairo prints about 9 digits; this is far more than the rounding


class CmykStandins:
    """The stand-in RGB values of one PDF's CMYK colours, made as the renderer meets each colour."""

    __slots__ = ("_index", "_inks")

    def __init__(self) -> None:
        self._index: dict[tuple[float, float, float, float], int] = {}
        self._inks: list[tuple[float, float, float, float]] = []

    def __len__(self) -> int:
        return len(self._inks)

    def rgb_for(self, inks: tuple[float, float, float, float]) -> tuple[float, float, float]:
        """The stand-in for *inks* (cyan, magenta, yellow, black: 0 to 100), as red, green, blue from 0 to 1.

        The same inks always get the same stand-in within a document."""
        number = self._index.get(inks)
        if number is None:
            number = len(self._inks)
            if number >= ROOM:
                raise ValueError(f"a PDF can hold {ROOM} different cmyk() colours; this one has more")
            self._index[inks] = number
            self._inks.append(inks)
        return (
            (LOW + number % 250) / SCALE,
            (LOW + number // 250 % 250) / SCALE,
            (BLUE_LOW + number // 62500) / SCALE,
        )

    def inks_for(self, red: float, green: float, blue: float) -> tuple[float, float, float, float] | None:
        """The inks of a stand-in read from a PDF's colour numbers, or None when it is a real RGB colour.

        Raises ValueError for numbers that are neither, or that look like a stand-in this document did not
        make, because a wrong colour in a print file is worse than no file."""
        codes = [round(value * SCALE) for value in (red, green, blue)]
        standin = [abs(value * SCALE - code) <= TOLERANCE and 1 <= code <= 255
                   for value, code in zip((red, green, blue), codes)]
        if not any(standin):
            return None                           # n / 255, a real colour (or numbers Cairo made another way)
        r, g, b = codes
        if all(standin) and LOW <= r <= HIGH and LOW <= g <= HIGH and BLUE_LOW <= b <= BLUE_HIGH:
            number = (r - LOW) + 250 * (g - LOW) + 62500 * (b - BLUE_LOW)
            if number < len(self._inks):
                return self._inks[number]
        raise ValueError(f"the colour {red:g} {green:g} {blue:g} looks like a cmyk() stand-in but is not one this document made")
