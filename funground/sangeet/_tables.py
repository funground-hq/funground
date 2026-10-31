"""Ragas and talas for learners (S-115, S-246; contract A8; D-057, D-062).

This module holds funground's small built-in table of Hindustani ragas and talas, and the plain
Python behind ``sangeet.tala()`` and ``sangeet.match_ragas()``. The table lives in ``data/ragas.json``;
every raga and tala there names the published sources its facts were checked against.
``docs/design/Ragas_Note.md`` gives the methods and their limits.

The drone, the pitch track, the tonic and the swara histogram are in ``sound/_swaras.py``: the sound
library needs them and must not import sangeet.

Like ``sound/_synth.py``, it uses only the standard library and computes lists of samples; the sangeet
library turns them into sounds.
"""
from __future__ import annotations

import json
import math
import random
import re
from dataclasses import dataclass
from operator import add
from pathlib import Path

from ..sound import _synth as synth

RATE = synth.RATE
_DATA = Path(__file__).resolve().parent.parent / "data" / "ragas.json"


# ---- the table
@dataclass(frozen=True)
class Raga:
    """One raga from funground's small table. It is read-only.

    You get one from sangeet.raga(name). Its parts are:
    name: the raga's name.
    thaat: the parent scale it belongs to.
    swaras: the notes it uses, as a tuple of letters such as ("S", "R", "G"). Small r, g, d and n are komal (flat). M is tivra (sharp) Ma.
    aroha: the way up, as a sargam string that sound.melody(text, sa=...) can play.
    avaroha: the way down, as a sargam string.
    pakad: a phrase that marks the raga, as a sargam string.
    vadi: the most important swara.
    samvadi: the second most important swara.
    time: the traditional time of day to perform it.
    notes: where the sources differ, and other things to know. It may be empty.
    sources: a tuple of texts that say where each fact was checked.

    str(raga) gives a short summary. A raga is much more than its notes, and the table gives a start, not
    the raga.

    Example:
        yaman = sangeet.raga("Yaman")
        print(yaman.thaat, yaman.swaras)
        sound.melody(yaman.aroha, sa="D4").play()

    See also: raga, ragas, melody, match_ragas
    """

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
    """One tala from funground's small table. It is read-only.

    You get one from sangeet.tala_info(name). Beats are counted from 1, so the sam is beat 1. Its parts are:
    name: the tala's name.
    beats: how many beats in one cycle.
    vibhag: the divisions, as a tuple of beat counts such as (4, 4, 4, 4).
    tali: the beat numbers that are claps.
    khali: the beat numbers that are waves (the empty beats).
    sam: the first beat, always 1.
    bols: the theka, the drum syllables, one for each beat.
    notes: where the sources differ, and other things to know. It may be empty.
    sources: a tuple of texts that say where each fact was checked.

    str(tala) gives a short summary. Use sangeet.tala(name) to hear the theka.

    Example:
        teentaal = sangeet.tala_info("Teentaal")
        print(teentaal.beats, teentaal.bols)

    See also: tala_info, talas, tala
    """

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


def find_raga(name, who: str = "sangeet.raga()") -> Raga:
    table = _load()
    found = table["raga_keys"].get(name.strip().lower()) if isinstance(name, str) else None
    if found is None:
        raise ValueError(f"{who}: {name!r} is not in funground's raga table. It has: {', '.join(raga_names())}")
    return found


def find_tala(name, who: str = "sangeet.tala_info()") -> Tala:
    table = _load()
    found = table["tala_keys"].get(name.strip().lower()) if isinstance(name, str) else None
    if found is None:
        raise ValueError(f"{who}: {name!r} is not in funground's tala table. It has: {', '.join(tala_names())}")
    return found


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


def strokes_of(bol: str, who: str = "sangeet.tala()") -> list[tuple[str, ...]]:
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


def tala(name, tempo=80, cycles=1, rng: random.Random | None = None, who: str = "sangeet.tala()") -> list[float]:
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


# ---- matching a histogram to the table
def match(histogram, who: str = "sangeet.match_ragas()") -> list[tuple[str, float]]:
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
