"""Microphone input (S-108; contract A4; D-058).

The real microphone is never opened here. Tests replace the device functions in
`funground.microphone_input` and play the microphone a known sound with `mic._feed(...)`.
"""
from __future__ import annotations

import math
from array import array

import pytest

import funground as f
from funground import api, microphone_input as mi, sound as sound_module

RATE = 44100


def sine(hz, seconds=0.5, amp=0.5):
    return [amp * math.sin(2 * math.pi * hz * i / RATE) for i in range(int(seconds * RATE))]


class FakeDevice:
    def __init__(self, callback):
        self.callback = callback
        self.paused = True
        self.closed = False

    def pause(self, flag):
        self.paused = bool(flag)

    def close(self):
        self.closed = True


@pytest.fixture
def fake(monkeypatch):
    """Two fake input devices, 'Fake USB mic' and 'Other input'."""
    state = {"opened": []}
    monkeypatch.setattr(mi, "_device_names", lambda: ["Fake USB mic", "Other input"])

    def open_capture(name, callback):
        device = FakeDevice(callback)
        state["opened"].append((name, device))
        return device, RATE

    monkeypatch.setattr(mi, "_open_capture", open_capture)
    monkeypatch.delenv("FUNGROUND_HEADLESS", raising=False)
    return state


def test_microphones_lists_the_device_names(fake):
    assert f.microphones() == ["Fake USB mic", "Other input"]


def test_microphones_is_empty_when_headless(monkeypatch, fake):
    monkeypatch.setenv("FUNGROUND_HEADLESS", "1")
    assert f.microphones() == []


def test_start_stop_and_is_listening(fake):
    mic = f.microphone()
    assert not mic.is_listening()
    mic.start()
    assert mic.is_listening()
    name, device = fake["opened"][0]
    assert name is None and not device.paused           # the default input, now listening
    mic.stop()
    assert not mic.is_listening() and device.paused
    mic.start()
    assert len(fake["opened"]) == 1 and mic.is_listening()   # the device is reused
    mic.close()
    assert device.closed


def test_name_picks_the_input_whose_name_contains_it(fake):
    f.microphone("other").start()
    assert fake["opened"][0][0] == "Other input"


def test_unknown_name_is_a_plain_error(fake):
    with pytest.raises(RuntimeError, match="no microphone has 'zzz'.*Fake USB mic"):
        f.microphone("zzz")


def test_a_bad_name_is_a_value_error(fake):
    with pytest.raises(ValueError):
        f.microphone("")


def test_a_sine_gives_level_spectrum_and_pitch(fake):
    mic = f.microphone()
    mic.start()
    mic._feed(sine(440))
    assert mic.level() == pytest.approx(0.5 / math.sqrt(2), abs=0.02)
    spectrum = mic.spectrum(32)
    assert len(spectrum) == 32
    peak = max(range(32), key=spectrum.__getitem__)
    ratio = (16000 / 40) ** (1 / 32)
    assert 40 * ratio ** peak <= 440 < 40 * ratio ** (peak + 1)
    assert mic.pitch() == pytest.approx(440, rel=0.01)
    assert f.frequency_to_note(mic.pitch()) == "A4"


def test_the_analysis_is_the_same_code_as_a_sounds(fake):
    mic = f.microphone()
    snd = f.create_sound(sine(300, 0.3))
    assert type(mic).level is type(snd).level
    assert type(mic).spectrum is type(snd).spectrum
    assert type(mic).pitch is type(snd).pitch


def test_silence_gives_zero_and_none(fake):
    mic = f.microphone()
    mic.start()
    mic._feed([0.0] * 5000)
    assert mic.level() == 0.0
    assert mic.spectrum(8) == [0.0] * 8
    assert mic.pitch() is None


def test_nothing_heard_yet_is_silence(fake):
    mic = f.microphone()
    mic.start()
    assert mic.level() == 0.0 and mic.pitch() is None and mic.spectrum(4) == [0.0] * 4


def test_not_listening_gives_zeros_and_none(fake):
    mic = f.microphone()
    mic._feed(sine(440))
    assert mic.level() == 0.0
    assert mic.spectrum(5) == [0.0] * 5
    assert mic.pitch() is None
    mic.start()
    mic._feed(sine(440))
    assert mic.level() > 0.3
    mic.stop()
    assert mic.level() == 0.0 and mic.pitch() is None


def test_spectrum_checks_bands(fake):
    with pytest.raises(ValueError, match="microphone.spectrum"):
        f.microphone().spectrum(0)


def test_ring_buffer_wraps_and_keeps_the_newest(fake):
    mic = f.microphone()
    mic.start()
    size = mi.BUFFER_SECONDS * RATE
    mic._feed([0.1] * (size - 10))
    mic._feed([0.2] * 30)                        # crosses the end of the buffer
    assert mic._latest(40) == pytest.approx([0.1] * 10 + [0.2] * 30)
    mic._feed([0.3] * (size + 5))                # more than the whole buffer
    assert mic._latest(size) == pytest.approx([0.3] * size)
    mic._feed(array("f", [0.4, 0.5]))
    assert mic._latest(3) == pytest.approx([0.3, 0.4, 0.5])


def test_start_forgets_what_was_heard_before(fake):
    mic = f.microphone()
    mic.start()
    mic._feed(sine(440))
    mic.stop()
    mic.start()
    assert mic._latest(100) == [0.0] * 100


def test_capture_is_a_sound_of_what_was_fed(fake):
    mic = f.microphone()
    mic.start()
    values = sine(220, 1.0)
    mic._feed(values)
    snd = mic.capture(0.5)
    assert isinstance(snd, sound_module.Sound)
    assert len(snd.samples()) == RATE // 2
    assert snd.samples() == pytest.approx(values[-(RATE // 2):], abs=1e-6)
    assert snd.duration() == pytest.approx(0.5, abs=0.001)


def test_capture_works_after_stop_and_pads_with_silence(fake):
    mic = f.microphone()
    mic.start()
    mic._feed([0.5] * 1000)
    mic.stop()
    values = mic.capture(1).samples()
    assert len(values) == RATE
    assert values[-1000:] == pytest.approx([0.5] * 1000, abs=1e-4)
    assert values[0] == 0.0


def test_capture_more_than_ten_seconds_is_an_error(fake):
    mic = f.microphone()
    with pytest.raises(ValueError, match="at most 10"):
        mic.capture(11)
    for bad in (0, -1, "2", True):
        with pytest.raises(ValueError):
            mic.capture(bad)


def test_capture_of_ten_seconds_is_allowed(fake):
    assert len(f.microphone().capture(10).samples()) == 10 * RATE


def test_the_audio_thread_path_stores_a_chunk(fake):
    mic = f.microphone()
    mic.start()
    fake["opened"][0][1].callback(array("f", [0.25] * 4))
    assert mic._latest(4) == [0.25] * 4


def test_headless_gives_a_silent_microphone(monkeypatch):
    monkeypatch.setenv("FUNGROUND_HEADLESS", "1")
    monkeypatch.setattr(mi, "_device_names", lambda: pytest.fail("no device is asked for"))
    mic = f.microphone()
    mic.start()
    assert mic.is_listening()
    assert mic.level() == 0.0 and mic.pitch() is None and mic.spectrum(3) == [0.0] * 3
    assert len(mic.capture(0.1).samples()) == RATE // 10
    mic.stop()


def test_no_device_is_a_plain_error_with_the_mac_hint(monkeypatch):
    monkeypatch.delenv("FUNGROUND_HEADLESS", raising=False)
    monkeypatch.setattr(mi, "_device_names", lambda: [])
    with pytest.raises(RuntimeError, match="no microphone was found.*System Settings"):
        f.microphone()


def test_a_refused_device_is_a_plain_error(monkeypatch, fake):
    def refuse(name, callback):
        raise RuntimeError(mi._no_device_message("the microphone could not be opened (denied)"))

    monkeypatch.setattr(mi, "_open_capture", refuse)
    mic = f.microphone()
    with pytest.raises(RuntimeError, match="could not be opened.*System Settings"):
        mic.start()
    assert not mic.is_listening()


def test_open_capture_wraps_a_failed_open(monkeypatch):
    class Audio:
        AUDIO_F32 = 1
        AUDIO_ALLOW_FORMAT_CHANGE = 2

        class AudioDevice:
            def __init__(self, **kw):
                raise OSError("permission denied")

    monkeypatch.setattr(mi, "_sdl2_audio", lambda: Audio)
    with pytest.raises(RuntimeError, match="permission denied.*System Settings"):
        mi._open_capture(None, lambda chunk: None)


def test_open_capture_converts_16_bit_and_averages_channels(monkeypatch):
    got = []

    class Audio:
        AUDIO_F32 = 1
        AUDIO_ALLOW_FORMAT_CHANGE = 2

        class AudioDevice:
            audioformat = 99                      # not float: 16-bit
            numchannels = 2
            frequency = 44100

            def __init__(self, callback, **kw):
                self.callback = callback

    monkeypatch.setattr(mi, "_sdl2_audio", lambda: Audio)
    device, rate = mi._open_capture(None, got.append)
    pcm = array("h", [16384, 0, -16384, -16384])  # two frames of two channels
    device.callback(device, memoryview(pcm.tobytes()))
    assert rate == 44100
    assert list(got[0]) == pytest.approx([0.25, -0.5])


def test_a_missing_experimental_module_names_the_pygame_version(monkeypatch):
    import builtins

    real = builtins.__import__

    def fake_import(name, *args, **kw):
        if name == "pygame._sdl2.audio":
            raise ImportError("gone")
        return real(name, *args, **kw)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    with pytest.raises(RuntimeError, match="pygame-ce 2.5 or newer"):
        mi._sdl2_audio()


def test_a_microphone_adds_nothing_to_the_ir_or_pixels(fake):
    sketch = api.active_sketch()
    f.size(40, 30)
    f.background("white")
    before_ops = list(sketch.frame.ops)
    before_pixels = bytes(sketch._renderer.pixels().data)
    mic = f.microphone()
    mic.start()
    mic._feed(sine(440))
    mic.level()
    mic.spectrum()
    mic.pitch()
    mic.capture(0.1)
    mic.stop()
    assert list(sketch.frame.ops) == before_ops
    assert bytes(sketch._renderer.pixels().data) == before_pixels
