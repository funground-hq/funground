"""The five tasks, from a source to a Body, a Hand, a Picture, some Words or a Heard: the work behind ``ml.pose()``, ``ml.hand()``,
``ml.person()``, ``ml.words()`` and ``ml.sound()`` (D-125, D-126).

There are two paths. On a computer the models run here, with onnxruntime. In a web page the host runs them (``host_services.models``,
S-232) and this module only sends it pictures and reads the newest answer. The desktop modules (``_fetch``, ``_glue``,
``_runtime``, and through them onnxruntime, numpy and Pillow) are imported inside the desktop path only, so a page never loads them.
"""
from __future__ import annotations

import weakref
from typing import TYPE_CHECKING

from funground import host_services
from funground.api import canvas_sketch
from funground.picture import Picture

from . import _hearing, _listen, _source
from ._results import Body, Hand, Heard, Words
from ._speech import MAX_SOUND_SECONDS

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


# What is kept for each microphone (an Ear) and each Sound (a Clip). The microphone or sound is the key, held weakly, and the value
# does not refer back to it, so neither is kept alive.
_ears: "weakref.WeakKeyDictionary" = weakref.WeakKeyDictionary()
_clips: "weakref.WeakKeyDictionary" = weakref.WeakKeyDictionary()
_sound_ears: "weakref.WeakKeyDictionary" = weakref.WeakKeyDictionary()       # the same for ml.sound(), kept apart from the words
_sound_clips: "weakref.WeakKeyDictionary" = weakref.WeakKeyDictionary()


def _frame() -> int:
    """The sketch's frame count: what "the same frame" means for the words (``Words.is_new`` and the same answer twice)."""
    return canvas_sketch().frame_count


def find_words(source: object, base_dir: str | None) -> Words | None:
    """The words heard by a microphone, or in a Sound, or None. *base_dir* is the sketch's folder (where ``models/`` is kept).

    A microphone is read for new phrases and the model works on them beside the sketch (a thread on a computer, the page's
    worker in a web page); the answer is the newest one that has come in. A Sound is one phrase: a computer waits for the
    answer, a web page gives None until it comes.
    """
    from funground.sound._engine import Sound
    from funground.sound._microphone import Microphone

    who = "ml.words()"
    if not isinstance(source, (Microphone, Sound)):
        raise TypeError(f"{who} needs a microphone from sound.microphone() or a sound, not {type(source).__name__}.")
    if isinstance(source, Sound) and source.duration() > MAX_SOUND_SECONDS:
        raise ValueError(f"{who}: this sound is {source.duration():.0f} seconds long, and the most it can listen to is "
                         f"{MAX_SOUND_SECONDS} seconds. Cut it shorter first.")
    models = host_services.models
    if models is not None:
        context, transcribe, make_sink = (models,), None, lambda: _listen.HostSink(models, id(source))
    else:
        from . import _fetch, _whisper

        paths = _fetch.ensure("words", base_dir, who)           # the first call downloads, here in the sketch's thread

        def transcribe(samples, rate):
            return _whisper.load(paths).transcribe(samples, rate)

        context, make_sink = tuple(sorted(paths.items())), lambda: _listen.Worker(transcribe)
    if isinstance(source, Sound):
        clip = _clips.get(source)
        if clip is None or clip.context != context:
            clip = _clips[source] = _listen.Clip(context, transcribe, make_sink() if models is not None else None)
        return clip.words(_frame(), source)
    ear = _ears.get(source)
    if ear is None or ear.context != context:
        if ear is not None:
            ear.close()
        ear = _ears[source] = _listen.Ear(context, source, make_sink())
    return ear.words(_frame(), source)


def find_sound(source: object, base_dir: str | None) -> Heard | None:
    """The name of the sound heard by a microphone, or in a Sound, or None. *base_dir* is the sketch's folder (where ``models/`` is kept).

    A microphone's newest 0.96 s is worked on every 0.48 s beside the sketch (a thread on a computer, the page's worker in a web
    page); the answer is the newest one that has come in. A Sound is one answer: a computer waits for it, a web page gives None
    until it comes.
    """
    from funground.sound._engine import Sound
    from funground.sound._microphone import Microphone

    who = "ml.sound()"
    if not isinstance(source, (Microphone, Sound)):
        raise TypeError(f"{who} needs a microphone from sound.microphone() or a sound, not {type(source).__name__}.")
    if isinstance(source, Sound) and source.duration() > MAX_SOUND_SECONDS:
        raise ValueError(f"{who}: this sound is {source.duration():.0f} seconds long, and the most it can listen to is "
                         f"{MAX_SOUND_SECONDS} seconds. Cut it shorter first.")
    models = host_services.models
    if models is not None:
        context, classify, make_sink = (models,), None, lambda: _hearing.SoundHostSink(models, id(source))
    else:
        from . import _fetch, _yamnet

        paths = _fetch.ensure("sound", base_dir, who)           # the first call downloads, here in the sketch's thread

        def classify(window, rate):
            return window.tag, (None if window.samples is None else _yamnet.load(paths).scores(window.samples, rate))

        context, make_sink = tuple(sorted(paths.items())), lambda: _listen.Worker(classify, name="funground sound")
    if isinstance(source, Sound):
        clip = _sound_clips.get(source)
        if clip is None or clip.context != context:
            clip = _sound_clips[source] = _hearing.SoundClip(context, classify, make_sink() if models is not None else None)
        return clip.heard(_frame(), source)
    ear = _sound_ears.get(source)
    if ear is None or ear.context != context:
        if ear is not None:
            ear.close()
        ear = _sound_ears[source] = _hearing.SoundEar(context, source, make_sink())
    return ear.heard(_frame(), source)


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
