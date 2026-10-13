"""Sound and the microphone under a host (story S-137, contract W1; Web_Runner_Note.md).

A fake host stands where the browser page does: it receives the sound commands and pushes microphone chunks.
The desktop path is the reference: the samples the host receives are the ones pygame's mixer would be given,
and the microphone's analysis of pushed chunks equals its analysis of the same samples on the desktop.
"""
from __future__ import annotations

import gc
import math
import os
import subprocess
import sys
import wave
from array import array
from pathlib import Path

import pytest

import funground as f
from funground import microphone_input as mi, sound as sound_module
from funground.web import Session

RATE = 44100
ROOT = Path(__file__).resolve().parent.parent


class Host:
    """The page: keeps every sound command (and a copy of the samples that came with it)."""

    def __init__(self) -> None:
        self.sounds: list[tuple[str, int, dict, array | None]] = []
        self.microphone: list[str] = []

    def on_sound(self, command, voice, fields, samples) -> None:
        copy = None
        if samples is not None:                          # the view is valid only during the call
            copy = array("f")
            copy.frombytes(samples.tobytes())
        self.sounds.append((command, voice, dict(fields), copy))

    def on_microphone(self, command) -> None:
        self.microphone.append(command)

    def commands(self) -> list[str]:
        return [c[0] for c in self.sounds]

    def loaded(self) -> list[array]:
        return [c[3] for c in self.sounds if c[0] == "load"]


@pytest.fixture
def host():
    """A Session wired to a fake host. It is stopped afterwards, which hands sound and microphone back."""
    page = Host()
    session = Session(640, 480, on_sound=page.on_sound, on_microphone=page.on_microphone)
    page.session = session
    yield page
    session.stop()


@pytest.fixture
def clock(monkeypatch):
    """Sound time that the test moves by hand."""
    now = [100.0]
    monkeypatch.setattr(sound_module, "clock", lambda: now[0])
    return now


def desktop_samples(make) -> list[float]:
    """What pygame's mixer is given for a sound made by *make()* on the desktop (headless), as floats."""
    raw = array("h")
    raw.frombytes(make()._snd.get_raw())
    return [v / 32768 for v in raw]


MAKERS = {
    "tone": lambda: f.tone(440, 0.25),
    "tone_square": lambda: f.tone(220, 0.2, wave="square", volume=0.8),
    "melody": lambda: f.melody("C4 E4 G4:2 - C5", tempo=240),
    "sargam_melody": lambda: f.melody("S R G m P", tempo=240, sa="D4"),
    "raga_drone": lambda: f.drone("D3", 2),
    "mix": lambda: f.mix(f.tone(440, 0.2), f.tone(660, 0.2)),
}


@pytest.mark.parametrize("name", MAKERS)
def test_the_host_receives_the_samples_pygame_would_be_given(name, host, monkeypatch):
    make = MAKERS[name]
    f.random_seed(0)
    snd = make()
    snd.play()
    assert host.commands() == ["load", "play"]
    _, _, fields, samples = host.sounds[0]
    assert (fields["rate"], fields["channels"]) == (RATE, 2)
    assert fields["frames"] * 2 == len(samples)

    host.session.stop()                                   # back to the desktop path, headless, for the reference
    monkeypatch.setenv("FUNGROUND_HEADLESS", "1")
    f.random_seed(0)
    assert list(samples) == desktop_samples(make)


def test_a_sound_is_sent_once_and_only_when_first_played(host):
    snd = f.tone(440, 0.2)
    snd.set_volume(0.5)
    snd.pan(-1)
    assert host.sounds == []                              # nothing to the host until something plays
    snd.play()
    snd.play()
    snd.loop()
    assert host.commands().count("load") == 1
    assert len(host.loaded()[0]) == 2 * len(snd.samples())


def test_play_loop_pause_resume_stop_volume_pan_commands(host):
    snd = f.tone(440, 1)
    snd.set_volume(0.25)
    snd.play()
    snd.pause()
    snd.play()                                            # carries on from the pause
    snd.pan(1)
    snd.set_volume(0.5)
    snd.stop()
    snd.loop()
    steps = [(c, v) for c, v, _, _ in host.sounds]
    assert [c for c, _ in steps] == ["load", "play", "pause", "resume", "pan", "volume", "stop", "play", "pan"]
    assert len({v for _, v in steps}) == 1                # one sound, one voice number
    assert host.sounds[1][2] == {"loops": 0, "volume": 0.25, "left": 1.0, "right": 1.0}
    assert host.sounds[4][2] == {"left": 0.0, "right": 1.0}          # pan 1: the left side fades to nothing
    assert host.sounds[5][2] == {"volume": 0.5}
    assert host.sounds[7][2]["loops"] == -1 and host.sounds[7][2]["volume"] == 0.5
    assert host.sounds[8][2] == {"left": 0.0, "right": 1.0}          # the pan is kept for the new play


def test_the_volume_and_pan_set_before_the_first_play_reach_the_host(host):
    snd = f.tone(440, 1)
    snd.set_volume(0.3)
    snd.pan(-0.5)
    snd.play()
    play = next(fields for c, _, fields, _ in host.sounds if c == "play")
    assert play["volume"] == 0.3
    assert (play["left"], play["right"]) == (1.0, 1.0)             # a new play starts in the middle...
    assert host.sounds[-1][:1] == ("pan",)                         # ...and pan follows at once, as on the desktop
    assert host.sounds[-1][2] == {"left": 1.0, "right": 0.5}


def test_two_sounds_have_two_voices(host):
    a, b = f.tone(440, 0.2), f.tone(660, 0.2)
    a.play()
    b.play()
    voices = [v for c, v, _, _ in host.sounds if c == "play"]
    assert len(set(voices)) == 2


def test_a_dropped_sound_is_freed(host):
    snd = f.tone(440, 0.2)
    snd.play()
    voice = host.sounds[0][1]
    del snd
    gc.collect()
    assert ("free", voice) in [(c, v) for c, v, _, _ in host.sounds]


def test_the_session_stopping_stops_every_sound_and_hands_the_mixer_back(host):
    f.tone(440, 1).loop()
    host.session.stop()
    assert host.sounds[-1][:2] == ("stop_all", 0)
    assert sound_module._host_mixer is None and mi._host_input is None


def test_the_sound_clock_is_the_same_under_a_host(host, clock):
    """Contract A1 and A2: is_playing, current_time and the end of a sound come from the clock, not the device."""
    snd = f.tone(440, 1)
    assert not snd.is_playing()
    snd.play()
    clock[0] += 0.4
    assert snd.is_playing() and snd.current_time() == pytest.approx(0.4)
    snd.pause()
    clock[0] += 5
    assert not snd.is_playing() and snd.current_time() == pytest.approx(0.4)
    snd.play()
    clock[0] += 0.4
    assert snd.current_time() == pytest.approx(0.8)
    clock[0] += 0.4
    assert not snd.is_playing() and snd.current_time() == 0          # it ended by itself

    snd.loop()
    clock[0] += 2.5
    assert snd.is_playing() and snd.current_time() == pytest.approx(0.5, abs=1e-6)
    snd.stop()
    assert not snd.is_playing() and snd.current_time() == 0


def test_analysis_is_the_same_under_a_host(host, clock, monkeypatch):
    snd = f.tone(440, 1)
    snd.play()
    clock[0] += 0.5
    under_host = (snd.level(), snd.pitch(), snd.spectrum(8))
    host.session.stop()
    monkeypatch.setenv("FUNGROUND_HEADLESS", "1")
    again = f.tone(440, 1)
    again.play()
    clock[0] += 0.5
    assert (again.level(), again.pitch(), again.spectrum(8)) == under_host


def test_a_wav_file_can_be_loaded_and_played(host, tmp_path):
    path = tmp_path / "beep.wav"
    values = [int(8000 * math.sin(2 * math.pi * 330 * i / 22050)) for i in range(2205)]    # 0.1 s at 22 050 Hz, mono
    with wave.open(str(path), "wb") as out:
        out.setnchannels(1)
        out.setsampwidth(2)
        out.setframerate(22050)
        out.writeframes(array("h", values).tobytes())
    snd = f.load_sound(str(path))
    assert snd.duration() == pytest.approx(0.1, abs=0.001)
    snd.play()
    samples = host.loaded()[0]
    assert len(samples) == 2 * round(0.1 * RATE) and samples[0::2] == samples[1::2]


def test_a_file_that_is_not_a_16_bit_wav_says_so(host, tmp_path):
    path = tmp_path / "tune.mp3"
    path.write_bytes(b"not a wav file")
    with pytest.raises(ValueError, match="16-bit WAV"):
        f.load_sound(str(path))


def test_pygame_is_not_imported():
    """The seam is the point: a host plays sound and listens without pygame (nothing to download).
    The runner sets FUNGROUND_HEADLESS=1, which keeps the sketch that follows a Session off pygame too."""
    script = (
        "import sys; sys.path.insert(0, sys.argv[1])\n"
        "import funground as f\n"
        "from funground.web import Session\n"
        "got = []\n"
        "s = Session(100, 100, on_sound=lambda *a: got.append(a[0]), on_microphone=lambda c: got.append('mic ' + c))\n"
        "f.tone(440, 0.2).play(); f.melody('C4 E4').loop(); f.drone('D3', 1).play()\n"
        "m = f.microphone(); m.start(); s.push_microphone([0.1] * 512); m.level(); m.capture(1).level()\n"
        "f.size(100, 100); f.microphones(); f.draw_wave(f.tone(440, 0.1), 0, 0, 50, 20)\n"
        "s.stop()\n"
        "assert 'pygame' not in sys.modules, 'pygame was imported'\n"
        "print(','.join(got))\n")
    done = subprocess.run([sys.executable, "-I", "-c", script, str(ROOT)], capture_output=True, text=True, timeout=300,
                          env={**os.environ, "FUNGROUND_HEADLESS": "1"})
    assert done.returncode == 0, done.stderr
    assert "load,play" in done.stdout and "mic start" in done.stdout


# ---- the microphone

def sine(hz, seconds=0.5, amp=0.5):
    return [amp * math.sin(2 * math.pi * hz * i / RATE) for i in range(int(seconds * RATE))]


def pushed(host, samples, chunk=1024):
    for at in range(0, len(samples), chunk):
        host.session.push_microphone(array("f", samples[at:at + chunk]))


def desktop_microphone(samples):
    """The desktop's microphone, fed the same samples straight into its ring buffer."""
    mic = mi.Microphone(None, silent=True)
    mic.start()
    mic._feed(samples)
    return mic


def readings(mic):
    return (mic.level(), mic.pitch(), mic.is_onset(), mic.spectrum(16), mic.chroma())


@pytest.mark.parametrize("hz", [220, 440, 880])
def test_pushed_chunks_read_the_same_as_the_desktop_path(host, hz):
    samples = sine(hz, 0.6)
    mic = f.microphone()
    mic.start()
    pushed(host, samples)
    assert readings(mic) == readings(desktop_microphone(samples))
    assert mic.pitch() == pytest.approx(hz, rel=0.01)
    assert mic.level() == pytest.approx(0.5 / math.sqrt(2), rel=0.05)


def test_chunks_of_any_size_read_the_same(host):
    samples = sine(330, 1.0) + [0.0] * 4000 + sine(330, 0.3, 0.8)
    mic = f.microphone()
    mic.start()
    at = 0                                                  # the page batches 128-sample worklet blocks; sizes vary
    for size in (128, 1000, 777, 5000) * 100:
        if at >= len(samples):
            break
        host.session.push_microphone(samples[at:at + size])    # a plain list is accepted too
        at += size
    assert readings(mic) == readings(desktop_microphone(samples))


def test_capture_is_the_same_sound(host):
    samples = sine(440, 1.0)
    mic = f.microphone()
    mic.start()
    pushed(host, samples)
    assert mic.capture(1).samples() == desktop_microphone(samples).capture(1).samples()


def test_not_listening_gives_zero_none_and_false(host):
    mic = f.microphone()
    assert not mic.is_listening()
    host.session.push_microphone(sine(440, 0.3))            # a host that pushes before start() is not heard
    assert (mic.level(), mic.pitch(), mic.is_onset()) == (0, None, False)
    assert mic.spectrum(4) == [0.0] * 4
    assert host.microphone == []                            # and nothing was asked of the page yet


def test_until_the_page_delivers_a_started_microphone_hears_silence(host):
    mic = f.microphone()
    mic.start()
    assert host.microphone == ["start"]
    assert (mic.level(), mic.pitch(), mic.is_onset()) == (0, None, False)      # nothing pushed yet: the "not listening" values


def test_start_stop_and_close_are_asked_of_the_page(host):
    mic = f.microphone()
    mic.start()
    mic.stop()
    assert not mic.is_listening()
    host.session.push_microphone(sine(440, 0.3))
    assert mic.level() == 0                                 # stopped: chunks still arriving are not heard
    mic.start()
    host.session.stop()
    assert host.microphone == ["start", "stop", "start", "close"]


def test_a_second_start_asks_the_page_nothing(host):
    mic = f.microphone()
    mic.start()
    mic.start()
    assert host.microphone == ["start"]


def test_choosing_a_microphone_by_name_is_desktop_only(host):
    with pytest.raises(RuntimeError, match="only works in the desktop version"):
        f.microphone("USB")
    assert f.microphones() == []
