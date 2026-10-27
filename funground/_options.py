"""The words each option parameter accepts, as ``Literal`` types (D-103, S-174).

Editors and type checkers read these to suggest the words and to underline a misspelt one. They change nothing at
run time: the functions still check the word themselves. A type checker cannot read a table, so each list is written
out here, and tests/test_constants.py checks that it equals the table in the code and the group in f.CONSTANTS.
"""
from __future__ import annotations

from typing import Literal

RectMode = Literal["corner", "corners", "center", "radius"]
EllipseMode = Literal["center", "radius", "corner", "corners"]
ImageMode = Literal["corner", "corners", "center"]
ArcMode = Literal["open", "chord", "pie"]
ColorMode = Literal["rgb", "hsb", "hsl"]
BlendMode = Literal["normal", "multiply", "screen", "overlay", "darken", "lighten", "add", "difference", "exclusion",
                    "dodge", "burn", "hard_light", "soft_light", "hue", "saturation", "color", "luminosity"]
TextAlignX = Literal["left", "center", "right", "justify"]
TextAlignY = Literal["top", "center", "baseline", "bottom"]
TextStyle = Literal["normal", "bold", "italic", "bold_italic"]
StrokeCap = Literal["round", "square", "butt"]
StrokeJoin = Literal["round", "miter", "bevel"]
CursorKind = Literal["arrow", "cross", "hand", "move", "text", "wait"]
FilterKind = Literal["threshold", "gray", "opaque", "invert", "blur", "posterize", "erode", "dilate", "edges"]
Wave = Literal["sine", "square", "saw", "triangle", "soft", "noise"]
Tuning = Literal["equal", "just"]
MarkAnchor = Literal["origin", "center", "top-left", "top", "top-right", "left", "right", "bottom-left", "bottom",
                     "bottom-right"]
MarkStyle = Literal["own", "current"]
SaveText = Literal["live", "shapes"]
Provider = Literal["google_fonts"]
KeyName = Literal["left", "right", "up", "down", "space", "enter", "escape"]
PageName = Literal["A3", "A4", "A5", "B5", "Letter", "Legal", "Tabloid", "Square"]
