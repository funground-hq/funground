"""Sound playback and analysis (S-098, S-099; contract A1, A2; D-046).

WAV files are made here with the `wave` module. Time is driven by replacing
`funground.sound.clock`, so nothing sleeps and every number is exact.
"""
from __future__ import annotations

import math
import os
import struct
import time
import wave
from pathlib import Path

import pytest

import funground as f
from funground import api, sound as sound_module

RATE = 44100


def write_wav(path: Path, seconds: float, freq: float | None = 440.0, amplitude: float = 1.0,
              channels: int = 1, rate: int = RATE) -> Path:
    """A WAV of a sine tone (or silence when *freq* is None). Full scale is amplitude 1."""
    frames = int(seconds * rate)
    data = bytearray()
    for i in range(frames):
        v = 0.0 if freq is None else amplitude * math.sin(2 * math.pi * freq * i / rate)
        sample = int(round(v * 32767))
        data += struct.pack("<h", sample) * channels
    with wave.open(str(path), "wb") as w:
        w.setnchannels(channels)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(bytes(data))
    return path


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


@pytest.fixture
def tone(tmp_path):
    return write_wav(tmp_path / "tone.wav", 2.0, 440.0)


# ---- loading and the files it finds (A1)
def test_load_sound_reports_duration(tone):
    s = f.load_sound(str(tone))
    assert s.duration() == pytest.approx(2.0, abs=0.01)


def test_stereo_file_loads(tmp_path):
    s = f.load_sound(str(write_wav(tmp_path / "st.wav", 0.5, 440.0, channels=2)))
    assert s.duration() == pytest.approx(0.5, abs=0.01)


def test_file_found_next_to_the_sketch(tmp_path, monkeypatch):
    folder = tmp_path / "sketchdir"
    folder.mkdir()
    write_wav(folder / "beep.wav", 0.5)
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)
    namespace = {"__file__": str(folder / "sketch.py")}
    exec(compile("import funground as f\nsnd = f.load_sound('beep.wav')", "sketch.py", "exec"), namespace)
    assert namespace["snd"].duration() == pytest.approx(0.5, abs=0.01)


def test_file_found_in_the_current_folder(tmp_path, monkeypatch):
    write_wav(tmp_path / "here.wav", 0.25)
    monkeypatch.chdir(tmp_path)
    assert f.load_sound("here.wav").duration() == pytest.approx(0.25, abs=0.01)


def test_missing_file_names_both_places(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    folder = tmp_path / "sk"
    folder.mkdir()
    namespace = {"__file__": str(folder / "sketch.py")}
    with pytest.raises(FileNotFoundError) as info:
        exec(compile("import funground as f\nf.load_sound('nope.wav')", "sketch.py", "exec"), namespace)
    message = str(info.value)
    assert str(folder / "nope.wav") in message and str(tmp_path / "nope.wav") in message


def test_not_a_sound_is_a_value_error(tmp_path):
    bad = tmp_path / "bad.wav"
    bad.write_bytes(b"this is not a sound file at all")
    with pytest.raises(ValueError, match="not a sound"):
        f.load_sound(str(bad))


# ---- playback state (A1)
def test_play_pause_stop_and_is_playing(tone, clock):
    s = f.load_sound(str(tone))
    assert not s.is_playing()
    s.play()
    assert s.is_playing()
    clock.advance(0.5)
    assert s.current_time() == pytest.approx(0.5)
    s.pause()
    assert not s.is_playing()
    clock.advance(10)
    assert s.current_time() == pytest.approx(0.5)            # kept at the pause
    s.play()
    assert s.is_playing()
    clock.advance(0.25)
    assert s.current_time() == pytest.approx(0.75)           # carried on from the pause
    s.stop()
    assert not s.is_playing()
    assert s.current_time() == 0.0                           # stop rewinds
    s.play()
    clock.advance(0.1)
    assert s.current_time() == pytest.approx(0.1)


def test_play_again_while_playing_starts_again(tone, clock):
    s = f.load_sound(str(tone))
    s.play()
    clock.advance(1.0)
    s.play()
    assert s.current_time() == pytest.approx(0.0)
    clock.advance(0.2)
    assert s.current_time() == pytest.approx(0.2)


def test_pause_when_not_playing_does_nothing(tone, clock):
    s = f.load_sound(str(tone))
    s.pause()
    assert not s.is_playing() and s.current_time() == 0.0
    s.play()
    clock.advance(0.3)
    s.pause()
    s.pause()
    assert s.current_time() == pytest.approx(0.3)


def test_is_playing_turns_false_at_the_end(tone, clock):
    s = f.load_sound(str(tone))
    s.play()
    clock.advance(1.9)
    assert s.is_playing()
    clock.advance(0.2)
    assert not s.is_playing()
    assert s.level() == 0.0
    s.play()                                             # a finished sound plays from the start
    assert s.is_playing() and s.current_time() == pytest.approx(0.0)


def test_loop_wraps_and_keeps_playing(tone, clock):
    s = f.load_sound(str(tone))
    s.loop()
    clock.advance(2.5)
    assert s.is_playing()
    assert s.current_time() == pytest.approx(0.5, abs=0.01)
    clock.advance(100)
    assert s.is_playing()
    s.stop()
    assert not s.is_playing()


def test_play_after_loop_does_not_loop(tone, clock):
    s = f.load_sound(str(tone))
    s.loop()
    s.play()
    clock.advance(2.5)
    assert not s.is_playing()


def test_loop_resumes_after_pause(tone, clock):
    s = f.load_sound(str(tone))
    s.loop()
    clock.advance(1.0)
    s.pause()
    clock.advance(5)
    s.loop()
    assert s.current_time() == pytest.approx(1.0)
    clock.advance(1.5)
    assert s.current_time() == pytest.approx(0.5, abs=0.01)


def test_several_sounds_play_together(tone, tmp_path, clock):
    a, b = f.load_sound(str(tone)), f.load_sound(str(write_wav(tmp_path / "b.wav", 1.0, 880.0)))
    a.play()
    b.play()
    clock.advance(1.5)
    assert a.is_playing() and not b.is_playing()


def test_set_volume(tone):
    s = f.load_sound(str(tone))
    assert s.get_volume() == 1.0
    s.set_volume(0.25)
    assert s.get_volume() == 0.25
    s.set_volume(0)
    s.set_volume(1)
    for bad in (-0.1, 1.1, "loud", None, True):
        with pytest.raises(ValueError):
            s.set_volume(bad)
    assert s.get_volume() == 1.0


# ---- analysis (A2)
def test_level_and_spectrum_are_zero_when_not_playing(tone, clock):
    s = f.load_sound(str(tone))
    assert s.level() == 0.0
    assert s.spectrum() == [0.0] * 32
    assert s.spectrum(7) == [0.0] * 7
    s.play()
    clock.advance(0.5)
    s.pause()
    assert s.level() == 0.0 and s.spectrum(4) == [0.0] * 4


def test_silent_sound_has_level_zero(tmp_path, clock):
    s = f.load_sound(str(write_wav(tmp_path / "quiet.wav", 1.0, None)))
    s.play()
    clock.advance(0.5)
    assert s.level() == 0.0
    assert s.spectrum() == [0.0] * 32


def test_full_scale_tone_has_level_of_about_0_707(tone, clock):
    s = f.load_sound(str(tone))
    s.play()
    clock.advance(0.5)
    assert s.level() == pytest.approx(0.707, abs=0.01)


def test_half_scale_tone_is_half_as_loud(tmp_path, clock):
    s = f.load_sound(str(write_wav(tmp_path / "half.wav", 1.0, 440.0, amplitude=0.5)))
    s.play()
    clock.advance(0.5)
    assert s.level() == pytest.approx(0.354, abs=0.01)


def test_stereo_is_mixed_to_mono(tmp_path, clock):
    s = f.load_sound(str(write_wav(tmp_path / "st.wav", 1.0, 440.0, channels=2)))
    s.play()
    clock.advance(0.5)
    assert s.level() == pytest.approx(0.707, abs=0.01)


def test_level_follows_the_position(tmp_path, clock):
    """Loud for the first second, silent after."""
    path = tmp_path / "burst.wav"
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        loud = b"".join(struct.pack("<h", int(32767 * math.sin(2 * math.pi * 440 * i / RATE))) for i in range(RATE))
        w.writeframes(loud + b"\x00\x00" * RATE)
    s = f.load_sound(str(path))
    s.play()
    clock.advance(0.5)
    assert s.level() > 0.6
    clock.advance(1.0)
    assert s.level() == 0.0


def band_of(hz: float, bands: int) -> int:
    ratio = (16000 / 40) ** (1 / bands)
    return int(math.log(hz / 40) / math.log(ratio))


def test_spectrum_length_and_range(tone, clock):
    s = f.load_sound(str(tone))
    s.play()
    clock.advance(0.5)
    for bands in (1, 2, 8, 32, 100, 256):
        values = s.spectrum(bands)
        assert len(values) == bands
        assert all(0.0 <= v <= 1.0 for v in values)
    assert len(s.spectrum()) == 32


def test_spectrum_bands_must_be_1_to_256(tone):
    s = f.load_sound(str(tone))
    for bad in (0, -1, 257, 2.5, "8", None):
        with pytest.raises(ValueError):
            s.spectrum(bad)


@pytest.mark.parametrize("bands", [8, 16])
def test_440_hz_peaks_in_its_band(tone, clock, bands):
    s = f.load_sound(str(tone))
    s.play()
    clock.advance(0.5)
    values = s.spectrum(bands)
    peak = values.index(max(values))
    assert peak == band_of(440, bands)
    assert values[peak] == pytest.approx(1.0, abs=0.2)      # a full-scale sine is about 1


def test_4_khz_peaks_higher_than_440_hz(tmp_path, clock):
    low = f.load_sound(str(write_wav(tmp_path / "low.wav", 1.0, 440.0)))
    high = f.load_sound(str(write_wav(tmp_path / "high.wav", 1.0, 4000.0)))
    for s in (low, high):
        s.play()
    clock.advance(0.5)
    low_values, high_values = low.spectrum(8), high.spectrum(8)
    assert high_values.index(max(high_values)) == band_of(4000, 8)
    assert high_values.index(max(high_values)) > low_values.index(max(low_values))
    assert max(high_values) == pytest.approx(1.0, abs=0.2)


def test_quiet_tone_gives_a_smaller_spectrum(tmp_path, clock):
    s = f.load_sound(str(write_wav(tmp_path / "q.wav", 1.0, 440.0, amplitude=0.25)))
    s.play()
    clock.advance(0.5)
    assert max(s.spectrum(8)) == pytest.approx(0.25, abs=0.06)


def test_analysis_at_the_very_start_does_not_fail(tone, clock):
    s = f.load_sound(str(tone))
    s.play()
    assert s.level() == 0.0                                  # nothing before the start yet
    s.spectrum()
    s.loop()
    s.level()
    s.spectrum()


def test_analysis_of_a_very_short_looping_sound(tmp_path, clock):
    s = f.load_sound(str(write_wav(tmp_path / "tiny.wav", 0.01, 440.0)))
    s.loop()
    clock.advance(0.5)
    s.level()
    assert len(s.spectrum(16)) == 16


def test_analysis_is_cached_once_per_frame(tone, clock, monkeypatch):
    s = f.load_sound(str(tone))
    sketch = api.active_sketch()
    s.play()
    clock.advance(0.5)
    sketch.frame_count = 5
    first = s.spectrum(8)
    calls = []
    original = s._compute_spectrum
    monkeypatch.setattr(s, "_compute_spectrum", lambda bands: calls.append(bands) or original(bands))
    clock.advance(0.1)
    assert s.spectrum(8) == first and calls == []            # same frame: not computed again
    first_level = s.level()
    clock.advance(0.01)
    assert s.level() == first_level
    sketch.frame_count = 6
    s.spectrum(8)
    assert calls == [8]                                      # a new frame: computed
    s.spectrum(4)
    assert calls == [8, 4]                                   # other band count: computed


def test_spectrum_time_is_small(tone, clock):
    s = f.load_sound(str(tone))
    s.play()
    clock.advance(0.5)
    sketch = api.active_sketch()
    s.spectrum()                                             # warm up: decode the samples
    start = time.perf_counter()
    for i in range(20):
        sketch.frame_count = i + 1
        clock.advance(0.01)
        s.spectrum()
    per_call = (time.perf_counter() - start) / 20
    assert per_call < 0.05, per_call                         # target 5 ms; slack for slow CI


# ---- devices and headless (A1)
def test_headless_sound_plays_silently_and_keeps_time(tone, clock, monkeypatch):
    monkeypatch.setenv("FUNGROUND_HEADLESS", "1")
    s = f.load_sound(str(tone))
    assert s._silent
    s.play()
    clock.advance(0.5)
    assert s.is_playing() and s.current_time() == pytest.approx(0.5)
    assert s.level() > 0.6
    s.pause()
    s.stop()
    s.set_volume(0.5)


def test_no_device_falls_back_to_a_silent_sound(tone, clock, monkeypatch):
    import pygame

    monkeypatch.setattr(sound_module, "_mixer_ready", False)
    monkeypatch.setattr(sound_module, "_audible", True)
    real_init = pygame.mixer.init
    attempts = []

    def fake_init(*args, **kwargs):
        attempts.append(os.environ.get("SDL_AUDIODRIVER"))
        if len(attempts) == 1:
            raise pygame.error("no audio device")
        return real_init(*args, **kwargs)

    pygame.mixer.quit()
    monkeypatch.setattr(pygame.mixer, "init", fake_init)
    s = f.load_sound(str(tone))
    assert s._silent and not sound_module._audible
    assert attempts[-1] == "dummy"
    s.play()
    clock.advance(0.5)
    assert s.is_playing() and s.level() > 0.6
    # leave the environment as it was
    assert os.environ.get("SDL_AUDIODRIVER") == "dummy"


def test_device_calls_when_audible(tone, clock, monkeypatch):
    """With a device the real mixer sound is played, paused, resumed and stopped."""
    monkeypatch.delenv("FUNGROUND_HEADLESS", raising=False)
    s = f.load_sound(str(tone))
    s._silent = False
    log = []

    class FakeChannel:
        def __init__(self, snd):
            self.snd = snd

        def get_sound(self):
            return self.snd

        def pause(self):
            log.append("pause")

        def unpause(self):
            log.append("unpause")

    class FakeSound:
        def get_length(self):
            return 2.0

        def play(self, loops=0):
            log.append(("play", loops))
            return FakeChannel(self)

        def stop(self):
            log.append("stop")

        def set_volume(self, v):
            log.append(("volume", v))

    fake = FakeSound()
    s._snd = fake
    s.play()
    s.pause()
    s.play()
    s.loop()
    s.set_volume(0.5)
    s.stop()
    assert log == [("play", 0), "pause", "unpause", "stop", ("play", -1), ("volume", 0.5), "stop"]


# ---- sounds are not drawing (A1)
def test_sound_adds_nothing_to_the_ir_or_pixels(tone, clock):
    sketch = api.active_sketch()
    f.size(40, 30)
    f.background("white")
    before_ops = list(sketch.frame.ops)
    before_pixels = bytes(sketch._renderer.pixels().data)
    s = f.load_sound(str(tone))
    s.play()
    clock.advance(0.5)
    s.level()
    s.spectrum()
    s.set_volume(0.5)
    s.pause()
    s.stop()
    assert list(sketch.frame.ops) == before_ops
    assert bytes(sketch._renderer.pixels().data) == before_pixels


def test_works_in_an_animated_sketch(tone, tmp_path):
    from conftest import run_sketch

    sketch = tmp_path / "s.py"
    sketch.write_text(
        "import funground as f\n"
        f"snd = f.load_sound({str(tone)!r})\n"
        "def setup():\n    f.size(60, 40)\n    snd.loop()\n"
        "def draw():\n    f.background('white')\n    f.rect(0, 0, 10 + 30 * snd.level(), 10)\n"
        "f.run()\n",
        encoding="utf-8",
    )
    (w, h), data = run_sketch(sketch, frames=5)
    assert len(data) == w * h * 3
