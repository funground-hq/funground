"""Sound playback and analysis (S-098, S-099; contract A1, A2; D-046).

This is the only funground module that uses ``pygame.mixer``. A sound keeps its own state
(playing, paused or stopped, and where it is), driven by a clock rather than by the sound
device. So ``is_playing()``, the position and the analysis behave the same with or without
audio (contract A2). With no device, or with FUNGROUND_HEADLESS=1, a sound is decoded the same
way and kept in time, but nothing is played.

The analysis is plain Python: no numpy.
"""
from __future__ import annotations

import cmath
import math
import os
import time
from array import array

from . import synth
from .typography import _resolve_path

# The time source, in seconds. It is the same clock the sketch's millis() uses
# (time.perf_counter). Tests replace it to drive time without sleeping.
clock = time.perf_counter

LEVEL_WINDOW = 1 / 30        # seconds of sound that level() measures
FFT_SIZE = 1024              # samples in the spectrum's window
LOW_HZ, HIGH_HZ = 40.0, 16000.0
MAX_BANDS = 256

_audible = True              # False once opening a real sound device has failed
_mixer_ready = False


def _is_headless() -> bool:
    return os.environ.get("FUNGROUND_HEADLESS", "").lower() in ("1", "true", "yes")


def _open_mixer(headless: bool, who: str = "f.load_sound()"):
    """Start pygame's mixer once. Returns the module. Falls back to SDL's silent 'dummy'
    driver (which still decodes files) when there is no device, or when headless."""
    global _audible, _mixer_ready
    import pygame

    mixer = pygame.mixer
    if _mixer_ready and mixer.get_init() and mixer.get_init()[1] == -16:
        return mixer
    if mixer.get_init() and mixer.get_init()[1] != -16:
        mixer.quit()                                  # we need plain 16-bit samples

    def start() -> bool:
        try:
            mixer.init(frequency=44100, size=-16, channels=2)
            return True
        except Exception:
            return False

    ok = False
    if not headless:
        ok = start()
        if not ok:
            _audible = False
    if not ok:
        old = os.environ.get("SDL_AUDIODRIVER")
        os.environ["SDL_AUDIODRIVER"] = "dummy"
        try:
            ok = start()
        finally:
            if old is None:
                del os.environ["SDL_AUDIODRIVER"]
            else:
                os.environ["SDL_AUDIODRIVER"] = old
        if not ok:
            raise ValueError(f"{who}: sound support is not available on this computer")
        if headless:
            _audible = False
    _mixer_ready = True
    return mixer


def load(path: str, base_dir: str | None, frame_source=None) -> "Sound":
    """Find, open and decode a sound file (contract A1). *frame_source* is a function giving
    the sketch's frame number, used to analyse at most once per frame."""
    resolved = _resolve_path(path, base_dir, "f.load_sound()", "sound")
    headless = _is_headless()
    mixer = _open_mixer(headless)
    try:
        device_sound = mixer.Sound(resolved)
    except Exception as exc:
        raise ValueError(f"f.load_sound(): {path!r} is not a sound funground can read ({exc})") from exc
    return Sound(device_sound, mixer, silent=headless or not _audible, frame_source=frame_source)


def create(samples, rate: int = 44100, frame_source=None, who: str = "f.create_sound()") -> "Sound":
    """A sound from a list of numbers from -1 to 1 (contract A3). Numbers outside are clipped."""
    if isinstance(rate, bool) or not isinstance(rate, int) or not 8000 <= rate <= 192000:
        raise ValueError(f"{who}: rate must be a whole number from 8000 to 192000, not {rate!r}")
    try:
        values = [float(v) for v in samples]
    except (TypeError, ValueError):
        raise ValueError(f"{who}: the samples must be a list of numbers from -1 to 1") from None
    if not values:
        raise ValueError(f"{who}: the samples list is empty, so there is no sound")
    if not all(math.isfinite(v) for v in values):
        raise ValueError(f"{who}: the samples must be numbers, not nan or infinity")
    if max(values) > 1.0 or min(values) < -1.0:
        values = [-1.0 if v < -1.0 else 1.0 if v > 1.0 else v for v in values]
    return _from_samples(values, rate, frame_source, who)


def _from_samples(values: list[float], rate: int, frame_source, who: str) -> "Sound":
    """Build a playable sound from clipped mono samples at *rate*."""
    if max(values) > 1.0 or min(values) < -1.0:         # a filter can overshoot a little
        values = [-1.0 if v < -1.0 else 1.0 if v > 1.0 else v for v in values]
    headless = _is_headless()
    mixer = _open_mixer(headless, who)
    mixer_rate, _, channels = mixer.get_init()
    data = synth.resample(values, rate, mixer_rate) if mixer_rate != rate else values
    mono = array("h", [int(round(v * 32767)) for v in data])
    if channels == 1:
        pcm = mono
    else:                                               # the same sound in every channel
        pcm = array("h", bytes(2 * len(mono) * channels))
        for c in range(channels):
            pcm[c::channels] = mono
    device_sound = mixer.Sound(buffer=pcm.tobytes())
    return Sound(device_sound, mixer, silent=headless or not _audible, frame_source=frame_source,
                 made=(values, rate, pcm))


def _pan_gains(pan: float) -> tuple[float, float]:
    """The pan law: a balance control. The side you move away from fades to nothing in a straight
    line, and the other side stays at full volume, so 0 (the middle) is the sound unchanged."""
    return min(1.0, 1.0 - pan), min(1.0, 1.0 + pan)


def _fft(values: list[complex]) -> list[complex]:
    """Iterative radix-2 FFT of FFT_SIZE values."""
    a = [values[i] for i in _REVERSED]
    size = FFT_SIZE
    for half, w in _STAGES:
        for start in range(0, size, half * 2):
            for k in range(half):
                i = start + k
                j = i + half
                t = w[k] * a[j]
                u = a[i]
                a[i] = u + t
                a[j] = u - t
    return a


_REVERSED = [int(format(i, "010b")[::-1], 2) for i in range(FFT_SIZE)]
_TWIDDLES = [cmath.exp(-2j * math.pi * k / FFT_SIZE) for k in range(FFT_SIZE // 2)]
_STAGES = [(half, _TWIDDLES[::FFT_SIZE // (half * 2)][:half]) for half in (1 << n for n in range(10))]
_HANN = [0.5 - 0.5 * math.cos(2 * math.pi * i / (FFT_SIZE - 1)) for i in range(FFT_SIZE)]


class _Analysis:
    """level(), spectrum() and pitch(), shared by sounds (A2, A3) and microphones (A4).

    A class using it provides ``_window(count)`` (the latest *count* mono samples), ``_rate``,
    ``_version``, ``_cache``, ``_frame_source``, ``_name``, ``_analysing()`` (is there anything to
    measure now?) and ``_ready()`` (make the samples available)."""

    def _cached(self, key, compute):
        frame = self._frame_source() if self._frame_source else 0
        if frame > 0:                                   # frame 0 (setup, scripts) is not cached
            full = (frame, self._version, key)
            hit = self._cache.get("entry")
            if hit and hit[0] == full:
                return hit[1]
        value = compute()
        if frame > 0:
            self._cache["entry"] = (full, value)
        return value

    def level(self) -> float:
        """How loud it is now, from 0 to 1 (root mean square of the last 1/30 second).
        0 when nothing is playing or listening."""
        if not self._analysing():
            return 0.0
        return self._cached("level", self._compute_level)

    def _compute_level(self) -> float:
        self._ready()
        window = self._window(max(1, round(self._rate * LEVEL_WINDOW)))
        return min(1.0, math.sqrt(sum(v * v for v in window) / len(window)))

    def spectrum(self, bands: int = 32) -> list[float]:
        """How strong the sound is now in each of *bands* ranges of pitch, from 0 to 1, low to
        high, evenly spaced in pitch from 40 Hz to 16 kHz. All zeros when not playing."""
        if isinstance(bands, bool) or not isinstance(bands, int) or not 1 <= bands <= MAX_BANDS:
            raise ValueError(f"{self._name}.spectrum(): bands must be a whole number from 1 to {MAX_BANDS}, not {bands!r}")
        if not self._analysing():
            return [0.0] * bands
        return list(self._cached(("spectrum", bands), lambda: self._compute_spectrum(bands)))

    def _compute_spectrum(self, bands: int) -> list[float]:
        self._ready()
        window = self._window(FFT_SIZE)
        if not any(window):
            return [0.0] * bands
        result = _fft([v * w + 0j for v, w in zip(window, _HANN)])
        # A full-scale sine at a bin's centre gives |X| = FFT_SIZE / 4 with a Hann window,
        # so dividing by that gives 1 for it. A band's strength is its strongest bin.
        norm = 4.0 / FFT_SIZE
        mags = [abs(result[k]) * norm for k in range(FFT_SIZE // 2 + 1)]
        bin_hz = self._rate / FFT_SIZE
        top = min(HIGH_HZ, self._rate / 2)
        ratio = (HIGH_HZ / LOW_HZ) ** (1.0 / bands)
        edges = [LOW_HZ * ratio ** i for i in range(bands + 1)]
        strongest = [None] * bands
        for k in range(1, FFT_SIZE // 2 + 1):
            hz = k * bin_hz
            if hz < LOW_HZ or hz >= HIGH_HZ:
                continue
            band = min(bands - 1, int(math.log(hz / LOW_HZ) / math.log(ratio)))
            if strongest[band] is None or mags[k] > strongest[band]:
                strongest[band] = mags[k]
        out = []
        for b in range(bands):
            if strongest[b] is not None:
                value = strongest[b]
            else:                                       # a band narrower than one bin:
                centre = math.sqrt(edges[b] * edges[b + 1]) / bin_hz   # read between bins
                if edges[b] >= top:
                    value = 0.0
                else:
                    lo = int(centre)
                    frac = centre - lo
                    value = mags[lo] * (1 - frac) + mags[min(lo + 1, len(mags) - 1)] * frac
            out.append(max(0.0, min(1.0, value)))
        return out

    def pitch(self) -> float | None:
        """The frequency, in hertz, of the one voice heard now, or None when it is quiet or has no
        clear pitch (or nothing is playing or listening). It looks at the last 2 048 samples. It is
        for one voice or instrument at a time, not chords."""
        if not self._analysing():
            return None
        return self._cached("pitch", self._compute_pitch)

    def _compute_pitch(self) -> float | None:
        self._ready()
        return synth.find_pitch(self._window(synth.PITCH_WINDOW), self._rate)


class Sound(_Analysis):
    """A sound from f.load_sound(). See contract A1 (playback) and A2 (analysis)."""

    def __init__(self, device_sound, mixer, silent: bool, frame_source=None, made=None):
        self._snd = device_sound
        self._mixer = mixer
        self._silent = silent
        self._frame_source = frame_source
        self._duration = float(device_sound.get_length())
        self._channel = None
        self._volume = 1.0
        self._state = "stopped"          # "stopped", "playing" or "paused"
        self._t0 = 0.0                   # clock value at position 0 while playing
        self._held = 0.0                 # position kept while paused
        self._loop = False
        self._version = 0                # changes whenever playback state changes
        self._samples: array | None = None
        self._channels = 1
        self._rate = 44100
        self._cache: dict = {}
        self._pan = 0.0
        self._name = "sound"
        self._made = None                # (mono samples, their rate) for a sound made from numbers
        if made is not None:             # keep the samples, as a loaded sound does after first use
            values, rate, pcm = made
            self._made = (values, rate)
            self._samples = pcm
            self._rate, _, self._channels = mixer.get_init()

    # ---- playback (A1)
    def _device_play(self, loops: int, resume: bool) -> None:
        if self._silent:
            return
        if resume and self._channel is not None and self._channel.get_sound() is self._snd:
            self._channel.unpause()
            return
        self._channel = self._snd.play(loops=loops)
        if self._pan != 0.0:                           # a new play starts at full volume, the middle
            self._apply_pan()

    def _apply_pan(self) -> None:
        """Pan is the channel's left and right volume. It needs no change to the sound itself, so it
        works on any sound, and level() and spectrum() (which read the sound) ignore it."""
        channel = self._channel
        if self._silent or channel is None or channel.get_sound() is not self._snd:
            return
        left, right = _pan_gains(self._pan)
        channel.set_volume(left, right)

    def pan(self, position: float) -> None:
        """Move the sound between the speakers, from -1 (all left) to 1 (all right). 0 is the middle."""
        if isinstance(position, bool) or not isinstance(position, (int, float)) or not -1 <= position <= 1:
            raise ValueError(f"sound.pan(): pan must be from -1 (left) to 1 (right), not {position!r}")
        self._pan = float(position)
        self._apply_pan()
    def _start(self, loop: bool) -> None:
        self._update()
        resume = self._state == "paused"
        if self._state == "playing":                   # already playing: start again
            self._device_stop()
        position = self._held if resume else 0.0
        self._loop = loop
        self._t0 = clock() - position
        self._state = "playing"
        self._version += 1
        self._device_play(-1 if loop else 0, resume and not self._silent)

    def _device_stop(self) -> None:
        if not self._silent:
            self._snd.stop()

    def play(self) -> None:
        """Play from the start, or from where pause() left it. Playing again starts it again."""
        self._start(False)

    def loop(self) -> None:
        """Play over and over."""
        self._start(True)

    def stop(self) -> None:
        """Stop and go back to the start."""
        self._device_stop()
        self._state = "stopped"
        self._held = 0.0
        self._version += 1

    def pause(self) -> None:
        """Stop and keep the place; play() carries on from there."""
        self._update()
        if self._state != "playing":
            return
        self._held = self._position_now()
        self._state = "paused"
        self._version += 1
        if not self._silent and self._channel is not None:
            self._channel.pause()

    def set_volume(self, volume: float) -> None:
        """Set the loudness, from 0 (silent) to 1 (full)."""
        if isinstance(volume, bool) or not isinstance(volume, (int, float)) or not 0 <= volume <= 1:
            raise ValueError(f"sound.set_volume(): volume must be from 0 to 1, not {volume!r}")
        self._volume = float(volume)
        if not self._silent:
            self._snd.set_volume(self._volume)

    def get_volume(self) -> float:
        """The loudness set by set_volume() (1 at first)."""
        return self._volume

    def is_playing(self) -> bool:
        """True while the sound is playing (a paused or finished sound is not playing)."""
        self._update()
        return self._state == "playing"

    def duration(self) -> float:
        """The length of the sound, in seconds."""
        return self._duration

    def current_time(self) -> float:
        """Where the sound is now, in seconds from its start."""
        self._update()
        return self._position_now()

    # ---- the clock
    def _position_now(self) -> float:
        if self._state == "playing":
            raw = clock() - self._t0
            if self._loop and self._duration > 0:
                return raw % self._duration
            return min(raw, self._duration)
        return self._held

    def _update(self) -> None:
        """A sound that is not looping stops when its time is up."""
        if self._state == "playing" and not self._loop and clock() - self._t0 >= self._duration:
            self._state = "stopped"
            self._held = 0.0
            self._version += 1

    # ---- analysis (A2): level, spectrum and pitch come from _Analysis
    def _analysing(self) -> bool:
        self._update()
        return self._state == "playing"

    def _ready(self) -> None:
        self._load_samples()

    def _load_samples(self) -> None:
        if self._samples is None:
            info = self._mixer.get_init()
            self._rate, _, self._channels = info
            samples = array("h")
            samples.frombytes(self._snd.get_raw())
            self._samples = samples

    def _window(self, count: int):
        """The *count* samples ending at the playing position, mixed to mono, as floats from
        -1 to 1. Before the start (or, when looping, across the wrap) it takes what is there."""
        self._load_samples()
        samples, channels = self._samples, self._channels
        frames = len(samples) // channels
        if frames == 0:
            return [0.0] * count
        end = int(self._position_now() * self._rate)
        end = min(end, frames)
        start = end - count
        if start >= 0:
            parts = [(start, end)]
            pad = 0
        elif self._loop:
            parts = [(max(frames + start, 0), frames), (0, end)]
            pad = max(0, -start - frames)
        else:
            parts = [(0, end)]
            pad = -start
        out = [0.0] * pad
        scale = 1.0 / (32768.0 * channels)
        for a, b in parts:
            chunk = samples[a * channels:b * channels]
            if channels == 1:
                out.extend(v / 32768.0 for v in chunk)
            elif channels == 2:
                out.extend((chunk[i] + chunk[i + 1]) * scale for i in range(0, len(chunk), 2))
            else:
                out.extend(sum(chunk[i:i + channels]) * scale for i in range(0, len(chunk), channels))
        return out

    # ---- the numbers, saving and pitch (A3)
    def samples(self) -> list[float]:
        """The sound as one list of numbers from -1 to 1 (one channel, however many it has).
        Draw it to see the wave. Pan and volume are not in it."""
        if self._made is not None:
            return list(self._made[0])
        self._load_samples()
        return _to_mono(self._samples, self._channels)

    def _samples_at(self, rate: int) -> list[float]:
        """The same numbers at *rate* samples a second."""
        if self._made is not None:
            return synth.resample(self._made[0], self._made[1], rate)
        return synth.resample(self.samples(), self._rate, rate)

    def save(self, path: str) -> None:
        """Write the sound to a 16-bit WAV file. The pan is kept; the volume is not."""
        import wave

        if not isinstance(path, str) or not path:
            raise ValueError(f"sound.save(): give a file name like 'tune.wav', not {path!r}")
        self._load_samples()
        pcm = self._samples
        if self._channels == 2 and self._pan != 0.0:
            left, right = _pan_gains(self._pan)
            pcm = array("h", pcm)
            pcm[0::2] = array("h", [int(round(v * left)) for v in pcm[0::2]])
            pcm[1::2] = array("h", [int(round(v * right)) for v in pcm[1::2]])
        try:
            with wave.open(path, "wb") as out:
                out.setnchannels(self._channels)
                out.setsampwidth(2)
                out.setframerate(self._rate)
                out.writeframes(pcm.tobytes())
        except OSError as exc:
            raise ValueError(f"sound.save(): could not write {path!r} ({exc})") from exc


def _to_mono(samples: array, channels: int) -> list[float]:
    if channels == 1:
        return [v / 32768.0 for v in samples]
    scale = 1.0 / (32768.0 * channels)
    return [sum(samples[i:i + channels]) * scale for i in range(0, len(samples), channels)]


def sequence(sounds, frame_source=None) -> "Sound":
    """Sounds one after another, as a new sound (contract A3)."""
    parts = _check_sounds(sounds, "f.sequence()")
    out: list[float] = []
    for s in parts:
        out.extend(s._samples_at(synth.RATE))
    return _from_samples(out, synth.RATE, frame_source, "f.sequence()")


def mix(sounds, frame_source=None) -> "Sound":
    """Sounds together, as a new sound. Scaled down only if the sum would clip."""
    parts = _check_sounds(sounds, "f.mix()")
    return _from_samples(synth.mix_samples([s._samples_at(synth.RATE) for s in parts]),
                         synth.RATE, frame_source, "f.mix()")


def _check_sounds(sounds, who: str) -> list:
    sounds = list(sounds)
    if not sounds:
        raise ValueError(f"{who}: give it at least one sound")
    for s in sounds:
        if not isinstance(s, Sound):
            raise ValueError(f"{who}: every argument must be a sound, not {s!r}")
    return sounds


def make(values: list[float], frame_source=None, who: str = "f.tone()") -> "Sound":
    """A sound from samples that synth.py computed (already from -1 to 1, at 44 100)."""
    return _from_samples(values, synth.RATE, frame_source, who)
