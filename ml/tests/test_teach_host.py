"""Tests of ``ml.teach()`` and ``ml.guess()`` in a web page (S-235, contract ML8): the page makes the vectors.

A recording ``on_models`` stands for the page. A test answers a job by pushing the vector of the picture's colour, as float32 bytes,
the way the page's worker does.
"""
from __future__ import annotations

import struct

import pytest

import funground_ml
from funground import host_services
from funground.platform.browser_models import HostModels
from funground_ml import _teach

from conftest import FakeCamera
from test_teach import DOWN, SIDE, UP, picture_of, repaint

COLOURS = {DOWN: (1.0, 0.0, 0.0), UP: (0.0, 1.0, 0.0), SIDE: (0.0, 0.0, 1.0)}
SIZES = {entry.task: entry.size for entry in _teach.PICTURE_MODELS.values()}     # the length of each task's real vector


class Sketch:
    pass


class Page:
    """Stands for the page: it records the requests and answers jobs when the test says so."""

    def __init__(self) -> None:
        self.asked: list[tuple[str, dict]] = []
        self.models = HostModels(lambda command, fields: self.asked.append((command, fields)))
        self.answered = 0

    def requests(self) -> list[dict]:
        return [fields for command, fields in self.asked if command == "request"]

    def colour_of(self, request: dict) -> tuple:
        return tuple(request["pixels"][:3])

    def answer(self, request: dict, size: int | None = None) -> None:
        """Push the vector of the colour of the request's first pixel (RGBA bytes), as float32 bytes: its three numbers, then
        zeros up to the length of the task's real vector (or *size* numbers in all), which changes no similarity."""
        red, green, blue = request["pixels"][0], request["pixels"][1], request["pixels"][2]
        vector = COLOURS[(red, green, blue)]
        size = size or SIZES[request["task"]]
        self.models.push_vector(request["task"], request["key"], struct.pack(f"<{size}f", *vector, *[0.0] * (size - 3)))

    def answer_all(self) -> None:
        for request in self.requests()[self.answered:]:
            self.answer(request)
        self.answered = len(self.requests())


class Frames:
    number = 1

    def next(self) -> None:
        self.number += 1


@pytest.fixture(autouse=True)
def sketch(monkeypatch):
    holder = {"sketch": Sketch()}
    monkeypatch.setattr(_teach, "canvas_sketch", lambda: holder["sketch"])
    return holder


@pytest.fixture(autouse=True)
def frames(monkeypatch):
    counter = Frames()
    from funground_ml import _tasks

    monkeypatch.setattr(_tasks, "_frame", lambda: counter.number)
    return counter


@pytest.fixture
def page(monkeypatch):
    stand_in = Page()
    monkeypatch.setattr(host_services, "models", stand_in.models)
    return stand_in


def teach_three(count: int = 5) -> None:
    for _ in range(count):
        funground_ml.teach("down", picture_of(DOWN))
        funground_ml.teach("up", picture_of(UP))
        funground_ml.teach("side", picture_of(SIDE))


# ---- teaching
def test_each_picture_is_one_request_with_a_job_number_the_task_the_pixels_and_the_size(page):
    funground_ml.teach("a", [picture_of(DOWN), picture_of(UP), picture_of(SIDE)])
    sent = page.requests()
    assert [r["key"] for r in sent] == [1, 2, 3]
    assert {r["task"] for r in sent} == {"picture_mobilenet"}
    assert (sent[0]["width"], sent[0]["height"]) == (8, 6)
    assert sent[0]["pixels"] == bytes([200, 10, 10, 255]) * 48          # RGBA, row by row


def test_dinov2_is_asked_for_when_it_is_chosen(page):
    funground_ml.teach("a", picture_of(DOWN), model="dinov2")
    assert [r["task"] for r in page.requests()] == ["picture_dinov2"]


def test_nothing_is_downloaded_here_and_nothing_is_dropped_for_being_busy(page, monkeypatch):
    from funground_ml import _fetch

    monkeypatch.setattr(_fetch, "ensure", lambda *a: pytest.fail("the page downloads its own model"))
    for _ in range(20):
        funground_ml.teach("a", picture_of(DOWN))
        funground_ml.teach("b", picture_of(UP))
    assert len(page.requests()) == 40
    assert [r["key"] for r in page.requests()] == list(range(1, 41))


def test_the_count_includes_examples_that_are_pending(page):
    assert funground_ml.teach("a", [picture_of(DOWN), picture_of(UP)]) == 2
    assert funground_ml.teach({"a": [picture_of(SIDE)], "b": [picture_of(UP)]}) == {"a": 3, "b": 1}


def test_a_camera_teaches_nothing_while_its_last_picture_is_pending(page):
    camera = FakeCamera(picture_of(DOWN))
    assert funground_ml.teach("a", camera) == 1
    repaint(camera.picture, UP)
    assert funground_ml.teach("a", camera) == 1 and len(page.requests()) == 1
    page.answer_all()
    assert funground_ml.teach("a", camera) == 2 and len(page.requests()) == 2


def test_the_same_picture_and_version_is_taught_once(page):
    picture = picture_of(DOWN)
    funground_ml.teach("a", picture)
    funground_ml.teach("a", picture)
    assert len(page.requests()) == 1


# ---- guessing a camera
def test_vectors_that_come_back_make_the_guess_right(page, frames):
    teach_three()
    camera = FakeCamera(picture_of(UP))
    assert guess_of(camera) is None                                           # no example has a vector yet
    page.answer_all()
    frames.next()
    result = guess_of(camera)
    assert result.name == "up" and result.score == 0.95
    assert [g.name for g in guess_of(camera, 3).next] == ["down", "side"]


def guess_of(source, k=1):
    return funground_ml.guess(source, k)


def test_a_camera_has_one_job_in_flight_and_the_newest_frame_waits_for_its_answer(page, frames):
    teach_three(1)
    page.answer_all()
    camera = FakeCamera(picture_of(DOWN))
    guess_of(camera)
    assert len(page.requests()) == 4                                       # three examples and the camera's first frame
    for colour in (UP, SIDE, UP):                                          # newer frames: only the newest is kept waiting
        frames.next()
        repaint(camera.picture, colour)
        guess_of(camera)
    assert len(page.requests()) == 4
    page.answer_all()
    frames.next()
    assert guess_of(camera).name == "down"                                    # the first frame's answer; the waiting one is sent now
    sent = page.requests()
    assert len(sent) == 5 and page.colour_of(sent[4]) == UP                # the newest frame, not SIDE
    page.answer_all()
    frames.next()
    assert guess_of(camera).name == "up"
    assert len(page.requests()) == 5                                       # nothing waiting, so nothing more is sent


# ---- guessing a picture
def test_a_picture_guess_is_none_until_its_vector_comes_and_it_is_asked_once(page, frames):
    teach_three(1)
    page.answer_all()
    picture = picture_of(SIDE)
    assert guess_of(picture) is None
    assert len(page.requests()) == 4
    frames.next()
    assert guess_of(picture) is None and len(page.requests()) == 4            # asked once for this picture and version
    page.answer_all()
    frames.next()
    assert guess_of(picture).name == "side"
    assert len(page.requests()) == 4
    repaint(picture, UP)                                                   # a new version is asked for again
    frames.next()
    assert guess_of(picture).name == "side" and len(page.requests()) == 5   # the newest answer, one behind (D-148)
    page.answer_all()
    frames.next()
    assert guess_of(picture).name == "up"


def test_a_picture_redrawn_every_frame_has_one_job_in_flight_and_does_not_flood_the_page(page, frames):
    """D-148: in a page a Picture goes the camera's way, so a focus box redrawn each frame sends one picture at a time."""
    teach_three(1)
    page.answer_all()
    box = picture_of(DOWN)
    for colour in (UP, SIDE, DOWN, UP):
        repaint(box, colour)
        guess_of(box)
        frames.next()
    assert len(page.requests()) == 4                                       # three taught, and one guess in flight
    page.answer_all()
    frames.next()
    assert guess_of(box) is not None and len(page.requests()) == 5         # the newest frame was waiting, and is sent now


# ---- the page cannot run the model
def test_when_the_page_cannot_run_the_model_examples_fail_the_sentence_prints_once_and_guess_is_none(page, frames, capsys):
    assert funground_ml.teach("a", [picture_of(DOWN), picture_of(UP)]) == 2
    page.models.unavailable("picture_mobilenet", "Could not download the picture model.")
    page.models.unavailable("picture_mobilenet", "Could not download the picture model.")
    assert funground_ml.teach("a", picture_of(SIDE)) == 0                  # the old two fail; the new one is not even sent
    assert capsys.readouterr().out == "Could not download the picture model.\n"
    frames.next()
    assert guess_of(picture_of(DOWN)) is None
    assert guess_of(FakeCamera(picture_of(DOWN))) is None
    assert len(page.requests()) == 2


def test_a_vector_of_the_wrong_length_from_the_page_is_an_error_not_a_quiet_wrong_guess(page):
    funground_ml.teach("a", picture_of(DOWN))
    page.answer(page.requests()[0], size=384)                              # a DINOv2-sized vector for the MobileNetV4 task
    with pytest.raises(RuntimeError, match="384 numbers for picture_mobilenet; funground expects 1280"):
        funground_ml.guess(picture_of(DOWN))


# ---- the run ends
def test_close_forgets_the_vectors_in_flight(page):
    funground_ml.teach("a", picture_of(DOWN))
    page.models.close()
    page.answer_all()                                                      # a late answer from the old run
    assert page.models.take_vector("picture_mobilenet", 1) is None
    assert page.asked[-1][0] == "close"

