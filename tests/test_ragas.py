"""Ragas for learners (S-115; contract A8; D-057, D-062).

The raga and tala table is data checked against published sources (funground/data/ragas.json);
these tests check that it is consistent and playable. The sounds are computed, so no files or
sound device are needed.
"""
from __future__ import annotations

import json
import math
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

import funground as f
from funground import hindustani as ragas, synth

RATE = 44100
SA = "D4"
DATA = Path(ragas.__file__).with_name("data") / "ragas.json"


def cents(hz, ref):
    return 1200 * math.log2(hz / ref)


# ---- the table
def test_the_table_lists_ragas_and_talas():
    names = f.ragas()
    assert len(names) >= 12
    for name in ("Yaman", "Bhupali", "Deshkar", "Bhairav", "Bhairavi"):
        assert name in names
    assert f.talas() == ["Teentaal", "Ektaal", "Jhaptaal", "Rupak", "Dadra", "Keherwa"]


def test_raga_lookup_ignores_capitals_and_is_read_only():
    yaman = f.raga("yAMAN")
    assert yaman is f.raga("Yaman")
    assert yaman.thaat == "Kalyan"
    assert yaman.swaras == ("S", "R", "G", "M", "P", "D", "N")
    assert (yaman.vadi, yaman.samvadi) == ("G", "N")
    with pytest.raises(FrozenInstanceError):
        yaman.vadi = "S"
    assert "Yaman" in str(yaman)


@pytest.mark.parametrize("call", [f.raga, f.tala_info])
def test_an_unknown_name_lists_the_table(call):
    with pytest.raises(ValueError) as info:
        call("Nonesuch")
    assert "Nonesuch" in str(info.value)
    names = f.ragas() if call is f.raga else f.talas()
    assert all(name in str(info.value) for name in names)
    with pytest.raises(ValueError):
        call(5)


@pytest.mark.parametrize("name", f.ragas())
def test_every_raga_is_consistent_and_playable(name):
    r = f.raga(name)
    assert r.thaat and r.time and r.sources
    assert len(r.sources) >= 2, "every raga cites at least two sources"
    assert r.swaras[0] == "S" and len(set(r.swaras)) == len(r.swaras)
    assert all(s in synth.SARGAM for s in r.swaras)
    assert list(r.swaras) == sorted(r.swaras, key=synth.SARGAM.index)
    assert r.vadi in r.swaras and r.samvadi in r.swaras and r.vadi != r.samvadi
    for phrase in (r.aroha, r.avaroha, r.pakad):
        f.melody(phrase, sa=SA)                                  # parses and plays
        for token in phrase.split():
            assert token.rstrip("',") in r.swaras, f"{name}: {token} is not one of its swaras"
    assert r.aroha.split()[-1] == "S'" and r.avaroha.split()[0] == "S'" and r.avaroha.split()[-1] == "S"


@pytest.mark.parametrize("name", f.talas())
def test_every_tala_is_consistent_and_playable(name):
    t = f.tala_info(name)
    assert len(t.bols) == t.beats == sum(t.vibhag)
    assert t.sam == 1
    starts = [1 + sum(t.vibhag[:i]) for i in range(len(t.vibhag))]
    assert sorted(t.tali + t.khali) == starts, "each vibhag starts with a clap or a wave"
    assert len(t.sources) >= 2
    for bol in t.bols:
        assert ragas.strokes_of(bol)


def test_tala_facts():
    assert (f.tala_info("teentaal").tali, f.tala_info("teentaal").khali) == ((1, 5, 13), (9,))
    assert f.tala_info("Ektaal").vibhag == (2, 2, 2, 2, 2, 2)
    assert f.tala_info("Jhaptaal").vibhag == (2, 3, 2, 3)
    rupak = f.tala_info("Rupak")
    assert rupak.vibhag == (3, 2, 2) and rupak.khali == (1,) and rupak.tali == (4, 6)   # sam is khali
    assert f.tala_info("Dadra").beats == 6 and f.tala_info("Keherwa").beats == 8


def test_the_data_file_cites_each_entry():
    data = json.loads(DATA.read_text(encoding="utf-8"))
    for entry in data["ragas"] + data["talas"]:
        for cite in entry["sources"]:
            assert cite["source"] in data["sources"] and cite["supports"]
    for source in data["sources"].values():
        assert source["title"] and source["where"]


# ---- the drone
def test_drone_length_and_no_clicks():
    f.random_seed(1)
    d = f.drone("D3", 6)
    v = d.samples()
    assert len(v) == round(6 * RATE)
    assert max(abs(x) for x in v) <= 0.8 + 1e-9
    # A click is a jump from one sample to the next far bigger than the wave's own steepness. The
    # brightest part of a pluck moves by up to about 0.2 a sample; a click would be near 0.8.
    assert max(abs(v[i + 1] - v[i]) for i in range(len(v) - 1)) < 0.25
    assert abs(v[0] - v[-1]) < 0.25                              # it loops without a click too


def test_drone_patterns_and_errors():
    f.random_seed(2)
    for pattern in ("m S' S' S", "N S' S' S", "P S"):
        assert f.drone("C3", 2, pattern).duration() == pytest.approx(2, abs=0.01)
    assert f.drone(146.83, 1).duration() == pytest.approx(1, abs=0.01)     # sa may be hertz
    for kwargs in (dict(sa="Q3", seconds=2), dict(sa="D3", seconds=0), dict(sa="D3", seconds=2, pattern=""),
                   dict(sa="D3", seconds=2, pattern="P X"), dict(sa=5, seconds=2)):
        with pytest.raises(ValueError):
            f.drone(**kwargs)


def test_drone_plays_its_strings():
    f.random_seed(3)
    sa = synth.note_to_frequency("D3")
    for pattern, ratio in (("P", 1.5), ("S'", 2.0), ("m", 4 / 3)):     # one string, tuned just
        v = f.drone("D3", 2, pattern).samples()
        assert abs(cents(synth.find_pitch(v[RATE:RATE + 2048], RATE), sa * ratio)) < 10


# ---- meend and kan
def test_meend_glides_smoothly():
    v = f.melody("S~G:2", tempo=60, sa=SA).samples()
    assert len(v) == 2 * RATE
    sa = synth.note_to_frequency(SA)
    heard = []
    for t in (0.1, 0.4, 0.7, 1.0, 1.3, 1.6, 1.9):
        i = int(t * RATE)
        heard.append(cents(synth.find_pitch(v[i - 1024:i + 1024], RATE), sa))
    assert abs(heard[0]) < 15 and abs(heard[-1] - 400) < 15
    assert abs(heard[3] - 200) < 20                              # half way in pitch, half way in time
    assert all(b > a for a, b in zip(heard, heard[1:]))           # always rising
    assert max(abs(v[i + 1] - v[i]) for i in range(len(v) - 1)) < 0.1


def test_meend_works_with_note_names_and_downwards():
    v = f.melody("G4~C4", tempo=60).samples()
    assert abs(cents(synth.find_pitch(v[-4096:-2048], RATE), synth.note_to_frequency("C4"))) < 25


def test_kan_touches_the_grace_note_for_60_ms():
    v = f.melody("(R)G", tempo=60, sa=SA).samples()
    assert len(v) == RATE
    sa = synth.note_to_frequency(SA)
    window = round(0.02 * RATE)

    def heard(t):
        i = round(t * RATE)
        return round(cents(synth.find_pitch(v[i:i + window], RATE), sa) / 100)

    assert heard(0.015) == 2 and heard(0.035) == 2                # Re
    assert heard(0.065) == 4 and heard(0.3) == 4                  # then Ga
    v2 = f.melody("(D4)E4 E4", tempo=60).samples()
    assert abs(cents(synth.find_pitch(v2[600:600 + window], RATE), synth.note_to_frequency("D4"))) < 25


@pytest.mark.parametrize("text, token", [("S (R)", "(R)"), ("S (R)-", "(R)-"), ("S~", "S~"),
                                         ("S~G~P", "S~G~P"), ("((R)G", "((R)G"), ("-~S", "-~S"),
                                         ("S~Z", "S~Z"), ("(Z)G", "(Z)G")])
def test_bad_ornaments_are_named(text, token):
    with pytest.raises(ValueError) as info:
        f.melody(text, sa=SA)
    assert repr(token) in str(info.value)


# ---- the tala
def test_tala_length():
    for name, tempo, cycles in (("Teentaal", 80, 1), ("Rupak", 120, 2), ("Ektaal", 60, 1)):
        beats = f.tala_info(name).beats
        assert len(f.tala(name, tempo=tempo, cycles=cycles).samples()) == round(beats * 60 / tempo * cycles * RATE)


def _onsets(v, frame=round(0.005 * RATE)):
    """Times where the loudness jumps: a frame much louder than the one before."""
    peaks = [max(abs(x) for x in v[i:i + frame]) for i in range(0, len(v) - frame, frame)]
    return [k * frame / RATE for k in range(1, len(peaks)) if peaks[k] > 1.8 * peaks[k - 1] + 0.02]


def test_tala_strokes_fall_on_the_beats():
    tempo = 90
    beat = 60 / tempo
    v = f.tala("Teentaal", tempo=tempo).samples()
    onsets = _onsets(v)
    for b in range(1, 16):                                       # every beat has a stroke
        assert any(abs(t - b * beat) < 0.012 for t in onsets), b
    for t in onsets:                                             # and nothing falls between
        assert abs(t / beat - round(t / beat)) * beat < 0.012, t


def test_tala_accents_the_sam_and_softens_the_khali():
    v = f.tala("Teentaal", tempo=60).samples()

    def loud(b):
        i = (b - 1) * RATE
        return max(abs(x) for x in v[i:i + 2000])

    assert loud(1) > loud(2)
    assert loud(10) < loud(2)                                    # Tin in the khali vibhag


def test_tala_errors():
    for kwargs in (dict(name="Nonesuch"), dict(name="Rupak", tempo=0), dict(name="Rupak", cycles=0),
                   dict(name="Rupak", cycles=1.5)):
        with pytest.raises(ValueError):
            f.tala(**kwargs)


# ---- listening
@pytest.fixture(scope="module")
def yaman_phrase():
    r = f.raga("Yaman")
    return f.melody(f"{r.aroha} {r.avaroha} {r.pakad}", tempo=150, sa=SA, tuning="just")


def test_tonic_over_a_drone():
    f.random_seed(4)
    phrase = f.melody("S R G:2 R S:2 N, D, P,:2 S:3 G M P:2 M G R S:3", tempo=100, sa=SA, tuning="just")
    sound = f.mix(phrase, f.drone("D3", phrase.duration()))
    sa = sound.tonic()
    assert sa is not None and abs(cents(sa, synth.note_to_frequency(SA))) < 30


def test_tonic_of_silence_is_none():
    assert f.create_sound([0.0] * RATE).tonic() is None


def test_swara_histogram_of_yaman(yaman_phrase):
    h = yaman_phrase.swara_histogram(SA)
    assert len(h) == 12 and sum(h) == pytest.approx(1)
    on = sum(h[synth.SARGAM.index(s)] for s in f.raga("Yaman").swaras)
    assert on > 0.95
    assert yaman_phrase.swara_histogram(synth.note_to_frequency(SA)) == h        # sa in hertz
    assert f.create_sound([0.0] * RATE).swara_histogram(SA) == [0.0] * 12
    with pytest.raises(ValueError):
        yaman_phrase.swara_histogram("nonsense")


def test_match_ranks_yaman_first(yaman_phrase):
    ranked = f.match_ragas(yaman_phrase.swara_histogram(SA))
    assert ranked[0][0] == "Yaman"
    assert len(ranked) == len(f.ragas())
    assert all(0 <= score <= 1 for _, score in ranked)
    assert [s for _, s in ranked] == sorted((s for _, s in ranked), reverse=True)


def test_match_ranks_bhupali_first_and_shows_the_limit():
    r = f.raga("Bhupali")
    h = f.melody(f"{r.aroha} {r.avaroha} {r.pakad}", tempo=150, sa=SA).swara_histogram(SA)
    ranked = dict(f.match_ragas(h))
    assert f.match_ragas(h)[0][0] == "Bhupali"
    # Bhupali and Deshkar use the same five swaras: the scores are almost the same, which is the
    # documented limit of comparing note sets.
    assert ranked["Bhupali"] - ranked["Deshkar"] < 0.05
    assert ranked["Bhupali"] - ranked["Yaman"] > 0.15


def test_match_errors():
    for bad in ([0.1] * 11, [0.0] * 12, [-1] + [0.1] * 11, "abc", None, [math.nan] * 12):
        with pytest.raises(ValueError):
            f.match_ragas(bad)
