"""A model's wait shown to the sketch (S-307, D-149): the downloading and the starting, then the end of the wait."""
from __future__ import annotations

import pytest

from funground import host_services
from funground_ml import _fetch, _runtime, _wait

from test_unit import _fake_models, _opener, clean_fetch  # noqa: F401  (the fixture and the fakes of the fetch tests)


@pytest.fixture
def waits(monkeypatch):
    seen: list = []
    monkeypatch.setattr(host_services, "waiting", seen.append)
    monkeypatch.setattr(_fetch, "TITLE_EVERY", 0)
    return seen


def test_a_download_says_how_far_it_has_come_and_then_ends_the_wait(monkeypatch, clean_fetch, waits):
    payloads = {"pose_detector": b"d" * 2_500_000, "pose_landmarks": b"l" * 3_000_000}
    models = _fake_models(monkeypatch, payloads)
    _opener(monkeypatch, {m.url: payloads[n] for n, m in models.items()})
    _fetch.ensure("pose", None, "ml.pose()")
    assert waits[0] == "Downloading the pose model"
    assert waits[-1] is None and waits.count(None) == 1
    steps = [int(w.split(": ")[1].split(" of ")[0]) for w in waits[1:-1]]
    assert steps == sorted(steps) and steps[-1] == 6 and len(steps) >= 4       # grows through both files
    assert all(w.endswith(" of 6 MB") for w in waits[1:-1])


def test_a_failed_download_still_ends_the_wait(monkeypatch, clean_fetch, waits):
    payloads = {"pose_detector": b"d" * 1500, "pose_landmarks": b"l" * 2500}
    models = _fake_models(monkeypatch, payloads)
    _opener(monkeypatch, {m.url: OSError("down") for m in models.values()})
    with pytest.raises(ConnectionError):
        _fetch.ensure("pose", None, "ml.pose()")
    assert waits[-1] is None


def test_starting_a_model_says_so_and_a_kept_session_does_not(monkeypatch, waits):
    made = []
    fake = type("Fake", (), {"InferenceSession": lambda self, key, providers: made.append(key) or key})()
    monkeypatch.setattr(_runtime, "_onnxruntime", lambda: fake)
    monkeypatch.setattr(_runtime, "_sessions", {})
    _runtime.session("a.onnx", "hand")
    _runtime.session("a.onnx", "hand")
    _runtime.session("b.onnx")                           # a worker thread says nothing
    assert waits == ["Starting the hand model", None] and made == ["a.onnx", "b.onnx"]


def test_with_no_sketch_listening_nothing_breaks(monkeypatch, clean_fetch):
    monkeypatch.setattr(host_services, "waiting", None)
    payloads = {"pose_detector": b"d" * 1500, "pose_landmarks": b"l" * 2500}
    models = _fake_models(monkeypatch, payloads)
    _opener(monkeypatch, {m.url: payloads[n] for n, m in models.items()})
    _fetch.ensure("pose", None, "ml.pose()")
    with _wait.waiting("x"):
        _wait.progress("y")
