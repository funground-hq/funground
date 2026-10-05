"""Music analysis: onsets, tempo, beats, chroma, chords and key (S-112, S-113; contract A5, A6; D-061).

This module is plain Python (``math`` and ``cmath`` only). It does not touch pygame, the sound device
or the sketch. ``sound.py`` gives its sounds and microphones the methods that call these functions.

Speed: a pure Python FFT is slow, so everything here first lowers the sample rate to about 11 025 a
second (it averages groups of samples). That is plenty for rhythm and for notes up to 2 kHz, and it
makes a three-minute song take a few seconds instead of a minute. Two real frames share one FFT.
"""
from __future__ import annotations

import cmath
import math
from operator import mul, sub

ANALYSIS_RATE = 11025            # the rate chroma and key work at (the input is reduced to about this)
RHYTHM_RATE = 5512               # the rate the rhythm analysis works at: still plenty for drums and plucks

# ---- rhythm
FLUX_FRAME = 256                 # samples in one analysis frame (46 ms at 5 512)
FLUX_HOP = 64                    # samples between frames (11.6 ms): for whole sounds
LIVE_HOP = 128                   # the same, for the live is_onset(), which only has to be quick
LIVE_SECONDS = 0.3               # how much recent sound is_onset() looks at
LOG_GAIN = 100.0                 # log compression: log(1 + LOG_GAIN * magnitude)
FLUX_LOW_HZ = 30.0               # flux ignores bins below this
THRESHOLD_FACTOR = 1.6           # an onset must beat the local median times this ...
THRESHOLD_SHARE = 0.15           # ... plus this share of the strongest flux ...
THRESHOLD_FLOOR = 2.0            # ... and never be weaker than this (silence and hiss give no onsets)
MEDIAN_SECONDS = 0.5             # the median is taken this far each side
MIN_GAP = 0.05                   # seconds between onsets
LIVE_GAP = 0.1                   # seconds between flashes of is_onset() (one onset can move a frame as it grows)
ONSET_DELAY = 0.018              # seconds: an onset is this far before the end of its peak frame (found by test)
TEMPO_LOW, TEMPO_HIGH = 60.0, 200.0
TEMPO_CENTRE = 120.0             # the mild prior: tempi near this are a little more likely
TEMPO_SPREAD = 1.0               # the prior's width in octaves
MIN_ONSETS_FOR_TEMPO = 4
MIN_PULSE = 0.12                 # how regular the onsets must be (autocorrelation, 0 to 1) for a tempo

# ---- harmony
CHROMA_LOW_HZ, CHROMA_HIGH_HZ = 65.0, 2000.0
CHROMA_FRAME = 2048              # samples (at the analysis rate) in a chroma frame: about 0.19 s
CHROMA_QUIET = 0.0005            # a spectrum with no peak above this (full scale is 1) has no chroma (quiet laptop microphones need it low)
CHORD_MIN_SCORE = 0.85           # how well a chord must match, from 0 to 1
SINGLE_VOICE = 0.2               # if the second strongest pitch class is below this, it is one voice
KEY_MIN_SCORE = 0.3              # correlation a key must have

NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
_FLAT_NAMES = {"Db": 1, "Eb": 3, "Gb": 6, "Ab": 8, "Bb": 10, "Cb": 11, "Fb": 4, "E#": 5, "B#": 0}

# Chord qualities: name suffix -> semitones above the root. The suffixes are the names in contract A6.
CHORD_QUALITIES = {
    "": (0, 4, 7),            # major
    "m": (0, 3, 7),           # minor
    "dim": (0, 3, 6),         # diminished
    "aug": (0, 4, 8),         # augmented
    "7": (0, 4, 7, 10),       # dominant seventh
    "maj7": (0, 4, 7, 11),    # major seventh
    "m7": (0, 3, 7, 10),      # minor seventh
}

# Krumhansl-Schmuckler key profiles: how well each pitch class (starting at the tonic) fits a key,
# from the probe-tone ratings of Krumhansl and Kessler, "Tracing the dynamic changes in perceived
# tonal organization in a spatial representation of musical keys", Psychological Review 89 (1982),
# 334-368 (the same numbers are in Krumhansl, "Cognitive Foundations of Musical Pitch", 1990).
# Checked 4 Oct 2026 against Aarden & von Hippel, Music Theory Online 10.2 (2004), and partitura's key_identification.
KEY_MAJOR = (6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88)
KEY_MINOR = (6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17)


# ---- the FFT
_TABLES: dict[int, tuple] = {}


def _tables(n: int):
    if n not in _TABLES:
        bits = n.bit_length() - 1
        rev = [int(format(i, f"0{bits}b")[::-1], 2) for i in range(n)]
        twiddles = [cmath.exp(-2j * math.pi * k / n) for k in range(n // 2)]
        stages = []
        half = 2
        while half < n:
            stages.append((half, twiddles[:: n // (half * 2)][:half]))
            half *= 2
        hann = [0.5 - 0.5 * math.cos(2 * math.pi * i / (n - 1)) for i in range(n)]
        _TABLES[n] = (rev, stages, hann)
    return _TABLES[n]


def fft(values: list[complex]) -> list[complex]:
    """The FFT of a list whose length is a power of two (at least 4)."""
    n = len(values)
    rev, stages, _ = _tables(n)
    a = [values[i] for i in rev]
    for s in range(0, n, 2):                       # the first stage needs no twiddles
        u = a[s]
        t = a[s + 1]
        a[s] = u + t
        a[s + 1] = u - t
    for half, w in stages:
        step = half * 2
        for s in range(0, n, step):
            lo = a[s:s + half]
            t = list(map(mul, w, a[s + half:s + step]))
            a[s:s + half] = [u + v for u, v in zip(lo, t)]
            a[s + half:s + step] = [u - v for u, v in zip(lo, t)]
    return a


def _two_spectra(first: list[float], second: list[float]):
    """The magnitudes (bins 0 to n/2) of two real frames of n samples, with one complex FFT.
    The frames are windowed with a Hann window. A full-scale sine at a bin's centre gives 1."""
    n = len(first)
    hann = _tables(n)[2]
    z = fft([complex(a * w, b * w) for a, b, w in zip(first, second, hann)])
    norm = 2.0 / n                                   # 4 / n for the Hann window, times 1/2 for the split
    half = n // 2
    rz = z[:1] + z[:0:-1]                            # z[(n - k) % n] for k = 0 .. n - 1
    mag_a = [abs(z[k] + rz[k].conjugate()) * norm for k in range(half + 1)]
    mag_b = [abs(z[k] - rz[k].conjugate()) * norm for k in range(half + 1)]
    return mag_a, mag_b


# ---- lowering the rate
def decimate(samples, rate: int, target: int = ANALYSIS_RATE) -> tuple[list[float], float]:
    """Average groups of samples so the rate comes down to about *target*.
    Returns the new samples and the new rate."""
    factor = max(1, round(rate / target))
    if factor == 1:
        return list(samples), float(rate)
    count = len(samples) // factor
    columns = [samples[i:count * factor:factor] for i in range(factor)]
    scale = 1.0 / factor
    return [sum(group) * scale for group in zip(*columns)], rate / factor


# ---- onsets
def flux(samples: list[float], rate: float, hop: int = FLUX_HOP) -> list[float]:
    """The onset strength: how much new sound there is in each frame, one number per *hop* samples.
    Spectral flux: the spectrum of each frame (log-compressed), keeping only the bins that rose."""
    n = FLUX_FRAME
    frames = max(1, -(-len(samples) // hop))
    padded = [0.0] * (n - hop) + list(samples) + [0.0] * hop
    low = max(1, int(FLUX_LOW_HZ * n / rate))
    log = math.log1p
    previous = None
    out: list[float] = []
    for k in range(0, frames, 2):
        a = padded[k * hop:k * hop + n]
        b = padded[(k + 1) * hop:(k + 1) * hop + n] if k + 1 < frames else [0.0] * n
        mags = _two_spectra(a, b)
        for m in mags[:2 if k + 1 < frames else 1]:
            cur = [log(LOG_GAIN * v) if v > 1e-9 else 0.0 for v in m[low:]]
            if previous is None:
                out.append(0.0)
            else:
                out.append(sum(d for d in map(sub, cur, previous) if d > 0.0))
            previous = cur
    return out


def pick_peaks(env: list[float], hop_seconds: float, confirmed: bool = True, start: int = 1) -> list[int]:
    """The frames where the onset strength has a clear peak (an adaptive threshold: a local median
    times a factor, plus a margin), with at least MIN_GAP between peaks. With *confirmed* False the
    last frame can also be a peak (it has no later frame to be compared with). Frames before *start* are
    not looked at."""
    n = len(env)
    if n < 3:
        return []
    top = max(env)
    margin = max(THRESHOLD_FLOOR, THRESHOLD_SHARE * top)
    reach = max(2, round(MEDIAN_SECONDS / hop_seconds))
    gap = max(1, round(MIN_GAP / hop_seconds))
    peaks: list[int] = []
    last = n - 1 if confirmed else n
    for i in range(max(1, start), last):
        v = env[i]
        if v < margin or v < env[i - 1] or (i + 1 < n and v <= env[i + 1]):
            continue
        lo = max(0, i - 2)
        hi = min(n, i + 3)
        if v < max(env[lo:hi]):
            continue
        window = sorted(env[max(0, i - reach):min(n, i + reach + 1)])
        median = window[len(window) // 2]
        if v < THRESHOLD_FACTOR * median + margin:
            continue
        if peaks and i - peaks[-1] < gap:
            if v > env[peaks[-1]]:
                peaks[-1] = i
            continue
        peaks.append(i)
    return peaks


def _onset_time(frame: int, hop: int, rate: float) -> float:
    """When a peak frame's onset happened, in seconds. A frame ends (frame + 1) * hop samples from
    the start of the sound, and the flux peaks a little after the sound starts to enter it."""
    return max(0.0, (frame + 1) * hop / rate - ONSET_DELAY)


class Rhythm:
    """The onsets, tempo and beats of a whole sound, worked out once."""

    def __init__(self, samples, rate: int):
        low, low_rate = decimate(samples, rate, RHYTHM_RATE)
        self.duration = len(samples) / rate
        self.env = flux(low, low_rate)
        hop_s = FLUX_HOP / low_rate
        peaks = pick_peaks(self.env, hop_s)
        self.onsets = [_onset_time(i, FLUX_HOP, low_rate) for i in peaks]
        self.strengths = [self.env[i] for i in peaks]
        self.hop_seconds = hop_s
        self.tempo, self.beats = self._tempo_and_beats()

    def _tempo_and_beats(self):
        env, hop_s = self.env, self.hop_seconds
        if len(self.onsets) < MIN_ONSETS_FOR_TEMPO:
            return None, []
        coarse = self._autocorrelation_tempo(env, hop_s)
        if coarse is None:
            return None, []
        return self._fit_grid(coarse)

    @staticmethod
    def _autocorrelation_tempo(env: list[float], hop_s: float) -> float | None:
        n = len(env)
        # The envelope minus its slow average, so a loud passage does not look like a pulse.
        reach = max(1, round(0.5 / hop_s))
        total = [0.0]
        for v in env:
            total.append(total[-1] + v)
        x = []
        for i, v in enumerate(env):
            lo, hi = max(0, i - reach), min(n, i + reach + 1)
            x.append(max(0.0, v - (total[hi] - total[lo]) / (hi - lo)))
        energy = sum(map(mul, x, x))
        if energy <= 0.0:
            return None
        lag_min = max(2, int(60.0 / TEMPO_HIGH / hop_s))
        lag_max = int(60.0 / TEMPO_LOW / hop_s) + 1
        if n < 4 * lag_max:                            # fewer than about 4 beats at the slowest tempo
            lag_max = n // 4
            if lag_max <= lag_min + 1:
                return None

        def r(lag: int) -> float:
            if lag >= n:
                return 0.0
            return sum(map(mul, x[:n - lag], x[lag:])) / energy * n / (n - lag)

        scores = {}
        raw = {}
        for lag in range(lag_min - 1, lag_max + 2):
            raw[lag] = r(lag)
        for lag in range(lag_min, lag_max + 1):
            bpm = 60.0 / (lag * hop_s)
            prior = math.exp(-0.5 * (math.log2(bpm / TEMPO_CENTRE) / TEMPO_SPREAD) ** 2)
            scores[lag] = raw[lag] * prior
        best = max(scores, key=scores.get)
        if raw[best] < MIN_PULSE:
            return None
        # Between frames: a parabola through the raw autocorrelation round the best lag.
        a, b, c = raw[best - 1], raw[best], raw[best + 1]
        bend = a - 2 * b + c
        shift = 0.5 * (a - c) / bend if bend < 0 else 0.0
        return 60.0 / ((best + max(-1.0, min(1.0, shift))) * hop_s)

    def _fit_grid(self, coarse: float):
        """Fine-tune the tempo and find where the beats fall, from the onset times themselves."""
        onsets, weights = self.onsets, self.strengths
        width = 0.005                                  # seconds: the size of a phase bin
        best = None
        for step in range(-24, 25):
            bpm = coarse * (1.0 + step * 0.0025)
            if not TEMPO_LOW * 0.95 <= bpm <= TEMPO_HIGH * 1.05:
                continue
            period = 60.0 / bpm
            bins = max(8, round(period / width))
            hist = [0.0] * bins
            for t, w in zip(onsets, weights):
                hist[int((t % period) / period * bins) % bins] += w
            span = max(1, round(0.015 / width))          # an onset counts if within about 15 ms
            summed = [sum(hist[(j + d) % bins] for d in range(-span, span + 1)) for j in range(bins)]
            peak = max(summed)
            j = summed.index(peak)
            score = peak - 0.2 * abs(step) * 0.0025 * sum(weights)   # a small pull towards the coarse tempo
            if best is None or score > best[0]:
                best = (score, bpm, period, bins, j)
        _, bpm, period, bins, j = best
        centre = (j + 0.5) / bins * period
        near = []
        for t, w in zip(onsets, weights):                # the strength-weighted mean of the nearby onsets
            d = ((t - centre + period / 2) % period) - period / 2
            if abs(d) <= 0.02:
                near.append((d, w))
        phase = centre + (sum(d * w for d, w in near) / sum(w for _, w in near) if near else 0.0)
        phase %= period
        if phase > period - 0.03:                      # a beat just before the start belongs at 0
            phase -= period
        beats = []
        t = phase
        while t <= self.duration:
            beats.append(max(0.0, t))
            t += period
        return round(bpm, 1), beats


# ---- live onsets
def live_onsets(window: list[float], rate: int) -> list[float]:
    """The onsets in the latest sound, for is_onset(): times in seconds from the start of *window*.
    The first frames are skipped (they hold the made-up silence before the window), and the newest frame
    counts as soon as it is rising above the threshold, so a light can flash with little delay."""
    low, low_rate = decimate(window, rate, RHYTHM_RATE)
    extra = len(low) % LIVE_HOP                       # so that the newest frame ends exactly at the end
    low = low[extra:]
    env = flux(low, low_rate, LIVE_HOP)
    peaks = pick_peaks(env, LIVE_HOP / low_rate, confirmed=False, start=FLUX_FRAME // LIVE_HOP)
    return [_onset_time(i, LIVE_HOP, low_rate) + extra / low_rate for i in peaks]


# ---- chroma
def chroma_of(window: list[float], rate: int) -> list[float]:
    """Twelve numbers, the strength of each pitch class (C, C#, ... B) in *window*, from 0 to 1 (largest
    is 1). All zeros when there is nothing to hear. Each peak in the spectrum between 65 Hz and 2 kHz
    is placed on its nearest note, weighted by its strength."""
    low, low_rate = decimate(window, rate)
    if len(low) < CHROMA_FRAME:
        low = [0.0] * (CHROMA_FRAME - len(low)) + low
    frame = low[-CHROMA_FRAME:]
    return _chroma_frame(frame, low_rate)


def _chroma_frame(frame: list[float], rate: float) -> list[float]:
    n = len(frame)
    if not any(frame):
        return [0.0] * 12
    mags, _ = _two_spectra(frame, [0.0] * n)
    bin_hz = rate / n
    lo = max(2, int(CHROMA_LOW_HZ / bin_hz))
    hi = min(len(mags) - 2, int(CHROMA_HIGH_HZ / bin_hz) + 1)
    out = [0.0] * 12
    for k in range(lo, hi + 1):
        m = mags[k]
        if m < CHROMA_QUIET or m < mags[k - 1] or m <= mags[k + 1]:
            continue
        a, b, c = mags[k - 1], m, mags[k + 1]              # a parabola through the peak: a between-bins pitch
        bend = a - 2 * b + c
        shift = 0.5 * (a - c) / bend if bend < 0 else 0.0
        hz = (k + max(-0.5, min(0.5, shift))) * bin_hz
        if not CHROMA_LOW_HZ <= hz <= CHROMA_HIGH_HZ:
            continue
        midi = round(69 + 12 * math.log2(hz / 440.0))
        out[midi % 12] += m
    top = max(out)
    if top <= 0.0:
        return out
    return [v / top for v in out]


def chord_of(chroma: list[float]) -> str | None:
    """The name of the chord that best matches *chroma*, such as "C", "Am", "G7", "Fmaj7" or "Bdim",
    or None when none matches well, or when one pitch class stands alone."""
    top = max(chroma)
    if top <= 0.0:
        return None
    if sorted(chroma)[-2] < SINGLE_VOICE * top:
        return None
    norm = math.sqrt(sum(v * v for v in chroma))
    best, best_name = 0.0, None
    for suffix, intervals in CHORD_QUALITIES.items():
        size = math.sqrt(len(intervals))
        for root in range(12):
            hit = sum(chroma[(root + i) % 12] for i in intervals)
            score = hit / (norm * size)
            if score > best + 1e-9:
                best, best_name = score, NOTE_NAMES[root] + suffix
    return best_name if best >= CHORD_MIN_SCORE else None


def chord_notes(name: str) -> list[str]:
    """The note names in a chord name: "C" gives ["C", "E", "G"], "Am" gives ["A", "C", "E"]."""
    root, suffix = _split_chord(name)
    return [NOTE_NAMES[(root + i) % 12] for i in CHORD_QUALITIES[suffix]]


def _split_chord(name) -> tuple[int, str]:
    who = "f.chord_notes()"
    kinds = ", ".join(repr(s) for s in CHORD_QUALITIES if s)
    if not isinstance(name, str) or not name.strip():
        raise ValueError(f"{who}: give a chord name such as 'C', 'Am', 'G7' or 'Fmaj7', not {name!r}")
    text = name.strip()
    letter = text[0].upper()
    if letter not in "CDEFGAB":
        raise ValueError(f"{who}: {name!r} does not start with a note from A to G. "
                         "Try 'C', 'Am', 'G7' or 'Fmaj7'")
    rest = text[1:]
    root = NOTE_NAMES.index(letter)
    if rest[:1] == "#":
        root, rest = (root + 1) % 12, rest[1:]
    elif rest[:1] == "b":
        root, rest = (root - 1) % 12, rest[1:]
    if rest not in CHORD_QUALITIES:
        raise ValueError(f"{who}: {name!r} is not a chord funground knows. After the note, use nothing "
                         f"(major) or one of {kinds}")
    return root, rest


# ---- key
def key_of(samples, rate: int) -> str | None:
    """The key of a whole sound, "G major" or "E minor", or None. The chroma of frames spread over
    the sound is added up and compared with the Krumhansl-Schmuckler major and minor profiles."""
    low, low_rate = decimate(samples, rate)
    if len(low) < CHROMA_FRAME // 4:
        return None
    frames = min(400, max(1, len(low) // (CHROMA_FRAME // 2)))
    span = max(0, len(low) - CHROMA_FRAME)
    total = [0.0] * 12
    used = 0
    for f in range(frames):
        start = round(span * f / max(1, frames - 1)) if frames > 1 else 0
        frame = low[start:start + CHROMA_FRAME]
        if len(frame) < CHROMA_FRAME:
            frame = frame + [0.0] * (CHROMA_FRAME - len(frame))
        c = _chroma_frame(frame, low_rate)
        if max(c) > 0.0:
            used += 1
            for i in range(12):
                total[i] += c[i]
    if not used:
        return None
    return best_key(total)


def best_key(chroma: list[float]) -> str | None:
    """The key whose profile correlates best with *chroma* (twelve numbers), or None."""
    best, best_name = -2.0, None
    for mode, profile in (("major", KEY_MAJOR), ("minor", KEY_MINOR)):
        for tonic in range(12):
            shifted = [chroma[(tonic + i) % 12] for i in range(12)]
            r = _correlation(shifted, profile)
            if r > best:
                best, best_name = r, f"{NOTE_NAMES[tonic]} {mode}"
    return best_name if best >= KEY_MIN_SCORE else None


def _correlation(a, b) -> float:
    n = len(a)
    ma, mb = sum(a) / n, sum(b) / n
    num = sum((x - ma) * (y - mb) for x, y in zip(a, b))
    den = math.sqrt(sum((x - ma) ** 2 for x in a) * sum((y - mb) ** 2 for y in b))
    return num / den if den > 0 else 0.0
