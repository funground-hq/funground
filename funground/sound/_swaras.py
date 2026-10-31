"""The swaras the sound library needs (S-115, S-246; contract A8; D-057, D-062).

The plain Python behind ``sound.drone()``, ``Sound.tonic()`` and ``Sound.swara_histogram()``: a tanpura-like
drone, a pitch track, the tonic and the swara histogram. It lives with the sound library, because the sound
library must work without the sangeet library. ``sangeet`` imports the sound library, never the reverse.
Like ``_synth.py``, it uses only the standard library and computes lists of samples.
"""
from __future__ import annotations

import math
import random
from operator import add

from . import _synth as synth

RATE = synth.RATE


def _sa_hz(sa, who: str) -> float:
    """Sa as a frequency: from a note name such as "D3", or a number of hertz (tonic() gives one)."""
    if isinstance(sa, str):
        return synth.note_to_frequency(sa, who=who)
    if isinstance(sa, bool) or not isinstance(sa, (int, float)) or not math.isfinite(sa) or not 20 <= sa <= 5000:
        raise ValueError(f"{who}: sa must be a note name like 'D3' or a frequency from 20 to 5000 Hz, not {sa!r}")
    return float(sa)


# ---- the drone (a tanpura-like sound)
DRONE_GAP = 0.7                # seconds between plucks; the last string is followed by one more gap
DRONE_RING = 5.0               # how long each pluck is kept, in seconds
DRONE_T60 = 6.0                # seconds for a string to die away by 60 dB
DRONE_SOFTNESS = 32            # how many times the pluck's burst of noise is smoothed


def _string(frequency: float, seconds: float, rng: random.Random) -> list[float]:
    """A plucked string with a long ring (Karplus-Strong, like synth.pluck, with two changes for a
    drone). The pluck is soft: the burst of noise is smoothed first, as a fingertip pluck has
    fewer sharp edges than a pick, so there are no jumps in the wave. And each trip round the loop
    loses only enough to fade by 60 dB in DRONE_T60 seconds. The burst is synth.soft_burst, the
    pluck's low-pass filtered burst, smoothed more."""
    n = max(1, round(seconds * RATE))
    delay = RATE / frequency - 0.5
    ring = int(delay - 0.5)
    frac = delay - ring
    a = (1.0 - frac) / (1.0 + frac)
    buf = synth.soft_burst(ring, rng, DRONE_SOFTNESS)
    keep = 0.5 * 10.0 ** (-3.0 / (DRONE_T60 * frequency))
    out = [0.0] * n
    idx = 0
    prev = buf[ring - 1]
    ap_in = ap_out = 0.0
    for i in range(n):
        x = buf[idx]
        out[i] = x
        lp = (x + prev) * keep
        prev = x
        y = a * lp + ap_in - a * ap_out
        ap_in = lp
        ap_out = y
        buf[idx] = y
        idx += 1
        if idx == ring:
            idx = 0
    start = min(n, round(0.004 * RATE))                 # a 4 ms fade in: no click at the pluck
    for i in range(start):
        out[i] *= i / start
    end = min(n, round(0.5 * RATE))                     # and a fade out where it is cut off
    for j in range(end):
        out[n - 1 - j] *= j / end
    return out


def drone(sa, seconds, pattern: str = "P S' S' S", rng: random.Random | None = None,
          who: str = "sound.drone()", volume: float = synth.DEFAULT_VOLUME) -> list[float]:
    """The samples of a tanpura-like drone (contract A8). The strings in *pattern* are swaras above
    *sa*, tuned in just intonation (Pa is exactly 3/2 of Sa, as tanpuras are tuned by ear). They
    are plucked in turn, DRONE_GAP seconds apart, with one gap of rest after the last, and each
    rings on under the next. The tails that pass the end are added back at the start, so the
    sound loops without a gap. Its loudest point is *volume*."""
    sa_hz = _sa_hz(sa, who)
    seconds = synth._number(seconds, who, "the length in seconds", 0, 600, low_open=True)
    volume = synth._number(volume, who, "volume", 0, 1)
    if not isinstance(pattern, str) or not pattern.split():
        raise ValueError(f"{who}: pattern must be swaras separated by spaces, like \"P S' S' S\", not {pattern!r}")
    strings = []
    for token in pattern.split():
        try:
            step, octave = synth._swara(token, who)
        except ValueError:
            raise ValueError(f"{who}: {token!r} in the pattern is not a swara. Use S r R g G m M P d D n N, "
                             "with ' for the octave above and , for the octave below") from None
        hz = sa_hz * synth.JUST_RATIOS[step] * 2.0 ** octave
        if not 30.0 <= hz <= 2000.0:
            raise ValueError(f"{who}: the string {token!r} would be {hz:.0f} Hz, too low or too high for a drone")
        strings.append(hz)
    rng = rng or random.Random()
    n = max(1, round(seconds * RATE))
    plucks: dict[float, list[float]] = {}
    out = [0.0] * n
    cycle = (len(strings) + 1) * DRONE_GAP
    t = 0.0
    k = 0
    while t < seconds:
        hz = strings[k % len(strings)]
        if hz not in plucks:
            plucks[hz] = _string(hz, min(DRONE_RING, max(seconds, 1.0)), rng)
        sound = plucks[hz]
        at = round(t * RATE)
        first = min(len(sound), n - at)
        out[at:at + first] = map(add, out[at:at + first], sound[:first])
        rest = sound[first:]
        while rest:                                      # wrap the tail round to the start
            take = min(len(rest), n)
            out[:take] = map(add, out[:take], rest[:take])
            rest = rest[take:]
        k += 1
        t = (k // len(strings)) * cycle + (k % len(strings)) * DRONE_GAP
    peak = max(max(out), -min(out)) or 1.0
    return [volume * v / peak for v in out]


# ---- listening: a pitch track, the tonic, the swara histogram
TRACK_RATE = 11025             # the pitch track works on a copy at a quarter of 44 100
TRACK_WINDOW = 1024            # samples of that copy in each measurement (about 0.09 s)
TRACK_MAX_FRAMES = 300         # a long sound is measured less often, not for longer
TRACK_HOP = 0.02               # seconds between measurements, at most


def pitch_track(samples: list[float], rate: int) -> tuple[list[float | None], float]:
    """The pitch every so often through *samples*: a list of hertz or None (quiet or no clear
    pitch), and the seconds between them. Each measurement is synth.find_pitch, the method of
    a sound's pitch(), on a copy at about 11 025 samples a second (averaging blocks of samples first,
    which also removes most sound above the pitches a voice sings)."""
    factor = max(1, round(rate / TRACK_RATE))
    if factor > 1:
        usable = len(samples) - len(samples) % factor
        small = [sum(samples[i:i + factor]) / factor for i in range(0, usable, factor)]
    else:
        small = list(samples)
    small_rate = rate / factor
    if len(small) < TRACK_WINDOW:
        return [], TRACK_HOP
    span = len(small) - TRACK_WINDOW
    hop = max(round(TRACK_HOP * small_rate), math.ceil(span / TRACK_MAX_FRAMES) if span else 1)
    track = [synth.find_pitch(small[i:i + TRACK_WINDOW], small_rate) for i in range(0, span + 1, hop)]
    return track, hop / small_rate


BIN_CENTS = 10                 # the tonic's histogram: 120 bins of 10 cents
PA_CENTS = 702                 # a pure fifth above Sa
MIN_VOICED = 10                # fewer measurements with a pitch than this, and tonic() says None


def tonic(track: list[float | None]) -> float | None:
    """Estimate Sa from a pitch track (a heuristic; contract A8).

    1. Each pitch is turned into cents within one octave (0 to 1 200, measured from A), so the
       same swara in any octave lands in the same place.
    2. These are counted in 120 bins of 10 cents, each pitch shared between its two nearest bins,
       and the counts are smoothed a little (over about 20 cents each way).
    3. Sa is the bin whose own count plus the count a pure fifth (702 cents) above it is largest:
       the bin that best explains a strong Sa-Pa pair, as Sa and Pa dominate when a drone plays
       and are the notes a melody rests on most. Its exact pitch is the average of the pitches
       within 30 cents of that bin.
    4. The octave is the one in which that pitch class was heard most often (the lower on a tie).

    It is wrong when Pa is weak or missing (a raga without Pa, or a drone tuned to Ma) and when
    the melody rests on another note far more than on Sa. None when fewer than MIN_VOICED pitches
    were heard."""
    voiced = [hz for hz in track if hz]
    if len(voiced) < MIN_VOICED:
        return None
    bins = 1200 // BIN_CENTS
    counts = [0.0] * bins
    cents = []
    for hz in voiced:
        c = (1200.0 * math.log2(hz / 440.0)) % 1200.0
        cents.append(c)
        pos = c / BIN_CENTS
        lo = int(pos) % bins
        frac = pos - int(pos)
        counts[lo] += 1.0 - frac
        counts[(lo + 1) % bins] += frac
    kernel = (1, 2, 3, 2, 1)
    smooth = [sum(w * counts[(i + k - 2) % bins] for k, w in enumerate(kernel)) for i in range(bins)]
    fifth = round(PA_CENTS / BIN_CENTS)
    best = max(range(bins), key=lambda i: (smooth[i] + smooth[(i + fifth) % bins], smooth[i]))
    centre = best * BIN_CENTS

    def offset(c: float) -> float:
        return (c - centre + 600.0) % 1200.0 - 600.0

    near = [offset(c) for c in cents if abs(offset(c)) <= 30.0]
    sa_class = centre + (sum(near) / len(near) if near else 0.0)
    octaves: dict[int, int] = {}
    for hz in voiced:
        steps = 1200.0 * math.log2(hz / 440.0) - sa_class
        k = round(steps / 1200.0)
        if abs(steps - 1200.0 * k) <= 50.0:
            octaves[k] = octaves.get(k, 0) + 1
    k = max(sorted(octaves), key=lambda o: octaves[o]) if octaves else 0
    return 440.0 * 2.0 ** ((sa_class + 1200.0 * k) / 1200.0)


def swara_histogram(track: list[float | None], sa_hz: float) -> list[float]:
    """The share of the voiced time spent on each of the 12 swaras (S r R g G m M P d D n N), in
    any octave, each swara owning the pitches within 50 cents of it. The shares add up to 1, or
    are all 0 when nothing with a pitch was heard."""
    counts = [0] * 12
    for hz in track:
        if hz:
            counts[round(12.0 * math.log2(hz / sa_hz)) % 12] += 1
    total = sum(counts)
    return [c / total for c in counts] if total else [0.0] * 12
