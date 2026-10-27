"""f.CONSTANTS: a name for every option word, in groups (D-103, S-174).

Written by hand. tests/test_constants.py checks it against the functions that take the words, in both directions.
The ``Literal`` types in ``_options.py`` list the same words.
"""
from __future__ import annotations

from typing import Final

from ._namespaces import _NamespaceMeta


class CONSTANTS(metaclass=_NamespaceMeta):
    """Names for the words that choose an option, in groups, so an editor can list them and a typing slip is caught.

    Each group is named after what it chooses: ``f.CONSTANTS.ALIGN.CENTER`` is the word ``"center"``. Write whichever
    you like: ``f.text_align(f.CONSTANTS.ALIGN.CENTER)`` and ``f.text_align("center")`` do the same. After
    ``from funground import *`` write ``CONSTANTS.ALIGN.CENTER``.

    The lists are fixed: you cannot add to them or change them. Iterate a group to get its words:
    ``list(f.CONSTANTS.BLEND)``. A group holds the words its functions accept.

    Example:
        f.text_align(f.CONSTANTS.ALIGN.CENTER)
        f.blend_mode(f.CONSTANTS.BLEND.MULTIPLY)

    See also: text_align, blend_mode, rect_mode, COLORS
    """

    class MODE(metaclass=_NamespaceMeta):
        """How rect_mode(), ellipse_mode() and image_mode() read their numbers. image_mode() has no RADIUS."""

        CORNER: Final = "corner"
        CORNERS: Final = "corners"
        CENTER: Final = "center"
        RADIUS: Final = "radius"

    class ARC(metaclass=_NamespaceMeta):
        """How arc() closes its shape."""

        OPEN: Final = "open"
        CHORD: Final = "chord"
        PIE: Final = "pie"

    class COLOR_MODE(metaclass=_NamespaceMeta):
        """The colour model for color_mode()."""

        RGB: Final = "rgb"
        HSB: Final = "hsb"
        HSL: Final = "hsl"

    class ALIGN(metaclass=_NamespaceMeta):
        """Where text_align() puts the text: the first four across, TOP to BOTTOM up and down."""

        LEFT: Final = "left"
        CENTER: Final = "center"
        RIGHT: Final = "right"
        JUSTIFY: Final = "justify"
        TOP: Final = "top"
        BASELINE: Final = "baseline"
        BOTTOM: Final = "bottom"

    class STYLE(metaclass=_NamespaceMeta):
        """The text styles for text_style() and FormattedString.append()."""

        NORMAL: Final = "normal"
        BOLD: Final = "bold"
        ITALIC: Final = "italic"
        BOLD_ITALIC: Final = "bold_italic"

    class CAP(metaclass=_NamespaceMeta):
        """The ends of a line for stroke_cap()."""

        ROUND: Final = "round"
        SQUARE: Final = "square"
        BUTT: Final = "butt"

    class JOIN(metaclass=_NamespaceMeta):
        """The corners of a line for stroke_join()."""

        ROUND: Final = "round"
        MITER: Final = "miter"
        BEVEL: Final = "bevel"

    class CURSOR(metaclass=_NamespaceMeta):
        """The mouse pointers for cursor()."""

        ARROW: Final = "arrow"
        CROSS: Final = "cross"
        HAND: Final = "hand"
        MOVE: Final = "move"
        TEXT: Final = "text"
        WAIT: Final = "wait"

    class BLEND(metaclass=_NamespaceMeta):
        """The blend modes for blend_mode()."""

        NORMAL: Final = "normal"
        MULTIPLY: Final = "multiply"
        SCREEN: Final = "screen"
        OVERLAY: Final = "overlay"
        DARKEN: Final = "darken"
        LIGHTEN: Final = "lighten"
        ADD: Final = "add"
        DIFFERENCE: Final = "difference"
        EXCLUSION: Final = "exclusion"
        DODGE: Final = "dodge"
        BURN: Final = "burn"
        HARD_LIGHT: Final = "hard_light"
        SOFT_LIGHT: Final = "soft_light"
        HUE: Final = "hue"
        SATURATION: Final = "saturation"
        COLOR: Final = "color"
        LUMINOSITY: Final = "luminosity"

    class FILTER(metaclass=_NamespaceMeta):
        """The filters for filter() and apply_filter()."""

        THRESHOLD: Final = "threshold"
        GRAY: Final = "gray"
        OPAQUE: Final = "opaque"
        INVERT: Final = "invert"
        BLUR: Final = "blur"
        POSTERIZE: Final = "posterize"
        ERODE: Final = "erode"
        DILATE: Final = "dilate"
        EDGES: Final = "edges"

    class WAVE(metaclass=_NamespaceMeta):
        """The sound waves for tone(), note() and melody()."""

        SINE: Final = "sine"
        SQUARE: Final = "square"
        SAW: Final = "saw"
        TRIANGLE: Final = "triangle"
        SOFT: Final = "soft"
        NOISE: Final = "noise"

    class TUNING(metaclass=_NamespaceMeta):
        """The tuning for melody()."""

        EQUAL: Final = "equal"
        JUST: Final = "just"

    class ANCHOR(metaclass=_NamespaceMeta):
        """The point of a mark that Mark.place() puts at x, y."""

        ORIGIN: Final = "origin"
        CENTER: Final = "center"
        TOP: Final = "top"
        BOTTOM: Final = "bottom"
        LEFT: Final = "left"
        RIGHT: Final = "right"
        TOP_LEFT: Final = "top-left"
        TOP_RIGHT: Final = "top-right"
        BOTTOM_LEFT: Final = "bottom-left"
        BOTTOM_RIGHT: Final = "bottom-right"

    class MARK_STYLE(metaclass=_NamespaceMeta):
        """Which paint Mark.place() uses."""

        OWN: Final = "own"
        CURRENT: Final = "current"

    class SAVE_TEXT(metaclass=_NamespaceMeta):
        """How save() keeps text."""

        LIVE: Final = "live"
        SHAPES: Final = "shapes"

    class PROVIDERS(metaclass=_NamespaceMeta):
        """The font providers for load_font(): a family found by its name."""

        GOOGLE_FONTS: Final = "google_fonts"

    class KEY(metaclass=_NamespaceMeta):
        """The named keys for key_down(), and the values f.key can hold for them."""

        UP: Final = "up"
        DOWN: Final = "down"
        LEFT: Final = "left"
        RIGHT: Final = "right"
        SPACE: Final = "space"
        ENTER: Final = "enter"
        ESCAPE: Final = "escape"

    class MOUSE(metaclass=_NamespaceMeta):
        """The values f.mouse_button can hold."""

        LEFT: Final = "left"
        CENTER: Final = "center"
        RIGHT: Final = "right"

    class PAGE(metaclass=_NamespaceMeta):
        """The page sizes for size(), new_page() and page_size()."""

        A3: Final = "A3"
        A4: Final = "A4"
        A5: Final = "A5"
        B5: Final = "B5"
        LETTER: Final = "Letter"
        LEGAL: Final = "Legal"
        TABLOID: Final = "Tabloid"
