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


def _open_mixer(headless: bool):
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
            raise ValueError("f.load_sound(): sound support is not available on this computer")
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


class Sound:
    """A sound from f.load_sound(). See contract A1 (playback) and A2 (analysis)."""

    def __init__(self, device_sound, mixer, silent: bool, frame_source=None):
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

    # ---- playback (A1)
    def _device_play(self, loops: int, resume: bool) -> None:
        if self._silent:
            return
        if resume and self._channel is not None and self._channel.get_sound() is self._snd:
            self._channel.unpause()
            return
        self._channel = self._snd.play(loops=loops)

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

    # ---- analysis (A2)
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
        """How loud the sound is now, from 0 to 1 (root mean square of the last 1/30 second).
        0 when the sound is not playing."""
        self._update()
        if self._state != "playing":
            return 0.0
        return self._cached("level", self._compute_level)

    def _compute_level(self) -> float:
        self._load_samples()
        window = self._window(max(1, round(self._rate * LEVEL_WINDOW)))
        return min(1.0, math.sqrt(sum(v * v for v in window) / len(window)))

    def spectrum(self, bands: int = 32) -> list[float]:
        """How strong the sound is now in each of *bands* ranges of pitch, from 0 to 1, low to
        high, evenly spaced in pitch from 40 Hz to 16 kHz. All zeros when not playing."""
        if isinstance(bands, bool) or not isinstance(bands, int) or not 1 <= bands <= MAX_BANDS:
            raise ValueError(f"sound.spectrum(): bands must be a whole number from 1 to {MAX_BANDS}, not {bands!r}")
        self._update()
        if self._state != "playing":
            return [0.0] * bands
        return list(self._cached(("spectrum", bands), lambda: self._compute_spectrum(bands)))

    def _compute_spectrum(self, bands: int) -> list[float]:
        self._load_samples()
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
