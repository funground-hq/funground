"""The two tasks, from a source to a Body or a Hand: the work behind ``ml.pose()`` and ``ml.hand()`` (D-125)."""
from __future__ import annotations

from . import _fetch, _glue, _runtime, _source
from ._results import Body, Hand


def find_body(source: object, base_dir: str | None) -> Body | None:
    """The body in *source*, or None. *base_dir* is the sketch's folder (where ``models/`` is kept), or None."""
    who = "ml.pose()"

    def make(frame: _source.Frame, tracker: _glue.Tracker) -> Body | None:
        paths = _fetch.ensure("pose", base_dir, who)
        detector, landmark_model = _runtime.session(paths["detector"]), _runtime.session(paths["landmarks"])
        image = frame.image()

        def detect_region():
            detection = _glue.detect(detector, image, _glue.POSE_DETECTOR)
            return None if detection is None else _glue.body_region(detection)

        found = tracker.find(image, detect_region, lambda region: _glue.body_landmarks(landmark_model, image, region))
        if found is None:
            return None
        return Body.from_points(_to_logical(frame, found.points), found.score, frame.mirrored)

    return _source.answer(source, "pose", who, make)


def find_hand(source: object, base_dir: str | None) -> Hand | None:
    """The hand in *source*, or None. *base_dir* is the sketch's folder (where ``models/`` is kept), or None."""
    who = "ml.hand()"

    def make(frame: _source.Frame, tracker: _glue.Tracker) -> Hand | None:
        paths = _fetch.ensure("hand", base_dir, who)
        detector, landmark_model = _runtime.session(paths["detector"]), _runtime.session(paths["landmarks"])
        image = frame.image()

        def detect_region():
            detection = _glue.detect(detector, image, _glue.PALM_DETECTOR)
            return None if detection is None else _glue.hand_region(detection)

        found = tracker.find(image, detect_region, lambda region: _glue.hand_landmarks(landmark_model, image, region))
        if found is None:
            return None
        return Hand.from_points(_to_logical(frame, found.points), found.score)

    return _source.answer(source, "hand", who, make)


def _to_logical(frame: _source.Frame, points):
    return [frame.to_logical(float(x), float(y)) for x, y in points]
