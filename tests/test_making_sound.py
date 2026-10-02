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
    assert max(values) > 0.9


# ---- wave shapes
def test_rms_of_each_wave():
    assert rms(f.tone(440, 1, "sine", attack=0, release=0).samples()) == pytest.approx(0.7071, abs=0.002)
    assert rms(f.tone(440, 1, "square", attack=0, release=0).samples()) == pytest.approx(1.0, abs=0.001)
    assert rms(f.tone(440, 1, "saw", attack=0, release=0).samples()) == pytest.approx(0.577, abs=0.01)
    assert rms(f.tone(440, 1, "triangle", attack=0, release=0).samples()) == pytest.approx(0.577, abs=0.01)
    assert rms(f.tone(440, 1, "noise", attack=0, release=0).samples()) == pytest.approx(0.577, abs=0.02)


def test_volume_scales_the_tone():
    loud = f.tone(440, 0.5, attack=0, release=0).samples()
    quiet = f.tone(440, 0.5, volume=0.25, attack=0, release=0).samples()
    assert max(quiet) == pytest.approx(0.25 * max(loud), rel=1e-6)


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
    v = f.tone(440, 1.0, "square", attack=0.1, release=0.2).samples()
    assert v[0] == 0.0 and abs(v[-1]) < 1e-3
    assert abs(v[2205]) == pytest.approx(0.5, abs=0.01)        # half way up the 0.1 s attack
    assert abs(v[len(v) - 1 - 4410]) == pytest.approx(0.5, abs=0.01)   # half way down the release
    assert abs(v[22050]) == 1.0                                 # full level in the middle


def test_fades_that_do_not_fit_are_made_shorter():
    v = f.tone(440, 0.04, "square").samples()                   # default fades add up to 0.06 s
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
    assert max(abs(v) for v in values) <= 1.0
    early = rms(values[2000:6000])
    late = rms(values[-4000:])
    assert late < 0.2 * early
    assert pitch_at(snd, clock, 0.15) == pytest.approx(220, rel=0.005)


@pytest.mark.parametrize("hz", [80, 110, 196, 330, 659, 880, 1000])
def test_pluck_pitch_across_the_range(clock, hz):
    assert pitch_at(f.pluck(hz, 1.0), clock, 0.15) == pytest.approx(hz, rel=0.005)


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
def test_melody_length_is_beats_times_tempo():
    assert f.melody("C4 E4 G4:2 - C4:0.5", tempo=120).duration() == pytest.approx(5.5 * 0.5, abs=0.001)
    assert f.melody("C4 D4 E4", tempo=60).duration() == pytest.approx(3.0, abs=0.001)
    assert len(f.melody("C4:1 D4:1 E4:1", tempo=100).samples()) == round(3 * 0.6 * RATE)
    # no drift over a long tune with beats that do not divide into whole samples
    assert len(f.melody(" ".join(["A4:0.3"] * 100), tempo=97).samples()) == round(30 * 60 / 97 * RATE)


def test_rests_are_silent():
    v = f.melody("- A4 -", tempo=60).samples()
    third = len(v) // 3
    assert all(x == 0.0 for x in v[:third]) and all(x == 0.0 for x in v[2 * third + 1:])
    assert rms(v[third:2 * third]) > 0.5


def test_a_note_in_a_melody_is_a_note():
    v = f.melody("A4", tempo=120, wave="square").samples()
    assert v == f.note("A4", 0.5, "square").samples()


def test_a_chord_is_a_mix():
    chord = f.melody("[C4 E4 G4]:2", tempo=120).samples()
    notes = [f.note(n, 1.0).samples() for n in ("C4", "E4", "G4")]
    expected = f.mix(*[f.create_sound(n) for n in notes]).samples()
    assert chord == pytest.approx(expected, abs=1 / 32767)
    assert max(abs(v) for v in chord) <= 1.0


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


def test_mix_scales_down_only_when_it_would_clip():
    quiet = f.create_sound([0.2, -0.2, 0.2])
    assert f.mix(quiet, quiet).samples() == pytest.approx([0.4, -0.4, 0.4])
    loud = f.create_sound([0.9, -0.9, 0.9])
    values = f.mix(loud, loud).samples()
    assert max(abs(v) for v in values) == pytest.approx(1.0)
    assert values == pytest.approx([1.0, -1.0, 1.0])
    values = f.mix(loud, f.create_sound([0.3, 0.0, -0.3])).samples()
    assert max(abs(v) for v in values) == pytest.approx(1.0)
    assert values[0] == pytest.approx(1.0) and values[2] == pytest.approx(0.6 / 1.2)


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
    assert max(abs(v) for v in data[0::2]) == 0 and max(abs(v) for v in data[1::2]) > 20000


def test_save_errors(tmp_path):
    snd = f.tone(330, 0.1)
    with pytest.raises(ValueError, match="save"):
        snd.save("")
    with pytest.raises(ValueError, match="save"):
        snd.save(str(tmp_path / "no_such_folder" / "x.wav"))


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
