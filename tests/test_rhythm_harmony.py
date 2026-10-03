"""Rhythm and harmony (S-112, S-113; contract A5, A6; D-061).

Every sound here is made from `tone`, `note`, `pluck`, `melody` and `mix`, so the right answers are
known. Time is driven by replacing `funground.sound.clock`, so nothing sleeps. The microphone is
never opened: it is silent (FUNGROUND_HEADLESS=1) and is played a known sound with `mic._feed(...)`.
"""
from __future__ import annotations

import math
import random
import time

import pytest

import funground as f
from funground import analysis, sound as sound_module

RATE = 44100
CHORDS = {
    "C": ["C4", "E4", "G4"],
    "Am": ["A3", "C4", "E4"],
    "G7": ["G3", "B3", "D4", "F4"],
    "Fmaj7": ["F3", "A3", "C4", "E4"],
    "Bdim": ["B3", "D4", "F4"],
    "Dm7": ["D3", "F3", "A3", "C4"],
    "Caug": ["C4", "E4", "G#4"],
    "F#": ["F#3", "A#3", "C#4"],
}


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


def chord_sound(notes, wave="sine"):
    return f.mix(*[f.note(n, 1.0, wave) for n in notes])


def pulse_track(kind: str, bpm: int, count: int = 16):
    """A sound with one hit on each of *count* beats."""
    beat = 60.0 / bpm
    if kind == "click":                      # a short blip, then silence
        return f.melody(" ".join("C6:0.25 -:0.75" for _ in range(count)), tempo=bpm)
    if kind == "notes":                      # notes that change, each one a beat long
        return f.melody(" ".join(["C4", "E4", "G4", "C5"][i % 4] for i in range(count)), tempo=bpm)
    parts = [f.pluck(["A3", "E4", "C#4"][i % 3], beat, 0.8, ) for i in range(count)]
    return f.sequence(*parts)


# ---- onsets, tempo and beats on whole sounds
@pytest.mark.parametrize("kind", ["click", "notes", "pluck"])
@pytest.mark.parametrize("bpm", [80, 100, 120, 150])
def test_tempo_onsets_and_beats(kind, bpm):
    snd = pulse_track(kind, bpm)
    beat = 60.0 / bpm
    truth = [i * beat for i in range(16)]
    assert snd.tempo() == pytest.approx(bpm, abs=2)
    onsets = snd.onsets()
    assert len(onsets) in (16, 17)                       # one a beat (a plucked string may add its ending)
    for t in truth:
        assert min(abs(o - t) for o in onsets) < 0.025
    beats = snd.beats()
    assert beats == sorted(beats)
    for t in truth:
        assert min(abs(b - t) for b in beats) < 0.025
    assert all(0 <= b <= snd.duration() for b in beats)


def test_results_are_remembered_and_are_copies():
    snd = pulse_track("click", 120, 8)
    first = snd.onsets()
    first.append(99.0)
    assert 99.0 not in snd.onsets()
    assert snd._rhythm() is snd._rhythm()


def test_silence_has_no_onsets_no_tempo_no_beats_no_key():
    snd = f.create_sound([0.0] * RATE * 3)
    assert snd.onsets() == []
    assert snd.tempo() is None
    assert snd.beats() == []
    assert snd.key() is None


def test_a_steady_tone_has_no_pulse():
    snd = f.tone(440, 4.0)
    assert snd.tempo() is None
    assert snd.beats() == []
    assert len(snd.onsets()) <= 1                        # only its own start


def test_hiss_has_no_pulse():
    rng = random.Random(5)
    snd = f.create_sound([rng.uniform(-0.3, 0.3) for _ in range(RATE * 4)])
    assert snd.tempo() is None


def test_a_quiet_click_track_still_works():
    loud = pulse_track("click", 120, 12)
    quiet = f.create_sound([v * 0.1 for v in loud.samples()])
    assert quiet.tempo() == pytest.approx(120, abs=2)
    assert len(quiet.onsets()) == 12


def test_a_three_minute_song_is_quick_enough():
    bar = [0.0] * (RATE * 2)                              # two seconds, four noisy hits
    rng = random.Random(1)
    for k in range(4):
        start = int(k * RATE * 0.5)
        for i in range(3000):
            bar[start + i] = (rng.random() * 2 - 1) * 0.9 * (1 - i / 3000)
    snd = f.create_sound(bar * 90)
    assert snd.duration() == pytest.approx(180, abs=0.1)
    started = time.perf_counter()
    tempo = snd.tempo()
    seconds = time.perf_counter() - started
    print(f"three-minute song: rhythm took {seconds:.1f} s")
    assert tempo == pytest.approx(120, abs=2)
    assert len(snd.onsets()) == pytest.approx(360, abs=4)
    assert seconds < 30                                   # a few seconds on a normal computer


# ---- the live is_onset()
def test_is_onset_flashes_once_for_each_note(clock):
    snd = f.melody("C4 E4 G4 E4 C4 E4 G4 E4", tempo=120)   # a note every half second
    assert snd.is_onset() is False                         # not playing yet
    snd.play()
    start = clock.now
    hits = []
    while clock.now - start < 3.9:
        clock.advance(1 / 60)
        if snd.is_onset():
            hits.append(clock.now - start)
    assert len(hits) == 8
    for k, t in enumerate(hits):
        assert 0.0 <= t - k * 0.5 < 0.08                   # no earlier than the note, and not much later


def test_is_onset_is_false_for_silence_and_steady_sound(clock):
    quiet = f.create_sound([0.0] * RATE * 2)
    quiet.play()
    flags = []
    for _ in range(60):
        clock.advance(1 / 60)
        flags.append(quiet.is_onset())
    assert not any(flags)
    steady = f.tone(440, 3.0)
    steady.play()
    clock.advance(0.5)                                     # let its own start go by
    flags = []
    for _ in range(90):
        clock.advance(1 / 60)
        flags.append(steady.is_onset())
    assert not any(flags)


def test_is_onset_starts_again_when_the_sound_does(clock):
    snd = f.melody("C4 E4", tempo=120)
    for _ in range(2):
        snd.play()
        start = clock.now
        hits = 0
        while clock.now - start < 0.95:
            clock.advance(1 / 60)
            hits += snd.is_onset()
        assert hits == 2
        snd.stop()


# ---- chroma and chords
@pytest.mark.parametrize("wave", ["sine", "triangle", "saw"])
@pytest.mark.parametrize("name", list(CHORDS))
def test_chord_names(name, wave, clock):
    snd = chord_sound(CHORDS[name], wave)
    snd.play()
    clock.advance(0.5)
    assert snd.chord() == name


def test_chroma_peaks_are_on_the_right_pitch_classes(clock):
    snd = chord_sound(["C4", "E4", "G4"])
    snd.play()
    clock.advance(0.5)
    chroma = snd.chroma()
    assert len(chroma) == 12
    assert max(chroma) == 1.0
    assert all(0.0 <= v <= 1.0 for v in chroma)
    strong = {i for i, v in enumerate(chroma) if v > 0.5}
    assert strong == {0, 4, 7}                             # C, E, G
    assert sum(v for i, v in enumerate(chroma) if i not in strong) < 0.1


def test_chroma_ignores_the_octave(clock):
    snd = f.mix(f.note("A2", 1.0), f.note("A5", 1.0))
    snd.play()
    clock.advance(0.5)
    chroma = snd.chroma()
    assert chroma.index(max(chroma)) == 9                  # A
    assert sorted(chroma)[-2] < 0.1


@pytest.mark.parametrize("notes", [["A4"], ["C3", "C4"], ["C4", "G4"]])
def test_one_voice_or_two_notes_is_not_a_chord(notes, clock):
    snd = f.mix(*[f.note(n, 1.0) for n in notes])
    snd.play()
    clock.advance(0.5)
    assert snd.chord() is None


def test_noise_is_not_a_chord(clock):
    rng = random.Random(2)
    snd = f.create_sound([rng.uniform(-0.3, 0.3) for _ in range(RATE)])
    snd.play()
    clock.advance(0.5)
    assert snd.chord() is None


def test_nothing_playing_gives_zeros_and_none(clock):
    snd = chord_sound(CHORDS["C"])
    assert snd.chroma() == [0.0] * 12
    assert snd.chord() is None
    snd.play()
    clock.advance(0.5)
    assert snd.chord() == "C"
    snd.stop()
    assert snd.chord() is None


def test_the_chord_follows_the_sound_as_it_plays(clock):
    snd = f.sequence(chord_sound(CHORDS["C"]), chord_sound(CHORDS["G7"]), chord_sound(CHORDS["Am"]))
    snd.play()
    seen = []
    for second in (0.6, 1.0, 1.0):
        clock.advance(second)
        seen.append(snd.chord())
    assert seen == ["C", "G7", "Am"]


# ---- key
@pytest.mark.parametrize("wave", ["sine", "triangle"])
def test_key_of_a_melody_in_g_major(wave):
    snd = f.melody("G4 B4 D5 G5:2 F#5 E5 D5 B4 C5 A4 G4:2 D5 C5 B4 A4 G4:3", tempo=140, wave=wave)
    assert snd.key() == "G major"


@pytest.mark.parametrize("wave", ["sine", "triangle"])
def test_key_of_a_melody_in_e_minor(wave):
    snd = f.melody("E4 G4 B4 E5:2 D5 B4 G4 F#4 E4 B3:2 C4 D4 E4 G4 F#4 E4:3", tempo=140, wave=wave)
    assert snd.key() == "E minor"


def test_key_is_remembered_and_none_for_one_voice_noise():
    snd = f.melody("C4 E4 G4 C5:2 B4 G4 E4 D4 C4:3", tempo=140)
    assert snd.key() == "C major"
    assert snd.key() == "C major"
    rng = random.Random(4)
    assert f.create_sound([rng.uniform(-0.3, 0.3) for _ in range(RATE * 2)]).key() is None


def test_key_profiles_are_the_published_ones():
    assert len(analysis.KEY_MAJOR) == len(analysis.KEY_MINOR) == 12
    assert analysis.KEY_MAJOR[0] == 6.35 and analysis.KEY_MINOR[0] == 6.33
    assert analysis.best_key(list(analysis.KEY_MAJOR)) == "C major"
    assert analysis.best_key(analysis.KEY_MINOR[3:] + analysis.KEY_MINOR[:3]) == "A minor"


# ---- chord_notes
def test_chord_notes_examples():
    assert f.chord_notes("C") == ["C", "E", "G"]
    assert f.chord_notes("Am") == ["A", "C", "E"]
    assert f.chord_notes("G7") == ["G", "B", "D", "F"]
    assert f.chord_notes("Fmaj7") == ["F", "A", "C", "E"]
    assert f.chord_notes("Bdim") == ["B", "D", "F"]
    assert f.chord_notes("C#m") == ["C#", "E", "G#"]
    assert f.chord_notes("Bb") == ["A#", "D", "F"]


@pytest.mark.parametrize("suffix", list(analysis.CHORD_QUALITIES))
@pytest.mark.parametrize("root", analysis.NOTE_NAMES)
def test_chord_notes_round_trip(root, suffix):
    notes = f.chord_notes(root + suffix)
    assert notes[0] == root
    # The notes, put on the chroma, are named by the chord finder (augmented chords share notes).
    chroma = [0.0] * 12
    for n in notes:
        chroma[analysis.NOTE_NAMES.index(n)] = 1.0
    name = analysis.chord_of(chroma)
    assert name is not None
    assert sorted(f.chord_notes(name)) == sorted(notes)


@pytest.mark.parametrize("bad", ["", "H", "Cx", "C#sus", 5, None])
def test_chord_notes_explains_a_bad_name(bad):
    with pytest.raises(ValueError, match="f.chord_notes"):
        f.chord_notes(bad)


# ---- the microphone
@pytest.fixture
def mic(monkeypatch):
    monkeypatch.setenv("FUNGROUND_HEADLESS", "1")
    microphone = f.microphone()
    microphone.start()
    return microphone


def chord_samples(notes, seconds=0.6):
    return chord_sound(notes).samples()[: int(seconds * RATE)]


def test_microphone_chroma_and_chord(mic):
    assert mic.chord() is None
    mic._feed(chord_samples(CHORDS["Am"]))
    chroma = mic.chroma()
    assert {i for i, v in enumerate(chroma) if v > 0.5} == {9, 0, 4}
    assert mic.chord() == "Am"


def test_microphone_not_listening_gives_nothing(mic):
    mic._feed(chord_samples(CHORDS["C"]))
    mic.stop()
    assert mic.chroma() == [0.0] * 12
    assert mic.chord() is None
    assert mic.is_onset() is False


def test_microphone_single_note_is_not_a_chord(mic):
    mic._feed(f.note("A4", 1.0).samples())
    assert mic.chord() is None


def test_microphone_is_onset(mic):
    mic._feed([0.0] * int(0.5 * RATE))
    assert mic.is_onset() is False
    hit = f.note("C5", 0.2).samples()
    mic._feed(hit[: int(0.03 * RATE)])
    assert mic.is_onset() is True
    mic._feed(hit[int(0.03 * RATE):])                      # the same note carrying on is not a new onset
    assert mic.is_onset() is False
    mic._feed([0.0] * int(0.3 * RATE))
    assert mic.is_onset() is False
    mic._feed(hit[: int(0.03 * RATE)])
    assert mic.is_onset() is True                          # a second note is


def test_microphone_points_to_capture_for_whole_sound_methods(mic):
    for name in ("onsets", "tempo", "beats", "key"):
        with pytest.raises(ValueError, match=f"capture.*{name}"):
            getattr(mic, name)()
    mic._feed(f.melody("C4 E4 G4 C5:2 B4 G4 E4 D4 C4:3", tempo=140).samples())
    assert mic.capture(5).key() == "C major"
