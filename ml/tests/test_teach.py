"""Tests of ``ml.teach()`` and ``ml.guess()`` (S-235, contract ML8) that need no model file and no network.

The picture model is a fake: a picture's vector is made from the colour of its first pixel, so pictures of the same colour are
alike. A gate lets a test hold the worker thread still, to see what happens while a picture is not yet a vector.
"""
from __future__ import annotations

import gc
import threading
import time

import numpy as np
import pytest

import funground_ml
from funground_ml import _fetch, _results, _tasks, _teach

from conftest import FakeCamera

DOWN = (200, 10, 10)        # a few colours that are far apart as vectors
UP = (10, 200, 10)
SIDE = (10, 10, 200)


def picture_of(rgb, width: int = 8, height: int = 6):
    from funground.picture import Picture

    red, green, blue = rgb
    return Picture.from_pixels(width, height, bytes([blue, green, red, 255]) * (width * height), "test")


def pictures(rgb, count: int) -> list:
    """*count* different pictures of one colour."""
    return [picture_of(rgb) for _ in range(count)]


def repaint(picture, rgb) -> None:
    """A new frame in the same Picture, as a camera makes one."""
    red, green, blue = rgb
    picture._write_pixels(bytes([blue, green, red, 255]) * (picture.width * picture.height))


def unit(values):
    vector = np.asarray(values, dtype=np.float64) + 1.0
    return (vector / np.linalg.norm(vector)).astype(np.float32)


class FakeModel:
    """The fake picture model. ``gate`` holds the worker still while it is cleared; ``seen`` is the colours it worked on."""

    def __init__(self) -> None:
        self.gate = threading.Event()
        self.gate.set()
        self.seen: list[tuple] = []
        self.loaded = 0
        self.error: BaseException | None = None

    def load(self, paths):
        self.loaded += 1
        if self.error is not None:
            raise self.error

        def vector(image):
            self.gate.wait(10)
            colour = image.getpixel((0, 0))
            self.seen.append(colour)
            return unit(colour)

        return vector


class Sketch:
    """Stands for the sketch the taught set belongs to."""


class Frames:
    number = 1

    def next(self) -> None:
        self.number += 1


@pytest.fixture(autouse=True)
def sketch(monkeypatch):
    """A new sketch for every test, so each starts with nothing taught."""
    holder = {"sketch": Sketch()}
    monkeypatch.setattr(_teach, "canvas_sketch", lambda: holder["sketch"])
    return holder


@pytest.fixture(autouse=True)
def frames(monkeypatch):
    counter = Frames()
    monkeypatch.setattr(_tasks, "_frame", lambda: counter.number)
    return counter


@pytest.fixture(autouse=True)
def model(monkeypatch):
    fake = FakeModel()
    for key in _teach.MODEL_NAMES:                  # both models are the fake; each keeps its own task
        monkeypatch.setitem(_teach.PICTURE_MODELS, key, _teach.PictureModel(_teach.PICTURE_MODELS[key].task, _teach.PICTURE_MODELS[key].size, fake.load))
    fake.downloads = []
    monkeypatch.setattr(_fetch, "ensure", lambda task, base_dir, who: fake.downloads.append((task, who)) or {})
    return fake


def settle() -> None:
    """Wait until every picture taught so far has its vector."""
    _teach._taught().worker.drain()


def wait_until(predicate, timeout: float = 10.0) -> bool:
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        if predicate():
            return True
        time.sleep(0.01)
    return False


def answer_for(camera, frames, k: int = 1):
    """Ask again each frame until a camera's guess arrives."""
    found = []

    def asked():
        frames.next()
        found[:] = [funground_ml.guess(camera, k)]
        return found[0] is not None

    assert wait_until(asked), "the worker gave no answer"
    return found[0]


def teach_three(count: int = 5) -> None:
    for _ in range(count):
        funground_ml.teach("down", picture_of(DOWN))
        funground_ml.teach("up", picture_of(UP))
        funground_ml.teach("side", picture_of(SIDE))


# ---- the names
def test_teach_and_guess_are_public_and_guess_is_a_result_class():
    assert funground_ml.__all__[-2:] == ["teach", "guess"]
    assert funground_ml.Guess is _results.Guess


def test_a_guess_says_its_name_and_prints_it():
    guess = _results.Guess("cat", 0.8333, (_results.Guess("dog", 0.2),))
    assert str(guess) == "cat" and guess.next[0].next == ()
    assert repr(guess) == "<Guess 'cat' score 0.83, next 'dog'>"
    assert repr(_results.Guess("dog", 0.2)) == "<Guess 'dog' score 0.20>"


# ---- arguments
@pytest.mark.parametrize("name, error", [(3, TypeError), (None, TypeError), (["a"], TypeError), ("", ValueError)])
def test_a_name_must_be_text_that_is_not_empty(name, error):
    with pytest.raises(error, match=r"ml\.teach\(\)"):
        funground_ml.teach(name, picture_of(DOWN))


def test_something_to_teach_must_be_a_camera_or_a_picture():
    with pytest.raises(TypeError, match=r"needs a camera from camera.open\(\) or a picture.*, not a str"):
        funground_ml.teach("cat", "a.png")
    with pytest.raises(TypeError, match=r"needs a camera or a picture to learn from after the name"):
        funground_ml.teach("cat")


def test_a_bad_item_in_a_list_names_its_position_and_nothing_before_it_is_taught():
    with pytest.raises(TypeError, match=r"item 2 of the list for \"cat\" is a int"):
        funground_ml.teach("cat", [picture_of(DOWN), FakeCamera(picture_of(UP)), 7])
    assert funground_ml.teach("cat", []) == 0                      # nothing was kept


def test_the_dict_form_takes_lists_and_nothing_else():
    with pytest.raises(TypeError, match=r"needs a list of cameras or pictures for \"cat\", not a Picture"):
        funground_ml.teach({"cat": picture_of(DOWN)})
    with pytest.raises(TypeError, match=r"item 1 of the list for \"dog\""):
        funground_ml.teach({"cat": [picture_of(DOWN)], "dog": [picture_of(UP), None]})
    with pytest.raises(ValueError, match="not empty"):
        funground_ml.teach({"": [picture_of(DOWN)]})
    with pytest.raises(TypeError, match="not both"):
        funground_ml.teach({"cat": [picture_of(DOWN)]}, picture_of(UP))


def test_the_model_is_one_of_two_names():
    with pytest.raises(ValueError, match=r'model must be "dinov2" or "mobilenet", not \'vit\''):
        funground_ml.teach("cat", picture_of(DOWN), model="vit")
    with pytest.raises(ValueError, match="mobilenet"):
        funground_ml.teach("cat", picture_of(DOWN), model=3)


@pytest.mark.parametrize("k, error", [(True, TypeError), (2.0, TypeError), ("2", TypeError), (None, TypeError),
                                      (0, ValueError), (-1, ValueError)])
def test_k_is_a_whole_number_of_at_least_one(k, error):
    with pytest.raises(error, match=r"ml\.guess\(\)"):
        funground_ml.guess(picture_of(DOWN), k)


def test_guess_wants_a_camera_or_a_picture_even_when_nothing_is_taught():
    with pytest.raises(TypeError, match=r"ml\.guess\(\) needs a camera"):
        funground_ml.guess("a.png")
    funground_ml.teach("cat", picture_of(DOWN))
    with pytest.raises(TypeError, match=r"ml\.guess\(\) needs a camera"):
        funground_ml.guess(3)


# ---- teaching
def test_teach_counts_the_examples_of_a_name_including_this_one():
    assert funground_ml.teach("cat", picture_of(DOWN)) == 1
    assert funground_ml.teach("cat", picture_of(DOWN)) == 2               # a Picture is always added
    assert funground_ml.teach("dog", picture_of(UP)) == 1
    assert funground_ml.teach("cat", picture_of(SIDE)) == 3


def test_the_list_form_teaches_each_item_in_order_and_the_dict_form_each_name():
    assert funground_ml.teach("cat", [picture_of(DOWN), picture_of(UP), FakeCamera(picture_of(SIDE))]) == 3
    assert funground_ml.teach({"dog": [picture_of(UP)], "cat": [picture_of(DOWN)], "bird": []}) == {"dog": 1, "cat": 4, "bird": 0}
    assert list(_teach._taught().names) == ["cat", "dog"]            # the order first taught; "bird" has nothing


def test_the_same_picture_and_version_taught_again_to_the_same_name_adds_nothing():
    picture = picture_of(DOWN)
    assert funground_ml.teach("cat", picture) == 1
    settle()
    assert funground_ml.teach("cat", picture) == 1
    assert funground_ml.teach("dog", picture) == 1                         # another name takes it
    settle()
    repaint(picture, UP)                                                   # a new version
    assert funground_ml.teach("cat", picture) == 2


def test_a_picture_redrawn_every_frame_teaches_one_at_a_time_as_a_camera_does(model):
    """D-148: a focus box is a Picture the sketch redraws each frame; holding a key must not queue one picture a frame."""
    model.gate.clear()                                                     # hold the thread, so the first stays pending
    box = picture_of(DOWN)
    assert funground_ml.teach("cat", box) == 1
    for colour in (UP, SIDE, DOWN):
        repaint(box, colour)
        assert funground_ml.teach("cat", box) == 1                         # still pending: nothing added
    assert funground_ml.teach("cat", [picture_of(UP), picture_of(SIDE)]) == 3   # other pictures are other sources
    model.gate.set()
    settle()
    repaint(box, UP)
    assert funground_ml.teach("cat", box) == 4


def test_a_camera_with_no_frame_yet_adds_nothing_and_makes_no_name():
    camera = FakeCamera(None)
    assert funground_ml.teach("cat", camera) == 0
    assert list(_teach._taught().names) == []
    camera.picture = picture_of(DOWN)
    assert funground_ml.teach("cat", camera) == 1


def test_a_camera_teaches_one_picture_at_a_time_and_the_count_stays_true(model):
    model.gate.clear()
    picture = picture_of(DOWN)
    camera = FakeCamera(picture)
    assert funground_ml.teach("cat", camera) == 1
    repaint(picture, UP)
    assert funground_ml.teach("cat", camera) == 1                                 # the last one is not a vector yet
    assert funground_ml.teach("dog", camera) == 0                                 # any name
    model.gate.set()
    settle()
    repaint(picture, SIDE)
    assert funground_ml.teach("dog", camera) == 1                                 # the next picture is taught
    settle()
    assert [len(v) for v in _teach._taught().names.values()] == [1, 1]
    assert model.seen == [DOWN, SIDE]                                      # the picture in between was never taught


def test_a_picture_is_added_even_while_a_camera_waits(model):
    model.gate.clear()
    camera = FakeCamera(picture_of(DOWN))
    funground_ml.teach("cat", camera)
    assert funground_ml.teach("cat", picture_of(UP)) == 2
    model.gate.set()
    settle()


def test_the_default_picture_model_is_mobilenet(model):
    assert _teach.DEFAULT_MODEL == "mobilenet"
    funground_ml.teach("cat", picture_of(DOWN))
    assert model.downloads == [("picture_mobilenet", "ml.teach()")]


def test_the_first_teach_fixes_the_picture_model_and_names_it_in_the_error(model):
    funground_ml.teach("cat", picture_of(DOWN), model="dinov2")
    assert model.downloads == [("picture_dinov2", "ml.teach()")]
    funground_ml.teach("cat", picture_of(UP))                              # None keeps the one in use
    with pytest.raises(ValueError, match=r'already teaches with the "dinov2" picture model, so it cannot also use "mobilenet"'):
        funground_ml.teach("cat", picture_of(SIDE), model="mobilenet")
    assert funground_ml.teach("cat", picture_of(SIDE), model="dinov2") == 3


def test_naming_mobilenet_first_fixes_it_and_dinov2_then_raises(model):
    funground_ml.teach("cat", picture_of(DOWN), model="mobilenet")
    with pytest.raises(ValueError, match=r'already teaches with the "mobilenet" picture model, so it cannot also use "dinov2"'):
        funground_ml.teach("cat", picture_of(SIDE), model="dinov2")
    assert funground_ml.teach("cat", picture_of(SIDE)) == 2


def test_the_model_is_fetched_once_in_the_sketchs_thread_and_a_failure_is_not_remembered(model, monkeypatch):
    def offline(task, base_dir, who):
        raise ConnectionError("no connection")

    monkeypatch.setattr(_fetch, "ensure", offline)
    with pytest.raises(ConnectionError):
        funground_ml.teach("cat", picture_of(DOWN))
    monkeypatch.setattr(_fetch, "ensure", lambda task, base_dir, who: model.downloads.append((task, who)) or {})
    funground_ml.teach("cat", picture_of(DOWN))
    funground_ml.teach("cat", picture_of(UP))
    settle()
    assert model.downloads == [("picture_mobilenet", "ml.teach()")] and model.loaded == 1


def test_the_picture_model_file_is_fetched_with_the_one_line_for_it(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv(_fetch.ENVIRONMENT, str(tmp_path))
    monkeypatch.undo()                                                       # the fake ensure goes; the env var must stay
    monkeypatch.setenv(_fetch.ENVIRONMENT, str(tmp_path))
    monkeypatch.setattr(_fetch, "_download", lambda *args: None)
    paths = _fetch.ensure("picture_mobilenet", None, "ml.teach()")
    assert capsys.readouterr().out.startswith("Downloading the picture model, 10 MB, once. After that funground uses the copy in ")
    assert paths["model"].endswith("mobilenetv4_conv_small_vector.onnx")


def test_both_picture_models_download_with_a_line_that_says_picture_model(tmp_path, monkeypatch, capsys):
    monkeypatch.undo()
    monkeypatch.setenv(_fetch.ENVIRONMENT, str(tmp_path))
    monkeypatch.setattr(_fetch, "_download", lambda *args: None)
    for task, size, file in (("picture_mobilenet", 10, "mobilenetv4_conv_small_vector.onnx"), ("picture_dinov2", 24, "dinov2_small_q8.onnx")):
        paths = _fetch.ensure(task, None, "ml.teach()")
        assert capsys.readouterr().out.startswith(f"Downloading the picture model, {size} MB, once.")
        assert paths["model"].endswith(file)


def test_a_new_sketch_starts_with_nothing_taught(sketch):
    funground_ml.teach("cat", picture_of(DOWN))
    sketch["sketch"] = Sketch()
    assert funground_ml.guess(picture_of(DOWN)) is None
    assert funground_ml.teach("cat", picture_of(DOWN)) == 1


def test_the_thread_ends_when_the_sketch_goes(sketch):
    funground_ml.teach("cat", picture_of(DOWN))
    settle()
    thread = _teach._taught().worker._thread
    sketch["sketch"] = Sketch()
    gc.collect()
    thread.join(5)
    assert not thread.is_alive()


# ---- guessing
def test_nothing_taught_gives_none_without_fetching_a_model(model):
    assert funground_ml.guess(picture_of(DOWN)) is None
    assert funground_ml.guess(FakeCamera(picture_of(DOWN))) is None
    assert model.downloads == []


def test_a_camera_with_no_frame_gives_none():
    funground_ml.teach("cat", picture_of(DOWN))
    assert funground_ml.guess(FakeCamera(None)) is None


def test_no_example_ready_gives_none_and_the_example_counts_once_it_is(model):
    model.gate.clear()
    picture = picture_of(DOWN)
    funground_ml.teach("cat", picture)
    result = []
    worker = threading.Thread(target=lambda: result.append(funground_ml.guess(picture)))
    worker.start()                                                          # on a computer a picture waits for the examples
    time.sleep(0.2)
    assert result == []
    model.gate.set()
    worker.join(10)
    assert result[0].name == "cat"


def test_a_picture_is_named_by_the_nearest_taught_name():
    teach_three(2)
    for colour, name in ((DOWN, "down"), (UP, "up"), (SIDE, "side")):
        guess = funground_ml.guess(picture_of(colour))
        assert guess.name == name and guess.score == 0.95 and guess.next == ()


def test_k_gives_the_next_names_each_once_nearest_first_and_fewer_when_fewer_are_taught():
    teach_three(2)
    guess = funground_ml.guess(picture_of((200, 100, 10)), k=3)                # between down and up, far from side
    assert [guess.name] + [g.name for g in guess.next] == ["down", "up", "side"] or guess.name in ("down", "up")
    assert len({guess.name, *(g.name for g in guess.next)}) == 3
    assert all(g.next == () for g in guess.next)
    assert guess.score >= 0.5 and all(0.05 <= g.score <= 0.5 for g in guess.next)
    assert len(funground_ml.guess(picture_of(DOWN), k=10).next) == 2


def test_a_name_is_judged_by_its_nearest_example_not_a_vote():
    funground_ml.teach("near", picture_of(DOWN))
    funground_ml.teach("far", [picture_of(UP), picture_of(UP), picture_of(UP), picture_of((120, 120, 10))])
    assert funground_ml.guess(picture_of(DOWN)).name == "near"


def test_equal_similarities_put_the_name_taught_first_first():
    funground_ml.teach("second-in-the-alphabet", picture_of(DOWN))
    funground_ml.teach("first-in-the-alphabet", picture_of(DOWN))
    guess = funground_ml.guess(picture_of(DOWN), k=2)
    assert guess.name == "second-in-the-alphabet" and guess.next[0].name == "first-in-the-alphabet"
    assert guess.score == guess.next[0].score == 0.5


def test_a_picture_never_seen_still_gets_the_nearest_name():
    teach_three(1)
    assert funground_ml.guess(picture_of((120, 120, 120))) is not None


# ---- the score
def similarities(*pairs):
    return _teach._Similarities(sorted(pairs, key=lambda pair: -pair[1]))


def test_the_score_is_half_plus_half_the_margin_over_a_tenth_between_005_and_095():
    result = similarities(("a", 0.80), ("b", 0.75), ("c", 0.30)).guess(3)
    assert result.name == "a" and result.score == pytest.approx(0.5 + 0.5 * 0.05 / 0.1)       # 0.75
    assert result.next[0].score == pytest.approx(0.25)                                         # 0.75 against a's 0.80
    assert result.next[1].score == 0.05                                                         # far behind: the floor
    assert similarities(("a", 0.90), ("b", 0.20)).guess(1).score == 0.95                      # far ahead: the ceiling


def test_two_names_taught_have_scores_that_add_up_to_one():
    for lead in (0.0, 0.01, 0.04, 0.09, 0.2, 0.7):
        result = similarities(("a", 0.5 + lead), ("b", 0.5)).guess(2)
        assert result.score + result.next[0].score == pytest.approx(1.0)


def test_one_name_taught_scores_half_with_nothing_next():
    result = similarities(("a", 0.3)).guess(5)
    assert (result.name, result.score, result.next) == ("a", 0.5, ())


def test_the_guess_is_cut_from_the_same_similarities_for_every_k():
    result = similarities(("a", 0.8), ("b", 0.7), ("c", 0.1))
    assert result.guess(2) is result.guess(2) and result.guess(2).score == result.guess(3).score
    assert result.guess(1).next == ()


# ---- the hints
def test_one_name_taught_prints_its_line_once_per_sketch(capsys, sketch):
    funground_ml.teach("cat", pictures(DOWN, 1) + pictures(UP, 5))
    guess = funground_ml.guess(picture_of(DOWN))
    assert (guess.name, guess.score, guess.next) == ("cat", 0.5, ())
    assert capsys.readouterr().out.splitlines()[0] == "Teach at least two things, so I can compare."
    funground_ml.guess(picture_of(UP))
    assert capsys.readouterr().out == ""
    sketch["sketch"] = Sketch()                                              # a new run says it again
    funground_ml.teach("cat", picture_of(DOWN))
    funground_ml.guess(picture_of(DOWN))
    assert "Teach at least two things" in capsys.readouterr().out


def test_few_examples_names_the_name_with_the_fewest_and_the_first_taught_on_a_tie(capsys):
    funground_ml.teach("thumbs up", pictures(DOWN, 2))
    funground_ml.teach("thumbs down", pictures(UP, 2))
    funground_ml.teach("flat", pictures(SIDE, 6))
    funground_ml.guess(picture_of(DOWN))
    assert capsys.readouterr().out == '"thumbs up" has 2 examples. 5 or more of each makes better guesses.\n'
    funground_ml.guess(picture_of(DOWN))
    assert capsys.readouterr().out == ""


def test_one_example_is_said_in_the_singular(capsys):
    funground_ml.teach("cat", pictures(DOWN, 1))
    funground_ml.teach("dog", pictures(UP, 6))
    funground_ml.guess(picture_of(DOWN))
    assert capsys.readouterr().out == '"cat" has 1 example. 5 or more of each makes better guesses.\n'


def test_five_examples_of_each_name_prints_nothing(capsys):
    teach_three(5)
    funground_ml.guess(picture_of(DOWN))
    assert capsys.readouterr().out == ""


# ---- cameras
def test_a_camera_gets_none_until_the_first_answer_then_a_guess(frames):
    teach_three(2)
    settle()
    camera = FakeCamera(picture_of(UP))
    assert funground_ml.guess(camera) is None
    assert answer_for(camera, frames).name == "up"


def test_two_calls_in_a_frame_give_the_same_guess_and_every_k_is_cut_from_the_same_similarities(frames):
    teach_three(2)
    camera = FakeCamera(picture_of(UP))
    funground_ml.guess(camera)
    answer_for(camera, frames)
    first, three = funground_ml.guess(camera), funground_ml.guess(camera, 3)
    assert funground_ml.guess(camera) is first and funground_ml.guess(camera, 3) is three
    assert (first.name, first.score) == (three.name, three.score)
    frames.next()
    assert funground_ml.guess(camera) is first                                # the same picture and taught set: the same answer
    repaint(camera.picture, DOWN)
    assert wait_until(lambda: (frames.next(), funground_ml.guess(camera))[1] not in (None, first))


def test_the_answer_changes_when_the_camera_shows_something_else(frames):
    teach_three(2)
    camera = FakeCamera(picture_of(UP))
    assert answer_for(camera, frames).name == "up"
    repaint(camera.picture, DOWN)
    assert wait_until(lambda: (frames.next(), funground_ml.guess(camera).name)[1] == "down")


def test_a_guess_after_teaching_is_fresh_even_in_the_same_frame(frames):
    teach_three(1)
    camera = FakeCamera(picture_of(UP))
    first = answer_for(camera, frames)
    funground_ml.teach("fourth", picture_of(UP))
    assert funground_ml.guess(camera) is not first
    assert funground_ml.guess(camera) is funground_ml.guess(camera)


def test_only_the_newest_frame_waits_and_the_worker_does_not_wait_for_draw(model, frames):
    teach_three(1)
    settle()
    model.seen.clear()
    model.gate.clear()
    picture = picture_of(UP)
    camera = FakeCamera(picture)
    funground_ml.guess(camera)                                                # taken by the worker, held at the gate
    assert wait_until(lambda: _teach._taught().worker._looks == {})
    for colour in (DOWN, SIDE, UP):                                           # three frames while it is busy
        repaint(picture, colour)
        frames.next()
        started = time.monotonic()
        assert funground_ml.guess(camera) is None
        assert time.monotonic() - started < 1.0
    model.gate.set()
    answer_for(camera, frames)
    assert wait_until(lambda: len(model.seen) == 2)
    assert model.seen == [UP, UP]                                             # the first frame, then only the newest


def test_teaching_goes_before_guessing(model, frames):
    model.gate.clear()
    first = picture_of(DOWN)
    funground_ml.teach("a", first)
    assert wait_until(lambda: _teach._taught().worker._working)
    camera = FakeCamera(picture_of(SIDE))
    funground_ml.guess(camera)                                                # waits for a turn
    funground_ml.teach("b", picture_of(UP))                                   # queued after it, but goes first
    model.gate.set()
    assert wait_until(lambda: len(model.seen) == 3)
    assert model.seen == [DOWN, UP, SIDE]


# ---- errors in the thread
def test_an_error_in_the_thread_is_raised_by_the_next_call_in_the_sketchs_thread(model):
    model.error = RuntimeError("the model is broken")
    funground_ml.teach("cat", picture_of(DOWN))                                # queued: teach never waits
    assert wait_until(lambda: _teach._taught().worker._error is not None)
    with pytest.raises(RuntimeError, match="the model is broken"):
        funground_ml.teach("cat", picture_of(UP))
    assert funground_ml.teach("cat", picture_of(UP)) == 1                      # the example that failed is not counted


def test_an_error_stops_a_guess_that_waits_instead_of_leaving_it_waiting_for_ever(model):
    model.error = RuntimeError("the model is broken")
    funground_ml.teach("cat", picture_of(DOWN))
    with pytest.raises(RuntimeError, match="the model is broken"):
        funground_ml.guess(picture_of(UP))


def test_an_error_is_raised_by_a_camera_guess_too(model):
    model.error = RuntimeError("the model is broken")
    funground_ml.teach("cat", picture_of(DOWN))
    assert wait_until(lambda: _teach._taught().worker._error is not None)
    with pytest.raises(RuntimeError, match="the model is broken"):
        funground_ml.guess(FakeCamera(picture_of(UP)))
