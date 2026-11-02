"""Tests that run the real model files on two test photographs (ml/tests/data/SOURCES.md says where they are from):
``gandhi_london_rain.jpg`` for the pose tests and ``standing_woman_640.jpg`` for the hand tests.

The files are kept in ml/tests/.models/ (FUNGROUND_ML_MODELS); the first run downloads them, and a run with no connection
skips these tests with a reason.

The expected points are not stored: they come from the S-231 spike's own numpy glue (spikes/16_models/onnx/ort_glue.py),
imported by path and run on the same picture with the same model files. funground-ml's code must give the same points
within 5 px (the tolerance the spike measured between platforms).
"""
from __future__ import annotations

import importlib.util
import sys

import numpy as np
import pytest
from PIL import Image

import funground as f
import funground_ml
from funground_ml import _glue, _tasks

from conftest import HAND_PHOTO, POSE_PHOTO, ROOT, FakeCamera

pytestmark = [pytest.mark.model, pytest.mark.usefixtures("real_models")]

SPIKE = ROOT / "spikes" / "16_models" / "onnx" / "ort_glue.py"
TOLERANCE = 5.0                  # pixels


@pytest.fixture(scope="module")
def photo():
    """The pose photograph."""
    return f.load_image(str(POSE_PHOTO))


@pytest.fixture(scope="module")
def hand_photo():
    return f.load_image(str(HAND_PHOTO))


@pytest.fixture(scope="module")
def spike_points(real_models):
    """The spike's own glue: (pose rows on the pose photograph, hand rows on the hand photograph), each x, y, ..."""
    if not SPIKE.exists():
        pytest.skip("the spike's glue (spikes/16_models/onnx/ort_glue.py) is not in this checkout")
    import onnxruntime as ort

    spec = importlib.util.spec_from_file_location("spike_ort_glue", SPIKE)
    spike = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(spike)
    pose_picture = np.asarray(Image.open(POSE_PHOTO).convert("RGB"))
    hand_picture = np.asarray(Image.open(HAND_PHOTO).convert("RGB"))
    folder = str(real_models)
    pose = spike.Pose(f"{folder}/person_detection_mediapipe_2023mar.onnx",
                      f"{folder}/pose_estimation_mediapipe_2023mar.onnx", ort)
    pose.find(pose_picture)
    hand = spike.Hand(f"{folder}/palm_detection_mediapipe_2023feb.onnx",
                      f"{folder}/handpose_estimation_mediapipe_2023feb.onnx", ort)
    hand.find(hand_picture)
    return pose.points(pose_picture), hand.points(hand_picture)


def _xy(points: dict) -> np.ndarray:
    return np.array([[p.x, p.y] for p in points.values()])


def test_a_body_is_found_in_the_photograph(photo):
    body = funground_ml.pose(photo)
    assert body is not None and body.score > 0.5
    assert len(body.points) == 33
    assert body.nose.y < body.left_hip.y and body.nose.y < body.right_hip.y     # the head is above the hips
    assert body.left_hip.y < body.left_knee.y < body.left_ankle.y
    width, height = photo.width, photo.height
    assert 0 < body.nose.x < width and 0 < body.nose.y < height


def test_the_body_agrees_with_the_spikes_glue_within_5_pixels(photo, spike_points):
    body = funground_ml.pose(photo)
    expected = spike_points[0][:, :2]
    assert np.abs(_xy(body.points) - expected).max() < TOLERANCE


def test_a_hand_is_found_in_the_photograph(hand_photo):
    hand = funground_ml.hand(hand_photo)
    assert hand is not None and hand.score >= 0.8
    assert len(hand.points) == 21
    assert hand.wrist.dist(hand.middle_finger_tip) > 20                     # a hand, not one point
    assert 0 < hand.wrist.x < hand_photo.width and 0 < hand.wrist.y < hand_photo.height


def test_the_hand_agrees_with_the_spikes_glue_within_5_pixels(hand_photo, spike_points):
    hand = funground_ml.hand(hand_photo)
    expected = spike_points[1][:, :2]
    assert np.abs(_xy(hand.points) - expected).max() < TOLERANCE


def test_the_same_answer_comes_twice_in_a_frame(photo, hand_photo):
    assert funground_ml.pose(photo) is funground_ml.pose(photo)
    camera = FakeCamera(hand_photo, mirror=False)
    assert funground_ml.hand(camera) is funground_ml.hand(camera)


def test_a_mirrored_camera_gives_the_learners_own_sides(photo):
    plain = funground_ml.pose(FakeCamera(photo, mirror=False))
    mirrored = funground_ml.pose(FakeCamera(photo, mirror=True))
    assert plain is not mirrored
    for name in ("shoulder", "elbow", "wrist", "hip", "knee", "ankle"):
        left, right = getattr(mirrored, f"left_{name}"), getattr(plain, f"right_{name}")
        assert (left.x, left.y) == (right.x, right.y)
    assert mirrored.nose.x == plain.nose.x


def test_a_picture_with_nobody_in_it_gives_none():
    f.size(200, 200)                                          # a picture of one's own needs a canvas first
    empty = f.create_graphics(640, 480)
    empty.background("#7f7f7f")
    assert funground_ml.pose(empty) is None
    assert funground_ml.hand(empty) is None


def test_the_next_frame_reuses_the_box_instead_of_running_the_detector(photo, monkeypatch):
    f.size(200, 200)
    picture = f.create_graphics(photo.width, photo.height)
    picture.image(photo, 0, 0)
    camera = FakeCamera(picture, mirror=False)
    looks = []
    real = _glue.detect
    monkeypatch.setattr(_glue, "detect", lambda *args: looks.append(1) or real(*args))
    first = funground_ml.pose(camera)
    picture.image(photo, 0, 0)                                # the next frame: a new version of the same picture
    second = funground_ml.pose(camera)
    assert first is not None and second is not None and first is not second
    assert len(looks) == 1                                    # one look for two frames
    assert np.abs(_xy(first.points) - _xy(second.points)).max() < 1.0


def test_the_models_are_run_by_the_cpu_provider_and_kept_once(photo, hand_photo):
    from funground_ml import _runtime

    before = len(_runtime._sessions)
    funground_ml.pose(photo)
    funground_ml.hand(hand_photo)
    assert len(_runtime._sessions) == before                  # no new session for a second call
    assert len(_runtime._sessions) >= 4
    assert all(s.get_providers() == ["CPUExecutionProvider"] for s in _runtime._sessions.values())
