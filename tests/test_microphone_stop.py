"""A microphone stops without freezing, and lets go of the device when the sketch ends (spike 19).

SDL calls the device's callback holding the device's lock; the callback needs the GIL; pygame's pause() and close() hold
the GIL and wait for the device. The tests with a fake device pin how `_Capture` avoids that. The last ones use SDL's
dummy audio driver, which needs no microphone, in a child process, because the bug freezes the whole interpreter: no
timeout inside this process could end it.
"""
from __future__ import annotations

import gc
import os
import subprocess
import sys
import textwrap
import threading
import time
import weakref

import pytest

from funground import frame_inputs, sound
from funground.sound import _microphone as mi

from conftest import run_sketch
from test_microphone import fake  # noqa: F401  (a fixture)


class FakeSdl:
    """Records which thread paused it, and what happened in what order."""

    def __init__(self):
        self.pausers = []
        self.log = []
        self.paused = True

    def pause(self, flag):
        self.log.append(f"pause({flag})")
        self.paused = bool(flag)
        if flag:
            self.pausers.append(threading.current_thread())

    def close(self):
        self.log.append("close")


@pytest.fixture
def audio_thread():
    """Start a thread that calls a capture's callback as SDL's audio thread does, until the test ends."""
    done = threading.Event()
    threads = []

    def start(capture, device):
        def calls():
            while not done.is_set():
                if not device.paused:             # as SDL: a paused device makes no callback
                    capture.on_audio(device, b"")
                time.sleep(0.001)
        thread = threading.Thread(target=calls)
        thread.start()
        threads.append(thread)
        return thread

    yield start
    done.set()
    for thread in threads:
        thread.join()


def open_capture():
    heard = []
    capture = mi._Capture(lambda device, view: heard.append(view))
    capture.device = FakeSdl()
    return capture, capture.device, heard


def test_a_listening_device_is_paused_by_its_own_audio_thread(audio_thread):
    capture, device, _ = open_capture()
    capture.pause(0)
    thread = audio_thread(capture, device)
    capture.pause(1)
    assert device.pausers == [thread]


def test_nothing_more_is_heard_once_paused(audio_thread):
    capture, device, heard = open_capture()
    capture.pause(0)
    audio_thread(capture, device)
    capture.pause(1)
    before = len(heard)
    time.sleep(0.01)
    assert len(heard) == before


def test_listening_again_after_a_pause(audio_thread):
    capture, device, heard = open_capture()
    capture.pause(0)
    audio_thread(capture, device)
    capture.pause(1)
    capture.pause(0)
    before = len(heard)
    deadline = time.monotonic() + 2
    while len(heard) == before and time.monotonic() < deadline:
        time.sleep(0.001)
    assert len(heard) > before


def test_a_device_that_has_gone_quiet_is_paused_after_a_short_wait(monkeypatch):
    monkeypatch.setattr(mi, "CALLBACK_WAIT", 0.01)
    capture, device, _ = open_capture()
    capture.pause(0)
    capture.pause(1)                                      # no callback ever comes
    assert device.pausers == [threading.current_thread()]


def test_pausing_a_paused_device_does_nothing():
    capture, device, _ = open_capture()
    capture.pause(1)
    assert device.log == []


def test_close_pauses_first_and_closing_twice_does_nothing(audio_thread):
    capture, device, _ = open_capture()
    capture.pause(0)
    audio_thread(capture, device)
    capture.close()
    capture.close()
    assert device.log == ["pause(0)", "pause(1)", "close"]


def test_a_dropped_capture_closes_its_device():
    capture, device, _ = open_capture()
    del capture
    gc.collect()
    assert device.log == ["close"]


# ---- the sketch's end
def test_the_end_of_a_sketch_closes_a_started_microphone(fake, tmp_path):  # noqa: F811
    sketch = tmp_path / "listens.py"
    sketch.write_text(textwrap.dedent("""\
        import funground as f
        from funground import sound
        mic = sound.microphone()
        mic.start()
        def draw():
            f.circle(50, 50, 10 + 100 * mic.level())
        f.run()
        """), encoding="utf-8")
    run_sketch(sketch, frames=2)
    _, device = fake["opened"][0]
    assert device.closed


def test_the_end_of_a_sketch_keeps_what_was_heard_and_it_can_start_again(fake):  # noqa: F811
    mic = sound.microphone()
    mic.start()
    mic._feed([0.5] * 100)
    frame_inputs.stop_all()
    assert not mic.is_listening() and fake["opened"][0][1].closed
    assert mic.capture(0.001).samples()[-1] == pytest.approx(0.5)
    mic.start()
    assert mic.is_listening() and len(fake["opened"]) == 2
    mic.close()


def test_a_microphone_that_is_closed_is_not_kept(fake):  # noqa: F811
    mic = sound.microphone()
    mic.start()
    mic.close()
    assert mic not in mi._started


def test_a_dropped_microphone_is_not_kept_alive(monkeypatch):
    monkeypatch.setenv("FUNGROUND_HEADLESS", "1")         # no device, whose callback would hold on to it
    mic = sound.microphone()
    mic.start()
    gone = weakref.ref(mic)
    del mic
    gc.collect()
    assert gone() is None


# ---- the real thing, on SDL's dummy driver
FREEZES = """
import gc, os, random, sys, time
from funground.sound import _microphone as mi
how = sys.argv[1]
random.seed(1)
for _ in range({rounds}):
    mic = mi.make()
    mic.start()
    until = time.perf_counter() + random.uniform(0.01, 0.05)
    while time.perf_counter() < until:                 # keep the GIL busy, as drawing frames does
        sum(range(2000))
    if how == "stop":
        mic.stop()
        mic.close()
    elif how == "close":
        mic.close()
    else:
        del mic
        gc.collect()
print("finished")
"""


@pytest.mark.parametrize("how", ["stop", "close", "collect"])
def test_a_running_device_never_freezes_the_interpreter(how):
    env = {**os.environ, "SDL_AUDIODRIVER": "dummy", "SDL_VIDEODRIVER": "dummy", "PYTHONFAULTHANDLER": "1"}
    env.pop("FUNGROUND_HEADLESS", None)
    done = subprocess.run([sys.executable, "-c", FREEZES.format(rounds=40), how], env=env, capture_output=True, text=True,
                          timeout=60)
    assert done.returncode == 0, done.stderr
    assert "finished" in done.stdout
