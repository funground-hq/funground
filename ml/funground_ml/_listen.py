"""Listening for words: what is kept for each microphone and each sound, and how phrases get to the model (S-234, contract ML6).

There are two sources.

* An **Ear** listens to a microphone. Each time ``ml.words(mic)`` is called it reads what the microphone has heard since the last
  call, cuts it into phrases (``_speech.PhraseCutter``) and hands each phrase to a **sink**, which works on it beside the sketch.
  It never waits for the model.
* A **Clip** is one Sound, answered once and kept.

There are two sinks, one for each way the models run. On a computer the ``Worker`` is a thread that holds at most one phrase
waiting (the newest wins) and works on it with Whisper. In a web page the ``HostSink`` sends the phrase to the host's models
(``host_services.models``), one in flight at a time with the newest waiting, and reads the newest answer back. Both give
``collect()`` the answers that have come in, and both keep an error from the thread or the host for the next call.

What the sketch sees is a ``Heard``: the newest answer, as a Words that is the same object for the whole of a frame.

This module imports neither numpy nor onnxruntime: a web page loads it too.
"""
from __future__ import annotations

import threading
import weakref
from array import array
from typing import Callable

from ._results import Words
from ._speech import MIN_SCORE, PhraseCutter

Answer = tuple[str, float]                      # the words heard and the score


class Heard:
    """The newest answer for one source, as the sketch sees it frame by frame (contract ML6).

    ``offer`` takes an answer as it comes in (from any time). ``words(frame)`` is what the sketch gets: the first call in a
    frame settles the answer for that frame, and every call in the frame gets that same object. An answer that arrived since is
    shown from the next frame on. It is ``is_new`` in the frame it first shows, and a plain copy in the frames after.
    """

    def __init__(self) -> None:
        self._waiting: Answer | None = None      # arrived, not shown yet
        self._shown: Words | None = None
        self._frame: int | None = None

    def offer(self, text: str, score: float) -> None:
        """An answer from the model. One that is not words (a low score, or no text) is dropped, so the last answer stays."""
        text = text.strip()
        if text and score >= MIN_SCORE:
            self._waiting = (text, score)

    def words(self, frame: int) -> Words | None:
        """The Words for *frame*, or None before the first answer."""
        if frame != self._frame:
            self._frame = frame
            if self._waiting is not None:
                self._shown, self._waiting = Words(*self._waiting, is_new=True), None
            elif self._shown is not None and self._shown.is_new:
                self._shown = Words(self._shown.text, self._shown.score, is_new=False)
        return self._shown


class Worker:
    """One daemon thread that works on phrases, the newest first: a phrase that comes while one is being worked on waits, and a
    newer one takes its place. The thread starts with the first phrase.

    *transcribe* is ``(samples, rate) -> (text, score)``; it runs in the thread, so it can take its time to load the model. An
    error in it is kept and raised by the next ``collect()``, in the sketch's thread.
    """

    def __init__(self, transcribe: Callable[[array, int], Answer]) -> None:
        self._transcribe = transcribe
        self._condition = threading.Condition()
        self._waiting: tuple[array, int] | None = None
        self._answers: list[Answer] = []
        self._error: BaseException | None = None
        self._closed = False
        self._thread: threading.Thread | None = None

    def submit(self, samples: array, rate: int) -> None:
        with self._condition:
            self._waiting = (samples, rate)
            if self._thread is None:
                self._thread = threading.Thread(target=self._run, name="funground words", daemon=True)
                self._thread.start()
            self._condition.notify()

    def collect(self) -> list[Answer]:
        """The answers that came in since the last call. Raises the error the thread stopped on, if it did."""
        with self._condition:
            answers, self._answers = self._answers, []
            error, self._error = self._error, None
        if error is not None:
            raise error
        return answers

    def close(self) -> None:
        """Let the thread end (it is waiting for a phrase; one it is working on is finished first)."""
        with self._condition:
            self._closed = True
            self._condition.notify()

    def _run(self) -> None:
        while True:
            with self._condition:
                while self._waiting is None and not self._closed:
                    self._condition.wait()
                if self._closed:
                    return
                job, self._waiting = self._waiting, None
            try:
                answer = self._transcribe(*job)
            except BaseException as error:           # kept for the sketch: a thread must not lose it
                with self._condition:
                    self._error = error
                continue
            with self._condition:
                self._answers.append(answer)


class HostSink:
    """The sink for a web page: phrases go to the host's models (``HostModels.request_sound``), one in flight for this source,
    the newest waiting; the answers come back through ``HostModels.latest``."""

    TASK = "words"

    def __init__(self, models, key: int) -> None:
        self._models = models
        self._key = key
        self._waiting: tuple[array, int] | None = None
        self._seen = None

    def submit(self, samples: array, rate: int) -> None:
        self._waiting = (samples, rate)

    def collect(self) -> list[Answer]:
        models = self._models
        if self._waiting is not None and not models.busy(self.TASK, self._key):
            samples, rate = self._waiting
            if models.request_sound(self.TASK, self._key, samples.tobytes(), rate):
                self._waiting = None
        result = models.latest(self.TASK, self._key)
        if result is None or result is self._seen:
            return []
        self._seen = result
        return [(result.text, result.score)]

    def close(self) -> None:
        pass


class Ear:
    """Listens to one microphone and keeps its newest words.

    Each ``words(frame)`` reads the new sound, hands the phrases that ended to the sink, takes the answers that have come in, and
    returns the words for the frame. A microphone that is not listening gives the last answer (a silent one, with no device, hears only silence). The first look
    starts from the sound the microphone has now; after the microphone is started again (which clears what it heard) it starts
    from the beginning. If the sketch looked so rarely that the microphone's buffer (10 s) wrapped, the part that is gone is
    skipped, and the phrase open at that point is ended.
    """

    def __init__(self, context: tuple, mic, sink) -> None:
        # The microphone is not kept: the memory of an Ear is held by the microphone itself (a weak dictionary in _tasks).
        self.context = context                           # what it was made for (the model files, or the host): see _tasks
        self._sink = sink
        self._heard = Heard()
        self._cutter = PhraseCutter(mic._rate)
        self._version = mic._version
        self._position = mic._total if mic._listening else 0
        weakref.finalize(self, sink.close)

    def close(self) -> None:
        """Let go of the sink (the worker thread ends)."""
        self._sink.close()

    def words(self, frame: int, mic) -> Words | None:
        self._read(mic)
        for answer in self._sink.collect():              # after the reading, so a host sink sends a phrase the moment it is cut
            self._heard.offer(*answer)
        return self._heard.words(frame)

    def _read(self, mic) -> None:
        if not mic._listening:
            self._send(self._cutter.flush())             # stopping ends the phrase being said
            return
        if mic._version != self._version or mic._rate != self._cutter.rate:
            self._send(self._cutter.flush())
            if mic._rate != self._cutter.rate:
                self._cutter = PhraseCutter(mic._rate)
            self._version, self._position = mic._version, 0     # start() cleared the buffer: read it from the beginning
        chunk, total = mic._since(self._position)       # one reading under the microphone's lock: every sample once
        if total - self._position > len(chunk):          # the buffer wrapped: what is gone is gone
            self._send(self._cutter.flush())
        self._position = total
        if not chunk:
            return
        for phrase in self._cutter.feed(chunk):
            self._send(phrase)

    def _send(self, phrase: array | None) -> None:
        if phrase is not None:
            self._sink.submit(phrase, self._cutter.rate)


class Clip:
    """One Sound's words: asked once, kept.

    With no sink (a computer) ``transcribe`` is ``(samples, rate) -> (text, score)`` and the call waits for it. With a sink (a web
    page) the whole sound is sent as one phrase and the answer is None until it comes.
    """

    def __init__(self, context: tuple, transcribe: Callable[[array, int], Answer] | None, sink=None) -> None:
        self.context = context
        self._transcribe = transcribe
        self._sink = sink
        self._heard = Heard()
        self._asked = False

    def words(self, frame: int, sound) -> Words | None:
        if not self._asked:
            self._asked = True
            samples = array("f", sound.samples())
            rate = sound._sample_rate()
            if self._sink is not None:
                self._sink.submit(samples, rate)
            else:
                self._heard.offer(*self._transcribe(samples, rate))
        if self._sink is not None:
            for answer in self._sink.collect():
                self._heard.offer(*answer)
        return self._heard.words(frame)
