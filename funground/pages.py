"""Page sizes for documents (story S-084, contract D1).

Sizes are in points (1/72 inch), the unit of a PDF page, which is also one logical pixel.
"""
from __future__ import annotations

PAGE_SIZES: dict[str, tuple[int, int]] = {
    "A3": (842, 1191),
    "A4": (595, 842),
    "A5": (420, 595),
    "B5": (499, 709),
    "Letter": (612, 792),
    "Legal": (612, 1008),
    "Tabloid": (792, 1224),
    "Square": (600, 600),
}

_BY_LOWER = {name.lower(): size for name, size in PAGE_SIZES.items()}


def page_size(name: str, landscape: bool = False) -> tuple[int, int]:
    """The (width, height) of a named page in points; ``landscape`` turns it on its side."""
    if not isinstance(name, str):
        raise TypeError(f"f.page_size() needs a page name such as \"A4\", not {name!r}")
    key = name.strip().lower()
    if key.endswith("landscape"):
        landscape = True
        key = key[: -len("landscape")].strip()
    size = _BY_LOWER.get(key)
    if size is None:
        raise ValueError(f"unknown page size {name!r}: use one of {', '.join(PAGE_SIZES)} "
                         "(add \"Landscape\" to turn it on its side, e.g. \"A4Landscape\")")
    width, height = size
    return (height, width) if landscape else (width, height)
