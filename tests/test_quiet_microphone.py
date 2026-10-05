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


def press(key):
    """An action for _run(): the learner presses *key* (the game's key_pressed() hears it)."""
    def action(ns):
        api.active_sketch().key = key
        ns["key_pressed"]()
    return action


def _run(path, frames, at=None):
    """Run an example for *frames* frames and give back its globals.

    *at* maps a frame number to an action, a function of the globals, run just before that frame is drawn."""
    namespace: dict[str, object] = {"__name__": "__sketch__", "__file__": str(path)}

    def harness_run(*, fps=1000, max_frames=frames):
        caller = inspect.currentframe().f_back
        if at:
            real_draw = caller.f_globals["draw"]

            def draw():
                if api.active_sketch().frame_count in at:
                    at[api.active_sketch().frame_count](caller.f_globals)
                real_draw()
            caller.f_globals["draw"] = draw
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


# Sensitivity after the maintainer found 8/25 dB too sensitive (5 Oct 2026): QUIET_DB = 15, RANGE_DB = 30.
# A whisper (0.003) shows on the mic bar but barely lifts the bird; speech lifts it; a clear "aaah" tops it.
@pytest.mark.parametrize("speech, low, high", [(0.003, 0.0, 0.15), (0.01, 0.25, 0.55), (0.05, 0.7, 1.0), (0.3, 0.95, 1.0)])
def test_the_game_hears_quiet_speech(monkeypatch, speech, low, high):
    _play(monkeypatch, speech, speech_from=60)
    ns = _run(GALLERY / "projects" / "04_voice_game.py", 120, at={30: press("enter")})     # past the setup screen
    assert ns["above"] > 10                                  # the mic bar shows the voice, even a whisper
    assert low <= ns["voice"] <= high
    if speech >= 0.01:
        assert ns["state"] == "play"                         # and speech makes the bird take off


def test_the_game_works_with_a_loud_room_and_a_louder_voice(monkeypatch):
    quiet = _room(0.005)
    loud = [a + b for a, b in zip(_voice(0.5), quiet)]
    monkeypatch.setattr(mi.Microphone, "_latest",
                        lambda self, n: ((loud if api.active_sketch().frame_count >= 60 else quiet) * 20)[:n])
    monkeypatch.setenv("FUNGROUND_HEADLESS", "1")
    ns = _run(GALLERY / "projects" / "04_voice_game.py", 120, at={30: press("enter")})
    assert ns["voice"] > 0.75                                # 40 dB above a loud room: near the top


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


# ---- the "set up your voice" screen

GAME = GALLERY / "projects" / "04_voice_game.py"


def test_the_game_opens_on_the_setup_screen_and_measures_the_room(monkeypatch):
    _play(monkeypatch, SPEECH_RMS, speech_from=10_000)
    ns = _run(GAME, 30)
    assert ns["state"] == "setup" and ns["calibrating"]()    # mid-way through the room check
    ns = _run(GAME, 90)
    assert ns["state"] == "setup" and not ns["calibrating"]()
    assert -70 < ns["floor"] < -55
    assert ns["settings"]() == (15, 45)                       # the defaults: QUIET_DB, QUIET_DB + RANGE_DB


def test_speech_does_not_start_the_game_from_the_setup_screen(monkeypatch):
    _play(monkeypatch, 0.3, speech_from=60)
    ns = _run(GAME, 120)
    assert ns["state"] == "setup" and ns["voice"] > 0.9


def test_the_marks_move_with_the_sliders_and_the_keys(monkeypatch):
    _play(monkeypatch, SPEECH_RMS, speech_from=10_000)
    ns = _run(GAME, 70, at={
        65: lambda ns: (ns["start_at"].value(20), ns["full_at"].value(50)),
    })
    assert ns["settings"]() == (20, 50)
    keys = {64: press("up"), 65: press("up"), 66: press("down"), 67: press("right"), 68: press("left"), 69: press("left")}
    ns = _run(GAME, 70, at=keys)
    assert ns["settings"]() == (16, 44)                       # up, up, down = +1; right, left, left = -1
    ns = _run(GAME, 70, at={65: lambda ns: ns["start_at"].value(39), 66: lambda ns: ns["full_at"].value(10)})
    assert ns["settings"]() == (39, 44)                       # full height stays a little above the start


def test_r_measures_the_room_again(monkeypatch):
    _play(monkeypatch, SPEECH_RMS, speech_from=10_000)
    ns = _run(GAME, 100, at={80: press("r")})
    assert ns["state"] == "setup" and ns["calibrating"]() and ns["calibrate_from"] == 80


def test_the_practice_bird_rises_with_speech(monkeypatch):
    _play(monkeypatch, 0.05, speech_from=10_000)
    quiet = _run(GAME, 120)["practice_y"]
    _play(monkeypatch, 0.05, speech_from=60)
    ns = _run(GAME, 120)
    assert quiet > ns["HIGH"] - 3                             # a quiet room leaves it on the floor
    assert ns["practice_y"] < ns["HIGH"] - 60                 # speech lifts it
    assert ns["state"] == "setup"


def test_the_practice_bird_follows_the_settings(monkeypatch):
    _play(monkeypatch, SPEECH_RMS, speech_from=60)
    gentle = _run(GAME, 120)["practice_y"]
    ns = _run(GAME, 120, at={5: lambda ns: (ns["start_at"].value(5), ns["full_at"].value(25))})
    assert ns["practice_y"] < gentle - 40                     # lower marks: the same voice goes higher


def test_starting_the_game_uses_the_chosen_settings(monkeypatch):
    _play(monkeypatch, SPEECH_RMS, speech_from=60)             # speech is about 28 dB above the room
    sensitive = _run(GAME, 130, at={5: lambda ns: (ns["start_at"].value(5), ns["full_at"].value(25)), 65: press("enter")})
    assert sensitive["voice"] > 0.95 and sensitive["state"] == "play"
    deaf = _run(GAME, 130, at={5: lambda ns: (ns["start_at"].value(35), ns["full_at"].value(60)), 65: press("enter")})
    assert deaf["voice"] == 0.0 and deaf["state"] == "ready"   # the settings stay: speech is under "starts at"


def test_s_returns_to_the_setup_screen_and_keeps_the_settings(monkeypatch):
    _play(monkeypatch, SPEECH_RMS, speech_from=10_000)
    ns = _run(GAME, 90, at={5: lambda ns: ns["start_at"].value(22), 70: press("enter"), 80: press("s")})
    assert ns["state"] == "setup" and ns["settings"]()[0] == 22


def test_without_a_microphone_space_starts_the_game(monkeypatch):
    monkeypatch.setenv("FUNGROUND_HEADLESS", "1")

    def no_mic(name=None, frame_source=None):
        raise RuntimeError("none")
    monkeypatch.setattr(funground, "microphone", no_mic)
    ns = _run(GAME, 20)
    assert ns["state"] == "setup"
    ns = _run(GAME, 20, at={10: press(" ")})
    assert ns["state"] == "play"
