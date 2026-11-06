"""Tests of ``ml.sound()`` that need no model file: the names and the rules for choosing them, the Heard object, the windows of a
microphone, the thread beside the sketch (with a stand-in for the model), the host path and the errors (S-250, contract ML7)."""
from __future__ import annotations

import gc
import math
import re
import struct
import threading
import time
import weakref
from array import array

import pytest

import funground_ml
from funground import host_services, sound
from funground.platform.browser_models import HostModels, SoundResult
from funground_ml import _fetch, _hearing, _listen, _results, _sound, _sound_names, _tasks, _yamnet
from funground_ml._results import Heard

from test_host import Page, _run

SETUP = {"model": "m"}
NAMES = _sound_names.NAMES


def scores_of(by_name: dict | None = None, **named) -> list[float]:
    """521 scores, all 0 but the named ones: ``scores_of(Dog=0.8)``, or a dict for a name with spaces or commas."""
    values = [0.0] * len(NAMES)
    for name, score in {**(by_name or {}), **named}.items():
        values[NAMES.index(name)] = score
    return values


def tone(seconds: float, rate: int, amplitude: float = 0.5) -> array:
    return array("f", (amplitude * math.sin(2 * math.pi * 300 * i / rate) for i in range(round(seconds * rate))))


def quiet(seconds: float, rate: int) -> array:
    return array("f", bytes(4 * round(seconds * rate)))


# ---- the names
def test_the_table_has_521_different_names_in_the_models_order():
    assert len(NAMES) == 521 and len(set(NAMES)) == 521
    assert NAMES[0] == "Speech" and NAMES[494] == "Silence" and NAMES[132] == "Music"


def test_the_header_says_where_the_names_came_from_and_the_credit():
    header = _sound_names.__doc__
    assert "audiomagic/yamnet-onnx" in header and "f25b741c2f0bdc6d7e6db24b5fddda23347dbafd" in header
    assert re.search(r"SHA-256\s+cdf24d19[0-9a-f]{52}6df2", header)
    assert "CC BY 4.0" in header and "AudioSet" in header and "Google LLC" in header


def test_every_hidden_name_is_one_of_the_521_and_speech_music_and_silence_stay():
    assert len(_sound.HIDDEN) == 15
    assert _sound.HIDDEN <= set(NAMES)
    assert not {"Speech", "Music", "Silence"} & _sound.HIDDEN
    assert "Animal" in _sound.HIDDEN and "Sound effect" in _sound.HIDDEN and "Outside, rural or natural" in _sound.HIDDEN


# ---- choosing
def test_the_best_name_and_up_to_four_more_likeliest_first():
    found = _sound.choose(scores_of(Dog=0.8, Bark=0.5, Growling=0.3, Howl=0.2, Yip=0.15, Cat=0.1))
    assert [name for name, _ in found] == ["Dog", "Bark", "Growling", "Howl", "Yip"]          # five: Cat is the sixth
    assert [score for _, score in found] == [0.8, 0.5, 0.3, 0.2, 0.15]


def test_the_model_scores_every_name_so_the_next_four_are_always_given():
    found = _sound.choose(scores_of(Dog=0.6))
    assert found[0] == ("Dog", 0.6) and len(found) == 5


def test_silence_as_the_likeliest_name_of_all_gives_nothing():
    assert _sound.choose(scores_of(Silence=0.6, Dog=0.3)) is None
    assert _sound.choose(scores_of(Silence=0.2, Dog=0.3)) is not None          # Silence is not first


def test_the_likeliest_name_of_all_decides_about_silence_even_a_hidden_one_above_it():
    # Animal (hidden) is above Silence: Silence is still the likeliest name shown, so there is nothing to name
    assert _sound.choose(scores_of(Animal=0.7, Silence=0.5, Dog=0.2)) is None


def test_silence_is_never_one_of_the_next_guesses():
    found = _sound.choose(scores_of(Dog=0.7, Silence=0.5, Bark=0.2))
    assert [name for name, _ in found][:2] == ["Dog", "Bark"]
    assert "Silence" not in [name for name, _ in found]


def test_the_broad_names_are_hidden_and_speech_and_music_are_not():
    values = scores_of(Animal=0.9, Vehicle=0.8, Mechanisms=0.7, Speech=0.5, Music=0.4)
    found = _sound.choose(values)
    names = [name for name, _ in found]
    assert names[:2] == ["Speech", "Music"] and not set(names) & _sound.HIDDEN
    for hidden in _sound.HIDDEN:                          # alone, a hidden name is never given
        assert _sound.choose(scores_of({hidden: 0.9, "Dog": 0.05})) is None


def test_a_best_shown_name_under_one_tenth_gives_nothing_and_exactly_one_tenth_is_enough():
    assert _sound.choose(scores_of(Dog=0.09, Animal=0.9)) is None
    assert _sound.choose(scores_of(Dog=0.0999)) is None
    assert _sound.choose(scores_of(Dog=0.1))[0] == ("Dog", 0.1)


def test_a_tie_keeps_the_models_order():
    found = _sound.choose(scores_of(Speech=0.4, Music=0.4))
    assert [name for name, _ in found][:2] == ["Speech", "Music"]


def test_choose_wants_521_scores():
    with pytest.raises(ValueError, match="521"):
        _sound.choose([0.5] * 10)


def test_nothing_to_name_when_every_score_is_zero():
    assert _sound.choose([0.0] * 521) is None


# ---- the level rule
def test_a_window_whose_loudest_30_ms_is_under_the_level_is_quiet():
    rate = 8000
    assert _sound.is_quiet(quiet(0.96, rate), rate)
    assert _sound.is_quiet(tone(0.96, rate, 0.02), rate)                     # level 0.014: under 0.02
    assert not _sound.is_quiet(tone(0.96, rate, 0.04), rate)                 # level 0.028
    assert _sound.is_quiet([], rate)


def test_one_loud_block_among_quiet_ones_is_enough():
    rate = 8000
    window = quiet(0.96, rate)
    window[4000:4000 + 240] = tone(0.03, rate, 0.5)
    assert not _sound.is_quiet(window, rate)


# ---- the Heard object
def test_a_heard_says_its_name_and_what_it_is():
    heard = Heard("Dog", 0.8, (Heard("Bark", 0.5),), is_new=True)
    assert str(heard) == "Dog" and heard.name == "Dog" and heard.score == 0.8 and heard.is_new
    assert [str(g) for g in heard.next] == ["Bark"] and heard.next[0].next == () and not heard.next[0].is_new
    assert repr(heard) == "<Heard 'Dog' score 0.80, next 'Bark', new>"
    assert repr(Heard("Dog", 0.8)) == "<Heard 'Dog' score 0.80>"


def test_a_heard_made_from_guesses_has_the_rest_as_its_next():
    heard = Heard.from_guesses([("A", 0.9), ("B", 0.5), ("C", 0.2)], is_new=True)
    assert heard.name == "A" and [g.name for g in heard.next] == ["B", "C"]
    assert all(not g.is_new and g.next == () for g in heard.next)


def test_the_public_names_are_pose_hand_person_words_and_sound():
    assert funground_ml.__all__ == ["pose", "hand", "person", "words", "sound"]
    assert funground_ml.Heard is _results.Heard


# ---- the newest answer, frame by frame
def guesses(name="Dog"):
    return [(name, 0.8), ("Bark", 0.5)]


def test_an_answer_is_new_for_the_whole_of_the_frame_it_first_shows_and_not_after():
    latest = _hearing.Latest()
    assert latest.heard(1) is None
    latest.offer(guesses())
    first = latest.heard(2)
    assert first.is_new and latest.heard(2) is first
    later = latest.heard(3)
    assert later.name == "Dog" and not later.is_new and latest.heard(3) is later and [g.name for g in later.next] == ["Bark"]


def test_an_answer_that_comes_in_the_middle_of_a_frame_shows_from_the_next_frame():
    latest = _hearing.Latest()
    latest.offer(guesses("Dog"))
    shown = latest.heard(1)
    latest.offer(guesses("Cat"))
    assert latest.heard(1) is shown and shown.name == "Dog"
    assert latest.heard(2).name == "Cat" and latest.heard(2).is_new


def test_the_same_name_twice_in_a_row_is_a_new_answer_each_time():
    latest = _hearing.Latest()
    latest.offer(guesses())
    latest.heard(1)
    latest.heard(2)
    latest.offer(guesses())
    assert latest.heard(3).is_new


def test_nothing_to_name_takes_the_old_answer_off_the_screen():
    latest = _hearing.Latest()
    latest.offer(guesses())
    assert latest.heard(1) is not None
    latest.offer(None)
    assert latest.heard(2) is None and latest.heard(3) is None


# ---- ml.sound on a computer, with a stand-in for the model
class Model:
    """Stands in for YAMNet: answers each window with the scores the test gives, and records what it was asked."""

    def __init__(self, answer=None):
        self.answer = answer if answer is not None else scores_of(Dog=0.8, Bark=0.5)
        self.asked = []

    def load(self, paths):
        return self

    def scores(self, samples, rate):
        self.asked.append((len(samples), rate, threading.current_thread()))
        if isinstance(self.answer, Exception):
            raise self.answer
        return self.answer


@pytest.fixture
def model(monkeypatch):
    stand_in = Model()
    monkeypatch.setattr(_fetch, "ensure", lambda task, base_dir, who: dict(SETUP))
    monkeypatch.setattr(_yamnet, "load", stand_in.load)
    return stand_in


class Frames:
    number = 1

    def next(self):
        self.number += 1


@pytest.fixture
def frames(monkeypatch):
    counter = Frames()
    monkeypatch.setattr(_tasks, "_frame", lambda: counter.number)
    return counter


def microphone():
    mic = sound.microphone()
    mic.start()
    return mic


def wait_for(mic, frames, predicate=lambda found: found is not None, timeout=5.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        frames.next()
        found = funground_ml.sound(mic)
        if predicate(found):
            return found
        time.sleep(0.01)
    raise AssertionError("the answer never came")


def test_something_that_is_not_a_microphone_or_a_sound_is_a_plain_type_error(model):
    with pytest.raises(TypeError, match=r"ml\.sound\(\) needs a microphone from sound\.microphone\(\) or a sound, not str\."):
        funground_ml.sound("dog.wav")


def test_a_sound_longer_than_thirty_seconds_is_a_value_error_in_one_sentence(model):
    long = sound.create([0.0] * 44100, 44100)
    long._duration = 31.0
    with pytest.raises(ValueError) as error:
        funground_ml.sound(long)
    text = str(error.value)
    assert text.count(".") == 3 and "31 seconds" in text and "30 seconds" in text and text.startswith("ml.sound():")


def test_a_microphone_that_has_not_heard_a_second_gives_none_and_does_no_work(model, frames):
    mic = microphone()
    assert funground_ml.sound(mic) is None
    mic._feed(tone(0.9, mic._rate))
    frames.next()
    assert funground_ml.sound(mic) is None and model.asked == []


def test_the_first_answer_comes_after_0_96_seconds_from_the_last_0_96_seconds_in_another_thread(model, frames):
    mic = microphone()
    funground_ml.sound(mic)
    mic._feed(tone(0.96, mic._rate))
    found = wait_for(mic, frames)
    assert isinstance(found, Heard) and found.name == "Dog" and found.score == 0.8 and found.is_new
    assert [g.name for g in found.next] == ["Bark", "Speech", "Child speech, kid speaking", "Conversation"]
    count, rate, thread = model.asked[0]
    assert (count, rate) == (round(0.96 * mic._rate), mic._rate) and thread.daemon and thread is not threading.current_thread()


def test_a_new_window_is_worked_on_every_half_second_of_sound(model, frames):
    mic = microphone()
    funground_ml.sound(mic)
    mic._feed(tone(0.96, mic._rate))
    wait_for(mic, frames)
    for _ in range(2):
        mic._feed(tone(0.2, mic._rate))
        frames.next()
        funground_ml.sound(mic)
    time.sleep(0.2)
    assert len(model.asked) == 1                                            # 0.4 s more: the next window is 0.48 s after the first
    mic._feed(tone(0.1, mic._rate))
    frames.next()
    funground_ml.sound(mic)
    deadline = time.monotonic() + 3
    while len(model.asked) < 2 and time.monotonic() < deadline:
        time.sleep(0.01)
    assert len(model.asked) == 2
    assert model.asked[1][0] == round(0.96 * mic._rate)                     # always the last 0.96 s


def test_a_quiet_window_is_not_sent_to_the_model_and_takes_the_old_answer_away(model, frames):
    mic = microphone()
    funground_ml.sound(mic)
    mic._feed(tone(0.96, mic._rate))
    assert wait_for(mic, frames).name == "Dog"
    mic._feed(quiet(1.0, mic._rate))
    assert wait_for(mic, frames, lambda found: found is None) is None
    assert len(model.asked) <= 2                                           # windows that held some of the tone may have been sent
    asked = len(model.asked)
    mic._feed(quiet(1.0, mic._rate))
    frames.next()
    assert funground_ml.sound(mic) is None and len(model.asked) == asked


def test_silence_as_the_models_answer_gives_none(model, frames):
    model.answer = scores_of(Silence=0.9)
    mic = microphone()
    funground_ml.sound(mic)
    mic._feed(tone(0.96, mic._rate))
    frames.next()
    funground_ml.sound(mic)
    time.sleep(0.3)
    frames.next()
    assert funground_ml.sound(mic) is None and len(model.asked) == 1


def test_a_low_score_gives_none(model, frames):
    model.answer = scores_of(Dog=0.05)
    mic = microphone()
    funground_ml.sound(mic)
    mic._feed(tone(0.96, mic._rate))
    frames.next()
    funground_ml.sound(mic)
    time.sleep(0.3)
    frames.next()
    assert funground_ml.sound(mic) is None and len(model.asked) == 1


def test_a_microphone_that_is_stopped_gives_none_and_a_window_still_being_worked_on_is_dropped(model, frames):
    release = threading.Event()
    original = model.scores

    def slow(samples, rate):
        release.wait(5)
        return original(samples, rate)

    model.scores = slow
    mic = microphone()
    funground_ml.sound(mic)
    mic._feed(tone(0.96, mic._rate))
    frames.next()
    funground_ml.sound(mic)
    time.sleep(0.1)
    mic.stop()
    frames.next()
    assert funground_ml.sound(mic) is None
    release.set()
    time.sleep(0.3)
    frames.next()
    assert funground_ml.sound(mic) is None                                  # the late answer belongs to the listening that ended


def test_starting_again_forgets_what_was_heard_and_needs_a_second_again(model, frames):
    mic = microphone()
    funground_ml.sound(mic)
    mic._feed(tone(0.96, mic._rate))
    wait_for(mic, frames)
    mic.stop()
    mic.start()
    frames.next()
    assert funground_ml.sound(mic) is None
    mic._feed(tone(0.5, mic._rate))
    frames.next()
    asked = len(model.asked)
    assert funground_ml.sound(mic) is None and len(model.asked) == asked
    mic._feed(tone(0.46, mic._rate))
    assert wait_for(mic, frames).name == "Dog"


def test_the_same_answer_twice_in_a_frame_and_is_new_only_in_the_first_frame(model, frames):
    mic = microphone()
    funground_ml.sound(mic)
    mic._feed(tone(0.96, mic._rate))
    first = wait_for(mic, frames)
    assert funground_ml.sound(mic) is first
    frames.next()
    again = funground_ml.sound(mic)
    assert again.name == "Dog" and not again.is_new and funground_ml.sound(mic) is again


def test_a_silent_microphone_gives_none(model, frames):
    mic = sound.microphone()                              # FUNGROUND_HEADLESS=1: silent
    mic.start()
    for _ in range(5):
        frames.next()
        assert funground_ml.sound(mic) is None
        time.sleep(0.05)
    assert model.asked == []
    mic = sound.microphone()                              # not listening
    assert funground_ml.sound(mic) is None


def test_an_error_in_the_model_is_raised_in_the_sketch_on_a_later_call(model, frames):
    model.answer = RuntimeError("the model broke")
    mic = microphone()
    funground_ml.sound(mic)
    mic._feed(tone(0.96, mic._rate))
    with pytest.raises(RuntimeError, match="the model broke"):
        wait_for(mic, frames)


def test_a_sound_is_answered_at_once_in_the_sketchs_thread_and_kept(model, frames):
    clip = sound.create(list(tone(2.0, 22050)), 22050)
    found = funground_ml.sound(clip)
    assert found.name == "Dog" and found.is_new and funground_ml.sound(clip) is found
    count, rate, thread = model.asked[0]
    assert (rate, thread) == (22050, threading.current_thread()) and abs(count - 44100) <= 2
    frames.next()
    later = funground_ml.sound(clip)
    assert later.name == "Dog" and not later.is_new
    assert len(model.asked) == 1                                           # asking again does no work


def test_a_sound_and_a_microphone_with_nothing_to_name_give_none_and_are_not_asked_again(model, frames):
    model.answer = scores_of(Silence=0.9)
    clip = sound.create(list(tone(1.0, 22050)), 22050)
    assert funground_ml.sound(clip) is None
    frames.next()
    assert funground_ml.sound(clip) is None and len(model.asked) == 1


def test_words_and_sound_keep_their_own_answers_for_one_sound(model, frames, monkeypatch):
    from funground_ml import _whisper

    class Whisper:
        def transcribe(self, samples, rate):
            return "hello", 0.9

    monkeypatch.setattr(_whisper, "load", lambda paths: Whisper())
    clip = sound.create(list(tone(1.0, 22050)), 22050)
    assert funground_ml.words(clip).text == "hello"
    assert funground_ml.sound(clip).name == "Dog"
    frames.next()
    assert funground_ml.words(clip).text == "hello" and funground_ml.sound(clip).name == "Dog"


def test_the_memory_does_not_keep_a_microphone_or_a_sound_alive_and_the_thread_ends(model, frames):
    mic = microphone()
    clip = sound.create([0.1] * 44100, 44100)
    funground_ml.sound(mic)
    mic._feed(tone(0.96, mic._rate))
    wait_for(mic, frames)
    funground_ml.sound(clip)
    refs = weakref.ref(mic), weakref.ref(clip)
    threads = [t for t in threading.enumerate() if t.name == "funground sound"]
    assert threads and all(t.daemon for t in threads)
    del mic, clip
    gc.collect()
    assert refs[0]() is None and refs[1]() is None
    deadline = time.monotonic() + 3
    while any(t.is_alive() for t in threads) and time.monotonic() < deadline:
        time.sleep(0.02)
    assert not any(t.is_alive() for t in threads)


def test_the_download_line_names_the_sound_model_and_its_true_size(monkeypatch, tmp_path, capsys):
    monkeypatch.setenv(_fetch.ENVIRONMENT, str(tmp_path))
    monkeypatch.setattr(_fetch, "_checked", set())

    def stop(*args, **kwargs):
        raise ConnectionError("no network in tests")

    monkeypatch.setattr(_fetch, "_download", stop)
    with pytest.raises(ConnectionError):
        _fetch.ensure("sound", None, "ml.sound()")
    assert "Downloading the sound model, 16 MB, once." in capsys.readouterr().out


def test_the_model_is_pinned():
    from funground_ml import _models

    model = _models.MODELS["sound_model"]
    assert model.url == ("https://huggingface.co/funground-hq/yamnet-onnx/resolve/9648eed1cf043f9163842e9cb6d5fd8291d0d1cf/yamnet.onnx")
    assert (model.size, model.licence) == (16093355, "Apache-2.0")
    assert model.sha256 == "d3835ffbbd4a1bb3e777f0ca217b5007907f5171dd5d17c4236b95b2af8f908e"
    assert _models.TASKS["sound"] == ("sound_model",) and _models.ROLES["sound"] == ("model",)


# ---- the host path (a web page)
def test_sound_scores_come_back_as_float32_bytes_for_a_window_that_is_in_flight():
    models = HostModels(lambda command, fields: None)
    values = scores_of(Dog=0.8125, Bark=0.5)
    data = struct.pack(f"<{len(values)}f", *values)
    models.push_sound_scores("sound", 4, data)
    assert models.latest("sound", 4) is None and models.generation == 0                 # not in flight: ignored
    models.request_sound("sound", 4, bytes(8), 8000)
    models.push_sound_scores("sound", 4, data)
    found = models.latest("sound", 4)
    assert isinstance(found, SoundResult) and found.scores == tuple(values) and models.generation == 1
    assert models.request_sound("sound", 4, bytes(8), 8000) is True


def test_sound_scores_must_be_whole_float32_numbers():
    models = HostModels(lambda command, fields: None)
    models.request_sound("sound", 4, bytes(8), 8000)
    with pytest.raises(ValueError, match="float32 bytes"):
        models.push_sound_scores("sound", 4, bytes(7))
    models.request_sound("sound", 5, bytes(8), 8000)
    models.push_sound_scores("sound", 5, [0.25, 0.5])                                    # a plain list of numbers is also fine
    assert models.latest("sound", 5).scores == (0.25, 0.5)


@pytest.fixture
def page():
    stand_in = Page()
    host_services.models = stand_in.models
    try:
        yield stand_in
    finally:
        host_services.models = None


def ask(source):
    return funground_ml.sound(source)


def push(page, key, **named):
    values = scores_of(**named)
    page.models.push_sound_scores("sound", key, struct.pack("<521f", *values))


def test_a_window_goes_to_the_page_every_half_second_and_the_scores_come_back(page, frames):
    mic = microphone()
    mic._rate = 8000
    assert funground_ml.sound(mic) is None and page.requests() == []
    mic._feed(tone(0.96, 8000))
    frames.next()
    assert funground_ml.sound(mic) is None
    [request] = page.requests()
    assert (request["task"], request["key"], request["rate"]) == ("sound", id(mic), 8000)
    assert len(request["samples"]) == 4 * round(0.96 * 8000)
    push(page, id(mic), Dog=0.8, Bark=0.5)
    frames.next()
    found = funground_ml.sound(mic)
    assert isinstance(found, Heard) and (found.name, found.score, found.is_new) == ("Dog", pytest.approx(0.8), True)
    assert funground_ml.sound(mic) is found
    frames.next()
    assert funground_ml.sound(mic).name == "Dog" and not funground_ml.sound(mic).is_new


def test_a_quiet_window_is_not_sent_to_the_page_and_still_clears_the_answer_in_order(page, frames):
    mic = microphone()
    mic._rate = 8000
    funground_ml.sound(mic)
    mic._feed(tone(0.96, 8000))
    frames.next()
    funground_ml.sound(mic)                                                              # the window is in flight
    mic._feed(quiet(0.96, 8000))
    frames.next()
    funground_ml.sound(mic)                                                              # a quiet one waits behind it
    assert len(page.requests()) == 1
    push(page, id(mic), Dog=0.8)
    frames.next()
    assert funground_ml.sound(mic) is None                                               # the answer came and the quiet cleared it
    assert len(page.requests()) == 1


def test_the_newest_window_waits_while_one_is_in_flight(page, frames):
    mic = microphone()
    mic._rate = 8000
    funground_ml.sound(mic)
    mic._feed(tone(0.96, 8000))
    frames.next()
    funground_ml.sound(mic)
    for _ in range(3):
        mic._feed(tone(0.5, 8000))
        frames.next()
        funground_ml.sound(mic)
    assert len(page.requests()) == 1
    push(page, id(mic), Dog=0.8)
    frames.next()
    assert funground_ml.sound(mic).name == "Dog"
    assert len(page.requests()) == 2


def test_a_stopped_microphone_drops_the_answer_of_a_window_in_flight(page, frames):
    mic = microphone()
    mic._rate = 8000
    funground_ml.sound(mic)
    mic._feed(tone(0.96, 8000))
    frames.next()
    funground_ml.sound(mic)
    mic.stop()
    frames.next()
    assert funground_ml.sound(mic) is None
    push(page, id(mic), Dog=0.8)
    frames.next()
    assert funground_ml.sound(mic) is None


def test_a_sound_is_sent_once_whole_and_gives_none_until_the_answer_arrives(page, frames):
    clip = sound.create(list(tone(1.0, 22050)), 22050)
    assert ask(clip) is None
    [request] = page.requests()
    assert (request["key"], request["rate"], len(request["samples"])) == (id(clip), 22050, 4 * 22050)
    frames.next()
    assert ask(clip) is None and len(page.requests()) == 1
    push(page, id(clip), Dog=0.8)
    frames.next()
    found = ask(clip)
    assert found.name == "Dog" and found.is_new and len(page.requests()) == 1
    assert ask(clip) is found


def test_a_quiet_answer_for_a_sound_in_a_page_is_none(page, frames):
    clip = sound.create(list(tone(1.0, 22050)), 22050)
    ask(clip)
    push(page, id(clip), Silence=0.9)
    frames.next()
    assert ask(clip) is None


def test_without_a_page_that_listens_nothing_is_sent_and_there_is_no_answer(page, frames):
    page.models._on_models = None
    clip = sound.create(list(tone(1.0, 22050)), 22050)
    assert ask(clip) is None and page.requests() == []


def test_the_host_path_for_sound_imports_no_numpy_pillow_or_desktop_module():
    code = (
        "import sys, struct\n"
        "from funground import host_services, sound\n"
        "from funground.platform.browser_models import HostModels\n"
        "from funground import ml\n"
        "import funground_ml._tasks as tasks\n"
        "frame = [1]\n"
        "tasks._frame = lambda: frame[0]\n"
        "page = []\n"
        "host_services.models = HostModels(lambda command, fields: page.append((command, fields)))\n"
        "clip = sound.create([0.1] * 4410, 44100)\n"
        "assert ml.sound(clip) is None\n"
        "scores = [0.0] * 521\n"
        "scores[0] = 0.9\n"
        "host_services.models.push_sound_scores('sound', page[0][1]['key'], struct.pack('<521f', *scores))\n"
        "frame[0] += 1\n"
        "assert ml.sound(clip).name == 'Speech'\n"
        "gone = [name for name in ('onnxruntime', 'numpy', 'PIL', 'funground_ml._runtime', 'funground_ml._yamnet', 'funground_ml._fetch') if name in sys.modules]\n"
        "print('imported:', gone)\n"
    )
    done = _run(code)
    assert done.returncode == 0, done.stderr
    assert done.stdout.strip().splitlines()[-1] == "imported: []"
