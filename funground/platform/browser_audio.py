"""Sound and the microphone for a host that owns the audio device (story S-137, Web_Runner_Note.md).

funground makes every sound itself, in Python, and keeps its own clock (contract A1, A2). The only thing it asks
of a device is to play a buffer, stop it, pause it and change its volume. `sound.py` asks pygame.mixer for
exactly that, through a few calls; `HostMixer` answers the same calls, and hands each to the host as a command
instead. So `sound.py` is unchanged below its choice of mixer, and pygame is not imported.

The host callback is `on_sound(command, voice, fields, samples)`:

    command   fields                                      samples
    load      rate, channels, frames                      float32 (a memoryview), interleaved, -1 to 1
    play      loops (-1 forever, 0 once), volume,         None
              left, right (the pan gains)
    pause     -                                           None
    resume    -                                           None
    volume    volume                                      None
    pan       left, right                                 None
    stop      -                                           None
    free      -                                           None   (the sound was dropped: forget its buffer)
    stop_all  -                                           None   (the run ended; voice is 0)

`voice` is the sound's number. A sound is sent once, with its first play, and then played by its number. The
host plays from its own clock and need not tell Python when a sound ends: Python's clock knows (contract A2).

The microphone is the other way round: the host opens the input, and pushes what it hears to
`HostMicrophone.feed(samples)`, which goes into the same ring buffer the desktop code fills.
`on_microphone(command)` is told "start", "stop" or "close".
"""
from __future__ import annotations

import wave
import weakref
from array import array
from collections.abc import Callable

from .. import synth

SoundCallback = Callable[[str, int, dict, "memoryview | None"], None]
MicrophoneCallback = Callable[[str], None]

RATE = 44100                          # the mixer's format, as pygame's mixer is opened (sound._open_mixer)
CHANNELS = 2
_TO_FLOAT = 1 / 32768.0               # 16-bit samples to the range -1 to 1


class HostChannel:
    """What pygame's mixer calls a channel: one play of a sound, which can be paused and given left and right volumes."""

    def __init__(self, sound: "HostSound") -> None:
        self._sound: HostSound | None = sound

    def get_sound(self) -> "HostSound | None":
        return self._sound

    def pause(self) -> None:
        if self._sound is not None:
            self._sound._command("pause")

    def unpause(self) -> None:
        if self._sound is not None:
            self._sound._command("resume")

    def set_volume(self, left: float, right: float) -> None:
        if self._sound is not None:
            self._sound._command("pan", left=float(left), right=float(right))

    def _ended(self) -> None:
        self._sound = None


class HostSound:
    """What pygame's mixer calls a Sound: samples that can be played, stopped, and given a volume."""

    def __init__(self, mixer: "HostMixer", pcm: bytes) -> None:
        self._mixer = mixer
        self._pcm = pcm                                       # 16-bit, CHANNELS interleaved, at RATE
        self._id = mixer._next_id()
        self._loaded = False
        self._volume = 1.0
        self._channel: HostChannel | None = None

    def get_length(self) -> float:
        return len(self._pcm) / (2 * CHANNELS * RATE)

    def get_raw(self) -> bytes:
        return self._pcm

    def play(self, loops: int = 0) -> HostChannel:
        self._load()
        self._finish_channel()
        self._channel = HostChannel(self)
        self._command("play", loops=loops, volume=self._volume, left=1.0, right=1.0)   # a new play starts in the middle
        return self._channel

    def stop(self) -> None:
        self._command("stop")
        self._finish_channel()

    def set_volume(self, volume: float) -> None:
        self._volume = float(volume)
        self._command("volume", volume=self._volume)

    # ---- the host
    def _load(self) -> None:
        """Send the samples, once, as 32-bit floats."""
        if self._loaded:
            return
        pcm = array("h")
        pcm.frombytes(self._pcm)
        samples = array("f", map(_TO_FLOAT.__mul__, pcm))
        self._loaded = True
        weakref.finalize(self, self._mixer._command, "free", self._id).atexit = False
        self._mixer._command("load", self._id, samples=memoryview(samples), rate=RATE, channels=CHANNELS,
                             frames=len(pcm) // CHANNELS)

    def _command(self, command: str, **fields) -> None:
        if self._loaded:
            self._mixer._command(command, self._id, **fields)

    def _finish_channel(self) -> None:
        if self._channel is not None:
            self._channel._ended()
            self._channel = None


class HostMixer:
    """The part of pygame.mixer that sound.py uses, with the host as the device."""

    def __init__(self, on_sound: SoundCallback | None = None) -> None:
        self._on_sound = on_sound
        self._ids = 0

    def get_init(self) -> tuple[int, int, int]:
        """(frequency, format, channels): 44 100 Hz, 16-bit, stereo, as the desktop's mixer is opened."""
        return (RATE, -16, CHANNELS)

    def Sound(self, source=None, buffer: bytes | None = None) -> HostSound:     # noqa: N802 (pygame's name)
        """A sound from a file path (a 16-bit WAV file) or from 16-bit stereo samples at 44 100 Hz."""
        if buffer is not None:
            return HostSound(self, bytes(buffer))
        return HostSound(self, _read_wav(source))

    def stop_all(self) -> None:
        self._command("stop_all", 0)

    def _next_id(self) -> int:
        self._ids += 1
        return self._ids

    def _command(self, command: str, voice: int, samples: "memoryview | None" = None, **fields) -> None:
        if self._on_sound is not None:
            self._on_sound(command, voice, fields, samples)


def _read_wav(path: str) -> bytes:
    """A WAV file as 16-bit stereo samples at 44 100 Hz (pygame does this for any file; here only 16-bit WAV is read)."""
    try:
        with wave.open(path, "rb") as source:
            channels, width, rate = source.getnchannels(), source.getsampwidth(), source.getframerate()
            raw = source.readframes(source.getnframes())
    except wave.Error as exc:
        raise ValueError(f"only 16-bit WAV files can be read in the browser (OGG and MP3 work on the desktop): {exc}") from exc
    if width != 2 or channels not in (1, 2):
        raise ValueError("only 16-bit WAV files, mono or stereo, can be read in the browser "
                         "(OGG and MP3 work on the desktop)")
    pcm = array("h")
    pcm.frombytes(raw)
    sides = [pcm[c::channels] for c in range(channels)]
    if rate != RATE:
        sides = [array("h", [round(v * 32768) for v in synth.resample([s / 32768 for s in side], rate, RATE)])
                 for side in sides]
    out = array("h", bytes(2 * CHANNELS * len(sides[0])))
    for c in range(CHANNELS):
        out[c::CHANNELS] = sides[min(c, channels - 1)]
    return out.tobytes()


class _CaptureDevice:
    """What SDL's capture device is to microphone_input: pause(0) listens, pause(1) stops, close() lets go."""

    def __init__(self, host: "HostMicrophone", callback: Callable[[array], None]) -> None:
        self._host = host
        self.callback = callback
        self.listening = False

    def pause(self, flag: int) -> None:
        self.listening = not flag
        self._host._request("stop" if flag else "start")

    def close(self) -> None:
        self.listening = False
        self._host._device = None
        self._host._request("close")


class HostMicrophone:
    """The host's microphone: it opens the input and pushes what it hears to `feed`."""

    RATE = RATE                                              # the host delivers 44 100 Hz, as the desktop asks SDL for

    def __init__(self, on_microphone: MicrophoneCallback | None = None) -> None:
        self._on_microphone = on_microphone
        self._device: _CaptureDevice | None = None

    def open_capture(self, callback: Callable[[array], None]) -> tuple[_CaptureDevice, int]:
        """The same answer as microphone_input._open_capture: (a device, its rate). Nothing is heard until pause(0)."""
        self._device = _CaptureDevice(self, callback)
        return self._device, RATE

    def feed(self, samples) -> None:
        """Mono samples from -1 to 1 at 44 100 Hz (any sequence of numbers, or a float32 buffer). Heard only while listening."""
        device = self._device
        if device is None or not device.listening:
            return
        device.callback(samples if isinstance(samples, array) and samples.typecode == "f" else array("f", samples))

    def close(self) -> None:
        """Let go of the input, if a sketch opened it."""
        if self._device is not None:
            self._device.close()

    def _request(self, command: str) -> None:
        if self._on_microphone is not None:
            self._on_microphone(command)
