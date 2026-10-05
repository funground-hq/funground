"""Quiet microphones: the microphone examples must hear a laptop microphone.

A laptop microphone can be very quiet: room noise near RMS 0.0005 and speech near RMS 0.01. These tests
play a silent (headless) microphone that kind of sound, frame by frame, and run the examples on it.
"""
from __future__ import annotations

import inspect
import math
import random
from pathlib import Path

import pytest

import funground
from funground import api, microphone_input as mi

from conftest import ROOT

RATE = 44100
GALLERY = ROOT / "examples" / "gallery"
ROOM_RMS = 0.0005
SPEECH_RMS = 0.01


def _scaled(values, rms):
    now = math.sqrt(sum(v * v for v in values) / len(values))
    return [v * rms / now for v in values]


def _voice(rms, hz=200.0, seconds=0.2):
    """A voice-like tone: 200 Hz and its harmonics, falling off."""
    n = int(seconds * RATE)
    return _scaled([sum(math.sin(2 * math.pi * hz * k * i / RATE) / k for k in range(1, 9)) for i in range(n)], rms)


def _room(rms, seconds=0.2):
    rng = random.Random(3)
    return _scaled([rng.gauss(0, 1) for _ in range(int(seconds * RATE))], rms)


def _play(monkeypatch, speech_rms, speech_from):
    """The microphone hears the room, and from frame *speech_from* a voice (over the room)."""
    quiet_room = _room(ROOM_RMS)
    speech = [a + b for a, b in zip(_voice(speech_rms), quiet_room)]

    def latest(self, count):
        signal = speech if api.active_sketch().frame_count >= speech_from else quiet_room
        return (signal * (count // len(signal) + 1))[:count]

    monkeypatch.setattr(mi.Microphone, "_latest", latest)
    monkeypatch.setenv("FUNGROUND_HEADLESS", "1")


def _run(path, frames):
    """Run an example for *frames* frames and give back its globals."""
    namespace: dict[str, object] = {"__name__": "__sketch__", "__file__": str(path)}

    def harness_run(*, fps=1000, max_frames=frames):
        caller = inspect.currentframe().f_back
        api.active_sketch().run_namespace(caller.f_globals, fps=fps, max_frames=frames)

    original = funground.run
    funground.run = harness_run
    try:
        exec(compile(path.read_text(encoding="utf-8"), str(path), "exec"), namespace)
    finally:
        funground.run = original
    return namespace


@pytest.fixture(autouse=True)
def _cwd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)


def test_the_game_stays_still_in_a_quiet_room(monkeypatch):
    _play(monkeypatch, SPEECH_RMS, speech_from=10_000)
    ns = _run(GALLERY / "projects" / "04_voice_game.py", 90)
    assert ns["voice"] == 0.0 and ns["above"] < 3          # the room is the floor
    assert -70 < ns["floor"] < -55                          # about 0.0005 in decibels


@pytest.mark.parametrize("speech", [0.003, 0.01, 0.05, 0.3])
def test_the_game_hears_quiet_speech(monkeypatch, speech):
    _play(monkeypatch, speech, speech_from=60)
    ns = _run(GALLERY / "projects" / "04_voice_game.py", 120)
    assert ns["above"] > 10                                  # the mic bar shows the voice
    assert ns["voice"] > 0.1                                 # clearly above 0
    if speech >= 0.01:
        assert ns["voice"] > 0.5
    assert ns["state"] == "play"                             # and the bird takes off


def test_the_game_works_with_a_loud_room_and_a_louder_voice(monkeypatch):
    quiet = _room(0.005)
    loud = [a + b for a, b in zip(_voice(0.5), quiet)]
    monkeypatch.setattr(mi.Microphone, "_latest",
                        lambda self, n: ((loud if api.active_sketch().frame_count >= 60 else quiet) * 20)[:n])
    monkeypatch.setenv("FUNGROUND_HEADLESS", "1")
    ns = _run(GALLERY / "projects" / "04_voice_game.py", 120)
    assert ns["voice"] > 0.9                                 # 40 dB above the room: the top


def test_the_game_without_a_microphone_still_says_so(monkeypatch):
    monkeypatch.setenv("FUNGROUND_HEADLESS", "1")
    def no_mic(name=None, frame_source=None):
        raise RuntimeError("none")
    monkeypatch.setattr(funground, "microphone", no_mic)
    ns = _run(GALLERY / "projects" / "04_voice_game.py", 5)
    assert ns["mic"] is None and ns["voice"] == 0.0


def test_the_tuner_names_a_quiet_voice(monkeypatch):
    _play(monkeypatch, SPEECH_RMS, speech_from=0)
    ns = _run(GALLERY / "sound" / "04_tuner.py", 40)
    assert ns["name"] == "G3"                                # 200 Hz is a little sharp of G3 (196 Hz)
    assert 20 < ns["needle"] <= 50
