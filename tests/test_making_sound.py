"""Making sound (S-110; contract A3; D-055, D-056; ADR-006).

Sounds here are computed, so no files are needed. Time is driven by replacing
`funground.sound.clock`, as in test_sound.py, so nothing sleeps.
"""
from __future__ import annotations

import math
import wave

import pytest

import funground as f
from funground import sound as sound_module, synth

RATE = 44100


class FakeClock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now

    def advance(self, seconds: float):
        self.now += seconds


@pytest.fixture
def clock(monkeypatch):
    fake = FakeClock()
    monkeypatch.setattr(sound_module, "clock", fake)
    return fake


def rms(values):
    return math.sqrt(sum(v * v for v in values) / len(values))


def pitch_at(snd, clock, seconds):
    snd.play()
    clock.advance(seconds)
    value = snd.pitch()
    snd.stop()
    return value


# ---- create_sound and samples
def test_create_sound_round_trip_and_clipping():
    snd = f.create_sound([0.0, 0.5, -0.5, 2.0, -3.0], rate=8000)
    assert snd.samples() == [0.0, 0.5, -0.5, 1.0, -1.0]
    assert snd.duration() == pytest.approx(5 / 8000, abs=1e-4)


def test_created_sound_is_an_ordinary_sound(clock):
    snd = f.create_sound([math.sin(i / 10) for i in range(RATE)])
    assert snd.duration() == pytest.approx(1.0, abs=0.001)
    snd.play()
    clock.advance(0.25)
    assert snd.is_playing() and snd.current_time() == pytest.approx(0.25)
    assert snd.level() > 0.5 and len(snd.spectrum(16)) == 16
    snd.pause()
    assert not snd.is_playing()
    snd.set_volume(0.5)
    assert snd.get_volume() == 0.5
    snd.loop()
    clock.advance(5.5)
    assert snd.is_playing()
    snd.stop()
    assert snd.current_time() == 0.0


def test_create_sound_resamples_to_the_mixer_rate(clock):
    snd = f.create_sound([0.5] * 22050, rate=22050)      # one second at 22 050 a second
    assert snd.duration() == pytest.approx(1.0, abs=0.001)
    assert len(snd.samples()) == 22050                    # samples() gives back what it was given


@pytest.mark.parametrize("bad", [[], ["a"], None, [float("nan")], [0, float("inf")]])
def test_create_sound_rejects_bad_samples(bad):
    with pytest.raises(ValueError, match="create_sound"):
        f.create_sound(bad)


def test_create_sound_rejects_bad_rate():
    with pytest.raises(ValueError, match="rate"):
        f.create_sound([0.0], rate=10)


def test_loaded_sounds_have_samples_too(tmp_path):
    path = tmp_path / "x.wav"
    f.tone(440, 0.2).save(str(path))
    loaded = f.load_sound(str(path))
    values = loaded.samples()
    assert len(values) == pytest.approx(0.2 * RATE, abs=2)
    assert 0.45 < max(values) <= 0.5 + 1e-4                   # made at the default volume, 0.5 (A9)


# ---- wave shapes
STEADY = dict(volume=1, attack=0, decay=0, sustain=1, release=0)     # the bare wave, peak 1


def test_rms_of_each_wave():
    # Square, saw and triangle are built from their harmonics (A9) and scaled to peak 1, so their
    # RMS is a little below the sharp-cornered shapes' (1, 0.577, 0.577); sine and noise are as before.
    assert rms(f.tone(440, 1, "sine", **STEADY).samples()) == pytest.approx(0.7071, abs=0.002)
    assert rms(f.tone(440, 1, "square", **STEADY).samples()) == pytest.approx(0.844, abs=0.01)
    assert rms(f.tone(440, 1, "saw", **STEADY).samples()) == pytest.approx(0.496, abs=0.01)
    assert rms(f.tone(440, 1, "triangle", **STEADY).samples()) == pytest.approx(0.582, abs=0.01)
    assert rms(f.tone(440, 1, "soft", **STEADY).samples()) == pytest.approx(0.649, abs=0.01)
    assert rms(f.tone(440, 1, "noise", **STEADY).samples()) == pytest.approx(0.577, abs=0.02)
    for wave_name in ("sine", "square", "saw", "triangle", "soft", "noise"):
        assert max(abs(v) for v in f.tone(440, 1, wave_name, **STEADY).samples()) == pytest.approx(1.0, abs=0.01)


def test_volume_scales_the_tone():
    loud = f.tone(440, 0.5, volume=1, attack=0, release=0).samples()
    quiet = f.tone(440, 0.5, volume=0.25, attack=0, release=0).samples()
    assert max(quiet) == pytest.approx(0.25 * max(loud), rel=1e-6)


def test_default_sounds_have_headroom():
    """A9: tone, note, pluck, melody and drone peak at about 0.5 by default."""
    for snd in (f.tone(440, 1.0), f.note("A4", 1.0, "square"), f.pluck("A3", 1.0), f.drone("D3", 3),
                f.melody("C4 - E4 -")):
        peak = max(abs(v) for v in snd.samples())
        assert 0.45 <= peak <= 0.5 + 1e-6, snd
    # Legato notes overlap: a note's attack can land on the release of the note before, so a
    # melody's peak can reach about 0.8 (here 0.76). That still leaves room below 1.
    peak = max(abs(v) for v in f.melody("C4 E4 G4 C5").samples())
    assert 0.5 < peak <= 0.8


def _naive_square(hz, n):
    """The old, sharp-cornered square: every sample is +1 or -1, so its corners alias."""
    return [1.0 if (i * hz / RATE) % 1.0 < 0.5 else -1.0 for i in range(n)]


def _outside_the_harmonics(values, hz):
    """The share of the energy that is not at hz, 2 hz, 3 hz, ... below half the sample rate.
    For a band-limited wave that is about 0. Aliased harmonics fold back to other frequencies,
    so for an aliasing wave it is not. *values* must hold a whole number of periods."""
    n = len(values)
    total = sum(v * v for v in values)
    harmonic = 0.0
    k = 1
    while k * hz < RATE / 2:
        w = 2 * math.pi * k * hz / RATE
        c = sum(v * math.cos(w * i) for i, v in enumerate(values))
        s = sum(v * math.sin(w * i) for i, v in enumerate(values))
        harmonic += 2 * (c * c + s * s) / n
        k += 1
    return max(0.0, total - harmonic) / total


@pytest.mark.parametrize("wave_name", ["square", "saw", "triangle", "soft"])
def test_band_limited_waves_do_not_alias(wave_name):
    hz = 3000                                    # 4 410 samples are exactly 300 periods
    values = f.tone(hz, 0.2, wave_name, **STEADY).samples()[1000:1000 + 4410]
    assert _outside_the_harmonics(values, hz) < 1e-4
    if wave_name == "square":
        assert _outside_the_harmonics(_naive_square(hz, 4410), hz) > 0.03     # the old square: about 5 %


@pytest.mark.parametrize("wave_name", ["sine", "square", "saw", "triangle"])
@pytest.mark.parametrize("hz", [220, 440, 880])
def test_pitch_and_spectrum_match_the_frequency(clock, wave_name, hz):
    snd = f.tone(hz, 1.0, wave_name)
    assert pitch_at(snd, clock, 0.5) == pytest.approx(hz, rel=0.005)
    snd.play()
    clock.advance(0.5)
    bands = 64
    strengths = snd.spectrum(bands)
    ratio = (16000 / 40) ** (1 / bands)
    expected = int(math.log(hz / 40) / math.log(ratio))
    assert abs(strengths.index(max(strengths)) - expected) <= 1


def test_noise_has_no_pitch_and_silence_has_none(clock):
    assert pitch_at(f.tone(300, 1.0, "noise"), clock, 0.5) is None
    assert pitch_at(f.create_sound([0.0] * RATE), clock, 0.5) is None


def test_pitch_is_none_when_not_playing_or_too_quiet(clock):
    snd = f.tone(440, 1.0)
    assert snd.pitch() is None                                  # not playing
    assert pitch_at(f.tone(440, 1.0, volume=0.005), clock, 0.5) is None   # below the loudness limit
    assert pitch_at(f.tone(440, 1.0, volume=0.05), clock, 0.5) == pytest.approx(440, rel=0.005)


def test_attack_and_release_shape_the_ends():
    v = f.tone(440, 1.0, "square", volume=1, attack=0.1, release=0.2, sustain=1).samples()
    assert v[0] == 0.0 and abs(v[-1]) < 1e-3
    assert max(abs(x) for x in v[:4410]) <= 1.0
    assert max(abs(x) for x in v[2000:2400]) == pytest.approx(0.881, abs=0.02)   # half way up the attack
    assert max(abs(x) for x in v[22050:22500]) == pytest.approx(1.0, abs=0.01)   # full level in the middle


def test_envelope_attack_decay_sustain_release():
    """A9: rise to 1 over the attack, fall to the sustain level over the decay, hold it, and fall to
    0 over the release, each on an exponential curve (fast at first, then levelling off)."""
    gains = synth.envelope(44100, 4410, 4410, 0.5, 8820)
    assert gains[0] == 0.0
    assert gains[2205] == pytest.approx(0.881, abs=0.001)      # half way up: the curve rises fast
    assert gains[4410] == pytest.approx(1.0)                   # the top, at the end of the attack
    assert gains[4410 + 2205] == pytest.approx(0.5 + 0.5 * 0.119, abs=0.001)   # half way down the decay
    assert gains[8820] == pytest.approx(0.5) and gains[22050] == pytest.approx(0.5)   # the sustain
    assert gains[44100 - 8820] == pytest.approx(0.5)           # the release starts from the sustain
    assert gains[44100 - 4410] == pytest.approx(0.5 * 0.119, abs=0.001)
    assert 0 <= gains[-1] < 1e-3
    assert all(a <= b for a, b in zip(gains[:4410], gains[1:4411]))           # rising, then
    assert all(a >= b for a, b in zip(gains[4410:], gains[4411:]))            # never rising again
    # A release that starts during the decay starts from the level there
    short = synth.envelope(4410 + 2205 + 1000, 4410, 4410, 0.5, 1000)
    assert short[4410 + 2205] == pytest.approx(0.5 + 0.5 * 0.119, abs=0.001)


def test_tone_takes_decay_and_sustain():
    v = f.tone(440, 1.0, "sine", volume=1, attack=0.01, decay=0.1, sustain=0.25, release=0.1).samples()
    assert max(abs(x) for x in v[400:600]) == pytest.approx(1.0, abs=0.02)    # the top of the attack
    assert max(abs(x) for x in v[22000:23000]) == pytest.approx(0.25, abs=0.01)
    plain = f.tone(440, 1.0, "sine", volume=1, sustain=1).samples()
    assert max(abs(x) for x in plain[22000:23000]) == pytest.approx(1.0, abs=0.01)
    for bad in (dict(sustain=1.5), dict(sustain=-0.1), dict(decay=-1)):
        with pytest.raises(ValueError, match="sustain|decay"):
            f.tone(440, 1.0, **bad)


def test_fades_that_do_not_fit_are_made_shorter():
    v = f.tone(440, 0.04, "square").samples()                   # default fades add up to 0.16 s
    assert len(v) == round(0.04 * RATE)
    assert abs(v[0]) < 0.01 and abs(v[-1]) < 0.01


@pytest.mark.parametrize("kwargs, text", [
    (dict(frequency=0, seconds=1), "frequency"),
    (dict(frequency=30000, seconds=1), "frequency"),
    (dict(frequency=440, seconds=0), "length"),
    (dict(frequency=440, seconds=1, wave="blip"), "wave"),
    (dict(frequency=440, seconds=1, volume=2), "volume"),
    (dict(frequency=440, seconds=1, attack=-1), "attack"),
    (dict(frequency="A4", seconds=1), "frequency"),
])
def test_tone_errors(kwargs, text):
    with pytest.raises(ValueError, match=text):
        f.tone(**kwargs)


# ---- notes and names
def test_note_frequencies():
    assert f.note_to_frequency("A4") == pytest.approx(440.0)
    assert f.note_to_frequency("C4") == pytest.approx(261.6256, abs=1e-3)
    assert f.note_to_frequency("C#5") == f.note_to_frequency("Db5")
    assert f.note_to_frequency("Bb3") == pytest.approx(233.0819, abs=1e-3)
    assert f.note_to_frequency("A5") == pytest.approx(880.0)


def test_note_makes_the_same_tone(clock):
    a = f.note("A4", 0.5, "square", volume=0.8).samples()
    b = f.tone(440, 0.5, "square", volume=0.8).samples()
    assert a == b


@pytest.mark.parametrize("bad", ["H4", "A", "4", "a4", "C##4", "", 440])
def test_bad_note_names(bad):
    with pytest.raises(ValueError):
        f.note_to_frequency(bad)
    with pytest.raises(ValueError, match="note"):
        f.note(bad, 1)


def test_frequency_to_note():
    assert f.frequency_to_note(440) == "A4"
    assert f.frequency_to_note(261.63) == "C4"
    assert f.frequency_to_note(466.16) == "A#4"
    assert f.frequency_to_note(450) == "A4"            # the nearest semitone
    assert f.frequency_to_note(27.5) == "A0"
    assert f.frequency_to_note(29) == "A#0"
    for name in ["C2", "F#3", "A#4", "B5", "D#6"]:
        assert f.frequency_to_note(f.note_to_frequency(name)) == name
    for bad in (0, -5, "A4", True):
        with pytest.raises(ValueError):
            f.frequency_to_note(bad)


def test_sargam_names_both_ways():
    assert f.note_to_frequency("S", sa="C4") == pytest.approx(261.6256, abs=1e-3)
    assert f.note_to_frequency("P", sa="C4") == pytest.approx(261.6256 * 2 ** (7 / 12), abs=1e-3)
    assert f.note_to_frequency("S'", sa="C4") == pytest.approx(523.2511, abs=1e-3)
    assert f.note_to_frequency("N,", sa="C4") == pytest.approx(261.6256 * 2 ** (11 / 12) / 2, abs=1e-3)
    assert f.frequency_to_note(f.note_to_frequency("G", sa="D4"), sa="D4") == "G"
    assert f.frequency_to_note(f.note_to_frequency("m,", sa="C4"), sa="C4") == "m,"
    assert f.frequency_to_note(f.note_to_frequency("d'", sa="C4"), sa="C4") == "d'"
    assert f.frequency_to_note(300, sa="C4") == "R"        # 2.3 semitones above Sa
    with pytest.raises(ValueError, match="swara"):
        f.note_to_frequency("T", sa="C4")


# ---- pluck
def test_pluck_is_a_normal_sound_that_dies_away(clock):
    snd = f.pluck("A3", 2.0)
    values = snd.samples()
    assert len(values) == 2 * RATE
    assert max(abs(v) for v in values) <= 0.5 + 1e-9               # the default volume (A9)
    early = rms(values[2000:6000])
    late = rms(values[-4000:])
    assert late < 0.2 * early
    assert pitch_at(snd, clock, 0.15) == pytest.approx(220, rel=0.005)


@pytest.mark.parametrize("hz", [80, 110, 196, 330, 659, 880, 1000])
def test_pluck_pitch_across_the_range(clock, hz):
    assert pitch_at(f.pluck(hz, 1.0), clock, 0.15) == pytest.approx(hz, rel=0.005)


def _brightness(values):
    """The spectral centroid of 2 048 samples, in hertz: where the middle of the sound's energy is."""
    from funground import sound as s
    n = s.FFT_SIZE
    total = weighted = 0.0
    for start in (0, n):
        spectrum = s._fft([v * w + 0j for v, w in zip(values[start:start + n], s._HANN)])
        for k in range(1, n // 2):
            m = abs(spectrum[k])
            total += m
            weighted += m * k * RATE / n
    return weighted / total


@pytest.mark.parametrize("hz", [110, 220, 440, 880])
def test_pluck_is_warmer_than_raw_noise(hz):
    """A9: the burst that starts the string is low-pass filtered. The first 50 ms are darker than
    with the old raw burst (which had its centroid at 3.3 to 7.6 kHz across these notes)."""
    import random
    old = synth.PLUCK_SOFTNESS
    try:
        synth.PLUCK_SOFTNESS = 0                                # the old, raw burst
        raw = synth.pluck(hz, 0.1, 1.0, random.Random(5))
    finally:
        synth.PLUCK_SOFTNESS = old
    soft = synth.pluck(hz, 0.1, 1.0, random.Random(5))
    assert _brightness(soft[:2205]) < 0.75 * _brightness(raw[:2205])


def test_pluck_accepts_names_and_numbers_and_checks_them():
    assert len(f.pluck(110.0, 0.1).samples()) == round(0.1 * RATE)
    for bad in ("Z9", 5, 99999, True):
        with pytest.raises(ValueError):
            f.pluck(bad, 1)


# ---- the sketch's random generator
def test_noise_and_pluck_repeat_after_random_seed():
    f.random_seed(7)
    a = (f.tone(200, 0.2, "noise").samples(), f.pluck("E3", 0.2).samples())
    f.random_seed(7)
    b = (f.tone(200, 0.2, "noise").samples(), f.pluck("E3", 0.2).samples())
    f.random_seed(8)
    c = f.tone(200, 0.2, "noise").samples()
    assert a == b
    assert a[0] != c


# ---- melody
RELEASE = round(0.15 * RATE)                  # a melody note's release rings on after its last beat
TAIL = RELEASE                                # so a melody ending on a note is 0.15 s longer (A9)


def test_melody_length_is_beats_times_tempo():
    # A melody lasts its beats, plus the last note's release when it ends on a note.
    assert len(f.melody("C4 E4 G4:2 - C4:0.5", tempo=120).samples()) == round(5.5 * 0.5 * RATE) + TAIL
    assert len(f.melody("C4 D4 E4", tempo=60).samples()) == 3 * RATE + TAIL
    assert len(f.melody("C4:1 D4:1 E4:1", tempo=100).samples()) == round(3 * 0.6 * RATE) + TAIL
    assert len(f.melody("C4 D4 -", tempo=60).samples()) == 3 * RATE           # a final rest holds the tail
    # no drift over a long tune with beats that do not divide into whole samples
    assert len(f.melody(" ".join(["A4:0.3"] * 100), tempo=97).samples()) == round(30 * 60 / 97 * RATE) + TAIL


def test_rests_are_silent():
    v = f.melody("- A4 -", tempo=60).samples()
    assert len(v) == 3 * RATE
    assert all(x == 0.0 for x in v[:RATE])                                  # before the note
    assert all(x == 0.0 for x in v[2 * RATE + TAIL:])                       # after its release
    assert rms(v[RATE:2 * RATE]) > 0.2


def test_melody_notes_are_legato():
    """A9: no silent gap between notes. Each note's release rings on over the next note."""
    v = f.melody("C4 E4 G4 E4 C4", tempo=120).samples()
    window = round(0.005 * RATE)
    body = rms(v[round(0.2 * RATE):round(0.3 * RATE)])          # the first note, sustained
    quietest = min(rms(v[i:i + window]) for i in range(RATE // 4, 2 * RATE, window // 10))
    assert quietest > 0.6 * body                 # about 0.8 here; the old envelope dipped to 0.05
    c4 = synth.voice_samples(f.note_to_frequency("C4"), RATE // 2, RELEASE)
    assert v[RATE // 2:RATE // 2 + RELEASE] != f.melody("- E4", tempo=120).samples()[RATE // 2:RATE // 2 + RELEASE]
    assert rms(c4[RATE // 2:RATE // 2 + 1000]) > 0.5 * rms(c4[RATE // 4:RATE // 2])   # C4 still sounds after E4 starts


def test_a_note_in_a_melody_is_a_note():
    # A note of one beat (0.5 s) whose release rings on after it is a note 0.65 s long.
    v = f.melody("A4", tempo=120, wave="square").samples()
    assert v == f.note("A4", (RATE // 2 + TAIL) / RATE, "square").samples()


def test_melody_volume_and_wave():
    loud = f.melody("A4 - C5", volume=1).samples()
    quiet = f.melody("A4 - C5", volume=0.2).samples()
    assert max(quiet) == pytest.approx(0.2 * max(loud), rel=1e-6)
    assert f.melody("A4").samples() == f.melody("A4", wave="soft").samples()   # soft is the default
    with pytest.raises(ValueError, match="volume"):
        f.melody("A4", volume=2)


def test_a_chord_is_a_mix():
    chord = f.melody("[C4 E4 G4]:2", tempo=120).samples()
    expected = f.mix(*[f.melody(f"{n}:2", tempo=120) for n in ("C4", "E4", "G4")]).samples()
    assert chord == pytest.approx(expected, abs=1 / 32767)
    assert max(abs(v) for v in chord) <= 0.9


def test_sargam_equal_and_just(clock):
    sa = f.note_to_frequency("C4")
    equal = f.melody("S R G m P D N S'", tempo=120, sa="C4")
    just = f.melody("S R G m P D N S'", tempo=120, sa="C4", tuning="just")
    steps = [0, 2, 4, 5, 7, 9, 11, 12]
    ratios = [1, 9 / 8, 5 / 4, 4 / 3, 3 / 2, 5 / 3, 15 / 8, 2]
    for snd, freqs in ((equal, [sa * 2 ** (s / 12) for s in steps]), (just, [sa * r for r in ratios])):
        values = snd.samples()
        for i, hz in enumerate(freqs):
            note = f.create_sound(values[i * 22050 + 2000:(i + 1) * 22050 - 2000])
            assert pitch_at(note, clock, 0.4) == pytest.approx(hz, rel=0.003), (i, hz)


def test_sargam_komal_tivra_and_octave_marks():
    sa = f.note_to_frequency("D4")
    for token, expected in {"r": 2 ** (1 / 12), "g": 2 ** (3 / 12), "M": 2 ** (6 / 12), "d": 2 ** (8 / 12),
                            "n": 2 ** (10 / 12), "S'": 2.0, "S,": 0.5, "P'": 2 * 2 ** (7 / 12), "G,": 2 ** (4 / 12) / 2}.items():
        assert f.note_to_frequency(token, sa="D4") == pytest.approx(sa * expected)


def test_the_just_ratios():
    assert synth.JUST_RATIOS == pytest.approx([1, 16 / 15, 9 / 8, 6 / 5, 5 / 4, 4 / 3, 45 / 32, 3 / 2, 8 / 5, 5 / 3,
                                               9 / 5, 15 / 8])
    assert synth.SARGAM == list("SrRgGmMPdDnN")


@pytest.mark.parametrize("text, kwargs, token", [
    ("C4 H4 E4", {}, "H4"),
    ("C4 E4:x", {}, "E4:x"),
    ("C4:0", {}, "C4:0"),
    ("C4:-1", {}, "C4:-1"),
    ("[C4 E4", {}, "[C4"),
    ("C4 E4]", {}, "E4]"),
    ("[]", {}, "[]"),
    ("[C4 -]", {}, "[C4 -]"),
    ("[C4 Q4]:2", {}, "[C4 Q4]:2"),
    ("C4", dict(sa="C4"), "C4"),
    ("S Z", dict(sa="C4"), "Z"),
    ("S' G,,x", dict(sa="C4"), "G,,x"),
    ("S'' P,,", dict(sa="C4"), None),
    ("C11", {}, "C11"),
])
def test_melody_bad_tokens_are_named(text, kwargs, token):
    if token is None:
        f.melody(text, **kwargs)
        return
    with pytest.raises(ValueError) as info:
        f.melody(text, **kwargs)
    assert repr(token) in str(info.value)


def test_melody_other_errors():
    for kwargs in (dict(text=""), dict(text="   "), dict(text=5), dict(text="C4", tempo=0),
                   dict(text="C4", wave="x"), dict(text="C4", tuning="odd"),
                   dict(text="C4", tuning="just"), dict(text="S", sa="Q9")):
        with pytest.raises(ValueError):
            f.melody(**kwargs)


# ---- sequence and mix
def test_sequence_and_mix_lengths():
    a = f.tone(440, 1.0, attack=0, release=0)
    b = f.tone(660, 0.5, attack=0, release=0)
    seq = f.sequence(a, b)
    assert seq.duration() == pytest.approx(1.5, abs=0.001)
    assert seq.samples() == a.samples() + b.samples()
    mixed = f.mix(a, b)
    assert mixed.duration() == pytest.approx(1.0, abs=0.001)
    assert len(mixed.samples()) == RATE


def test_mix_limits_the_peak_softly():
    """A9: a quiet sum is unchanged; a loud one goes through a soft limiter that keeps it at or
    below 0.9: samples up to 0.7 pass, louder ones bend smoothly (and a sum above 1.2 is first
    scaled down to 1.2)."""
    quiet = f.create_sound([0.2, -0.2, 0.2])
    assert f.mix(quiet, quiet).samples() == pytest.approx([0.4, -0.4, 0.4])
    loud = f.create_sound([0.9, -0.9, 0.9])
    top = 0.7 + 0.2 * math.tanh(2.5)                         # 1.8 scaled to 1.2, then bent: 0.897
    assert f.mix(loud, loud).samples() == pytest.approx([top, -top, top], abs=1e-4)
    values = f.mix(f.create_sound([0.5, 0.3, -0.3]), f.create_sound([0.3, 0.3, -0.1])).samples()
    assert values[1] == pytest.approx(0.6, abs=1e-4)          # below the knee: kept
    assert values[0] == pytest.approx(0.7 + 0.2 * math.tanh(0.5), abs=1e-4)   # 0.8, bent to 0.792


def test_mix_of_five_sounds_peaks_at_most_0_9():
    parts = [f.note(n, 1.0, "saw") for n in ("C4", "E4", "G4", "B4", "D5")]
    assert sum(max(abs(v) for v in p.samples()) for p in parts) > 2.0        # the plain sum would clip
    values = f.mix(*parts).samples()
    assert 0.85 < max(abs(v) for v in values) <= 0.9


def test_combining_checks_its_arguments():
    for fn in (f.sequence, f.mix):
        with pytest.raises(ValueError):
            fn()
        with pytest.raises(ValueError, match="sound"):
            fn(f.tone(440, 0.1), "A4")


def test_combining_sounds_made_at_other_rates(clock):
    slow = f.create_sound([0.5] * 8000, rate=8000)          # one second
    fast = f.create_sound([0.25] * 44100)
    assert f.sequence(slow, fast).duration() == pytest.approx(2.0, abs=0.001)


# ---- pan
class FakeChannel:
    def __init__(self, owner):
        self.owner = owner
        self.volumes = []

    def get_sound(self):
        return self.owner

    def set_volume(self, left, right):
        self.volumes.append((left, right))

    def pause(self):
        pass

    def unpause(self):
        pass


class FakeDeviceSound:
    def __init__(self):
        self.channel = FakeChannel(self)

    def get_length(self):
        return 1.0

    def play(self, loops=0):
        return self.channel

    def stop(self):
        pass

    def set_volume(self, v):
        pass


def test_pan_sets_the_channels_left_and_right_volume(clock):
    device = FakeDeviceSound()
    snd = sound_module.Sound(device, None, silent=False)
    snd.play()
    assert device.channel.volumes == []                      # the middle: nothing to change
    snd.pan(-1)
    assert device.channel.volumes[-1] == (1.0, 0.0)          # all left, while it plays
    snd.pan(0.5)
    assert device.channel.volumes[-1] == (0.5, 1.0)
    snd.pan(1)
    assert device.channel.volumes[-1] == (0.0, 1.0)
    snd.pan(0.25)
    snd.play()                                               # playing again keeps the pan
    assert device.channel.volumes[-1] == (0.75, 1.0)


@pytest.mark.parametrize("bad", [-1.5, 2, "left", None, True])
def test_pan_range(bad):
    with pytest.raises(ValueError, match="pan"):
        f.tone(440, 0.1).pan(bad)


def test_pan_works_on_loaded_sounds_and_does_not_change_analysis(clock, tmp_path):
    path = tmp_path / "t.wav"
    f.tone(440, 1.0).save(str(path))
    loaded = f.load_sound(str(path))
    made = f.tone(440, 1.0)
    for snd in (loaded, made):
        snd.play()
        clock.advance(0.5)
        level, spectrum, hz = snd.level(), snd.spectrum(16), snd.pitch()
        snd.pan(-1)
        assert (snd.level(), snd.spectrum(16), snd.pitch()) == (level, spectrum, hz)
        snd.stop()


# ---- save
def test_save_round_trip(tmp_path):
    original = f.tone(330, 0.3, "triangle", volume=0.8)
    path = tmp_path / "out.wav"
    original.save(str(path))
    with wave.open(str(path), "rb") as w:
        assert w.getsampwidth() == 2
        assert w.getframerate() == RATE
        channels = w.getnchannels()
        frames = w.readframes(w.getnframes())
    import array
    data = array.array("h")
    data.frombytes(frames)
    left = [v / 32767 for v in data[0::channels]]
    assert len(left) == len(original.samples())
    assert left == pytest.approx(original.samples(), abs=2 / 32767)
    again = f.load_sound(str(path))
    assert again.duration() == pytest.approx(0.3, abs=0.001)


def test_save_keeps_pan(tmp_path):
    snd = f.tone(330, 0.1)
    snd.pan(1)
    snd.save(str(tmp_path / "p.wav"))
    with wave.open(str(tmp_path / "p.wav"), "rb") as w:
        if w.getnchannels() != 2:
            pytest.skip("the mixer has one channel here")
        import array
        data = array.array("h")
        data.frombytes(w.readframes(w.getnframes()))
    assert max(abs(v) for v in data[0::2]) == 0 and max(abs(v) for v in data[1::2]) > 15000     # volume 0.5


def test_save_errors(tmp_path):
    snd = f.tone(330, 0.1)
    with pytest.raises(ValueError, match="save"):
        snd.save("")
    with pytest.raises(ValueError, match="save"):
        snd.save(str(tmp_path / "no_such_folder" / "x.wav"))


# ---- reverb (A9)
def test_reverb_adds_a_tail_and_amount_0_is_dry():
    dry = f.tone(440, 1.0, "soft")
    body = rms(dry.samples()[RATE // 2:3 * RATE // 4])
    assert dry.reverb(0).samples() == dry.samples()
    after = []
    for amount, tail in ((0.3, 0.45), (1, 1.5)):
        values = dry.reverb(amount).samples()
        assert len(values) == len(dry.samples()) + round(tail * RATE)
        assert max(abs(v) for v in values) <= max(abs(v) for v in dry.samples()) + 1e-9   # no louder
        after.append(rms(values[RATE:RATE + RATE // 10]))          # the room rings on after the end:
        assert abs(values[-1]) < 1e-3                               # and fades out at last
    assert 0.1 * body < after[0] < after[1] < body                  # -13 dB at 0.3, -6 dB at 1 here
    assert len(dry.reverb().samples()) == len(dry.reverb(0.3).samples())         # 0.3 by default


def test_reverb_works_on_any_sound_and_checks_amount(tmp_path):
    path = tmp_path / "t.wav"
    f.tone(440, 0.3).save(str(path))
    wet = f.load_sound(str(path)).reverb(0.5)
    assert wet.duration() == pytest.approx(0.3 + 0.75, abs=0.002)
    for bad in (-0.1, 1.5, "big", None, True):
        with pytest.raises(ValueError, match="reverb"):
            f.tone(440, 0.1).reverb(bad)


def test_reverb_of_five_seconds_is_quick():
    import time
    snd = f.melody("C4 E4 G4 C5 " * 5, tempo=120)              # 10 beats a bar: 5 seconds
    start = time.perf_counter()
    snd.reverb(1)
    assert time.perf_counter() - start < 2.0                 # about 0.3 s here; the limit is generous


# ---- the names
def test_public_names_exist():
    for name in ("create_sound", "tone", "note", "pluck", "melody", "sequence", "mix",
                 "note_to_frequency", "frequency_to_note"):
        assert name in f.__all__ and callable(getattr(f, name))


def test_three_second_tone_is_quick():
    import time
    start = time.perf_counter()
    f.tone(440, 3.0, "sine")
    f.pluck("A3", 3.0)
    assert time.perf_counter() - start < 1.0                 # about 0.1 s here; the limit is generous
    for wave_name in ("square", "saw", "triangle", "soft"):
        start = time.perf_counter()
        f.tone(330, 3.0, wave_name)
        assert time.perf_counter() - start < 0.5             # about 0.05 s here (S-118 aims for 0.2)
