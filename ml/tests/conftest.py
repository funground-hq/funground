"""Shared pieces for the funground-ml tests."""
from __future__ import annotations

import os
from pathlib import Path

import pytest

os.environ.setdefault("FUNGROUND_HEADLESS", "1")

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
POSE_PHOTO = HERE / "data" / "gandhi_london_rain.jpg"      # the pose tests (SOURCES.md)
HAND_PHOTO = HERE / "data" / "standing_woman_640.jpg"      # the hand tests (SOURCES.md)
PERSON_PHOTO = HAND_PHOTO                                  # the person tests: she stands alone, so the outline is clean
MODELS_FOLDER = HERE / ".models"


class FakeCamera:
    """Anything with ``_current_picture()`` is a source, as the core's FrameSource says."""

    def __init__(self, picture=None, mirror: bool = True) -> None:
        self.picture = picture
        self._mirror = mirror

    def _current_picture(self):
        return self.picture


def solid_picture(width: int = 64, height: int = 48, blue: int = 0):
    """A small opaque picture (blue, green, red, alpha for each pixel)."""
    from funground.picture import Picture

    return Picture.from_pixels(width, height, bytes([blue, 90, 120, 255]) * (width * height), "test")


@pytest.fixture
def camera_with_picture():
    return FakeCamera(solid_picture())


@pytest.fixture(scope="session")
def real_models():
    """The real model files in ml/tests/.models/ (downloaded on the first run). Skips the test when offline."""
    from funground_ml import _fetch

    previous = os.environ.get(_fetch.ENVIRONMENT)
    os.environ[_fetch.ENVIRONMENT] = str(MODELS_FOLDER)
    try:
        for task in ("pose", "hand", "person"):
            try:
                _fetch.ensure(task, None, "the tests")
            except ConnectionError as error:
                pytest.skip(f"the {task} model files are not in ml/tests/.models/ and cannot be downloaded: {error}")
        yield MODELS_FOLDER
    finally:
        if previous is None:
            os.environ.pop(_fetch.ENVIRONMENT, None)
        else:
            os.environ[_fetch.ENVIRONMENT] = previous


SPEECH = HERE / "data" / "tts.wav"          # the words tests (SOURCES.md): 7.2 s, 16 kHz, mono
SPEECH_TEXT = ("Draw a red circle in the middle of the screen, then make it bounce off the walls and change color every time "
               "it hits one.")


@pytest.fixture(scope="session")
def words_models():
    """The words model files in ml/tests/.models/ (downloaded on the first run). Skips the test when offline."""
    from funground_ml import _fetch

    previous = os.environ.get(_fetch.ENVIRONMENT)
    os.environ[_fetch.ENVIRONMENT] = str(MODELS_FOLDER)
    try:
        try:
            _fetch.ensure("words", None, "the tests")
        except ConnectionError as error:
            pytest.skip(f"the words model files are not in ml/tests/.models/ and cannot be downloaded: {error}")
        yield MODELS_FOLDER
    finally:
        if previous is None:
            os.environ.pop(_fetch.ENVIRONMENT, None)
        else:
            os.environ[_fetch.ENVIRONMENT] = previous


WHISTLE = HERE / "data" / "whistle.wav"      # the sound tests (SOURCES.md): 4.9 s, 16 kHz, mono
CLAPPING = HERE / "data" / "clapping.wav"    # 8 s, 16 kHz, mono


@pytest.fixture(scope="session")
def sound_models():
    """The sound model file in ml/tests/.models/ (downloaded on the first run). Skips the test when offline."""
    from funground_ml import _fetch

    previous = os.environ.get(_fetch.ENVIRONMENT)
    os.environ[_fetch.ENVIRONMENT] = str(MODELS_FOLDER)
    try:
        try:
            _fetch.ensure("sound", None, "the tests")
        except ConnectionError as error:
            pytest.skip(f"the sound model file is not in ml/tests/.models/ and cannot be downloaded: {error}")
        yield MODELS_FOLDER
    finally:
        if previous is None:
            os.environ.pop(_fetch.ENVIRONMENT, None)
        else:
            os.environ[_fetch.ENVIRONMENT] = previous


@pytest.fixture(scope="session")
def picture_models():
    """The picture model file in ml/tests/.models/ (downloaded on the first run). Skips the test when offline."""
    from funground_ml import _fetch

    previous = os.environ.get(_fetch.ENVIRONMENT)
    os.environ[_fetch.ENVIRONMENT] = str(MODELS_FOLDER)
    try:
        try:
            _fetch.ensure("picture", None, "the tests")
        except ConnectionError as error:
            pytest.skip(f"the picture model file is not in ml/tests/.models/ and cannot be downloaded: {error}")
        yield MODELS_FOLDER
    finally:
        if previous is None:
            os.environ.pop(_fetch.ENVIRONMENT, None)
        else:
            os.environ[_fetch.ENVIRONMENT] = previous
