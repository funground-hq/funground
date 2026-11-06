"""Hearing sounds: what is kept for each microphone and each sound, and how windows get to the model (S-250, contract ML7).

The same shape as ``_listen.py`` (words), for names of sounds.

* A **SoundEar** listens to a microphone. Each time ``ml.sound(mic)`` is called it reads what the microphone has heard since the
  last call and keeps the newest 0.96 s. Every 0.48 s of sound it cuts a **window**, the last 0.96 s, and hands it to a **sink**,
  which works on it beside the sketch. It never waits for the model.
* A **SoundClip** is one Sound, answered once and kept: the whole sound is one window, and the model gives the mean of its parts.

The sinks are the ones of ``_listen.py`` (a ``Worker`` thread on a computer) and ``SoundHostSink`` for a web page. What a sink
carries is a ``Window``: a tag, and the samples, or None for a window that was too quiet. A quiet window is never sent to the
model, but it travels through the sink in its place, so the "nothing to name" answer comes in order after the answers before it.
The sink gives back ``(tag, scores)`` (scores None for a quiet window). The names are chosen here, in the sketch's thread, by
``_sound.choose``, the same code on both platforms.

A tag says which "listening" a window came from. When the microphone stops or starts again the tag changes, and an answer for an
older one is dropped, so a sound that stopped does not come back from a window that was still being worked on.

This module imports neither numpy nor onnxruntime: a web page loads it too.
"""
from __future__ import annotations

import weakref
from array import array
from typing import NamedTuple

from ._results import Heard
from ._sound import HOP_SECONDS, WINDOW_SECONDS, choose, is_quiet

Answer = tuple[int, tuple | None]            # (the window's tag, the model's scores, or None for a quiet window)


class Window(NamedTuple):
    """One piece of sound on its way to the model."""
    tag: int
    samples: array | None                    # mono floats, or None when the window was quiet


class Latest:
    """The newest answer for one source, as the sketch sees it frame by frame (contract ML7).

    ``offer`` takes the guesses of an answer as they come in (``_sound.choose``'s list, or None for nothing to name).
    ``heard(frame)`` is what the sketch gets: the first call in a frame settles the answer for that frame, and every call in the
    frame gets that same object. An answer that arrived since is shown from the next frame on. It is ``is_new`` in the frame it
    first shows, and a plain copy in the frames after.
    """

    def __init__(self) -> None:
        self._offered = False                # an answer came in that is not shown yet
        self._waiting: list | None = None
        self._shown: Heard | None = None
        self._frame: int | None = None

    def offer(self, guesses: list | None) -> None:
        self._waiting, self._offered = guesses, True

    def heard(self, frame: int) -> Heard | None:
        if frame != self._frame:
            self._frame = frame
            if self._offered:
                self._shown = None if self._waiting is None else Heard.from_guesses(self._waiting, is_new=True)
                self._waiting, self._offered = None, False
            elif self._shown is not None and self._shown.is_new:
                self._shown = Heard(self._shown.name, self._shown.score, self._shown.next, is_new=False)
        return self._shown


class SoundHostSink:
    """The sink for a web page: windows go to the host's models (``HostModels.request_sound``, the "sound" task), one in flight
    for this source, the newest waiting; the scores come back through ``HostModels.latest``."""

    TASK = "sound"

    def __init__(self, models, key: int) -> None:
        self._models = models
        self._key = key
        self._waiting: tuple[Window, int] | None = None
        self._in_flight_tag: int | None = None
        self._seen = None

    def submit(self, window: Window, rate: int) -> None:
        self._waiting = (window, rate)

    def collect(self) -> list[Answer]:
        models, answers = self._models, []
        result = models.latest(self.TASK, self._key)
        if result is not None and result is not self._seen:         # the answer to the window in flight
            self._seen = result
            if self._in_flight_tag is not None:
                answers.append((self._in_flight_tag, result.scores))
                self._in_flight_tag = None
        if self._waiting is not None and not models.busy(self.TASK, self._key):
            window, rate = self._waiting
            if window.samples is None:                              # quiet: nothing to ask, only to say so, in order
                answers.append((window.tag, None))
                self._waiting = None
            elif models.request_sound(self.TASK, self._key, window.samples.tobytes(), rate):
                self._in_flight_tag, self._waiting = window.tag, None
        return answers

    def close(self) -> None:
        pass


def _guesses(scores) -> list | None:
    return None if scores is None else choose(scores)


class SoundEar:
    """Listens to one microphone and keeps its newest answer.

    Each ``heard(frame, mic)`` reads the new sound, cuts a window when 0.48 s more has come (the first when 0.96 s has been heard),
    hands it to the sink, takes the answers that have come in, and returns the Heard for the frame (or None). A microphone that
    is not listening gives None. The first look starts from the sound the microphone has now; after the microphone is started
    again it starts from the beginning. If the sketch looked so rarely that the microphone's buffer (10 s) wrapped, the 0.96 s
    starts again from what is left.
    """

    def __init__(self, context: tuple, mic, sink) -> None:
        # The microphone is not kept: the memory of an Ear is held by the microphone itself (a weak dictionary in _tasks).
        self.context = context
        self._sink = sink
        self._latest = Latest()
        self._rate = mic._rate
        self._version = mic._version
        self._position = mic._total if mic._listening else 0
        self._tag = 0                            # changes whenever the listening starts again or ends
        self._open = False                       # something has been heard since the last clear
        self._tail = array("f")                  # the newest 0.96 s
        self._heard = 0                          # samples heard since the last clear
        self._next_at = round(WINDOW_SECONDS * mic._rate)       # the count of heard samples at which the next window is cut
        weakref.finalize(self, sink.close)

    def close(self) -> None:
        """Let go of the sink (the worker thread ends)."""
        self._sink.close()

    def heard(self, frame: int, mic) -> Heard | None:
        self._read(mic)
        for tag, scores in self._sink.collect():         # after the reading, so a host sink sends a window the moment it is cut
            if tag == self._tag:
                self._latest.offer(_guesses(scores))
        return self._latest.heard(frame)

    def _clear(self) -> None:
        """Forget what was heard: nothing to name now, and answers for windows already sent are dropped."""
        self._tag += 1
        self._tail, self._heard, self._open = array("f"), 0, False
        self._next_at = round(WINDOW_SECONDS * self._rate)
        self._latest.offer(None)

    def _read(self, mic) -> None:
        if not mic._listening:
            if self._open:
                self._clear()
            return
        if mic._version != self._version or mic._rate != self._rate:
            self._rate, self._version, self._position = mic._rate, mic._version, 0
            self._clear()
        chunk, total = mic._since(self._position)
        if total - self._position > len(chunk):           # the buffer wrapped: what is gone is gone
            self._tail, self._heard = array("f"), 0
            self._next_at = round(WINDOW_SECONDS * self._rate)
        self._position = total
        if not chunk:
            return
        window = round(WINDOW_SECONDS * self._rate)
        self._open = True
        self._tail.extend(chunk)
        del self._tail[:-window]
        self._heard += len(chunk)
        if self._heard >= max(self._next_at, window):
            hop = round(HOP_SECONDS * self._rate)
            while self._next_at <= self._heard:
                self._next_at += hop
            quiet = is_quiet(self._tail, self._rate)
            self._sink.submit(Window(self._tag, None if quiet else array("f", self._tail)), self._rate)


class SoundClip:
    """One Sound's answer: asked once, kept.

    With no sink (a computer) ``classify`` is ``(Window, rate) -> (tag, scores)`` and the call waits for it. With a sink (a web
    page) the whole sound is sent as one window and the answer is None until it comes.
    """

    def __init__(self, context: tuple, classify, sink=None) -> None:
        self.context = context
        self._classify = classify
        self._sink = sink
        self._latest = Latest()
        self._asked = False

    def heard(self, frame: int, sound) -> Heard | None:
        if not self._asked:
            self._asked = True
            samples = array("f", sound.samples())
            rate = sound._sample_rate()
            if len(samples):
                window = Window(0, samples)
                if self._sink is not None:
                    self._sink.submit(window, rate)
                else:
                    self._latest.offer(_guesses(self._classify(window, rate)[1]))
        if self._sink is not None:
            for _tag, scores in self._sink.collect():
                self._latest.offer(_guesses(scores))
        return self._latest.heard(frame)
