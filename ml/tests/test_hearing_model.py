"""Tests of ``ml.sound()`` that run the real YAMNet file on the recordings in ``data/`` (SOURCES.md): a computer voice, a whistle and
clapping. The file is kept in ml/tests/.models/ (FUNGROUND_ML_MODELS); the first run downloads it, and a run with no connection
skips these tests with a reason. The expected names are what the model gave when this test was written."""
from __future__ import annotations

import time
import wave
from array import array

import numpy as np
import pytest

import funground_ml
from funground import sound
from funground_ml import _fetch, _sound, _tasks, _yamnet

from conftest import CLAPPING, SPEECH, WHISTLE

pytestmark = [pytest.mark.model, pytest.mark.usefixtures("sound_models")]


def recording(path):
    """The recording's samples (floats, -1 to 1) and its rate."""
    with wave.open(str(path)) as wav:
        assert wav.getnchannels() == 1 and wav.getsampwidth() == 2
        raw = wav.readframes(wav.getnframes())
        return np.frombuffer(raw, "<i2").astype(np.float32) / 32768.0, wav.getframerate()


@pytest.fixture
def frames(monkeypatch):
    state = {"n": 1}
    monkeypatch.setattr(_tasks, "_frame", lambda: state["n"])
    return lambda: state.update(n=state["n"] + 1)


def test_speech_is_named_speech():
    heard = funground_ml.sound(sound.load(str(SPEECH)))
    assert heard.name == "Speech" and heard.score > 0.5 and heard.is_new and str(heard) == "Speech"
    assert len(heard.next) == 4 and all(g.next == () and not g.is_new for g in heard.next)
    assert [g.score for g in heard.next] == sorted((g.score for g in heard.next), reverse=True)
    assert heard.next[0].score <= heard.score


def test_a_whistle_is_named_whistling():
    heard = funground_ml.sound(sound.load(str(WHISTLE)))
    assert heard.name == "Whistling" and heard.score > 0.2
    assert "Whistle" in [g.name for g in heard.next]


def test_clapping_is_named_hands_with_a_low_score_and_broad_guesses():
    heard = funground_ml.sound(sound.load(str(CLAPPING)))
    assert heard.name == "Hands" and 0.1 <= heard.score < 0.5


def test_the_scores_are_521_numbers_from_0_to_1_and_the_mean_of_the_windows():
    audio, rate = recording(WHISTLE)
    model = _yamnet.load(_fetch.ensure("sound", None, "the tests"))
    scores = model.scores(audio, rate)
    assert len(scores) == 521 and all(0.0 <= v <= 1.0 for v in scores)
    rows = model._session.run(None, {"waveform": audio})[0]
    assert rows.shape[0] > 1
    assert np.allclose(scores, rows.mean(axis=0), atol=1e-6)
    assert _sound.choose(scores)[0][0] == "Whistling"


def test_a_microphone_that_hears_the_whistle_names_it_beside_the_sketch(frames):
    audio, rate = recording(WHISTLE)
    mic = sound.microphone()
    mic.start()
    assert funground_ml.sound(mic) is None                                  # the first call also makes sure the model file is there
    size = int(1.5 * rate)                                                  # the loudest 1.5 s: the whistle starts softly
    power = np.convolve(audio.astype(np.float64) ** 2, np.ones(size), "valid")
    start = int(power.argmax())
    audio = audio[start:start + size]
    positions = np.arange(int(len(audio) * mic._rate / rate)) * rate / mic._rate         # up to the microphone's rate
    heard_by_mic = np.interp(positions, np.arange(len(audio)), audio).astype(np.float32)
    mic._feed(array("f", heard_by_mic.tolist()))
    started, found = time.monotonic(), None
    while found is None and time.monotonic() - started < 60:
        frames()
        found = funground_ml.sound(mic)
        time.sleep(0.02)
    assert found is not None, "the thread gave no answer in 60 s"
    assert found.name in ("Whistling", "Whistle") and found.is_new and found.score > 0.1
    mic._feed(array("f", bytes(4 * 2 * mic._rate)))                          # two seconds of quiet: nothing to name
    started = time.monotonic()
    while found is not None and time.monotonic() - started < 30:
        frames()
        found = funground_ml.sound(mic)
        time.sleep(0.02)
    assert found is None
