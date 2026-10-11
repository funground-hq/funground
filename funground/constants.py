"""Option words and colours as names (D-090). SPIKE PROTOTYPE (S-175): only what the examples need.

Each constant holds the word that funground already accepts, so ``text_align(LEFT)`` and
``text_align("left")`` are the same call, and a mistyped name fails at once instead of being read as a word.
"""

CENTER = "center"
LEFT = "left"
RIGHT = "right"
TOP = "top"
BOTTOM = "bottom"
BASELINE = "baseline"
JUSTIFY = "justify"
NORMAL = "normal"
BOLD = "bold"
ITALIC = "italic"


class colors:
    """Colour names as attributes: ``fill(colors.TOMATO)``. Each holds the name that fill() accepts."""

    BLACK = "black"
    WHITE = "white"
    GRAY = "gray"
    RED = "red"
    TOMATO = "tomato"
    NAVY = "navy"
    SEAGREEN = "seagreen"
    GOLD = "gold"
    CORAL = "coral"
    IVORY = "ivory"
    FIREBRICK = "firebrick"
    DARKSLATEGRAY = "darkslategray"
    LIGHTGRAY = "lightgray"
    WHITESMOKE = "whitesmoke"


OPTION_WORDS = tuple(name for name in globals() if name.isupper())
