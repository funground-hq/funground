"""Making sound from numbers (S-110, S-118; contracts A3 and A9; D-055, D-056, D-064; ADR-006).

This module is plain Python (``math`` and ``random`` only) and does not touch the sound device. It
computes lists of samples: numbers from -1 to 1 at 44 100 a second. ``sound.py`` turns a list into a
playable sound.

Everything here is computed before it plays. Square, saw, triangle and soft waves are built from their
harmonics, stopping below half the sample rate, so high notes do not alias (S-118). Notes have an
attack-decay-sustain-release envelope with smooth exponential curves. Sounds are made at half volume
by default, so a few of them can play together without clipping.
"""
from __future__ import annotations

import math
import random
import re
from operator import add, mul

RATE = 44100
WAVES = ("sine", "square", "saw", "triangle", "soft", "noise")

# ---- notes and sargam
_SEMITONES = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
_SHARP_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
_NOTE = re.compile(r"^([A-G])([#b]?)(-?\d+)$")

SARGAM = ["S", "r", "R", "g", "G", "m", "M", "P", "d", "D", "n", "N"]
# Just-intonation ratios from Sa (the usual 5-limit set).
JUST_RATIOS = [1.0, 16 / 15, 9 / 8, 6 / 5, 5 / 4, 4 / 3, 45 / 32, 3 / 2, 8 / 5, 5 / 3, 9 / 5, 15 / 8]
_SWARA = re.compile(r"^([SrRgGmMPdDnN])('*|,*)$")

# The envelope defaults (contract A9): seconds, except SUSTAIN, the level held after the decay.
DEFAULT_VOLUME = 0.5           # about -6 dB, so a few sounds can play together without clipping
DEFAULT_ATTACK = 0.01
DEFAULT_DECAY = 0.15
DEFAULT_SUSTAIN = 0.7
DEFAULT_RELEASE = 0.15
ENVELOPE_CURVE = 4.0           # how sharply each envelope segment bends (0 would be a straight line)
LEGATO_LEAD = 0.0              # the share of a melody note's release before the note ends (S-118 note)

# Band-limited waves (S-118): harmonics stop below TOP_HZ, a little under half the sample rate.
TOP_HZ = 20000.0
TABLE_SIZE = 4096              # samples in one period of a wave table
SOFT_HARMONICS = (1.0, 0.35, 0.15, 0.06)   # the "soft" wave: a few gently falling harmonics

PLUCK_DECAY = 0.996            # how much of a plucked string's sound is left after each trip
PLUCK_SOFTNESS = 4             # passes of smoothing on the pluck's burst of noise (about a 4 kHz low-pass)

# mix(): a soft limiter keeps the peak at or below LIMIT_PEAK (contract A9).
LIMIT_KNEE = 0.7               # below this, samples are not changed
LIMIT_PEAK = 0.9
LIMIT_INPUT = 1.2              # louder sums are first scaled down to this peak, so the knee stays gentle

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


# ---- band-limited waves (S-118, contract A9)
def _harmonics(wave: str, count: int) -> list[tuple[int, float]]:
    """(harmonic number, strength) for the first *count* harmonics of a wave. A minus sign is a
    harmonic turned upside down (the triangle needs that)."""
    if wave == "saw":
        return [(k, 1.0 / k) for k in range(1, count + 1)]
    if wave == "square":
        return [(k, 1.0 / k) for k in range(1, count + 1, 2)]
    if wave == "triangle":
        return [(k, (1.0 if k % 4 == 1 else -1.0) / (k * k)) for k in range(1, count + 1, 2)]
    return [(k, a) for k, a in enumerate(SOFT_HARMONICS[:count], start=1)]


def _fft(values: list[complex]) -> list[complex]:
    """A plain radix-2 FFT with a + sign in the exponent, so it adds waves up (an inverse FFT
    without the division)."""
    n = len(values)
    bits = n.bit_length() - 1
    out = [values[int(format(i, f"0{bits}b")[::-1], 2)] for i in range(n)]
    half = 1
    while half < n:
        turns = [complex(math.cos(math.pi * k / half), math.sin(math.pi * k / half)) for k in range(half)]
        for start in range(0, n, 2 * half):
            for k in range(half):
                i, j = start + k, start + k + half
                t = turns[k] * out[j]
                out[i], out[j] = out[i] + t, out[i] - t
        half *= 2
    return out


# How many harmonics a table may have: every whole number up to 16, then steps of an eighth of
# an octave. A note uses the size at or just below its own count, so tables are shared.
_BANDS = sorted({*range(1, 17), *(int(16 * 2.0 ** (i / 8)) for i in range(1, 80))})
_TABLES: dict[tuple[str, int], list[float]] = {}


def _table(wave: str, frequency: float, rate: int = RATE) -> list[float]:
    """One period of *wave* at *frequency*: the sum of its harmonics below TOP_HZ (and below half
    of *rate*), scaled so its peak is 1, with the first sample repeated at the end for reading
    between samples. Tables are kept for reuse."""
    top = min(TOP_HZ, rate / 2 - 50.0)
    count = max(1, min(TABLE_SIZE // 2 - 1, int(top / frequency)))
    count = max(b for b in _BANDS if b <= count)
    key = (wave, count)
    table = _TABLES.get(key)
    if table is None:
        spectrum = [0j] * TABLE_SIZE
        for k, strength in _harmonics(wave, count):
            spectrum[k] = complex(strength)
        table = [z.imag for z in _fft(spectrum)]              # the sum of the sin(2 pi k n / N) waves
        peak = max(abs(v) for v in table) or 1.0
        table = [v / peak for v in table]
        table.append(table[0])
        _TABLES[key] = table
    return table


def _wave(frequency: float, n: int, wave: str, rng, rate: int = RATE) -> list[float]:
    """*n* samples of a steady wave with peak 1. Every wave but noise starts at 0 and rises."""
    if wave == "sine":
        w = 2.0 * math.pi * frequency / rate
        sin = math.sin
        return [sin(w * i) for i in range(n)]
    if wave == "noise":
        uniform = (rng or random).random
        return [2.0 * uniform() - 1.0 for _ in range(n)]
    table = _table(wave, frequency, rate)
    step = frequency / rate * TABLE_SIZE
    size = float(TABLE_SIZE)
    out = [0.0] * n
    pos = 0.0
    for i in range(n):
        j = int(pos)
        a = table[j]
        out[i] = a + (table[j + 1] - a) * (pos - j)
        pos += step
        if pos >= size:
            pos -= size
    return out


# ---- the envelope (contract A9)
def _rise(u: float, c: float = ENVELOPE_CURVE) -> float:
    """0 to 1 as u goes from 0 to 1: fast at first, then levelling off (an exponential curve)."""
    return (1.0 - math.exp(-c * u)) / (1.0 - math.exp(-c))


def _fall(u: float, c: float = ENVELOPE_CURVE) -> float:
    """1 to 0 as u goes from 0 to 1: fast at first, then slowing down (an exponential curve)."""
    return (math.exp(-c * u) - math.exp(-c)) / (1.0 - math.exp(-c))


def envelope(n: int, attack: int, decay: int, sustain: float, release: int) -> list[float]:
    """The loudness, from 0 to 1, of each of *n* samples. Attack: a rise from 0 to 1 over *attack*
    samples. Decay: a fall from 1 to *sustain* over *decay* samples. Then *sustain* is held.
    Release: the last *release* samples fall from the level reached there to 0, so a release that
    starts during the attack or the decay starts from that level."""
    release = min(release, n)
    hold = n - release
    depth = 1.0 - sustain
    shape = _shape("fall", decay) if decay else []
    gains = _shape("rise", attack)[:hold] + [sustain + depth * v for v in shape[:max(0, hold - attack)]]
    gains += [sustain] * (hold - len(gains))
    if release:
        if hold <= 0:
            start = 0.0
        elif hold < attack:
            start = _rise(hold / attack)
        elif hold < attack + decay:
            start = sustain + depth * _fall((hold - attack) / decay)
        else:
            start = sustain
        gains += [start * v for v in _shape("fall", release)]
    return gains


_SHAPES: dict[tuple[str, int], list[float]] = {}


def _shape(kind: str, count: int) -> list[float]:
    """_rise or _fall at *count* even steps from 0 (kept, as notes share their lengths)."""
    key = (kind, count)
    if key not in _SHAPES:
        curve = _rise if kind == "rise" else _fall
        _SHAPES[key] = [curve(i / count) for i in range(count)]
    return _SHAPES[key]


# ---- tones
def voice_samples(frequency: float, hold: int, release: int, wave: str = "soft",
                  volume: float = DEFAULT_VOLUME, attack: float = DEFAULT_ATTACK,
                  decay: float = DEFAULT_DECAY, sustain: float = DEFAULT_SUSTAIN,
                  rng: random.Random | None = None, rate: int = RATE) -> list[float]:
    """One note: *hold* samples of attack, decay and sustain, then *release* samples of release.
    An attack longer than the hold is shortened to fit it."""
    n = max(1, hold + release)
    attack_n = min(round(attack * rate), max(0, hold))
    gains = envelope(n, attack_n, round(decay * rate), sustain, release)
    return list(map(mul, _wave(frequency, n, wave, rng, rate), [volume * g for g in gains]))


def tone_samples(frequency: float, seconds: float, wave: str = "sine", volume: float = DEFAULT_VOLUME,
                 attack: float = DEFAULT_ATTACK, release: float = DEFAULT_RELEASE,
                 rng: random.Random | None = None, rate: int = RATE, decay: float = DEFAULT_DECAY,
                 sustain: float = DEFAULT_SUSTAIN) -> list[float]:
    """The samples of one tone, *seconds* long with its release at the end, inside that time. The
    arguments are already checked. Attack and release that do not fit are shortened in proportion (A3)."""
    n = max(1, round(seconds * rate))
    attack, release = _fade_times(seconds, attack, release)
    r = min(n, round(release * rate))
    return voice_samples(frequency, n - r, r, wave, volume, attack, decay, sustain, rng, rate)


def tone(frequency, seconds, wave="sine", volume=DEFAULT_VOLUME, attack=DEFAULT_ATTACK,
         release=DEFAULT_RELEASE, rng=None, who: str = "f.tone()", decay=DEFAULT_DECAY,
         sustain=DEFAULT_SUSTAIN) -> list[float]:
    """Check the arguments of f.tone(), then make the samples."""
    frequency = _number(frequency, who, "the frequency", 0, low_open=True)
    if frequency >= RATE / 2:
        raise ValueError(f"{who}: the frequency must be below {RATE // 2} Hz, not {frequency!r}")
    seconds = _number(seconds, who, "the length in seconds", 0, low_open=True)
    _check_wave(wave, who)
    volume = _number(volume, who, "volume", 0, 1)
    attack = _number(attack, who, "attack", 0)
    decay = _number(decay, who, "decay", 0)
    sustain = _number(sustain, who, "sustain", 0, 1)
    release = _number(release, who, "release", 0)
    return tone_samples(frequency, seconds, wave, volume, attack, release, rng, RATE, decay, sustain)


def soft_burst(ring: int, rng, passes: int) -> list[float]:
    """The burst of noise that starts a plucked string: *ring* random numbers, smoothed *passes*
    times round the loop by (1, 2, 1) / 4 averaging. That is a gentle low-pass filter: the more
    passes, the darker and softer the string. The average is taken away and the loudest is 1."""
    burst = [2.0 * rng.random() - 1.0 for _ in range(ring)]
    for _ in range(passes):
        burst = [(burst[i - 1] + 2.0 * burst[i] + burst[(i + 1) % ring]) / 4.0 for i in range(ring)]
    mean = sum(burst) / ring
    peak = max(abs(v - mean) for v in burst) or 1.0
    return [(v - mean) / peak for v in burst]


def pluck(frequency, seconds, volume=DEFAULT_VOLUME, rng=None, who: str = "f.pluck()") -> list[float]:
    """A plucked string (Karplus-Strong). A burst of random numbers, smoothed a little so the string
    sounds warm rather than metallic (S-118), goes round a loop that averages neighbours (so the
    high notes die first) and loses a little each trip."""
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
    buf = soft_burst(ring, rng or random, PLUCK_SOFTNESS)    # loudest at 1, like the other waves
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


def melody_samples(text, tempo=120, wave="soft", sa=None, tuning="equal", rng=None,
                   who: str = "f.melody()", volume=DEFAULT_VOLUME) -> list[float]:
    """Read a melody string and make its samples (contracts A3, A8 and A9)."""
    if not isinstance(text, str):
        raise ValueError(f"{who}: the melody must be a string like 'C4 E4 G4:2 -', not {text!r}")
    tempo = _number(tempo, who, "tempo (beats a minute)", 0, low_open=True)
    _check_wave(wave, who)
    volume = _number(volume, who, "volume", 0, 1)
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

    # (frequencies, beats, ornament); frequencies [] is a rest. The ornament (S-115, contract A8)
    # is None, or (grace frequency or None, glide-to frequency or None) for kan and meend.
    parsed = []
    for token in _split(text, who):
        m = re.match(r"^\[([^\[\]]*)\](?::(.*))?$", token)
        if m:
            names = m.group(1).split()
            if not names:
                raise ValueError(f"{who}: bad token {token!r}: the chord is empty")
            parsed.append(([hz_of(name, token) for name in names], _beats(m.group(2), token, who), None))
            continue
        name, colon, beats_text = token.partition(":")
        beats = _beats(beats_text if colon else None, token, who)
        ornament = _ornament(name, token, who)
        if ornament is None:
            parsed.append(([] if name == "-" else [hz_of(name, token)], beats, None))
            continue
        grace, start, end = ornament
        parsed.append(([hz_of(start, token)], beats,
                       (hz_of(grace, token) if grace else None, hz_of(end, token) if end else None)))
    if not parsed:
        raise ValueError(f"{who}: the melody has no notes in it")

    # Legato (contract A9; the timing is pinned in S-118). Each note starts on its beat and holds
    # (attack, decay, sustain) until its last beat ends. Then its release (DEFAULT_RELEASE, or the
    # note's own length if that is shorter) rings on over the next note, so there is no gap. The
    # melody lasts its beats, plus the last note's release (at most 0.15 s) where that rings past
    # the end; a final rest at least that long holds it. LEGATO_LEAD would move part of each
    # release before the note's end: that helps swara_histogram() a little but leaves a dip
    # between the notes (measurements in docs/design/Sound_Making_Note.md).
    seconds_per_beat = 60.0 / tempo
    full_release = round(DEFAULT_RELEASE * RATE)
    sounding: list[tuple[int, list[float]]] = []
    elapsed = 0.0
    stop = 0
    for freqs, beats, ornament in parsed:
        start = round(elapsed * seconds_per_beat * RATE)           # whole tune timing: no drift
        elapsed += beats
        stop = round(elapsed * seconds_per_beat * RATE)
        if stop <= start or not freqs:
            continue
        release = min(full_release, stop - start)
        hold = stop - start - round(release * LEGATO_LEAD)
        if ornament is not None:
            grace, end = ornament
            sound = ornament_samples(freqs[0], end or freqs[0], hold, release, wave, grace, volume, rng,
                                     glide=stop - start)
        else:
            voices = [voice_samples(hz, hold, release, wave, volume, rng=rng) for hz in freqs]
            sound = voices[0] if len(voices) == 1 else mix_samples(voices)
        sounding.append((start, sound))
    out = [0.0] * max([stop] + [start + len(sound) for start, sound in sounding])
    for start, sound in sounding:
        end = start + len(sound)
        out[start:end] = map(add, out[start:end], sound)
    if max(out) > 1.0 or min(out) < -1.0:          # overlapping notes would clip: limit as mix() does
        out = _limit(out)
    return out


# ---- meend and kan (S-115, contract A8)
KAN_SECONDS = 0.06             # how long the grace note of a kan, (R)G, lasts
_KAN = re.compile(r"^\(([^()]+)\)(.+)$")


def _ornament(name: str, token: str, who: str):
    """(grace, start, end) for a token with a kan "(R)G" or a meend "S~G", each part a note name or
    swara (grace and end may be None). None for a plain note or rest."""
    if "(" not in name and ")" not in name and "~" not in name:
        return None
    grace = None
    m = _KAN.match(name)
    if m:
        grace, name = m.groups()
    if "(" in name or ")" in name or name == "-":
        raise ValueError(f"{who}: bad token {token!r}: a kan is the grace note in brackets and then the "
                         "note, like (R)G")
    parts = name.split("~")
    if len(parts) > 2 or "" in parts or "-" in parts:
        raise ValueError(f"{who}: bad token {token!r}: a meend is two notes joined by ~, like S~G")
    return grace, parts[0], parts[1] if len(parts) == 2 else None


def ornament_samples(start_hz: float, end_hz: float, hold: int, release: int, wave: str = "soft",
                     grace_hz: float | None = None, volume: float = DEFAULT_VOLUME,
                     rng: random.Random | None = None, rate: int = RATE,
                     glide: int | None = None) -> list[float]:
    """One note whose pitch moves, *hold* samples and then *release* samples of release. With
    *grace_hz* it first touches that note for KAN_SECONDS (a kan). Then it glides from *start_hz*
    to *end_hz* (a meend), on a smooth S-shaped curve in pitch, reaching it after *glide* samples
    (the hold, if not given), and stays there. The wave keeps its phase as the pitch changes, so
    there is no click, and it has the same envelope as a plain note. Band-limited waves use the
    table for the highest pitch it reaches, so nothing aliases."""
    n = max(1, hold + release)
    glide = hold if glide is None else glide
    g = min(round(KAN_SECONDS * rate), glide // 2) if grace_hz else 0
    span = math.log(end_hz / start_hz)
    rest = max(1, glide - g - 1)
    uniform = (rng or random).random
    table = None
    if wave not in ("sine", "noise"):
        table = _table(wave, max(start_hz, end_hz, grace_hz or 0.0), rate)
    out = [0.0] * n
    phase = 0.0
    tau = 2.0 * math.pi
    for i in range(n):
        if i < g:
            hz = grace_hz
        else:
            t = min(1.0, (i - g) / rest)
            hz = start_hz * math.exp(span * t * t * (3.0 - 2.0 * t))
        if table is not None:
            pos = phase * TABLE_SIZE
            j = int(pos)
            v = table[j] + (table[j + 1] - table[j]) * (pos - j)
        elif wave == "sine":
            v = math.sin(tau * phase)
        else:
            v = 2.0 * uniform() - 1.0
        out[i] = v
        phase += hz / rate
        if phase >= 1.0:
            phase -= 1.0
    attack_n = min(round(DEFAULT_ATTACK * rate), max(0, hold))
    gains = envelope(n, attack_n, round(DEFAULT_DECAY * rate), DEFAULT_SUSTAIN, release)
    return [v * volume * e for v, e in zip(out, gains)]


# ---- combining
def _limit(values: list[float]) -> list[float]:
    """The soft limiter (contract A9). Samples below LIMIT_KNEE are kept. Louder ones are bent
    smoothly (a tanh curve) so that nothing passes LIMIT_PEAK. A sum louder than LIMIT_INPUT is
    first scaled down to it, so the bend stays gentle."""
    peak = max(max(values), -min(values))
    if peak <= LIMIT_KNEE:
        return list(values)
    scale = LIMIT_INPUT / peak if peak > LIMIT_INPUT else 1.0
    knee, room = LIMIT_KNEE, LIMIT_PEAK - LIMIT_KNEE
    tanh = math.tanh
    out = []
    for v in values:
        v *= scale
        if v > knee:
            v = knee + room * tanh((v - knee) / room)
        elif v < -knee:
            v = -knee - room * tanh((-v - knee) / room)
        out.append(v)
    return out


def mix_samples(parts: list[list[float]]) -> list[float]:
    """Add sounds together, then the soft limiter keeps the peak at or below LIMIT_PEAK. A sum
    whose peak is LIMIT_KNEE or less is not changed."""
    n = max(len(p) for p in parts)
    out = [0.0] * n
    for p in parts:
        out[:len(p)] = map(add, out[:len(p)], p)
    return _limit(out)


# ---- reverb (S-118, contract A9)
# A small Schroeder-style room: four feedback combs side by side, each with a little damping in its
# loop (so high sounds die first), then two all-pass filters in a row to thicken the echoes. The
# delays are in samples at 44 100 a second and share no common factors, so the echoes do not line up.
REVERB_COMBS = (1229, 1373, 1499, 1621)
REVERB_ALLPASSES = ((373, 0.6), (131, 0.6))
REVERB_DAMPING = 0.3           # the share of the loop's sound taken from one sample earlier
REVERB_WET = 2.2               # how loud the room is at amount 1 (it grows with the square root of amount)
REVERB_MAX_TAIL = 1.5          # seconds of tail added at amount 1


def _comb(x: list[float], delay: int, gain: float, damping: float) -> list[float]:
    """The echoes of a feedback comb, y[n] - x[n], where
    y[n] = x[n] + gain * ((1 - damping) * y[n - delay] + damping * y[n - delay - 1]).
    Computed a block of *delay* samples at a time, as each block needs only earlier blocks."""
    pad = delay + 1
    y = [0.0] * pad + x
    a, b = gain * (1.0 - damping), gain * damping
    size = len(y)
    for s in range(pad, size, delay):
        e = min(s + delay, size)
        y[s:e] = [v + a * p + b * q for v, p, q in zip(y[s:e], y[s - delay:e - delay], y[s - delay - 1:e - delay - 1])]
    return [v - u for v, u in zip(y[pad:], x)]


def _allpass(x: list[float], delay: int, gain: float) -> list[float]:
    """y[n] = -gain * x[n] + x[n - delay] + gain * y[n - delay], a block at a time."""
    xs = [0.0] * delay + x
    y = [0.0] * len(xs)
    size = len(xs)
    for s in range(delay, size, delay):
        e = min(s + delay, size)
        y[s:e] = [p - gain * v + gain * q for v, p, q in zip(xs[s:e], xs[s - delay:e - delay], y[s - delay:e - delay])]
    return y[delay:]


def reverb_samples(values: list[float], amount: float, rate: int = RATE) -> list[float]:
    """*values* in a room. *amount* 0 is dry (the same numbers back); 1 is a large hall. The room
    rings for longer and louder as *amount* grows; the tail added at the end is REVERB_MAX_TAIL
    seconds at 1, less for smaller amounts, and fades out. The result's peak is never higher than
    the input's, so the reverb keeps the headroom."""
    if amount == 0 or not values:
        return list(values)
    t60 = 0.3 + 1.7 * amount                          # seconds for the room to fall by 60 dB
    tail = round(REVERB_MAX_TAIL * amount * rate)
    x = list(values) + [0.0] * tail
    scale = rate / 44100.0
    wet = [0.0] * len(x)
    for d in REVERB_COMBS:
        delay = max(1, round(d * scale))
        gain = 10.0 ** (-3.0 * delay / (t60 * rate))
        wet = list(map(add, wet, _comb(x, delay, gain, REVERB_DAMPING)))
    for d, gain in REVERB_ALLPASSES:
        wet = _allpass(wet, max(1, round(d * scale)), gain)
    level = REVERB_WET * math.sqrt(amount) / len(REVERB_COMBS)
    out = [v + level * w for v, w in zip(x, wet)]
    fade = min(tail, round(0.3 * rate))               # the end of the tail fades to nothing
    n = len(out)
    for j in range(fade):
        out[n - 1 - j] *= j / fade
    before = max(max(values), -min(values))
    after = max(max(out), -min(out))
    if after > before > 0:
        out = [v * before / after for v in out]
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
