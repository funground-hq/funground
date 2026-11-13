"""Tests of ``ml.teach()`` and ``ml.guess()`` that run the real MobileNetV4-small and DINOv2-small files on the test photographs (data/SOURCES.md).

The file is kept in ml/tests/.models/ (FUNGROUND_ML_MODELS); the first run downloads them, and a run with no connection skips these
tests with a reason. The expected vector is worked out here, from spike 23's recipe written out again, so that a change in
funground-ml's own code cannot move the reference with it.
"""
from __future__ import annotations

import numpy as np
import pytest
from PIL import Image

import funground as f
import funground_ml
from funground_ml import _pictures, _fetch, _runtime, _teach, _tasks

from conftest import HAND_PHOTO, POSE_PHOTO

pytestmark = [pytest.mark.model, pytest.mark.usefixtures("picture_models")]


class Sketch:
    pass


@pytest.fixture(autouse=True)
def a_new_sketch(monkeypatch):
    monkeypatch.setattr(_teach, "canvas_sketch", lambda sketch=Sketch(): sketch)
    monkeypatch.setattr(_tasks, "_frame", lambda: 1)


def reference_vector(path, task: str) -> np.ndarray:
    """Spike 23's recipe: RGB, shorter side 256 (bicubic), the middle 224 x 224, ImageNet's mean and spread, then the model's vector
    (MobileNetV4: its one output; DINOv2: the CLS token), length 1."""
    image = Image.open(path).convert("RGB")
    width, height = image.size
    k = 256 / min(width, height)
    image = image.resize((round(width * k), round(height * k)), Image.BICUBIC)
    width, height = image.size
    left, top = (width - 224) // 2, (height - 224) // 2
    image = image.crop((left, top, left + 224, top + 224))
    x = np.asarray(image, dtype=np.float32) / 255.0
    x = (x - np.array([0.485, 0.456, 0.406], dtype=np.float32)) / np.array([0.229, 0.224, 0.225], dtype=np.float32)
    x = x.transpose(2, 0, 1)[None].astype(np.float32)
    session = _runtime.session(_fetch.ensure(task, None, "the tests")["model"])
    out = session.run(None, {session.get_inputs()[0].name: x})[0]
    token = out[0] if task == "picture_mobilenet" else out[0, 0]
    return token / np.linalg.norm(token)


def test_the_vector_of_a_dinov2_photo_is_the_references():
    paths = _fetch.ensure("picture_dinov2", None, "the tests")
    image = f.load_image(str(HAND_PHOTO))
    from funground_ml import _source

    mine = _pictures.load(paths, _pictures.dinov2_vector)(_source.open_source(image, "the tests")[0].image())
    assert mine.shape == (384,) and mine.dtype == np.float32
    assert float(np.linalg.norm(mine)) == pytest.approx(1.0, abs=1e-5)
    assert float(mine @ reference_vector(HAND_PHOTO, "picture_dinov2")) > 0.9999


def test_the_vector_of_a_mobilenet_photo_is_the_references():
    paths = _fetch.ensure("picture_mobilenet", None, "the tests")
    image = f.load_image(str(HAND_PHOTO))
    from funground_ml import _source

    mine = _pictures.load(paths, _pictures.mobilenet_vector)(_source.open_source(image, "the tests")[0].image())
    assert mine.shape == (1280,) and mine.dtype == np.float32
    assert float(np.linalg.norm(mine)) == pytest.approx(1.0, abs=1e-5)
    assert float(mine @ reference_vector(HAND_PHOTO, "picture_mobilenet")) > 0.9999


def test_two_different_photos_taught_under_two_names_are_guessed_right_by_dinov2(capsys):
    woman, man = f.load_image(str(HAND_PHOTO)), f.load_image(str(POSE_PHOTO))
    assert funground_ml.teach({"woman": [woman], "man": [man]}, model="dinov2") == {"woman": 1, "man": 1}
    assert funground_ml.guess(woman).name == "woman" and funground_ml.guess(woman).score > 0.5
    guess = funground_ml.guess(man, k=2)
    assert guess.name == "man" and guess.score > 0.5
    assert guess.next[0].name == "woman" and guess.next[0].score < 0.5


def test_two_different_photos_taught_under_two_names_are_guessed_right_by_the_default_mobilenet(capsys):
    woman, man = f.load_image(str(HAND_PHOTO)), f.load_image(str(POSE_PHOTO))
    assert funground_ml.teach({"woman": [woman], "man": [man]}) == {"woman": 1, "man": 1}
    assert funground_ml.guess(woman).name == "woman" and funground_ml.guess(woman).score > 0.5
    guess = funground_ml.guess(man, k=2)
    assert guess.name == "man" and guess.score > 0.5
    assert guess.next[0].name == "woman" and guess.next[0].score < 0.5
