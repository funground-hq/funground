"""The two tasks, from a source to a Body or a Hand: the work behind ``ml.pose()`` and ``ml.hand()`` (D-125).

There are two paths. On a computer the models run here, with onnxruntime. In a web page the host runs them (``host_services.models``,
S-232) and this module only sends it pictures and reads the newest answer. The desktop modules (``_fetch``, ``_glue``,
``_runtime``, and through them onnxruntime, numpy and Pillow) are imported inside the desktop path only, so a page never loads them.
"""
from __future__ import annotations

from funground import host_services

from . import _source
from ._results import Body, Hand


def find_body(source: object, base_dir: str | None) -> Body | None:
    """The body in *source*, or None. *base_dir* is the sketch's folder (where ``models/`` is kept), or None."""
    who = "ml.pose()"
    if host_services.models is not None:
        return _from_host(host_services.models, "pose", source, who, Body.from_points)
    from . import _fetch, _glue, _runtime

    def make(frame: _source.Frame, state: _source._State) -> Body | None:
        paths = _fetch.ensure("pose", base_dir, who)
        detector, landmark_model = _runtime.session(paths["detector"]), _runtime.session(paths["landmarks"])
        image = frame.image()

        def detect_region():
            detection = _glue.detect(detector, image, _glue.POSE_DETECTOR)
            return None if detection is None else _glue.body_region(detection)

        found = state.tracker.find(image, detect_region, lambda region: _glue.body_landmarks(landmark_model, image, region))
        if found is None:
            return None
        return Body.from_points(_to_logical(frame, found.points), found.score, frame.mirrored)

    return _source.answer(source, "pose", who, make)


def find_hand(source: object, base_dir: str | None) -> Hand | None:
    """The hand in *source*, or None. *base_dir* is the sketch's folder (where ``models/`` is kept), or None."""
    who = "ml.hand()"
    if host_services.models is not None:
        return _from_host(host_services.models, "hand", source, who, lambda points, score, mirrored: Hand.from_points(points, score))
    from . import _fetch, _glue, _runtime

    def make(frame: _source.Frame, state: _source._State) -> Hand | None:
        paths = _fetch.ensure("hand", base_dir, who)
        detector, landmark_model = _runtime.session(paths["detector"]), _runtime.session(paths["landmarks"])
        image = frame.image()

        def detect_region():
            detection = _glue.detect(detector, image, _glue.PALM_DETECTOR)
            return None if detection is None else _glue.hand_region(detection)

        found = state.tracker.find(image, detect_region, lambda region: _glue.hand_landmarks(landmark_model, image, region))
        if found is None:
            return None
        return Hand.from_points(_to_logical(frame, found.points), found.score)

    return _source.answer(source, "hand", who, make)


def _to_logical(frame: _source.Frame, points):
    return [frame.to_logical(float(x), float(y)) for x, y in points]


def _from_host(models, task: str, source: object, who: str, build):
    """The answer in a web page: send the picture when it is new, and build the result from the newest one the host has.

    The host runs the models beside the sketch, so the result is for this picture or an earlier one: None until the first
    arrives, and it can be one frame behind (contract ML3). It sends the model's own points, in the pixels of the picture it
    was given; the sides are swapped for a mirrored camera here, as on the desktop.
    """
    def make(frame: _source.Frame, state: _source._State):
        sent = (id(frame.picture), frame.version)
        if state.requested != sent and not models.busy(task, state.key):
            pixels, width, height = frame.rgba()
            models.request(task, state.key, pixels, width, height)
            state.requested = sent
        result = models.latest(task, state.key)
        if result is None or result.points is None:
            return None
        size = (result.width, result.height)
        points = [frame.to_logical(x, y, size) for x, y in result.points]
        return build(points, result.score, frame.mirrored)

    return _source.answer(source, task, who, make, stamp=lambda: models.generation)
