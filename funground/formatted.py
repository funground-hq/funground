"""FormattedString: mixed styles in one text (story S-091, contract T14; DrawBot's FormattedString).

A FormattedString is a list of runs. Each run is some text plus the settings that were given for it.
A setting that was left out stays unset, and follows the drawing state when the text is drawn.
This module holds the data and the line breaking. The Sketch does the measuring and drawing.
"""
from __future__ import annotations

import inspect
import os
import re
from dataclasses import dataclass
from numbers import Real

from .color import Color


@dataclass(frozen=True, slots=True)
class Run:
    """One run of text and its own settings. None means "not given"."""

    text: str
    font: str | None = None            # the font registry key (T11)
    size: int | None = None
    style: str | None = None
    color: Color | None = None
    tracking: float | None = None
    features: tuple | None = None      # sorted (tag, bool) pairs
    variations: tuple | None = None    # sorted (tag, number) pairs

    def apply(self, state):
        """The GraphicsState to draw this run with: *state*, with this run's own settings on top."""
        changes = {}
        if self.font is not None:
            changes["font"] = self.font
        if self.size is not None:
            changes["text_size"] = self.size
        if self.style is not None:
            changes["text_style"] = self.style
        if self.tracking is not None:
            changes["text_tracking"] = self.tracking
        if self.features is not None:
            changes["text_features"] = self.features
        if self.variations is not None:
            changes["font_variations"] = self.variations
        return state.with_(**changes) if changes else state

    def with_text(self, text: str) -> "Run":
        return Run(text, self.font, self.size, self.style, self.color, self.tracking,
                   self.features, self.variations)


class FormattedString:
    """Text made of runs, each with its own font, size, style, colour and so on (contract T14)."""

    __slots__ = ("_runs",)

    def __init__(self) -> None:
        self._runs: tuple[Run, ...] = ()

    @classmethod
    def _of(cls, runs) -> "FormattedString":
        fs = cls()
        fs._runs = tuple(runs)
        return fs

    # ---- building
    def append(self, text: object, font=None, size: float | None = None, style: str | None = None,
               color=None, tracking: float | None = None, features: dict | None = None,
               variations: dict | None = None) -> "FormattedString":
        """Add a run. Every setting you give belongs to this run; one you leave out follows the
        drawing state when the text is drawn. Returns the same FormattedString, so calls chain."""
        from .api import active_sketch
        from .sketch import Sketch
        from .typography import TEXT_STYLES, Font

        sketch = active_sketch()
        key = None
        if font is not None:
            if isinstance(font, Font):
                key = font.name
            elif isinstance(font, str):
                base_dir = None
                caller = inspect.currentframe()
                if caller is not None and caller.f_back is not None:
                    sketch_file = caller.f_back.f_globals.get("__file__")
                    if sketch_file:
                        base_dir = os.path.dirname(os.path.abspath(sketch_file))
                key = sketch.load_font(font, base_dir=base_dir).name
            else:
                raise TypeError(
                    f"FormattedString.append() needs a font from f.load_font() or a path, not {type(font).__name__}")
        if size is not None:
            if isinstance(size, bool) or not isinstance(size, Real):
                raise TypeError(f"FormattedString.append() takes a number for size, not {type(size).__name__}")
            if size <= 0:
                raise ValueError("text size must be positive")
            size = int(size)
        if style is not None and style not in TEXT_STYLES:
            raise ValueError(
                f"FormattedString.append() takes a style of {', '.join(map(repr, TEXT_STYLES))}, not {style!r}")
        paint = sketch._paint(color) if color is not None else None     # read in the colour mode of now
        if tracking is not None:
            if isinstance(tracking, bool) or not isinstance(tracking, Real):
                raise TypeError(
                    f"FormattedString.append() takes a number of pixels for tracking, not {type(tracking).__name__}")
            tracking = float(tracking)
        feature_pairs = None
        if features is not None:
            if not isinstance(features, dict):
                raise TypeError("FormattedString.append() takes features as a dict, like {'liga': False}")
            merged = {}
            for tag, value in features.items():
                if not isinstance(value, bool):
                    raise TypeError(
                        f"FormattedString.append() takes True or False for each feature, not {value!r} for {tag!r}")
                merged[Sketch._tag(tag, "FormattedString.append")] = value
            feature_pairs = tuple(sorted(merged.items()))
        variation_pairs = None
        if variations is not None:
            if not isinstance(variations, dict):
                raise TypeError("FormattedString.append() takes variations as a dict, like {'wght': 700}")
            merged = {}
            for tag, value in variations.items():
                if isinstance(value, bool) or not isinstance(value, Real):
                    raise TypeError(
                        f"FormattedString.append() takes a number for each axis, not {value!r} for {tag!r}")
                merged[Sketch._tag(tag, "FormattedString.append")] = float(value)
            variation_pairs = tuple(sorted(merged.items()))
        text = str(text)
        if text:
            self._runs += (Run(text, key, size, style, paint, tracking, feature_pairs, variation_pairs),)
        return self

    # ---- reading
    @property
    def runs(self) -> tuple[Run, ...]:
        return self._runs

    def __str__(self) -> str:
        return "".join(r.text for r in self._runs)

    def __len__(self) -> int:
        return sum(len(r.text) for r in self._runs)

    def __repr__(self) -> str:
        return f"FormattedString({len(self._runs)} runs, {str(self)!r})"

    def __add__(self, other):
        if isinstance(other, FormattedString):
            return FormattedString._of(self._runs + other._runs)
        if isinstance(other, str):
            return FormattedString._of(self._runs + ((Run(other),) if other else ()))
        return NotImplemented

    def __radd__(self, other):
        if isinstance(other, str):
            return FormattedString._of(((Run(other),) if other else ()) + self._runs)
        return NotImplemented

    # ---- layout helpers (used by the Sketch)
    def _flat(self) -> tuple[str, list[int]]:
        """The whole text, and for each character the index of the run it belongs to."""
        text = "".join(r.text for r in self._runs)
        owner = [i for i, r in enumerate(self._runs) for _ in r.text]
        return text, owner

    def _from(self, start: int) -> "FormattedString":
        """What is left from character *start* on, keeping every run's settings."""
        runs, at = [], 0
        for r in self._runs:
            end = at + len(r.text)
            if end > start:
                runs.append(r if start <= at else r.with_text(r.text[start - at:]))
            at = end
        return FormattedString._of(runs)

    def lines(self) -> list[list[tuple[str, int | None]]]:
        """Split at every "\\n": each line is a list of (text, run index) pieces."""
        return self.wrap(None)[0]

    def wrap(self, fits) -> tuple[list[list[tuple[str, int | None]]], list[int]]:
        """Break into lines (contract T10, T14). *fits(pieces)* says whether a candidate line, a list of
        (text, run index) pieces, is narrow enough; None means no wrapping, only "\\n" breaks.

        Returns (lines, starts): starts[i] is the character where line i begins, so
        `self._from(starts[i])` is the text from that line on. Lines break at spaces; a word wider
        than the box is broken between letters. A blank line keeps one empty piece, so it still has a height.
        """
        text, owner = self._flat()
        lines: list[list[tuple[str, int | None]]] = []
        starts: list[int] = []

        def pieces(idxs: list[int]) -> list[tuple[str, int | None]]:
            out: list[tuple[str, int | None]] = []
            for i in idxs:
                if out and out[-1][1] == owner[i]:
                    out[-1] = (out[-1][0] + text[i], owner[i])
                else:
                    out.append((text[i], owner[i]))
            return out

        def emit(idxs: list[int], start: int, blank_run: int | None = None) -> None:
            lines.append(pieces(idxs) if idxs else [("", blank_run)])
            starts.append(start)

        def blank_owner(offset: int, length: int) -> int | None:
            for i in (offset + length, offset - 1):     # the newline that ends it, else the one before it
                if 0 <= i < len(owner):
                    return owner[i]
            return None

        offset = 0
        for paragraph in text.split("\n"):
            if fits is None:
                idxs = list(range(offset, offset + len(paragraph)))
                emit(idxs, offset, blank_owner(offset, len(paragraph)))
                offset += len(paragraph) + 1
                continue
            words: list[tuple[list[int], int]] = []      # (letters, the first space before the word)
            start: int | None = None
            prev_end = 0

            def line_of(ws) -> list[int]:
                out: list[int] = []
                for n, (letters, gap) in enumerate(ws):
                    if n:
                        out.append(gap)
                    out.extend(letters)
                return out

            for m in re.finditer(r"[^ ]+", paragraph):
                at = offset + m.start()
                word = (list(range(at, offset + m.end())), offset + prev_end)
                prev_end = m.end()
                if fits(pieces(line_of(words + [word]))):
                    words.append(word)
                    start = at if start is None else start
                    continue
                if words:
                    emit(line_of(words), start)
                letters = word[0]
                while len(letters) > 1 and not fits(pieces(letters)):      # a word wider than the box
                    cut = len(letters) - 1
                    while cut > 1 and not fits(pieces(letters[:cut])):
                        cut -= 1
                    emit(letters[:cut], letters[0])
                    letters = letters[cut:]
                words, start = [(letters, word[1])], letters[0]
            if words:
                emit(line_of(words), start)
            else:
                emit([], offset if start is None else start, blank_owner(offset, len(paragraph)))
            offset += len(paragraph) + 1
        return lines, starts
