"""Tests of ``ml.words()`` that run the real Whisper model files on ``data/tts.wav`` (a computer voice, 7.2 s; SOURCES.md).

The files are kept in ml/tests/.models/ (FUNGROUND_ML_MODELS); the first run downloads them, and a run with no connection skips
these tests with a reason. The expected sentence is the one the S-231 spike's own script gave for the same sound.
"""
from __future__ import annotations

import time
import wave
from array import array

import numpy as np
import pytest

import funground_ml
from funground import sound
from funground_ml import _tasks, _whisper

from conftest import SPEECH, SPEECH_TEXT

pytestmark = [pytest.mark.model, pytest.mark.usefixtures("words_models")]


def recording():
    """The recording's samples (floats, -1 to 1) and its rate."""
    with wave.open(str(SPEECH)) as wav:
        assert wav.getnchannels() == 1 and wav.getsampwidth() == 2
        raw = wav.readframes(wav.getnframes())
        return np.frombuffer(raw, "<i2").astype(np.float32) / 32768.0, wav.getframerate()


@pytest.fixture
def frames(monkeypatch):
    state = {"n": 1}
    monkeypatch.setattr(_tasks, "_frame", lambda: state["n"])
    return lambda: state.update(n=state["n"] + 1)


def test_a_sound_of_the_recording_gives_the_sentence_that_was_said():
    heard = funground_ml.words(sound.load(str(SPEECH)))
    assert heard.text == SPEECH_TEXT
    assert heard.score > 0.9 and heard.is_new
    assert str(heard) == SPEECH_TEXT


def test_the_samples_at_16k_give_the_same_sentence_and_a_score():
    from funground_ml import _fetch

    audio, rate = recording()
    assert rate == 16000

    text, score = _whisper.load(_fetch.ensure("words", None, "the tests")).transcribe(audio, rate)
    assert text == SPEECH_TEXT and 0.9 < score <= 1.0


def test_a_microphone_that_hears_the_recording_gives_the_same_words_beside_the_sketch(frames):
    audio, rate = recording()
    mic = sound.microphone()
    mic.start()
    assert funground_ml.words(mic) is None                                  # the first call also makes sure the model files are there
    positions = np.arange(int(len(audio) * mic._rate / rate)) * rate / mic._rate         # up to the microphone's rate
    heard_by_mic = np.interp(positions, np.arange(len(audio)), audio).astype(np.float32)
    mic._feed(array("f", heard_by_mic.tolist()))
    mic._feed(array("f", bytes(4 * mic._rate)))                              # one second of quiet ends the phrase
    started, found = time.monotonic(), None
    while found is None and time.monotonic() - started < 60:
        frames()
        found = funground_ml.words(mic)
        time.sleep(0.02)
    assert found is not None, "the thread gave no answer in 60 s"
    assert found.text == SPEECH_TEXT and found.is_new and found.score > 0.9
