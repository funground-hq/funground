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

from . import analysis, synth
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
    """The listening methods that a sound and a microphone share.

    level(), spectrum(), pitch(), is_onset(), chroma(), chord(), tonic() and swara_histogram() work in the
    same way on a Sound and on a Microphone. They tell you about the sound as it is now, so call them in
    draw(). They give 0, a list of zeros, None or False when nothing is playing or listening.

    The numbers are worked out in plain Python, in analysis.py and hindustani.py.
    """

    # Contract A2, A3, A5, A6 (sounds) and A4 (microphones). A class using this provides
    # ``_window(count)`` (the latest *count* mono samples), ``_rate``, ``_version``, ``_cache``,
    # ``_frame_source``, ``_name``, ``_analysing()`` (is there anything to measure now?) and
    # ``_ready()`` (make the samples available).

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
        """How loud the sound is right now, from 0 (silent) to 1.

        It is the root mean square of the last 1/30 of a second, so it follows the music. It is 0 when the
        sound is not playing, or the microphone is not listening.

        Returns:
            a number from 0 to 1.

        Example:
            snd = f.load_sound("song.wav")   # your own file
            snd.loop()
            f.circle(200, 200, 50 + 300 * snd.level())

        See also: spectrum, pitch, is_onset
        """
        if not self._analysing():
            return 0.0
        return self._cached("level", self._compute_level)

    def _compute_level(self) -> float:
        self._ready()
        window = self._window(max(1, round(self._rate * LEVEL_WINDOW)))
        return min(1.0, math.sqrt(sum(v * v for v in window) / len(window)))

    def spectrum(self, bands: int = 32) -> list[float]:
        """How strong the sound is now in each of several ranges of pitch, from low notes to high notes.

        The ranges are called bands. They are spaced evenly in pitch, from 40 Hz to 16 kHz, so each one is
        about the same number of notes wide. A band is strong when the sound has a lot of that pitch. You get
        a list of zeros when the sound is not playing, or the microphone is not listening.

        Arguments:
            bands: how many ranges to split the sound into, a whole number from 1 to 256. It is 32 at first.

        Returns:
            a list of `bands` numbers from 0 to 1, lowest pitch first.

        Raises:
            ValueError: if bands is not a whole number from 1 to 256.

        Example:
            snd = f.tone(220, 2)
            snd.play()
            for i, strength in enumerate(snd.spectrum(16)):
                f.rect(20 + i * 24, 380, 20, -300 * strength)

        See also: level, pitch, chroma
        """
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
        """The frequency of the one voice or instrument heard right now.

        It looks at the last 2 048 samples. It is for one note at a time, not for chords. It looks for
        pitches from 50 to 2000 Hz. It gives None when the sound is quiet, when it has no clear pitch (noise
        has none), or when nothing is playing or listening.

        Returns:
            the frequency in hertz, or None.

        Example:
            mic = f.microphone()
            mic.start()
            hz = mic.pitch()
            if hz:
                f.text(f.frequency_to_note(hz), 20, 40)

        See also: chroma, chord, level
        """
        if not self._analysing():
            return None
        return self._cached("pitch", self._compute_pitch)

    def _compute_pitch(self) -> float | None:
        self._ready()
        return synth.find_pitch(self._window(synth.PITCH_WINDOW), self._rate)

    def is_onset(self) -> bool:
        """Whether a new note or hit is heard in this frame.

        Use it to flash a light on each beat or note. It looks at the last 0.3 seconds. It is False
        when nothing is playing or listening.

        Returns:
            True in the frame where a new note or hit begins, otherwise False.

        Example:
            if song.is_onset():
                f.background("white")

        See also: onsets, level
        """
        if not self._analysing():
            self._onset_last = -1.0
            return False
        return self._cached("onset", self._compute_onset)

    def _compute_onset(self) -> bool:
        self._ready()
        now = self._stream_time()
        last = getattr(self, "_onset_last", -1.0)
        if now < last:                                  # the sound started again or looped
            last = -1.0
        count = max(1, round(self._rate * analysis.LIVE_SECONDS))
        window = self._window(count)
        times = analysis.live_onsets(window, self._rate)
        found = False
        for t in times:
            when = now - count / self._rate + t
            if when > last + analysis.LIVE_GAP:
                last = when
                found = True
        self._onset_last = last
        return found

    def chroma(self) -> list[float]:
        """How strong each of the twelve note names is right now, whatever the octave.

        The numbers are for C, C#, D, D#, E, F, F#, G, G#, A, A# and B, in that order. The strongest is 1.
        All of them are 0 when nothing is playing or listening, or when it is quiet.

        Returns:
            a list of 12 numbers from 0 to 1.

        Example:
            notes = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
            for i, strength in enumerate(song.chroma()):
                f.text(notes[i], 20 + i * 30, 380 - 200 * strength)

        See also: chord, pitch, key
        """
        if not self._analysing():
            return [0.0] * 12
        return list(self._cached("chroma", self._compute_chroma))

    def _compute_chroma(self) -> list[float]:
        self._ready()
        count = analysis.CHROMA_FRAME * max(1, round(self._rate / analysis.ANALYSIS_RATE))
        return analysis.chroma_of(self._window(count), self._rate)

    def chord(self) -> str | None:
        """The chord sounding now, as a name.

        The name is a note followed by nothing (major), m, dim, aug, 7, maj7 or m7, such as "C", "Am", "G7",
        "Fmaj7" or "Bdim". One voice on its own is not a chord. It is meant for clear chords on a piano, a
        guitar or a synth, not for a busy band.

        Returns:
            the chord name, or None when no chord stands out.

        Example:
            f.text(song.chord() or "-", 150, 100)

        See also: chroma, key, chord_notes
        """
        if not self._analysing():
            return None
        return self._cached("chord", lambda: analysis.chord_of(self._compute_chroma()))

    # ---- ragas (S-115, contract A8)
    def _pitch_track(self) -> list:
        """The pitch through the whole sound, or through the last 10 seconds a microphone heard
        (hindustani.pitch_track). A sound's track is kept, as its samples do not change."""
        from . import hindustani as ragas

        if isinstance(self, Sound):
            if "track" not in self._cache:
                self._cache["track"] = ragas.pitch_track(self._samples_at(synth.RATE), synth.RATE)[0]
            return self._cache["track"]
        return ragas.pitch_track(self._window(10 * self._rate), self._rate)[0]

    def tonic(self) -> float | None:
        """A guess at Sa, the starting note of a singer, in hertz.

        It counts how long each pitch was heard, folded into one octave. It then picks the pitch that best
        explains a strong Sa and Pa. It is a rough guide, not an answer. For a microphone it uses the last
        10 seconds. For a sound it uses the whole sound.

        Returns:
            the frequency of Sa in hertz, or None when too little had a clear pitch.

        Example:
            sa = recording.tonic()
            if sa:
                print(f.frequency_to_note(sa))

        See also: swara_histogram, pitch, match_ragas
        """
        from . import hindustani as ragas

        return ragas.tonic(self._pitch_track())

    def swara_histogram(self, sa) -> list[float]:
        """How much of the singing was on each swara.

        Each number is the share of the time with a clear pitch that was spent within 50 cents (half a
        semitone) of that swara, in any octave. The twelve swaras above Sa are S, r, R, g, G, m, M, P, d, D,
        n and N. The numbers add up to 1, or are all 0 if nothing had a pitch.

        Arguments:
            sa: the note that Sa is, as a note name like "D4" or as a number of hertz.

        Returns:
            a list of 12 numbers, the first for S and the last for N.

        Example:
            hist = recording.swara_histogram("D4")
            print(f.match_ragas(hist)[0])

        See also: tonic, match_ragas
        """
        from . import hindustani as ragas

        sa_hz = ragas._sa_hz(sa, f"{self._name}.swara_histogram()")
        return ragas.swara_histogram(self._pitch_track(), sa_hz)


class Sound(_Analysis):
    """A sound that you can play, listen to and change.

    You get one from f.load_sound() (a file), f.create_sound() (a list of numbers), f.tone(), f.note(),
    f.pluck(), f.melody(), f.drone() and f.tala() (made for you), f.sequence() and f.mix() (made from
    other sounds), and mic.capture() (made from what a microphone heard). All of them are the same kind
    of object.

    A sound keeps its own place and state (playing, paused or stopped), kept by a clock. So is_playing()
    and the listening methods behave the same with or without a sound device. With no device, or with
    FUNGROUND_HEADLESS=1, a sound plays silently and keeps time.

    Methods that change a sound's state (play, loop, stop, pause, set_volume, pan) change this sound.
    Methods that make something new (reverb) give you a new sound and leave this one alone.

    Example:
        beep = f.tone(440, 1)
        beep.play()
        f.circle(200, 200, 50 + 300 * beep.level())

    See also: load_sound, create_sound, tone, mix, Microphone
    """

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
        self._rhythm_result = None       # onsets, tempo and beats, worked out on first use (A5)
        self._key_result = None          # (key,) once worked out (A6)
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
        """Move the sound between the left and right speakers.

        It works on any sound. level() and spectrum() do not change with pan. save() keeps the pan.

        Arguments:
            position: a number from -1 (all left) to 1 (all right). 0 is the middle.

        Raises:
            ValueError: if position is not a number from -1 to 1.

        Example:
            snd = f.tone(440, 1)
            snd.pan(-1)     # left speaker only
            snd.play()

        See also: set_volume, play
        """
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
        """Play the sound from the start, or from where pause() left it.

        Playing a sound that is already playing starts it again from the start. A sound that is not
        looping stops by itself at the end.

        Example:
            beep = f.tone(440, 1)
            beep.play()

        See also: loop, pause, stop, is_playing
        """
        self._start(False)

    def loop(self) -> None:
        """Play the sound over and over, until you call stop() or pause().

        Example:
            drone = f.drone("D3", 8)
            drone.loop()

        See also: play, stop, pause
        """
        self._start(True)

    def stop(self) -> None:
        """Stop the sound and go back to its start.

        Example:
            snd = f.tone(440, 5)
            snd.play()
            snd.stop()

        See also: pause, play
        """
        self._device_stop()
        self._state = "stopped"
        self._held = 0.0
        self._version += 1

    def pause(self) -> None:
        """Stop the sound and keep the place, so that play() carries on from there.

        Nothing happens if the sound is not playing.

        Example:
            snd = f.tone(440, 5)
            snd.play()
            snd.pause()
            snd.play()     # carries on

        See also: play, stop, current_time
        """
        self._update()
        if self._state != "playing":
            return
        self._held = self._position_now()
        self._state = "paused"
        self._version += 1
        if not self._silent and self._channel is not None:
            self._channel.pause()

    def set_volume(self, volume: float) -> None:
        """Set how loud the sound plays.

        It does not change the numbers inside the sound, so level() and samples() are not affected.

        Arguments:
            volume: a number from 0 (silent) to 1 (full). It is 1 at first.

        Raises:
            ValueError: if volume is not a number from 0 to 1.

        Example:
            snd = f.tone(440, 1)
            snd.set_volume(0.3)
            snd.play()

        See also: get_volume, pan
        """
        if isinstance(volume, bool) or not isinstance(volume, (int, float)) or not 0 <= volume <= 1:
            raise ValueError(f"sound.set_volume(): volume must be from 0 to 1, not {volume!r}")
        self._volume = float(volume)
        if not self._silent:
            self._snd.set_volume(self._volume)

    def get_volume(self) -> float:
        """The loudness set by set_volume().

        Returns:
            a number from 0 to 1. It is 1 until you change it.

        Example:
            snd = f.tone(440, 1)
            snd.set_volume(0.5)
            print(snd.get_volume())

        See also: set_volume
        """
        return self._volume

    def is_playing(self) -> bool:
        """Whether the sound is playing now.

        A paused sound is not playing. A sound that has reached its end is not playing.

        Returns:
            True while the sound is playing, otherwise False.

        Example:
            if not song.is_playing():
                song.play()

        See also: play, pause, stop
        """
        self._update()
        return self._state == "playing"

    def duration(self) -> float:
        """The length of the sound.

        Returns:
            the length in seconds.

        Example:
            snd = f.tone(440, 2)
            print(snd.duration())     # 2.0 or a little more

        See also: current_time
        """
        return self._duration

    def current_time(self) -> float:
        """Where the sound is now.

        A sound that is stopped is at 0. A paused sound stays where it stopped.

        Returns:
            the time in seconds from the start of the sound.

        Example:
            snd = f.melody("C4 E4 G4")
            snd.loop()
            f.rect(0, 190, 400 * snd.current_time() / snd.duration(), 20)

        See also: duration, pause
        """
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

    def _stream_time(self) -> float:
        return self._position_now()

    # ---- rhythm and key of the whole sound (A5, A6)
    def _whole(self):
        """(all the samples as mono floats, their rate)."""
        if self._made is not None:
            return self._made
        return self.samples(), self._rate

    def _rhythm(self) -> "analysis.Rhythm":
        if self._rhythm_result is None:
            values, rate = self._whole()
            self._rhythm_result = analysis.Rhythm(values, rate)
        return self._rhythm_result

    def onsets(self) -> list[float]:
        """The times where a note or a hit begins.

        It looks at the whole sound. It is worked out once, then remembered. A three-minute song takes a few
        seconds the first time. A microphone has no whole sound, so use mic.capture(seconds).onsets().

        Returns:
            a list of times in seconds from the start, earliest first.

        Example:
            song = f.melody("C4 E4 G4 C5")
            print(song.onsets())

        See also: is_onset, tempo, beats
        """
        return list(self._rhythm().onsets)

    def tempo(self) -> float | None:
        """The speed of the music.

        It looks at the whole sound, and is worked out once. A sound with no clear pulse has no tempo.

        Returns:
            the speed in beats a minute, from 60 to 200, or None when there is no clear pulse.

        Example:
            song = f.melody("C4 E4 G4 E4 A3 C4 E4 C4", tempo=100, wave="triangle")
            print(song.tempo())

        See also: beats, onsets
        """
        return self._rhythm().tempo

    def beats(self) -> list[float]:
        """The times of the beats, at the sound's tempo.

        They are lined up with the onsets. It looks at the whole sound.

        Returns:
            a list of times in seconds from the start, or an empty list when there is no clear pulse.

        Example:
            song = f.melody("C4 E4 G4 E4 A3 C4 E4 C4", tempo=100, wave="triangle")
            beats = song.beats()
            song.play()

        See also: tempo, onsets, is_onset
        """
        return list(self._rhythm().beats)

    def key(self) -> str | None:
        """The key of the whole sound.

        It adds up the chroma over the whole sound and says which key fits best. It is worked out once.

        Returns:
            a name like "G major" or "E minor", or None when no key stands out.

        Example:
            song = f.melody("C4 E4 G4 C5 G4 E4 C4")
            print(song.key())

        See also: chord, chroma
        """
        if self._key_result is None:
            values, rate = self._whole()
            self._key_result = (analysis.key_of(values, rate),)
        return self._key_result[0]

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
        """The sound as a list of numbers.

        A sound is a long list of numbers, one for each tiny slice of time. A mono sound has 44 100 of them
        a second. If the sound has more than one channel, they are mixed into one. Draw them to see the wave.
        The pan and the volume are not in the numbers.

        Returns:
            a list of numbers from -1 to 1.

        Example:
            wave = f.tone(220, 1).samples()
            for x in range(399):
                f.line(x, 100 - 80 * wave[x * 4], x + 1, 100 - 80 * wave[x * 4 + 4])

        See also: create_sound, save
        """
        if self._made is not None:
            return list(self._made[0])
        self._load_samples()
        return _to_mono(self._samples, self._channels)

    def _sample_rate(self) -> int:
        """How many numbers a second samples() has."""
        if self._made is not None:
            return self._made[1]
        self._load_samples()
        return self._rate

    def _samples_at(self, rate: int) -> list[float]:
        """The same numbers at *rate* samples a second."""
        if self._made is not None:
            return synth.resample(self._made[0], self._made[1], rate)
        return synth.resample(self.samples(), self._rate, rate)

    def reverb(self, amount: float = 0.3) -> "Sound":
        """Make a new sound that is this sound played in a room.

        The room's echoes ring on after the end, so the new sound is longer, by up to 1.5 seconds at 1. The
        new sound has one channel. The volume and pan are not carried over. This sound is not changed.

        It takes a moment to work out: about a twentieth of a second for each second of sound. Make the new
        sound once, at the start, not in draw().

        Arguments:
            amount: the size of the room, from 0 (no room, the sound is unchanged) to 1 (a large hall). It is 0.3 at first.

        Returns:
            a new Sound.

        Raises:
            ValueError: if amount is not a number from 0 to 1.

        Example:
            dry = f.pluck("G3", 1.5)
            wet = dry.reverb(0.5)
            wet.play()

        See also: mix, sequence
        """
        if isinstance(amount, bool) or not isinstance(amount, (int, float)) or not 0 <= amount <= 1:
            raise ValueError(f"sound.reverb(): amount must be from 0 (dry) to 1 (a large hall), not {amount!r}")
        values = synth.reverb_samples(self._samples_at(synth.RATE), float(amount))
        return _from_samples(values, synth.RATE, self._frame_source, "sound.reverb()")

    def save(self, path: str) -> None:
        """Write the sound to a 16-bit WAV file.

        The pan is kept in the file. The volume is not.

        Arguments:
            path: the file name, such as "tune.wav".

        Raises:
            ValueError: if path is empty or not text, or the file cannot be written.

        Example:
            f.melody("C4 E4 G4").save("tune.wav")    # writes a new file

        See also: samples, create_sound
        """
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
    """Sounds together, as a new sound. A soft limiter keeps the peak at or below 0.9 (A9)."""
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
