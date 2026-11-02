"""The three tasks, from a source to a Body, a Hand or a Picture: the work behind ``ml.pose()``, ``ml.hand()`` and ``ml.person()`` (D-125).

There are two paths. On a computer the models run here, with onnxruntime. In a web page the host runs them (``host_services.models``,
S-232) and this module only sends it pictures and reads the newest answer. The desktop modules (``_fetch``, ``_glue``,
``_runtime``, and through them onnxruntime, numpy and Pillow) are imported inside the desktop path only, so a page never loads them.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from funground import host_services
from funground.picture import Picture

from . import _source
from ._results import Body, Hand

if TYPE_CHECKING:
    from funground.platform.browser_models import MaskResult, PointsResult


def find_body(source: object, base_dir: str | None) -> Body | None:
    """The body in *source*, or None. *base_dir* is the sketch's folder (where ``models/`` is kept), or None."""
    who = "ml.pose()"
    if host_services.models is not None:
        return _from_host(host_services.models, "pose", source, who, _points_of(Body.from_points))
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
        return _from_host(host_services.models, "hand", source, who,
                          _points_of(lambda points, score, mirrored: Hand.from_points(points, score)))
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


def find_person(source: object, base_dir: str | None) -> Picture | None:
    """A copy of *source* in which everything but the person is see-through, or None for a camera with no frame yet.

    *base_dir* is the sketch's folder (where ``models/`` is kept), or None. The model always gives a mask, so a picture with
    nobody in it gives a picture that is see-through everywhere, never None. On the desktop the model runs here; in a web page
    the host runs it and the newest mask it has is used (it can be one frame behind).
    """
    who = "ml.person()"
    if host_services.models is not None:
        return _from_host(host_services.models, "person", source, who, _mask_of)
    from . import _fetch, _glue, _runtime

    def make(frame: _source.Frame, state: _source._State) -> Picture:
        session = _runtime.session(_fetch.ensure("person", base_dir, who)["model"])
        return frame.picture._masked_copy(_glue.person_mask(session, frame.image()), _glue.MASK_SIZE, _glue.MASK_SIZE)

    return _source.answer(source, "person", who, make)


def _to_logical(frame: _source.Frame, points):
    return [frame.to_logical(float(x), float(y)) for x, y in points]


def _points_of(build):
    """A builder for ``_from_host`` from a points task: nobody found gives None, else ``build(points, score, mirrored)`` with
    the points in the source's logical pixels."""
    def points_answer(frame: _source.Frame, result: PointsResult):
        if result.points is None:
            return None
        size = (result.width, result.height)
        return build([frame.to_logical(x, y, size) for x, y in result.points], result.score, frame.mirrored)

    return points_answer


def _mask_of(frame: _source.Frame, result: MaskResult) -> Picture:
    """The person's picture from the page's mask: the frame being drawn now, cut out by the newest mask."""
    return frame.picture._masked_copy(result.mask, result.mask_width, result.mask_height)


def _from_host(models, task: str, source: object, who: str, build):
    """The answer in a web page: send the picture when it is new, and build the answer from the newest result the host has.

    The host runs the models beside the sketch, so the result is for this picture or an earlier one: None until the first
    arrives, and it can be one frame behind (contract ML3). ``build(frame, result)`` makes the answer from the frame being
    drawn and the host's ``PointsResult`` (the model's own points, in the pixels of the picture it was given; the sides are
    swapped for a mirrored camera by the builder, as on the desktop) or ``MaskResult`` (the person's mask, which covers the
    whole picture however big it is).
    """
    def make(frame: _source.Frame, state: _source._State):
        sent = (id(frame.picture), frame.version)
        if state.requested != sent and not models.busy(task, state.key):
            pixels, width, height = frame.rgba()
            models.request(task, state.key, pixels, width, height)
            state.requested = sent
        result = models.latest(task, state.key)
        return None if result is None else build(frame, result)

    return _source.answer(source, task, who, make, stamp=lambda: models.generation)
