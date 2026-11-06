"""What ``ml.pose()``, ``ml.hand()`` and ``ml.words()`` give back: a Body, a Hand and some Words (D-125, D-126).

Each named point is an attribute and an ``f.Vector`` in the pixels of the source as drawn at (0, 0). The names are
MediaPipe's own, so its documentation still helps.
"""
from __future__ import annotations

import difflib

from funground import Vector

BODY_NAMES = (
    "nose", "left_eye_inner", "left_eye", "left_eye_outer", "right_eye_inner", "right_eye", "right_eye_outer",
    "left_ear", "right_ear", "mouth_left", "mouth_right", "left_shoulder", "right_shoulder", "left_elbow",
    "right_elbow", "left_wrist", "right_wrist", "left_pinky", "right_pinky", "left_index", "right_index",
    "left_thumb", "right_thumb", "left_hip", "right_hip", "left_knee", "right_knee", "left_ankle", "right_ankle",
    "left_heel", "right_heel", "left_foot_index", "right_foot_index",
)

HAND_NAMES = (
    "wrist", "thumb_cmc", "thumb_mcp", "thumb_ip", "thumb_tip",
    "index_finger_mcp", "index_finger_pip", "index_finger_dip", "index_finger_tip",
    "middle_finger_mcp", "middle_finger_pip", "middle_finger_dip", "middle_finger_tip",
    "ring_finger_mcp", "ring_finger_pip", "ring_finger_dip", "ring_finger_tip",
    "pinky_mcp", "pinky_pip", "pinky_dip", "pinky_tip",
)


def other_side(name: str) -> str:
    """``left_wrist`` for ``right_wrist`` and the other way round; a name with no side stays as it is."""
    if name.startswith("left_"):
        return "right_" + name[len("left_"):]
    if name.startswith("right_"):
        return "left_" + name[len("right_"):]
    return name


class _Points:
    """The part a Body and a Hand share: named points as attributes, ``points``, ``score`` and a helpful error."""

    _names: tuple = ()

    def __init__(self, points: dict[str, Vector], score: float) -> None:
        self.points = points
        self.score = score
        self.__dict__.update(points)

    def __getattr__(self, name: str):
        # Only reached for a name that is not a point (a point is an attribute).
        kind = type(self).__name__
        if name.startswith("_"):
            raise AttributeError(f"{kind!r} object has no attribute {name!r}")
        close = difflib.get_close_matches(name, self._names, n=1, cutoff=0.6)
        hint = f" Did you mean '{close[0]}'?" if close else f" Its points are listed in {kind.lower()}.points."
        raise AttributeError(f"A {kind.lower()} has no point called '{name}'.{hint}")

    def __repr__(self) -> str:
        first = self._names[0]
        where = self.points[first]
        return (f"<{type(self).__name__} score {self.score:.2f}, {len(self.points)} points, "
                f"{first} at ({where.x:.0f}, {where.y:.0f})>")


class Body(_Points):
    """One body found by ``ml.pose()``.

    It has 33 named points, each an ``f.Vector`` in the source's pixels: ``body.nose``, ``body.left_shoulder``,
    ``body.right_ankle`` and so on (the list is in ``ml.pose``). ``body.points`` is a dict of every name and point, in
    the model's order. ``body.score`` is how sure the model is, from 0 to 1.

    Left and right are the person's own sides. With a mirrored camera the left wrist is the learner's own left wrist,
    wherever it shows on the screen.
    """

    _names = BODY_NAMES

    @classmethod
    def from_points(cls, xy, score: float, mirrored: bool) -> "Body":
        """*xy* is the model's 33 (x, y) rows in BODY_NAMES order. For a mirrored picture the sides are swapped.

        Why the swap is right: the model decides left and right by where a limb is in the picture, as a person facing a
        normal camera has their left side on the picture's right. A mirrored picture shows the learner as in a mirror:
        their own left wrist is on the picture's left, so the model calls it "right_wrist". The learner's own left wrist
        is therefore the model's "right_wrist", and the same for every other pair. The points stay where they are drawn.
        """
        index = {name: i for i, name in enumerate(BODY_NAMES)}
        points = {}
        for name in BODY_NAMES:
            row = xy[index[other_side(name) if mirrored else name]]
            points[name] = Vector(float(row[0]), float(row[1]))
        return cls(points, score)


class Hand(_Points):
    """One hand found by ``ml.hand()``.

    It has 21 named points, each an ``f.Vector`` in the source's pixels: ``hand.wrist``, ``hand.thumb_tip``,
    ``hand.index_finger_tip`` and so on (the list is in ``ml.hand``). ``hand.points`` is a dict of every name and point, in
    the model's order. ``hand.score`` is how sure the model is, from 0 to 1. A hand has no side in this version.
    """

    _names = HAND_NAMES

    @classmethod
    def from_points(cls, xy, score: float) -> "Hand":
        points = {name: Vector(float(row[0]), float(row[1])) for name, row in zip(HAND_NAMES, xy)}
        return cls(points, score)


class Words:
    """The words heard by ``ml.words()``.

    ``words.text`` is what was said, with the model's own capitals and punctuation, and is never empty. ``words.score`` (0 to 1)
    is how sure the model is. ``words.is_new`` is True in the frame the answer first shows up, and False in the frames after, so
    ``if words and words.is_new:`` does something once for each thing said. ``str(words)`` is the text.
    """

    def __init__(self, text: str, score: float, is_new: bool = False) -> None:
        self.text = text
        self.score = score
        self.is_new = is_new

    def __str__(self) -> str:
        return self.text

    def __repr__(self) -> str:
        shown = self.text if len(self.text) <= 40 else self.text[:37] + "..."
        return f"<Words {shown!r} score {self.score:.2f}{', new' if self.is_new else ''}>"


class Heard:
    """The name of a sound, given by ``ml.sound()``.

    ``heard.name`` is the sound's name in English, for example ``"Dog"`` or ``"Speech"``. ``heard.score`` (0 to 1) is how sure the
    model is of that name. ``heard.next`` is up to four more guesses, the likeliest first; each is a Heard too, with its own name
    and score, no guesses of its own, and ``is_new`` False. ``heard.is_new`` is True in the frame an answer first shows up, and False
    in the frames after. ``str(heard)`` is the name. The name is often a broad one, and it can be wrong.
    """

    def __init__(self, name: str, score: float, next: tuple["Heard", ...] = (), is_new: bool = False) -> None:
        self.name = name
        self.score = score
        self.next = tuple(next)
        self.is_new = is_new

    @classmethod
    def from_guesses(cls, guesses, is_new: bool) -> "Heard":
        """The answer for ``_sound.choose``'s list of (name, score): the best one, with the rest as its ``next``."""
        (name, score), rest = guesses[0], guesses[1:]
        return cls(name, score, tuple(cls(n, s) for n, s in rest), is_new)

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        names = f", next {', '.join(repr(g.name) for g in self.next)}" if self.next else ""
        return f"<Heard {self.name!r} score {self.score:.2f}{names}{', new' if self.is_new else ''}>"
