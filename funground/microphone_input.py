"""Microphone input (S-108; contract A4; D-058).

With ``sound.py`` this is the only funground module that uses pygame's audio. It uses
``pygame._sdl2.audio``, which is pygame-ce's *experimental* module (pygame-ce 2.5 or newer), so all
access to it is in ``_sdl2_audio()``, ``_device_names()`` and ``_open_capture()``.

A microphone listens on SDL's audio thread. The callback copies what it hears into a ring buffer of
the last 10 seconds of mono samples. A lock guards the buffer, because the callback writes on that
thread while the sketch reads on its own. The analysis (level, spectrum, pitch) is the same code that
sounds use (``sound._Analysis``). The microphone is never played back.
"""
from __future__ import annotations

from array import array
from threading import Lock

from . import sound as _sound
from .sound import _Analysis, _is_headless

BUFFER_SECONDS = 10
RATE = 44100
CHUNK = 512

_NEEDS_NEW_PYGAME = ("microphone input needs pygame-ce 2.5 or newer (its pygame._sdl2.audio module "
                     "was not found). Update it with: pip install --upgrade pygame-ce")


def _no_device_message(extra: str = "") -> str:
    return ("f.microphone(): " + (extra or "no microphone was found on this computer")
            + ". Check that one is plugged in. On a Mac, allow microphone access in System Settings, "
              "Privacy & Security, Microphone.")


# ---- a host's microphone (the web runner)
_host_input = None           # the host's microphone while a web Session runs (platform/browser_audio.py), else None


def use_host_input(host) -> None:
    """Listen through a host's microphone (the web runner, Web_Runner_Note.md) instead of SDL's, or with None back to SDL.

    The host opens the device and pushes what it hears into `host.feed(samples)`; the Microphone's ring buffer and
    everything that reads it are unchanged. See platform/browser_audio.HostMicrophone."""
    global _host_input
    _host_input = host


# ---- the one place that touches the experimental module
def _sdl2_audio():
    try:
        import pygame
        import pygame._sdl2.audio as audio

        audio.AudioDevice, audio.get_audio_device_names, audio.AUDIO_F32, audio.AUDIO_ALLOW_FORMAT_CHANGE
    except (ImportError, AttributeError):
        raise RuntimeError(_NEEDS_NEW_PYGAME) from None
    if not pygame.get_init():                 # the audio listing needs pygame started
        pygame.init()
    return audio


def _device_names() -> list[str]:
    """The names of the computer's input devices."""
    audio = _sdl2_audio()
    try:
        return list(audio.get_audio_device_names(True))
    except Exception as exc:
        raise RuntimeError(_no_device_message(f"the computer's audio system did not answer ({exc})")) from exc


def _open_capture(name: str | None, callback):
    """Open an input device that calls ``callback(samples)`` with a list of floats from -1 to 1.
    Returns ``(device, rate)``. The device has ``pause(0)`` to listen, ``pause(1)`` to stop and
    ``close()``."""
    if _host_input is not None:
        return _host_input.open_capture(callback)
    audio = _sdl2_audio()

    def on_audio(device, view):
        # Keep this short: it runs on SDL's audio thread.
        raw = bytes(view)
        if device.audioformat == audio.AUDIO_F32:
            chunk = array("f")
            chunk.frombytes(raw[: len(raw) // 4 * 4])
        else:                                                    # S16 (or whatever else was granted)
            ints = array("h")
            ints.frombytes(raw[: len(raw) // 2 * 2])
            chunk = array("f", [v / 32768.0 for v in ints])
        channels = device.numchannels
        if channels > 1:
            chunk = array("f", [sum(chunk[i:i + channels]) / channels
                                for i in range(0, len(chunk) - channels + 1, channels)])
        callback(chunk)

    try:
        device = audio.AudioDevice(devicename=name, iscapture=True, frequency=RATE,
                                   audioformat=audio.AUDIO_F32, numchannels=1, chunksize=CHUNK,
                                   allowed_changes=audio.AUDIO_ALLOW_FORMAT_CHANGE, callback=on_audio)
    except Exception as exc:
        raise RuntimeError(_no_device_message(f"the microphone could not be opened ({exc})")) from exc
    return device, int(getattr(device, "frequency", RATE) or RATE)


def microphones() -> list[str]:
    """The names of the computer's microphones (inputs). Empty when headless, and in the browser (it picks the input)."""
    if _host_input is not None or _is_headless():
        return []
    return _device_names()


def make(name: str | None = None, frame_source=None) -> "Microphone":
    """A microphone for the default input, or the first whose name contains *name* (A4)."""
    if name is not None and (not isinstance(name, str) or not name):
        raise ValueError(f"f.microphone(): name must be text such as 'USB', not {name!r}")
    if _host_input is not None:
        if name is not None:
            raise RuntimeError("f.microphone(name): choosing a microphone by name only works in the desktop version. "
                               "In the browser, use f.microphone() and choose the input in the browser's own settings.")
        return Microphone(None, frame_source)
    if _is_headless():
        return Microphone(None, frame_source, silent=True)
    names = _device_names()
    if not names:
        raise RuntimeError(_no_device_message())
    if name is None:
        return Microphone(None, frame_source)                     # None means the default input
    for candidate in names:
        if name.lower() in candidate.lower():
            return Microphone(candidate, frame_source)
    raise RuntimeError(_no_device_message(f"no microphone has {name!r} in its name (they are: "
                                          + ", ".join(repr(n) for n in names) + ")"))


class Microphone(_Analysis):
    """A microphone that your sketch can listen to.

    You get one from f.microphone(). Call start() to begin listening and stop() to end. While it listens,
    level(), spectrum(), pitch(), is_onset(), chroma(), chord(), tonic() and swara_histogram() work as they
    do on a Sound. They tell you about the last fraction of a second. When it is not listening they give 0,
    a list of zeros, None or False.

    capture(seconds) gives you a Sound made of the last few seconds it heard (up to 10), so you can play
    it, save it, draw it or look at its whole-sound features such as tempo().

    The microphone is never played back, so there is no squeal from the speakers. Nothing is recorded to a
    file unless you call save() on a capture. With FUNGROUND_HEADLESS=1 it is silent and hears nothing.

    Example:
        mic = f.microphone()
        mic.start()
        f.circle(200, 200, 20 + 400 * mic.level())

    See also: microphone, microphones, Sound
    """

    def __init__(self, device_name: str | None, frame_source=None, silent: bool = False):
        self._device_name = device_name
        self._silent = silent
        self._frame_source = frame_source
        self._name = "microphone"
        self._device = None
        self._listening = False
        self._rate = RATE
        self._version = 0                 # changes when listening starts or stops
        self._cache: dict = {}
        self._lock = Lock()
        self._size = BUFFER_SECONDS * RATE
        self._ring = array("f", bytes(4 * self._size))
        self._total = 0                   # samples ever written; the newest is at (_total - 1) % size

    # ---- listening
    def start(self) -> None:
        """Start listening.

        It forgets what it heard before. Calling it when it is already listening does nothing.

        Raises:
            RuntimeError: if there is no microphone, or the computer will not let funground use it.

        Example:
            mic = f.microphone()
            mic.start()

        See also: stop, is_listening, capture
        """
        if self._listening:
            return
        with self._lock:
            self._total = 0
        if not self._silent:
            if self._device is None:
                self._device, self._rate = _open_capture(self._device_name, self._feed)
                self._size = BUFFER_SECONDS * self._rate
                self._ring = array("f", bytes(4 * self._size))
            self._device.pause(0)
        self._listening = True
        self._version += 1

    def stop(self) -> None:
        """Stop listening, but keep what was heard, so that capture() still works.

        Example:
            recording = mic.capture(2)
            mic.stop()

        See also: start, capture
        """
        if not self._listening:
            return
        if self._device is not None:
            self._device.pause(1)
        self._listening = False
        self._version += 1

    def is_listening(self) -> bool:
        """Whether the microphone is listening.

        Returns:
            True between start() and stop(), otherwise False.

        Example:
            if not mic.is_listening():
                mic.start()

        See also: start, stop
        """
        return self._listening

    # ---- the ring buffer
    def _feed(self, samples) -> None:
        """Add samples (floats from -1 to 1) to what the microphone has heard. The audio thread
        calls this; tests call it to play a microphone a known sound."""
        data = samples if isinstance(samples, array) and samples.typecode == "f" else array("f", samples)
        count = len(data)
        if count == 0:
            return
        with self._lock:
            if count >= self._size:                         # only the newest fit
                data = data[count - self._size:]
                count = self._size
            at = self._total % self._size
            first = min(count, self._size - at)
            self._ring[at:at + first] = data[:first]
            if first < count:
                self._ring[:count - first] = data[first:]
            self._total += count

    def _latest(self, count: int) -> list[float]:
        """The newest *count* samples, oldest first. Silence fills in what has not been heard."""
        with self._lock:
            have = min(count, self._total, self._size)
            end = self._total % self._size
            start = end - have
            if start >= 0:
                chunk = self._ring[start:end]
            else:
                chunk = self._ring[start:] + self._ring[:end]
        return [0.0] * (count - have) + chunk.tolist()

    # ---- analysis (A2, A3, A4): level, spectrum and pitch come from _Analysis
    def _analysing(self) -> bool:
        return self._listening

    def _ready(self) -> None:
        pass

    def _window(self, count: int) -> list[float]:
        return self._latest(count)

    def _stream_time(self) -> float:
        return self._total / self._rate

    # ---- not for a microphone: these look at a whole sound, so use capture() first (A5, A6)
    def _whole_sound_only(self, what: str):
        raise ValueError(f"microphone.{what}() looks at a whole sound. Use "
                         f"microphone.capture(seconds).{what}() to look at what was heard")

    def onsets(self):
        """Not for a microphone, because it looks at a whole sound.

        Use mic.capture(seconds).onsets() to look at what was heard.

        Raises:
            ValueError: always, with a message that points to capture().

        See also: capture, is_onset
        """
        self._whole_sound_only("onsets")

    def tempo(self):
        """Not for a microphone, because it looks at a whole sound.

        Use mic.capture(seconds).tempo() to look at what was heard.

        Raises:
            ValueError: always, with a message that points to capture().

        See also: capture
        """
        self._whole_sound_only("tempo")

    def beats(self):
        """Not for a microphone, because it looks at a whole sound.

        Use mic.capture(seconds).beats() to look at what was heard.

        Raises:
            ValueError: always, with a message that points to capture().

        See also: capture
        """
        self._whole_sound_only("beats")

    def key(self):
        """Not for a microphone, because it looks at a whole sound.

        Use mic.capture(seconds).key() to look at what was heard.

        Raises:
            ValueError: always, with a message that points to capture().

        See also: capture, chroma
        """
        self._whole_sound_only("key")

    # ---- capture
    def capture(self, seconds: float):
        """Make a new sound from the last few seconds the microphone heard.

        If it has heard less than that, the start is silence, so the sound is always as long as you asked.
        It is an ordinary Sound: play it, save it, or draw its wave with samples().

        Arguments:
            seconds: how much to keep, more than 0 and at most 10.

        Returns:
            a new Sound that is `seconds` long.

        Raises:
            ValueError: if seconds is not more than 0 and at most 10.

        Example:
            mic = f.microphone()
            mic.start()
            recording = mic.capture(1)   # use it after about a second
            recording.save("heard.wav")  # writes a new file

        See also: start, stop
        """
        if (isinstance(seconds, bool) or not isinstance(seconds, (int, float))
                or not 0 < seconds <= BUFFER_SECONDS):
            raise ValueError(f"microphone.capture(): seconds must be more than 0 and at most "
                             f"{BUFFER_SECONDS}, not {seconds!r}")
        count = max(1, round(seconds * self._rate))
        values = [max(-1.0, min(1.0, v)) for v in self._latest(count)]
        return _sound._from_samples(values, self._rate, self._frame_source, "microphone.capture()")

    def close(self) -> None:
        """Stop listening and let go of the microphone.

        funground calls it when a sketch ends, so you do not need to.

        Example:
            mic.close()

        See also: stop
        """
        self.stop()
        if self._device is not None:
            try:
                self._device.close()
            except Exception:
                pass
            self._device = None
