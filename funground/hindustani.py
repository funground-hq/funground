"""Ragas and talas for learners (S-115; contract A8; D-057, D-062).

This module holds funground's small built-in table of Hindustani ragas and talas, and the plain
Python behind ``f.drone()``, ``f.tala()``, ``sound.tonic()``, ``sound.swara_histogram()`` and
``f.match_ragas()``. The table lives in ``data/ragas.json``; every raga and tala there names the
published sources its facts were checked against. ``docs/design/Ragas_Note.md`` gives the methods
and their limits.

Like ``synth.py``, it uses only the standard library and computes lists of samples; ``api.py``
turns them into sounds.
"""
from __future__ import annotations

import json
import math
import random
import re
from dataclasses import dataclass
from operator import add
from pathlib import Path

from . import synth

RATE = synth.RATE
_DATA = Path(__file__).with_name("data") / "ragas.json"


# ---- the table
@dataclass(frozen=True)
class Raga:
    """One raga from the table. Read-only. The phrases are sargam strings for f.melody(sa=...)."""

    name: str
    thaat: str
    swaras: tuple[str, ...]
    aroha: str
    avaroha: str
    pakad: str
    vadi: str
    samvadi: str
    time: str
    notes: str = ""
    sources: tuple[str, ...] = ()

    def __str__(self) -> str:
        return (f"{self.name} ({self.thaat} thaat): {' '.join(self.swaras)}; vadi {self.vadi}, "
                f"samvadi {self.samvadi}; {self.time}")


@dataclass(frozen=True)
class Tala:
    """One tala from the table. Read-only. Beats are counted from 1, so the sam is beat 1."""

    name: str
    beats: int
    vibhag: tuple[int, ...]
    tali: tuple[int, ...]
    khali: tuple[int, ...]
    sam: int
    bols: tuple[str, ...]
    notes: str = ""
    sources: tuple[str, ...] = ()

    def __str__(self) -> str:
        return f"{self.name}: {self.beats} beats ({'+'.join(map(str, self.vibhag))}); {' '.join(self.bols)}"


_table: dict | None = None


def _load() -> dict:
    """Read the JSON table once, into Raga and Tala objects keyed by lower-case name and alias."""
    global _table
    if _table is None:
        data = json.loads(_DATA.read_text(encoding="utf-8"))
        cite = data["sources"]

        def sources(entry) -> tuple[str, ...]:
            return tuple(f"{cite[s['source']]['title']}, {s.get('url') or cite[s['source']]['where']}: "
                         f"{s['supports']}" for s in entry["sources"])

        ragas, talas, raga_keys, tala_keys = [], [], {}, {}
        for r in data["ragas"]:
            raga = Raga(r["name"], r["thaat"], tuple(r["swaras"]), r["aroha"], r["avaroha"], r["pakad"],
                        r["vadi"], r["samvadi"], r["time"], r.get("notes", ""), sources(r))
            ragas.append(raga)
            for key in [r["name"], *r.get("aliases", [])]:
                raga_keys[key.lower()] = raga
        for t in data["talas"]:
            tala = Tala(t["name"], t["beats"], tuple(t["vibhag"]), tuple(t["tali"]), tuple(t["khali"]),
                        t["sam"], tuple(t["bols"]), t.get("notes", ""), sources(t))
            talas.append(tala)
            for key in [t["name"], *t.get("aliases", [])]:
                tala_keys[key.lower()] = tala
        _table = {"ragas": ragas, "talas": talas, "raga_keys": raga_keys, "tala_keys": tala_keys}
    return _table


def raga_names() -> list[str]:
    return [r.name for r in _load()["ragas"]]


def tala_names() -> list[str]:
    return [t.name for t in _load()["talas"]]


def find_raga(name, who: str = "f.raga()") -> Raga:
    table = _load()
    found = table["raga_keys"].get(name.strip().lower()) if isinstance(name, str) else None
    if found is None:
        raise ValueError(f"{who}: {name!r} is not in funground's raga table. It has: {', '.join(raga_names())}")
    return found


def find_tala(name, who: str = "f.tala_info()") -> Tala:
    table = _load()
    found = table["tala_keys"].get(name.strip().lower()) if isinstance(name, str) else None
    if found is None:
        raise ValueError(f"{who}: {name!r} is not in funground's tala table. It has: {', '.join(tala_names())}")
    return found


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
          who: str = "f.drone()", volume: float = synth.DEFAULT_VOLUME) -> list[float]:
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


# ---- the tala (simple synthesised tabla strokes)
# Each syllable of a bol is one stroke. A bol written as one word, like DhaGe or TiRaKiTa, is split
# at its capital letters and its strokes share the beat.
_STROKES = {
    "dha": ("bass", "open"), "dhin": ("bass", "ring"), "dhi": ("bass", "ring"), "dhe": ("bass", "open"),
    "ge": ("bass",), "ghe": ("bass",), "ga": ("bass",), "gi": ("bass",),
    "na": ("open",), "ta": ("open",), "tin": ("ring",), "tun": ("ring",), "tu": ("ring",),
    "ti": ("light",), "te": ("light",), "ra": ("light",), "ri": ("light",),
    "ka": ("click",), "ke": ("click",), "ki": ("click",), "kat": ("click",), "kath": ("click",),
}
TABLA_HZ = 280.0               # the pitch of the right-hand drum (the dayan)
TALA_PEAK = 0.5                # the loudest stroke, the same headroom as the other sounds (A9)


def strokes_of(bol: str, who: str = "f.tala()") -> list[tuple[str, ...]]:
    """The strokes of one bol: "DhaGe" -> [("bass", "open"), ("bass",)]."""
    parts = re.findall(r"[A-Z][a-z]*", bol)
    if not parts or "".join(parts) != bol:
        raise ValueError(f"{who}: cannot play the bol {bol!r}")
    out = []
    for part in parts:
        if part.lower() not in _STROKES:
            raise ValueError(f"{who}: cannot play the bol {bol!r} ({part!r} is not a stroke it knows)")
        out.append(_STROKES[part.lower()])
    return out


def _stroke(kind: str, rng: random.Random) -> list[float]:
    """One drum sound. bass: the left-hand drum, a low thud that falls in pitch. open: a bright,
    short ring of the right-hand drum (Na, Ta). ring: a longer, purer ring (Tin, Tun). light: a
    soft short tap (Ti, Ra). click: a dry, damped slap (Ka, Ke)."""
    if kind == "click":
        n = round(0.03 * RATE)
        out, low = [], 0.0
        for i in range(n):
            low += 0.35 * ((2.0 * rng.random() - 1.0) - low)          # a dull slap, not a hiss
            out.append(1.6 * low * math.exp(-i / (0.006 * RATE)))
        return out
    if kind == "bass":
        n = round(0.45 * RATE)
        out, phase = [], 0.0
        for i in range(n):
            t = i / RATE
            hz = 75.0 + 45.0 * math.exp(-t / 0.05)
            phase += hz / RATE
            out.append(math.sin(2 * math.pi * phase) * math.exp(-t / 0.13))
        return out
    seconds, decay, partials, level = {
        "open": (0.4, 0.09, (1.0, 0.6, 0.45, 0.3, 0.2), 0.8),
        "ring": (0.8, 0.28, (1.0, 0.35, 0.15, 0.08), 0.8),
        "light": (0.15, 0.03, (1.0, 0.5, 0.4, 0.3), 0.5),
    }[kind]
    n = round(seconds * RATE)
    w = 2 * math.pi * TABLA_HZ / RATE
    out = []
    for i in range(n):
        t = i / RATE
        v = sum(p * math.sin(w * (k + 1) * i) * math.exp(-t * (k + 1) ** 0.5 / decay)
                for k, p in enumerate(partials))
        out.append(level * v / sum(partials))
    for i in range(round(0.003 * RATE)):                 # a little noise at the strike
        out[i] += 0.3 * (2.0 * rng.random() - 1.0) * (1.0 - i / (0.003 * RATE))
    return out


def tala(name, tempo=80, cycles=1, rng: random.Random | None = None, who: str = "f.tala()") -> list[float]:
    """The samples of a tala's theka played *cycles* times at *tempo* beats a minute. The sam (beat
    1) is accented; the khali vibhag is played more softly. The sound lasts exactly
    beats * 60 / tempo * cycles seconds; the last strokes are cut off there with a short fade."""
    info = find_tala(name, who)
    tempo = synth._number(tempo, who, "tempo (beats a minute)", 10, 600)
    if isinstance(cycles, bool) or not isinstance(cycles, int) or not 1 <= cycles <= 64:
        raise ValueError(f"{who}: cycles must be a whole number from 1 to 64, not {cycles!r}")
    rng = rng or random.Random(115)
    beat = 60.0 / tempo
    n = round(info.beats * beat * cycles * RATE)
    out = [0.0] * n
    cache: dict[str, list[float]] = {}
    khali_beats = set()
    start = 1
    for size in info.vibhag:
        if start in info.khali:
            khali_beats.update(range(start, start + size))
        start += size
    for c in range(cycles):
        for b, bol in enumerate(info.bols, start=1):
            gain = 1.0 if b == info.sam else 0.7
            if b in khali_beats:
                gain *= 0.6
            strokes = strokes_of(bol, who)
            for s, kinds in enumerate(strokes):
                at = round(((c * info.beats + b - 1) + s / len(strokes)) * beat * RATE)
                for kind in kinds:
                    if kind not in cache:
                        cache[kind] = _stroke(kind, rng)
                    sound = cache[kind]
                    take = min(len(sound), n - at)
                    if take > 0:
                        out[at:at + take] = map(add, out[at:at + take], (gain * v for v in sound[:take]))
    fade = min(n, round(0.005 * RATE))
    for j in range(fade):
        out[n - 1 - j] *= j / fade
    peak = max(max(out), -min(out)) or 1.0
    return [TALA_PEAK * v / peak for v in out]


# ---- listening: a pitch track, the tonic, the swara histogram
TRACK_RATE = 11025             # the pitch track works on a copy at a quarter of 44 100
TRACK_WINDOW = 1024            # samples of that copy in each measurement (about 0.09 s)
TRACK_MAX_FRAMES = 300         # a long sound is measured less often, not for longer
TRACK_HOP = 0.02               # seconds between measurements, at most


def pitch_track(samples: list[float], rate: int) -> tuple[list[float | None], float]:
    """The pitch every so often through *samples*: a list of hertz or None (quiet or no clear
    pitch), and the seconds between them. Each measurement is synth.find_pitch, the method of
    sound.pitch(), on a copy at about 11 025 samples a second (averaging blocks of samples first,
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


# ---- matching a histogram to the table
def match(histogram, who: str = "f.match_ragas()") -> list[tuple[str, float]]:
    """Rank the table's ragas by how well their swaras fit *histogram* (12 numbers, as from
    swara_histogram). A learning aid that compares note sets, not a raga recogniser.

    For each raga, with k swaras:
    - fit: the share of the histogram on the raga's swaras (the rest is on notes it does not use);
    - coverage: how many of its swaras were heard at all (a swara counts in full once it has a
      quarter of an even share, 1 / (4k));
    - stress: how much the vadi (counted twice) and samvadi stand out, x = (2 vadi + samvadi) * k / 3,
      turned into 0..1 as x / (1 + x).
    The score is fit squared, times coverage, times (0.85 + 0.15 stress): from 0 to 1, best first.
    Ragas with the same swaras (Bhupali and Deshkar, Khamaj and Desh) get almost the same score;
    only the stress tells them apart, a little."""
    try:
        values = [float(v) for v in histogram]
    except (TypeError, ValueError):
        values = []
    if len(values) != 12 or not all(math.isfinite(v) and v >= 0 for v in values):
        raise ValueError(f"{who}: the histogram must be 12 numbers of 0 or more (as from swara_histogram), "
                         f"not {histogram!r}")
    total = sum(values)
    if total <= 0:
        raise ValueError(f"{who}: the histogram is all zeros, so nothing was heard to match")
    h = [v / total for v in values]
    results = []
    for r in _load()["ragas"]:
        steps = [synth.SARGAM.index(s) for s in r.swaras]
        k = len(steps)
        fit = sum(h[i] for i in steps)
        coverage = sum(min(1.0, h[i] * 4.0 * k) for i in steps) / k
        x = (2.0 * h[synth.SARGAM.index(r.vadi)] + h[synth.SARGAM.index(r.samvadi)]) * k / 3.0
        score = fit * fit * coverage * (0.85 + 0.15 * x / (1.0 + x))
        results.append((r.name, round(score, 4)))
    results.sort(key=lambda pair: -pair[1])
    return results
