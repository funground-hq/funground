"""Making sound from numbers (S-110; contract A3; D-055, D-056; ADR-006).

This module is plain Python (``math``, ``array`` and ``random`` only) and does not touch the sound
device. It computes lists of samples: numbers from -1 to 1 at 44 100 a second. ``sound.py`` turns a
list into a playable sound.

Everything here is computed before it plays. The wave shapes are the naive ones (square, saw and
triangle are made from their formulas), so their high notes have some aliasing. That is fine for
teaching, and it keeps the code short enough to read.
"""
from __future__ import annotations

import math
import random
import re
from operator import mul

RATE = 44100
WAVES = ("sine", "square", "saw", "triangle", "noise")

# ---- notes and sargam
_SEMITONES = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
_SHARP_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
_NOTE = re.compile(r"^([A-G])([#b]?)(-?\d+)$")

SARGAM = ["S", "r", "R", "g", "G", "m", "M", "P", "d", "D", "n", "N"]
# Just-intonation ratios from Sa (the usual 5-limit set).
JUST_RATIOS = [1.0, 16 / 15, 9 / 8, 6 / 5, 5 / 4, 4 / 3, 45 / 32, 3 / 2, 8 / 5, 5 / 3, 9 / 5, 15 / 8]
_SWARA = re.compile(r"^([SrRgGmMPdDnN])('*|,*)$")

# The fades a melody's notes get, and the tone() defaults.
DEFAULT_ATTACK = 0.01
DEFAULT_RELEASE = 0.05
PLUCK_DECAY = 0.996            # how much of a plucked string's sound is left after each trip

# pitch(): the numbers that decide "no clear pitch" (contract A3).
PITCH_WINDOW = 2048
PITCH_MIN_HZ, PITCH_MAX_HZ = 50.0, 2000.0
PITCH_MIN_RMS = 0.01           # quieter than this (about -40 dB) is "quiet"
PITCH_MIN_CLARITY = 0.7        # a repeating wave scores about 1, noise about 0.1


def _midi(name: str, who: str) -> int:
    m = _NOTE.match(name) if isinstance(name, str) else None
    if not m:
        raise ValueError(f"{who}: {name!r} is not a note name. Try a letter A-G, an optional # or b, "
                         "and an octave, like 'A4', 'C#5' or 'Bb3'")
    letter, accidental, octave = m.groups()
    return 12 * (int(octave) + 1) + _SEMITONES[letter] + (1 if accidental == "#" else -1 if accidental == "b" else 0)


def _midi_to_hz(midi: float) -> float:
    return 440.0 * 2.0 ** ((midi - 69) / 12.0)


def _swara(token: str, who: str) -> tuple[int, int]:
    """(semitones above Sa, octave) for a sargam token such as "G" or "N,"."""
    m = _SWARA.match(token) if isinstance(token, str) else None
    if not m:
        raise ValueError(f"{who}: {token!r} is not a swara. Use S r R g G m M P d D n N, "
                         "with ' after it for the octave above or , for the octave below")
    mark = m.group(2)
    octave = len(mark) if mark.startswith("'") else -len(mark)
    return SARGAM.index(m.group(1)), octave


def note_to_frequency(name: str, sa: str | None = None, who: str = "f.note_to_frequency()") -> float:
    """Frequency in hertz of a note name ("A4" is 440), or, with *sa*, of a swara above that Sa."""
    if sa is None:
        return _midi_to_hz(_midi(name, who))
    sa_hz = _midi_to_hz(_midi(sa, who))
    step, octave = _swara(name, who)
    return sa_hz * 2.0 ** (step / 12.0 + octave)


def frequency_to_note(hz: float, sa: str | None = None) -> str:
    """The name of the nearest note ("A4"), or, with *sa*, of the nearest swara ("G'")."""
    who = "f.frequency_to_note()"
    if isinstance(hz, bool) or not isinstance(hz, (int, float)) or not math.isfinite(hz) or hz <= 0:
        raise ValueError(f"{who}: the frequency must be a number above 0, not {hz!r}")
    if sa is None:
        midi = round(69 + 12 * math.log2(hz / 440.0))
        return f"{_SHARP_NAMES[midi % 12]}{midi // 12 - 1}"
    steps = round(12 * math.log2(hz / _midi_to_hz(_midi(sa, who))))
    octave, step = divmod(steps, 12)
    return SARGAM[step] + ("'" * octave if octave > 0 else "," * -octave)


# ---- checking arguments
def _number(value, who: str, what: str, low=None, high=None, low_open=False) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"{who}: {what} must be a number, not {value!r}")
    if low is not None and (value <= low if low_open else value < low):
        raise ValueError(f"{who}: {what} must be {'more than' if low_open else 'at least'} {low}, not {value!r}")
    if high is not None and value > high:
        raise ValueError(f"{who}: {what} must be at most {high}, not {value!r}")
    return float(value)


def _check_wave(wave, who: str) -> str:
    if wave not in WAVES:
        raise ValueError(f"{who}: wave must be one of {', '.join(WAVES)}, not {wave!r}")
    return wave


def _fade_times(seconds: float, attack: float, release: float) -> tuple[float, float]:
    """A fade that would not fit is made shorter, keeping the same proportion."""
    if attack + release > seconds:
        scale = seconds / (attack + release)
        return attack * scale, release * scale
    return attack, release


# ---- tones
def tone_samples(frequency: float, seconds: float, wave: str = "sine", volume: float = 1.0,
                 attack: float = DEFAULT_ATTACK, release: float = DEFAULT_RELEASE,
                 rng: random.Random | None = None, rate: int = RATE) -> list[float]:
    """The samples of one tone. The arguments are already checked."""
    n = max(1, round(seconds * rate))
    sin = math.sin
    if wave == "sine":
        w = 2.0 * math.pi * frequency / rate
        out = [volume * sin(w * i) for i in range(n)]
    elif wave == "noise":
        uniform = (rng or random).random
        out = [volume * (2.0 * uniform() - 1.0) for _ in range(n)]
    else:
        step = frequency / rate
        if wave == "square":
            hi, lo = volume, -volume
            out = [hi if (i * step) % 1.0 < 0.5 else lo for i in range(n)]
        elif wave == "saw":
            out = [volume * (2.0 * ((i * step + 0.5) % 1.0) - 1.0) for i in range(n)]
        else:  # triangle, starting at 0 and rising
            out = [volume * (1.0 - 4.0 * abs(((i * step + 0.25) % 1.0) - 0.5)) for i in range(n)]
    attack, release = _fade_times(seconds, attack, release)
    a = min(n, round(attack * rate))
    for i in range(a):
        out[i] *= i / a
    r = min(n, round(release * rate))
    for j in range(r):
        out[n - 1 - j] *= j / r
    return out


def tone(frequency, seconds, wave="sine", volume=1.0, attack=DEFAULT_ATTACK, release=DEFAULT_RELEASE,
         rng=None, who: str = "f.tone()") -> list[float]:
    """Check the arguments of f.tone(), then make the samples."""
    frequency = _number(frequency, who, "the frequency", 0, low_open=True)
    if frequency >= RATE / 2:
        raise ValueError(f"{who}: the frequency must be below {RATE // 2} Hz, not {frequency!r}")
    seconds = _number(seconds, who, "the length in seconds", 0, low_open=True)
    _check_wave(wave, who)
    volume = _number(volume, who, "volume", 0, 1)
    attack = _number(attack, who, "attack", 0)
    release = _number(release, who, "release", 0)
    return tone_samples(frequency, seconds, wave, volume, attack, release, rng)


def pluck(frequency, seconds, volume=1.0, rng=None, who: str = "f.pluck()") -> list[float]:
    """A plucked string (Karplus-Strong). A burst of random numbers goes round a loop that
    averages neighbours (so the high notes die first) and loses a little each trip."""
    if isinstance(frequency, str):
        frequency = note_to_frequency(frequency, who=who)
    frequency = _number(frequency, who, "the frequency", 20, 5000)
    seconds = _number(seconds, who, "the length in seconds", 0, low_open=True)
    volume = _number(volume, who, "volume", 0, 1)
    n = max(1, round(seconds * RATE))
    # The loop delay must be RATE / frequency samples. The averaging filter delays by half a
    # sample; a whole-number ring length and an all-pass filter make up the rest.
    delay = RATE / frequency - 0.5
    ring = int(delay - 0.5)
    frac = delay - ring                                  # from 0.5 to 1.5
    a = (1.0 - frac) / (1.0 + frac)
    uniform = (rng or random).random
    buf = [2.0 * uniform() - 1.0 for _ in range(ring)]
    mean = sum(buf) / ring
    peak = max(abs(v - mean) for v in buf) or 1.0
    buf = [(v - mean) / peak for v in buf]            # loudest at 1, like the other waves
    half_decay = 0.5 * PLUCK_DECAY
    out = [0.0] * n
    idx = 0
    prev = buf[ring - 1]
    ap_in = ap_out = 0.0
    for i in range(n):
        x = buf[idx]
        out[i] = x * volume
        lp = (x + prev) * half_decay
        prev = x
        y = a * lp + ap_in - a * ap_out
        ap_in = lp
        ap_out = y
        buf[idx] = y
        idx += 1
        if idx == ring:
            idx = 0
    attack = min(n, round(0.002 * RATE))                 # no click at the start
    for i in range(attack):
        out[i] *= i / attack
    return out


# ---- melody
def _beats(text: str | None, token: str, who: str) -> float:
    if text is None:
        return 1.0
    try:
        beats = float(text)
    except ValueError:
        beats = float("nan")
    if not math.isfinite(beats) or beats <= 0:
        raise ValueError(f"{who}: bad token {token!r}: the beats after ':' must be a number above 0")
    return beats


def _split(text: str, who: str) -> list[str]:
    tokens = re.findall(r"\[[^\[\]]*\]\S*|\S+", text)
    for token in tokens:
        if ("[" in token or "]" in token) and not re.match(r"^\[[^\[\]]*\](:[^\[\]]*)?$", token):
            raise ValueError(f"{who}: bad token {token!r}: a chord is [ notes ] with the beats after it, "
                             "like [C4 E4 G4]:2")
    return tokens


def melody_samples(text, tempo=120, wave="sine", sa=None, tuning="equal", rng=None,
                   who: str = "f.melody()") -> list[float]:
    """Read a melody string and make its samples (contract A3)."""
    if not isinstance(text, str):
        raise ValueError(f"{who}: the melody must be a string like 'C4 E4 G4:2 -', not {text!r}")
    tempo = _number(tempo, who, "tempo (beats a minute)", 0, low_open=True)
    _check_wave(wave, who)
    if tuning not in ("equal", "just"):
        raise ValueError(f"{who}: tuning must be 'equal' or 'just', not {tuning!r}")
    if sa is not None:
        sa_hz = note_to_frequency(sa, who=who)
    elif tuning == "just":
        raise ValueError(f"{who}: tuning='just' needs sa=, the note that Sa is, like sa='C4'")

    def hz_of(name: str, token: str) -> float:
        try:
            if sa is None:
                hz = note_to_frequency(name, who=who)
            else:
                step, octave = _swara(name, who)
                ratio = JUST_RATIOS[step] if tuning == "just" else 2.0 ** (step / 12.0)
                hz = sa_hz * ratio * 2.0 ** octave
        except ValueError:
            raise ValueError(f"{who}: bad token {token!r}: {name!r} is not "
                             f"{'a swara' if sa is not None else 'a note name'}") from None
        if not 20.0 <= hz < 20000.0:
            raise ValueError(f"{who}: bad token {token!r}: {hz:.0f} Hz is too low or too high to play")
        return hz

    parsed = []                                    # (frequencies, beats); frequencies [] is a rest
    for token in _split(text, who):
        m = re.match(r"^\[([^\[\]]*)\](?::(.*))?$", token)
        if m:
            names = m.group(1).split()
            if not names:
                raise ValueError(f"{who}: bad token {token!r}: the chord is empty")
            parsed.append(([hz_of(name, token) for name in names], _beats(m.group(2), token, who)))
            continue
        name, colon, beats_text = token.partition(":")
        beats = _beats(beats_text if colon else None, token, who)
        parsed.append(([] if name == "-" else [hz_of(name, token)], beats))
    if not parsed:
        raise ValueError(f"{who}: the melody has no notes in it")

    seconds_per_beat = 60.0 / tempo
    out: list[float] = []
    elapsed = 0.0
    for freqs, beats in parsed:
        elapsed += beats
        n = round(elapsed * seconds_per_beat * RATE) - len(out)     # no drift over a long tune
        if n <= 0:
            continue
        length = n / RATE
        if not freqs:
            out.extend([0.0] * n)
        else:
            notes = [tone_samples(hz, length, wave, 1.0, DEFAULT_ATTACK, DEFAULT_RELEASE, rng) for hz in freqs]
            out.extend(notes[0] if len(notes) == 1 else mix_samples(notes))
    return out


# ---- combining
def mix_samples(parts: list[list[float]]) -> list[float]:
    """Add sounds together. They are scaled down only if the peak would pass 1."""
    n = max(len(p) for p in parts)
    out = [0.0] * n
    for p in parts:
        for i, v in enumerate(p):
            out[i] += v
    peak = max(max(out), -min(out))
    if peak > 1.0:
        out = [v / peak for v in out]
    return out


def resample(values: list[float], src: int, dst: int) -> list[float]:
    """Change a list of samples from *src* to *dst* samples a second (linear interpolation)."""
    if src == dst or not values:
        return list(values)
    n = max(1, round(len(values) * dst / src))
    last = len(values) - 1
    ratio = src / dst
    out = []
    for i in range(n):
        pos = i * ratio
        j = int(pos)
        if j >= last:
            out.append(values[last])
        else:
            frac = pos - j
            out.append(values[j] * (1.0 - frac) + values[j + 1] * frac)
    return out


# ---- pitch
def find_pitch(window: list[float], rate: int) -> float | None:
    """The frequency of the one voice in *window* (the last PITCH_WINDOW samples, -1 to 1),
    by normalised autocorrelation. None if it is quiet or has no clear pitch."""
    n = len(window)
    if n < 64:
        return None
    mean = sum(window) / n
    x = [v - mean for v in window]
    total = 0.0
    cum = [0.0]
    for v in x:
        total += v * v
        cum.append(total)
    if math.sqrt(total / n) < PITCH_MIN_RMS:
        return None
    lo = max(2, int(rate / PITCH_MAX_HZ))
    hi = min(int(rate / PITCH_MIN_HZ) + 1, n // 2)
    r = {}
    for lag in range(lo - 1, hi + 2):
        den = math.sqrt(cum[n - lag] * (total - cum[lag]))
        r[lag] = sum(map(mul, x[:n - lag], x[lag:])) / den if den > 0 else 0.0
    peaks = [lag for lag in range(lo, hi + 1) if r[lag] > r[lag - 1] and r[lag] >= r[lag + 1]]
    if not peaks:
        return None
    best = max(r[lag] for lag in peaks)
    if best < PITCH_MIN_CLARITY:
        return None
    lag = next(p for p in peaks if r[p] >= 0.9 * best)   # the first strong peak: not an octave down
    a, b, c = r[lag - 1], r[lag], r[lag + 1]
    bend = a - 2 * b + c
    shift = 0.5 * (a - c) / bend if bend < 0 else 0.0     # parabola through the three points
    return rate / (lag + max(-1.0, min(1.0, shift)))
