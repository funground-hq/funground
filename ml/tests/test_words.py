"""Tests of ``ml.words()`` that need no model file: the phrase cutter, the token decoder, the resampling, the Words object, the
thread beside the sketch (with a stand-in for the model), and the errors (S-234, contract ML6)."""
from __future__ import annotations

import gc
import json
import math
import threading
import time
import weakref
from array import array

import numpy as np
import pytest

import funground_ml
from funground import sound
from funground_ml import _fetch, _listen, _speech, _tasks, _whisper
from funground_ml._results import Words

from conftest import FakeCamera, solid_picture

RATE = 8000                      # a low rate keeps the synthetic sounds small; the cutter takes any rate
SETUP = {"encoder": "e", "decoder": "d", "vocabulary": "v"}


def tone(seconds: float, amplitude: float = 0.5, rate: int = RATE) -> array:
    """A 300 Hz sine of the given length (its level, the RMS, is amplitude / sqrt(2))."""
    return array("f", (amplitude * math.sin(2 * math.pi * 300 * i / rate) for i in range(round(seconds * rate))))


def quiet(seconds: float, rate: int = RATE) -> array:
    return array("f", bytes(4 * round(seconds * rate)))


def length(phrase: array, rate: int = RATE) -> float:
    return len(phrase) / rate


# ---- the cutter
def test_silence_gives_no_phrase():
    assert _speech.PhraseCutter(RATE).feed(quiet(5)) == []


def test_a_burst_then_a_pause_is_one_phrase_with_the_pause_that_ended_it():
    phrases = _speech.PhraseCutter(RATE).feed(quiet(1) + tone(1) + quiet(1))
    assert len(phrases) == 1
    # a little quiet before (3 blocks of 30 ms), the second of sound, and the 0.6 s of quiet that ended it
    assert 1.6 < length(phrases[0]) < 1.8
    assert max(phrases[0]) > 0.4


def test_a_phrase_that_has_not_ended_is_not_given_yet_and_is_given_when_the_pause_is_long_enough():
    cutter = _speech.PhraseCutter(RATE)
    assert cutter.feed(tone(1)) == [] and cutter.is_open
    assert cutter.feed(quiet(0.5)) == []                      # 0.5 s of quiet is not 0.6 s
    assert len(cutter.feed(quiet(0.2))) == 1 and not cutter.is_open


def test_a_sound_shorter_than_three_tenths_of_a_second_is_ignored():
    assert _speech.PhraseCutter(RATE).feed(tone(0.2) + quiet(1)) == []
    assert len(_speech.PhraseCutter(RATE).feed(tone(0.4) + quiet(1))) == 1


def test_a_sound_under_the_level_is_not_speech_and_one_over_it_is():
    assert _speech.PhraseCutter(RATE).feed(tone(1, 0.02) + quiet(1)) == []          # level 0.014
    assert len(_speech.PhraseCutter(RATE).feed(tone(1, 0.04) + quiet(1))) == 1      # level 0.028


def test_a_pause_inside_a_phrase_is_kept_and_a_long_pause_splits_it():
    assert len(_speech.PhraseCutter(RATE).feed(tone(1) + quiet(0.4) + tone(1) + quiet(1))) == 1
    assert len(_speech.PhraseCutter(RATE).feed(tone(1) + quiet(0.8) + tone(1) + quiet(1))) == 2


def test_a_phrase_is_cut_at_ten_seconds_and_the_rest_starts_a_new_one():
    phrases = _speech.PhraseCutter(RATE).feed(tone(25) + quiet(1))
    assert [round(length(p)) for p in phrases] == [10, 10, 6]


def test_the_pieces_can_be_any_size():
    sound_in = quiet(0.5) + tone(1) + quiet(1) + tone(0.7) + quiet(1)
    whole = _speech.PhraseCutter(RATE).feed(sound_in)
    cutter, pieces = _speech.PhraseCutter(RATE), []
    for at in range(0, len(sound_in), 337):                     # not a multiple of the 30 ms block
        pieces += cutter.feed(sound_in[at:at + 337])
    assert len(whole) == len(pieces) == 2
    assert [list(p) for p in pieces] == [list(p) for p in whole]


def test_flush_ends_the_open_phrase_and_forgets_a_short_one():
    cutter = _speech.PhraseCutter(RATE)
    cutter.feed(tone(1))
    assert length(cutter.flush()) > 0.9 and not cutter.is_open
    assert cutter.flush() is None
    cutter.feed(tone(0.1))
    assert cutter.flush() is None


def test_the_numbers_are_the_contracts():
    assert (_speech.START_LEVEL, _speech.END_SILENCE_SECONDS, _speech.MIN_PHRASE_SECONDS, _speech.MAX_PHRASE_SECONDS,
            _speech.BLOCK_SECONDS, _speech.MIN_SCORE, _speech.MAX_SOUND_SECONDS, _speech.MAX_TOKENS) == (
        0.02, 0.6, 0.3, 10.0, 0.03, 0.4, 30, 224)


# ---- the token decoder
def test_the_byte_table_is_gpt2s():
    table = _speech._bytes_to_characters()
    assert len(set(table.values())) == 256
    assert table[ord("a")] == "a" and table[ord("~")] == "~"
    assert table[32] == "Ġ" and table[10] == "Ċ" and table[0] == "Ā"
    assert table[0xAD] == "Ń" and table[0xA1] == "¡"


def test_pieces_join_into_text_and_a_space_is_the_g_with_a_dot():
    vocabulary = ["Hello", ",", "Ġworld", "!", "Ġ"]
    assert _speech.decode([0, 1, 2, 3], vocabulary) == "Hello, world!"
    assert _speech.decode([4, 0, 4], vocabulary) == "Hello"               # no space at either end


def test_numbers_at_or_above_the_end_of_text_are_skipped():
    vocabulary = ["a", "b"]
    assert _speech.decode([0, 50256, 1, 50257, 50362], vocabulary) == "ab"


def test_a_character_made_of_two_pieces_comes_out_whole():
    # "e with an acute accent" is the two bytes C3 A9, which the table shows as two characters; here two pieces share it.
    assert _speech.decode([0, 1], ["Ã", "©"]) == "é"
    assert _speech.decode([0], ["Ã"]) == "�"                      # half of one is not lost silently


def test_the_vocabulary_is_a_list_indexed_by_number(tmp_path):
    path = tmp_path / "vocab.json"
    path.write_text(json.dumps({"b": 2, "a": 0, "Ġc": 1}), encoding="utf-8")
    assert _speech.load_vocabulary(str(path)) == ["a", "Ġc", "b"]


# ---- resampling and the log-mel
def reference_resample(x, rate):
    """The documented formula, one sample at a time."""
    out = []
    for j in range(len(x) * 16000 // rate):
        p = j * rate / 16000
        i = math.floor(p)
        t = p - i
        out.append(x[i] * (1 - t) + x[min(i + 1, len(x) - 1)] * t)
    return out


@pytest.mark.parametrize("rate", [44100, 48000, 22050, 8000])
def test_resampling_follows_the_documented_formula(rate):
    x = [math.sin(i * 0.05) + 0.1 * math.cos(i * 0.7) for i in range(3000)]
    got = _whisper.to_model_rate(x, rate)
    want = reference_resample(x, rate)
    assert got.dtype == np.float32 and len(got) == len(want)
    assert np.allclose(got, want, atol=1e-5)


def test_resampling_at_16k_changes_nothing_and_an_empty_sound_stays_empty():
    x = [0.1, -0.2, 0.3]
    assert list(_whisper.to_model_rate(x, 16000)) == pytest.approx(x)
    assert len(_whisper.to_model_rate([], 44100)) == 0


def test_the_log_mel_of_silence_is_flat_and_the_size_the_encoder_expects():
    picture = _whisper.log_mel(np.zeros(16000, np.float32))
    assert picture.shape == (1, 80, 3000) and picture.dtype == np.float32
    assert np.allclose(picture, -1.5)                                        # log10(1e-10) = -10, (-10 + 4) / 4
    assert _whisper.log_mel(np.zeros(16000 * 40, np.float32)).shape == (1, 80, 3000)       # past 30 s is cut


def test_a_tone_lights_up_the_bands_around_its_pitch():
    t = np.arange(16000 * 2) / 16000
    picture = _whisper.log_mel((0.5 * np.sin(2 * np.pi * 1000 * t)).astype(np.float32))[0]
    rows = picture[:, 100]                                                   # a column in the middle of the tone
    assert 25 < int(rows.argmax()) < 40                                      # 1000 Hz is near the middle of the mel scale
    assert picture[:, 2500].max() < rows.max()                               # and the silence after it is dimmer


# ---- Words
def test_words_say_their_text_and_what_they_are():
    words = Words("Hello there.", 0.91)
    assert (words.text, words.score, words.is_new) == ("Hello there.", 0.91, False)
    assert str(words) == "Hello there."
    assert repr(words) == "<Words 'Hello there.' score 0.91>"
    assert repr(Words("Hi", 0.5, is_new=True)) == "<Words 'Hi' score 0.50, new>"
    assert len(repr(Words("word " * 50, 0.9))) < 80


# ---- what the sketch sees of an answer
def test_an_answer_is_new_for_the_whole_of_the_frame_it_first_shows_and_not_after():
    heard = _listen.Heard()
    assert heard.words(1) is None
    heard.offer("Hello", 0.9)
    first = heard.words(2)
    assert first.text == "Hello" and first.is_new
    assert heard.words(2) is first                                          # the same object, twice in a frame
    later = heard.words(3)
    assert later.text == "Hello" and not later.is_new
    assert heard.words(3) is later and heard.words(4) is later              # nothing changed: no new object


def test_an_answer_that_comes_in_the_middle_of_a_frame_shows_from_the_next_frame():
    heard = _listen.Heard()
    heard.offer("One", 0.9)
    one = heard.words(1)
    heard.offer("Two", 0.9)
    assert heard.words(1) is one                                            # still frame 1
    two = heard.words(2)
    assert two.text == "Two" and two.is_new and one.is_new                  # the object the sketch kept does not change under it


def test_an_answer_that_is_not_words_is_dropped_and_the_last_one_stays():
    heard = _listen.Heard()
    heard.offer("Thank you.", 0.39)
    heard.offer("   ", 0.99)
    heard.offer("", 0.99)
    assert heard.words(1) is None
    heard.offer("Hello", 0.4)                                               # 0.4 is enough
    assert heard.words(2).text == "Hello"
    heard.offer("Noise", 0.1)
    heard.offer("", 0.9)
    assert heard.words(3).text == "Hello" and not heard.words(3).is_new


def test_the_text_is_trimmed():
    heard = _listen.Heard()
    heard.offer("  Hello. \n", 0.9)
    assert heard.words(1).text == "Hello."


# ---- the worker thread
def test_the_worker_does_the_newest_phrase_and_forgets_the_ones_it_passed():
    started, release, done = threading.Event(), threading.Event(), []

    def transcribe(samples, rate):
        done.append(samples[0])
        started.set()
        release.wait(5)
        return f"phrase {samples[0]:.0f}", 0.9

    worker = _listen.Worker(transcribe)
    worker.submit(array("f", [1.0]), RATE)
    assert started.wait(5)
    worker.submit(array("f", [2.0]), RATE)                                  # waits while 1 is worked on
    worker.submit(array("f", [3.0]), RATE)                                  # takes 2's place
    release.set()
    answers = []
    deadline = time.monotonic() + 5
    while len(answers) < 2 and time.monotonic() < deadline:
        answers += worker.collect()
        time.sleep(0.01)
    assert answers == [("phrase 1", 0.9), ("phrase 3", 0.9)] and done == [1.0, 3.0]
    worker.close()


def test_an_error_in_the_thread_is_raised_by_the_next_call_and_only_once():
    def transcribe(samples, rate):
        raise RuntimeError("the model broke")

    worker = _listen.Worker(transcribe)
    worker.submit(array("f", [0.5]), RATE)
    deadline = time.monotonic() + 5
    with pytest.raises(RuntimeError, match="the model broke"):
        while time.monotonic() < deadline:
            worker.collect()
            time.sleep(0.01)
    assert worker.collect() == []
    worker.close()


def test_the_thread_is_a_daemon_and_starts_with_the_first_phrase():
    seen = []
    worker = _listen.Worker(lambda samples, rate: seen.append(threading.current_thread()) or ("hi", 0.9))
    assert worker._thread is None
    worker.submit(array("f", [0.5]), RATE)
    deadline = time.monotonic() + 5
    while not seen and time.monotonic() < deadline:
        time.sleep(0.01)
    assert seen[0].daemon and seen[0] is not threading.current_thread()
    worker.close()


# ---- ml.words on a computer, with a stand-in for the model
class Model:
    """Stands in for Whisper: answers each phrase with the text the test gives, and records what it was asked."""

    def __init__(self, answer=("hello there", 0.9)):
        self.answer, self.asked = answer, []

    def load(self, paths):
        return self

    def transcribe(self, samples, rate):
        self.asked.append((len(samples), rate, threading.current_thread()))
        if isinstance(self.answer, Exception):
            raise self.answer
        return self.answer


@pytest.fixture
def model(monkeypatch):
    stand_in = Model()
    monkeypatch.setattr(_fetch, "ensure", lambda task, base_dir, who: dict(SETUP))
    monkeypatch.setattr(_whisper, "load", stand_in.load)
    return stand_in


class Frames:
    """The sketch's frame count, moved by the test."""
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


def say(mic, seconds: float = 1.0):
    """Play the microphone some speech, then enough quiet to end the phrase."""
    mic._feed(tone(seconds, rate=mic._rate))
    mic._feed(quiet(0.8, rate=mic._rate))


def wait_for_words(mic, frames, timeout=5.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        frames.next()
        found = funground_ml.words(mic)
        if found is not None:
            return found
        time.sleep(0.01)
    raise AssertionError("no words arrived")


def test_something_that_is_not_a_microphone_or_a_sound_is_a_plain_type_error(model):
    for source in (FakeCamera(solid_picture()), solid_picture(), "hello", None, 3):
        with pytest.raises(TypeError, match=r"ml\.words\(\) needs a microphone from sound\.microphone\(\) or a sound, not "):
            funground_ml.words(source)
    assert model.asked == []


def test_a_sound_longer_than_thirty_seconds_is_a_value_error_in_one_sentence(model):
    long_one = sound.create([0.0] * (44100 * 31), 44100)
    with pytest.raises(ValueError, match=r"ml\.words\(\): this sound is 31 seconds long, and the most it can listen to is 30 seconds"):
        funground_ml.words(long_one)
    assert model.asked == []
    funground_ml.words(sound.create([0.1] * (44100 * 30), 44100))            # exactly 30 s is fine


def test_a_microphone_that_has_heard_nothing_gives_none_and_does_no_work(model, frames):
    mic = microphone()
    assert funground_ml.words(mic) is None
    mic._feed(quiet(2, rate=mic._rate))
    frames.next()
    assert funground_ml.words(mic) is None and model.asked == []


def test_a_phrase_is_worked_on_in_another_thread_and_the_words_arrive_later(model, frames):
    mic = microphone()
    assert funground_ml.words(mic) is None
    say(mic)
    found = wait_for_words(mic, frames)
    assert isinstance(found, Words) and found.text == "hello there" and found.score == 0.9 and found.is_new
    count, rate, thread = model.asked[0]
    assert rate == mic._rate and thread.daemon and thread is not threading.current_thread()
    assert 1.5 < count / rate < 1.8


def test_the_first_call_downloads_in_the_callers_thread(monkeypatch, model, frames):
    callers = []
    monkeypatch.setattr(_fetch, "ensure", lambda task, base_dir, who: callers.append(threading.current_thread()) or dict(SETUP))
    funground_ml.words(microphone())
    assert callers == [threading.current_thread()]


def test_the_download_line_names_the_words_model_and_its_true_size(monkeypatch, tmp_path, capsys):
    kept = tmp_path / "kept"
    monkeypatch.setenv(_fetch.ENVIRONMENT, str(kept))
    monkeypatch.setattr(_fetch, "_checked", set())
    monkeypatch.setattr(_fetch, "_download", lambda model, target, who, folder_word: None)
    paths = _fetch.ensure("words", None, "ml.words()")
    assert set(paths) == {"encoder", "decoder", "vocabulary"}
    assert capsys.readouterr().out == f"Downloading the words model, 42 MB, once. After that funground uses the copy in {kept}/.\n"


def test_the_same_words_twice_in_a_frame_and_is_new_only_in_the_first_frame(model, frames):
    mic = microphone()
    funground_ml.words(mic)
    say(mic)
    first = wait_for_words(mic, frames)
    assert first.is_new and funground_ml.words(mic) is first and funground_ml.words(mic) is first
    frames.next()
    second = funground_ml.words(mic)
    assert second.text == first.text and not second.is_new and funground_ml.words(mic) is second


def test_a_second_thing_said_gives_new_words(model, frames):
    mic = microphone()
    funground_ml.words(mic)
    say(mic)
    wait_for_words(mic, frames)
    model.answer = ("and again", 0.8)
    say(mic)
    deadline = time.monotonic() + 5
    found = None
    while time.monotonic() < deadline:
        frames.next()
        found = funground_ml.words(mic)
        if found.text == "and again":
            break
        time.sleep(0.01)
    assert found.text == "and again" and found.is_new


def test_low_scores_and_empty_text_are_dropped_and_the_last_words_stay(model, frames):
    mic = microphone()
    funground_ml.words(mic)
    say(mic)
    assert wait_for_words(mic, frames).text == "hello there"
    for dropped in (("you", 0.2), ("", 0.99)):
        model.answer, asked = dropped, len(model.asked)
        say(mic)
        deadline = time.monotonic() + 5
        while len(model.asked) == asked and time.monotonic() < deadline:
            frames.next()
            funground_ml.words(mic)
            time.sleep(0.01)
        time.sleep(0.05)
        frames.next()
        assert funground_ml.words(mic).text == "hello there"


def test_a_microphone_that_is_stopped_gives_the_last_words_and_a_phrase_open_at_the_stop_is_finished(model, frames):
    mic = microphone()
    funground_ml.words(mic)
    mic._feed(tone(1, rate=mic._rate))
    frames.next()
    assert funground_ml.words(mic) is None                                  # still speaking: the phrase has not ended
    mic.stop()
    found = wait_for_words(mic, frames)                                     # stopping ended it
    assert found.text == "hello there"
    frames.next()
    assert funground_ml.words(mic).text == "hello there"                    # not listening: the last words


def test_starting_again_clears_the_buffer_and_listening_goes_on(model, frames):
    mic = microphone()
    funground_ml.words(mic)
    say(mic)
    wait_for_words(mic, frames)
    mic.stop()
    mic.start()                                                             # the buffer starts again at zero
    model.answer = ("second run", 0.9)
    say(mic)
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        frames.next()
        if funground_ml.words(mic).text == "second run":
            break
        time.sleep(0.01)
    assert funground_ml.words(mic).text == "second run"


def test_a_sketch_that_looks_rarely_catches_up_with_what_the_buffer_holds(model, frames):
    mic = microphone()
    funground_ml.words(mic)
    mic._feed(tone(2, rate=mic._rate))
    mic._feed(quiet(1, rate=mic._rate))
    mic._feed(tone(1.5, rate=mic._rate))
    mic._feed(quiet(1, rate=mic._rate))
    assert wait_for_words(mic, frames).text == "hello there"
    time.sleep(0.2)
    assert 1 <= len(model.asked) <= 2                                       # both phrases were cut; the newest never waits behind


def test_an_error_in_the_model_is_raised_in_the_sketch_on_a_later_call(model, frames):
    model.answer = RuntimeError("the model broke")
    mic = microphone()
    funground_ml.words(mic)
    say(mic)
    with pytest.raises(RuntimeError, match="the model broke"):
        wait_for_words(mic, frames)


def test_a_sound_is_answered_at_once_in_the_sketchs_thread_and_kept(model, frames):
    clip = sound.create(tone(2, rate=44100).tolist(), 44100)
    first = funground_ml.words(clip)
    assert first.text == "hello there" and first.is_new
    assert model.asked[0][2] is threading.current_thread() and model.asked[0][1] == 44100 and model.asked[0][0] == 88200
    assert funground_ml.words(clip) is first and len(model.asked) == 1       # asking again does no work
    frames.next()
    later = funground_ml.words(clip)
    assert later.text == "hello there" and not later.is_new and len(model.asked) == 1


def test_a_sound_with_no_words_in_it_gives_none_and_is_not_asked_again(model, frames):
    model.answer = ("", 0.0)
    clip = sound.create([0.0] * 44100, 44100)
    assert funground_ml.words(clip) is None
    frames.next()
    assert funground_ml.words(clip) is None and len(model.asked) == 1


def test_two_microphones_do_not_share_answers(model, frames):
    first, second = microphone(), microphone()
    funground_ml.words(first), funground_ml.words(second)
    say(first)
    assert wait_for_words(first, frames).text == "hello there"
    frames.next()
    assert funground_ml.words(second) is None


def test_the_memory_does_not_keep_a_microphone_or_a_sound_alive(model, frames):
    mic = microphone()
    clip = sound.create([0.1] * 4410, 44100)
    funground_ml.words(mic)
    funground_ml.words(clip)
    refs = weakref.ref(mic), weakref.ref(clip)
    del mic, clip
    gc.collect()
    assert refs[0]() is None and refs[1]() is None


# ---- a model stuck in a loop (S-257, D-131)
def test_a_piece_or_a_pair_said_four_times_is_a_loop_and_the_first_is_kept():
    assert _speech.loop_tail([1, 2, 7, 7, 7, 7]) == 3
    assert _speech.loop_tail([1, 7, 8, 7, 8, 7, 8, 7, 8]) == 6


def test_three_times_is_not_a_loop_and_nor_is_ordinary_speech():
    assert _speech.loop_tail([7, 7, 7]) == 0
    assert _speech.loop_tail([7, 8, 7, 8, 7, 8]) == 0
    assert _speech.loop_tail([1, 2, 3, 4, 5, 6, 7, 8]) == 0
    assert _speech.loop_tail([]) == 0


def test_the_limit_on_pieces_follows_the_length_of_the_sound():
    assert _speech.token_limit(0.3) == _speech.MIN_TOKENS
    assert _speech.token_limit(7.2) == 72
    assert _speech.token_limit(30) == _speech.MAX_TOKENS


class ScriptedDecoder:
    """Stands in for the decoder: it chooses these pieces in turn, then "end", and counts how often it was run."""

    def __init__(self, pieces):
        self.pieces, self.runs = list(pieces) + [_speech.END_OF_TEXT], 0

    def run(self, _outputs, _inputs):
        logits = np.zeros((1, 1, 51864), np.float32)
        logits[0, 0, self.pieces[min(self.runs, len(self.pieces) - 1)]] = 20.0
        self.runs += 1
        return [logits]


def words_the_model_may_say(count):
    return [n for n in range(1000, 2000) if n not in _speech.SUPPRESSED][:count]


def scripted_whisper(pieces):
    """A Whisper with no model files. Piece n of the vocabulary reads " wn", with the model's mark for a space."""
    whisper = object.__new__(_whisper.Whisper)
    whisper._encoder = type("Encoder", (), {"run": lambda self, _outputs, _inputs: [np.zeros((1, 1500, 384), np.float32)]})()
    whisper._decoder, whisper._past_names, whisper._present_names = ScriptedDecoder(pieces), [], []
    whisper._vocabulary = [f"Ġw{n}" for n in range(_speech.END_OF_TEXT)]
    whisper._suppressed = np.array(_speech.SUPPRESSED)
    return whisper


def test_the_loop_stops_at_the_repeat_and_keeps_the_words_before_it():
    whisper = scripted_whisper([1000, 1001] + [1002] * 200)
    text, score = whisper.transcribe(np.zeros(16000 * 10, np.float32), 16000)
    assert text == "w1000 w1001 w1002"
    assert whisper._decoder.runs == 6                          # stopped as soon as it was sure, not after 100 pieces
    assert score > 0.99


def test_words_without_a_loop_are_all_kept():
    pieces = words_the_model_may_say(50)
    whisper = scripted_whisper(pieces)
    text, _ = whisper.transcribe(np.zeros(16000 * 10, np.float32), 16000)
    assert text.split() == [f"w{n}" for n in pieces]


def test_a_short_sound_cannot_give_a_long_answer():
    whisper = scripted_whisper(words_the_model_may_say(200))
    text, _ = whisper.transcribe(np.zeros(16000, np.float32), 16000)
    assert len(text.split()) == _speech.MIN_TOKENS
