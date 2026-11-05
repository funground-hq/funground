"""Tests of funground-ml that need no model file and no network."""
from __future__ import annotations

import ast
import io
import os
import re
import subprocess
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError

import pytest

import funground as f
import funground_ml
from funground_ml import _fetch, _glue, _models, _results, _source, _tasks

from conftest import ROOT, FakeCamera, solid_picture

CODE = (ROOT / "ml" / "funground_ml")


# ---- names and results
def test_the_public_names_are_pose_hand_person_and_words_only():
    assert funground_ml.__all__ == ["pose", "hand", "person", "words"]
    assert all(callable(getattr(funground_ml, name)) for name in funground_ml.__all__)
    assert funground_ml.Words is _results.Words and funground_ml.Body is _results.Body       # importable, like Body, not starred


def test_there_are_33_body_names_and_21_hand_names_without_repeats():
    assert len(_results.BODY_NAMES) == 33 and len(set(_results.BODY_NAMES)) == 33
    assert len(_results.HAND_NAMES) == 21 and len(set(_results.HAND_NAMES)) == 21
    assert _results.BODY_NAMES[0] == "nose" and _results.BODY_NAMES[-1] == "right_foot_index"
    assert _results.HAND_NAMES[0] == "wrist" and _results.HAND_NAMES[-1] == "pinky_tip"


def _rows(n):
    return [(float(i), float(i) * 2) for i in range(n)]      # the point numbered i is at (i, 2i)


def test_a_body_has_every_name_as_a_vector_attribute_and_a_dict():
    body = _results.Body.from_points(_rows(33), 0.9, mirrored=False)
    assert list(body.points) == list(_results.BODY_NAMES)
    assert isinstance(body.left_wrist, f.Vector)
    assert (body.left_wrist.x, body.left_wrist.y) == (15.0, 30.0)
    assert body.points["left_wrist"] is body.left_wrist
    assert body.score == 0.9


def test_a_mirrored_picture_swaps_every_left_and_right_name():
    plain = _results.Body.from_points(_rows(33), 0.9, mirrored=False)
    mirrored = _results.Body.from_points(_rows(33), 0.9, mirrored=True)
    assert list(mirrored.points) == list(plain.points)             # the order of the names is the model's
    for name in _results.BODY_NAMES:
        other = name.replace("left_", "\0").replace("right_", "left_").replace("\0", "right_")
        assert (mirrored.points[name].x, mirrored.points[name].y) == (plain.points[other].x, plain.points[other].y)
    assert mirrored.nose.x == plain.nose.x                         # nothing is swapped for a point with no side
    assert mirrored.left_wrist.x == plain.right_wrist.x == 16.0
    assert mirrored.mouth_left.x == plain.mouth_left.x             # "mouth_left" does not start with a side


def test_a_hand_has_21_named_points():
    hand = _results.Hand.from_points(_rows(21), 0.95)
    assert list(hand.points) == list(_results.HAND_NAMES)
    assert hand.index_finger_tip.x == 8.0 and hand.pinky_tip.y == 40.0


def test_the_repr_says_what_it_is():
    body = _results.Body.from_points([(1.4, 2.6)] + _rows(32), 0.876, mirrored=False)
    assert repr(body) == "<Body score 0.88, 33 points, nose at (1, 3)>"
    hand = _results.Hand.from_points(_rows(21), 0.95)
    assert repr(hand) == "<Hand score 0.95, 21 points, wrist at (0, 0)>"


def test_a_misspelt_point_name_suggests_the_nearest():
    body = _results.Body.from_points(_rows(33), 0.9, mirrored=False)
    with pytest.raises(AttributeError, match=r"no point called 'left_wrst'\. Did you mean 'left_wrist'\?"):
        body.left_wrst
    hand = _results.Hand.from_points(_rows(21), 0.95)
    with pytest.raises(AttributeError, match=r"Did you mean 'index_finger_tip'\?"):     # the hand's tip is not "index_tip"
        hand.index_tip
    with pytest.raises(AttributeError, match=r"listed in hand\.points"):
        hand.qqqqqq


def test_a_private_name_that_is_missing_is_a_plain_attribute_error():
    body = _results.Body.from_points(_rows(33), 0.9, mirrored=False)
    assert not hasattr(body, "__deepcopy__")


# ---- the source
def test_something_that_is_not_a_source_is_a_plain_type_error():
    with pytest.raises(TypeError) as info:
        funground_ml.pose("a.png")
    assert str(info.value) == ("ml.pose() needs a camera from camera.open() or a picture from f.load_image(), "
                               "not str.")
    with pytest.raises(TypeError, match=r"ml\.hand\(\) needs a camera .* not int"):
        funground_ml.hand(3)
    with pytest.raises(TypeError):
        funground_ml.pose(None)


def test_a_camera_with_no_frame_yet_gives_none_without_touching_the_models(monkeypatch):
    def boom(*args):
        raise AssertionError("the models must not be asked for")

    monkeypatch.setattr(_fetch, "ensure", boom)
    assert funground_ml.pose(FakeCamera(None)) is None
    assert funground_ml.hand(FakeCamera(None)) is None
    assert funground_ml.person(FakeCamera(None)) is None


def test_a_mirrored_camera_gives_a_mirrored_frame_and_a_picture_does_not():
    picture = solid_picture()
    frame, _ = _source.open_source(FakeCamera(picture, mirror=True), "ml.pose()")
    assert frame.mirrored
    frame, _ = _source.open_source(FakeCamera(picture, mirror=False), "ml.pose()")
    assert not frame.mirrored
    frame, _ = _source.open_source(picture, "ml.pose()")
    assert not frame.mirrored


def test_the_frame_is_a_pillow_image_of_the_pictures_size():
    image = _source.open_source(solid_picture(64, 48), "ml.pose()")[0].image()
    assert image.mode == "RGB" and image.size == (64, 48)
    assert image.getpixel((0, 0)) == (120, 90, 0)                   # the picture's red, green and blue


def test_the_result_is_kept_for_a_frame_and_made_again_for_the_next_one():
    picture = solid_picture()
    camera = FakeCamera(picture)
    made = []

    def make(frame, tracker):
        made.append(frame.version)
        return object() if len(made) != 2 else None

    first = _source.answer(camera, "t", "who", make)
    assert _source.answer(camera, "t", "who", make) is first        # the same answer in the same frame
    assert len(made) == 1
    picture._write_pixels(bytes([9, 9, 9, 255]) * (64 * 48))         # a new frame: the same Picture, a new version
    assert _source.answer(camera, "t", "who", make) is None         # "nobody" is made once and kept as well
    assert _source.answer(camera, "t", "who", make) is None
    assert len(made) == 2 and made[0] != made[1]
    assert _source.answer(camera, "other task", "who", make) is not None     # tasks keep their own answers


def test_two_cameras_do_not_share_answers():
    a, b = FakeCamera(solid_picture()), FakeCamera(solid_picture())
    made = []
    for camera in (a, b):
        _source.answer(camera, "t", "who", lambda frame, tracker: made.append(1))
    assert len(made) == 2


def test_the_cache_does_not_keep_a_picture_alive():
    import gc
    import weakref

    picture = solid_picture()
    _source.answer(picture, "t", "who", lambda frame, tracker: 1)
    ref = weakref.ref(picture)
    del picture
    gc.collect()
    assert ref() is None


# ---- the box that is reused
class _Image:
    size = (640, 480)


def _landmarks(score):
    return _glue.Landmarks(None, score)


def test_a_good_box_is_reused_up_to_the_limit_then_the_detector_looks_again():
    tracker, seen = _glue.Tracker(), {"detect": 0, "landmarks": 0}

    def detect():
        seen["detect"] += 1
        return "region"

    def landmarks(region):
        seen["landmarks"] += 1
        return _landmarks(0.99)

    for _ in range(_glue.REUSE_LIMIT + 1):
        tracker.find(_Image, detect, landmarks)
    assert seen["detect"] == 1                                       # one look, then REUSE_LIMIT reused frames
    tracker.find(_Image, detect, landmarks)
    assert seen["detect"] == 2                                       # the bound: the detector looks again


def test_a_weak_result_makes_the_detector_look_again_in_the_same_call():
    tracker, calls = _glue.Tracker(), []

    def detect():
        calls.append("detect")
        return "region"

    scores = iter([0.99, 0.6, 0.99])           # the first look, the reused box does badly, the second look is good

    def landmarks(region):
        calls.append("landmarks")
        return _landmarks(next(scores))

    tracker.find(_Image, detect, landmarks)
    found = tracker.find(_Image, detect, landmarks)
    assert found.score == 0.99
    assert calls == ["detect", "landmarks", "landmarks", "detect", "landmarks"]


def test_a_result_that_is_only_just_good_enough_is_given_but_its_box_is_not_reused():
    tracker, detects = _glue.Tracker(), []

    def detect():
        detects.append(1)
        return "region"

    for _ in range(3):
        found = tracker.find(_Image, detect, lambda region: _landmarks(0.6))
        assert found.score == 0.6
    assert len(detects) == 3


def test_nobody_found_forgets_the_box():
    tracker = _glue.Tracker()
    tracker.find(_Image, lambda: "region", lambda region: _landmarks(0.99))
    assert tracker.can_reuse()
    assert tracker.find(_Image, lambda: None, lambda region: None) is None      # the reused box finds no one, nor does the detector
    assert not tracker.can_reuse()


def test_a_picture_of_another_size_starts_again():
    class Bigger:
        size = (1280, 720)

    tracker, detects = _glue.Tracker(), []
    tracker.find(_Image, lambda: detects.append(1) or "region", lambda region: _landmarks(0.99))
    tracker.find(Bigger, lambda: detects.append(1) or "region", lambda region: _landmarks(0.99))
    assert len(detects) == 2


# ---- the model table and the download
def test_the_table_has_eight_pinned_files_from_the_hub():
    assert len(_models.MODELS) == 8
    for model in _models.MODELS.values():
        assert re.fullmatch(r"https://huggingface\.co/(opencv|onnx-community)/[a-z_.-]+/resolve/[0-9a-f]{40}/[\w./]+\.(onnx|json)", model.url), model.url
        assert "/main/" not in model.url
        assert re.fullmatch(r"[0-9a-f]{64}", model.sha256) and model.size > 100_000
        assert model.licence == "Apache-2.0"
        assert "/" not in model.local_name                                  # a copy is kept straight in models/
    assert set(name for names in _models.TASKS.values() for name in names) == set(_models.MODELS)


def test_the_person_task_has_one_file_that_is_the_general_selfie_model():
    assert _models.TASKS["person"] == ("person_mask",)
    model = _models.MODELS["person_mask"]
    assert model.repo == "onnx-community/mediapipe_selfie_segmentation" and model.file == "onnx/model.onnx"
    assert model.local_name == "mediapipe_selfie_segmentation.onnx" and model.size == 462352
    assert _models.MODELS["pose_detector"].local_name == _models.MODELS["pose_detector"].file     # the others keep their own names


class _Response(io.BytesIO):
    """What ``urlopen`` gives: readable and a context manager (BytesIO already is both)."""


def _fake_models(monkeypatch, payloads: dict[str, bytes]):
    """Make the table describe small fake files whose real checksums are those of *payloads* (by role)."""
    import hashlib

    models = {}
    for name, data in payloads.items():
        models[name] = _models.Model(name, "opencv/test", "0" * 40, f"{name}.onnx", len(data),
                                     hashlib.sha256(data).hexdigest(), "Apache-2.0")
    monkeypatch.setattr(_fetch, "MODELS", {**_models.MODELS, **models})
    return models


def _opener(monkeypatch, answers: dict):
    """Replace the network: the address -> bytes, or an exception to raise. Records the addresses asked for."""
    asked = []

    def opener(request, timeout=None):
        asked.append(request.full_url)
        answer = answers[request.full_url]
        if isinstance(answer, Exception):
            raise answer
        return _Response(answer)

    monkeypatch.setattr(_fetch, "_open", opener)
    return asked


@pytest.fixture
def clean_fetch(monkeypatch, tmp_path):
    monkeypatch.setenv(_fetch.ENVIRONMENT, str(tmp_path / "kept"))
    monkeypatch.setattr(_fetch, "_checked", set())
    return tmp_path / "kept"


def test_a_download_is_checked_kept_and_announced_once(monkeypatch, clean_fetch, capsys):
    payloads = {"pose_detector": b"d" * 1500, "pose_landmarks": b"l" * 2500}
    models = _fake_models(monkeypatch, payloads)
    asked = _opener(monkeypatch, {m.url: payloads[n] for n, m in models.items()})
    paths = _fetch.ensure("pose", None, "ml.pose()")
    assert Path(paths["detector"]).read_bytes() == payloads["pose_detector"]
    assert Path(paths["landmarks"]).read_bytes() == payloads["pose_landmarks"]
    assert len(asked) == 2 and not list(clean_fetch.glob("*.part"))
    out = capsys.readouterr().out
    assert out.count("Downloading the pose model, 1 MB, once.") == 1 and "After that funground uses the copy in" in out
    _fetch.ensure("pose", None, "ml.pose()")                         # the second time: no network and no line
    assert len(asked) == 2 and capsys.readouterr().out == ""


def test_a_kept_copy_is_used_after_a_restart_without_the_network(monkeypatch, clean_fetch, capsys):
    payloads = {"pose_detector": b"d" * 1500, "pose_landmarks": b"l" * 2500}
    models = _fake_models(monkeypatch, payloads)
    _opener(monkeypatch, {m.url: payloads[n] for n, m in models.items()})
    _fetch.ensure("pose", None, "ml.pose()")
    capsys.readouterr()
    monkeypatch.setattr(_fetch, "_checked", set())                    # a new process
    asked = _opener(monkeypatch, {})
    _fetch.ensure("pose", None, "ml.pose()")
    assert asked == [] and capsys.readouterr().out == ""


def test_a_checksum_that_does_not_match_deletes_the_file_and_says_so(monkeypatch, clean_fetch):
    payloads = {"pose_detector": b"d" * 1500, "pose_landmarks": b"l" * 2500}
    models = _fake_models(monkeypatch, payloads)
    _opener(monkeypatch, {models["pose_detector"].url: b"x" * 1500, models["pose_landmarks"].url: payloads["pose_landmarks"]})
    with pytest.raises(ValueError, match="not the one funground expects"):
        _fetch.ensure("pose", None, "ml.pose()")
    assert list(clean_fetch.iterdir()) == []                          # not the file, not a temporary one


def test_a_file_that_is_too_long_is_refused(monkeypatch, clean_fetch):
    payloads = {"pose_detector": b"d" * 1500, "pose_landmarks": b"l" * 2500}
    models = _fake_models(monkeypatch, payloads)
    _opener(monkeypatch, {models["pose_detector"].url: b"d" * 5000, models["pose_landmarks"].url: payloads["pose_landmarks"]})
    with pytest.raises(ValueError):
        _fetch.ensure("pose", None, "ml.pose()")
    assert list(clean_fetch.iterdir()) == []


def test_a_wrong_copy_on_disk_is_downloaded_again(monkeypatch, clean_fetch):
    payloads = {"pose_detector": b"d" * 1500, "pose_landmarks": b"l" * 2500}
    models = _fake_models(monkeypatch, payloads)
    clean_fetch.mkdir()
    (clean_fetch / models["pose_detector"].file).write_bytes(b"damaged")
    _opener(monkeypatch, {m.url: payloads[n] for n, m in models.items()})
    paths = _fetch.ensure("pose", None, "ml.pose()")
    assert Path(paths["detector"]).read_bytes() == payloads["pose_detector"]


def test_no_connection_gives_one_plain_sentence(monkeypatch, clean_fetch):
    payloads = {"pose_detector": b"d" * 1500, "pose_landmarks": b"l" * 2500}
    models = _fake_models(monkeypatch, payloads)
    _opener(monkeypatch, {models["pose_detector"].url: URLError(OSError("getaddrinfo failed"))})
    with pytest.raises(ConnectionError) as info:
        _fetch.ensure("pose", None, "ml.pose()")
    assert "ml.pose(): could not download the pose detector" in str(info.value)
    assert "Run the sketch once while online; after that funground uses the copy in" in str(info.value)


def test_a_site_error_names_the_address(monkeypatch, clean_fetch):
    payloads = {"pose_detector": b"d" * 1500, "pose_landmarks": b"l" * 2500}
    models = _fake_models(monkeypatch, payloads)
    url = models["pose_detector"].url
    _opener(monkeypatch, {url: HTTPError(url, 404, "Not Found", {}, None)})
    with pytest.raises(ConnectionError, match="the site answered 404"):
        _fetch.ensure("pose", None, "ml.pose()")


def test_the_folder_is_beside_the_sketch_or_named_by_the_variable(monkeypatch, tmp_path):
    monkeypatch.delenv(_fetch.ENVIRONMENT, raising=False)
    assert _fetch.models_folder(str(tmp_path)) == str(tmp_path / "models")
    assert _fetch.models_folder(None) == os.path.join(os.getcwd(), "models")
    monkeypatch.setenv(_fetch.ENVIRONMENT, str(tmp_path / "elsewhere"))
    assert _fetch.models_folder(str(tmp_path)) == str(tmp_path / "elsewhere")


# ---- the provider boundary, telemetry and the core's stub
def _imported_modules(path: Path) -> set[str]:
    found: set[str] = set()
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            found.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            found.add(node.module.split(".")[0])
    return found


def test_only_the_runtime_module_imports_onnxruntime():
    offenders = [p.name for p in CODE.glob("*.py") if "onnxruntime" in _imported_modules(p) and p.name != "_runtime.py"]
    assert offenders == []
    assert "onnxruntime" in _imported_modules(CODE / "_runtime.py")
    core = [p for p in (ROOT / "funground").rglob("*.py") if "onnxruntime" in _imported_modules(p)]
    assert core == []


def _run(code: str, **env) -> subprocess.CompletedProcess:
    full = {k: v for k, v in os.environ.items() if k != "ORT_DISABLE_TELEMETRY"}
    full.update(env, FUNGROUND_HEADLESS="1")
    return subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=300, env=full)


def test_the_telemetry_switch_is_set_before_onnxruntime_is_imported():
    code = (
        "import os, sys\n"
        "seen = {}\n"
        "class Spy:\n"
        "    def find_spec(self, name, path=None, target=None):\n"
        "        if name == 'onnxruntime' and 'value' not in seen:\n"
        "            seen['value'] = os.environ.get('ORT_DISABLE_TELEMETRY')\n"
        "        return None\n"
        "sys.meta_path.insert(0, Spy())\n"
        "from funground import ml\n"
        "assert 'onnxruntime' not in sys.modules, 'imported too early'\n"
        "from funground_ml import _runtime\n"
        "_runtime._onnxruntime()\n"
        "print(seen.get('value'))\n"
    )
    done = _run(code)
    assert done.returncode == 0, done.stderr
    assert done.stdout.strip().splitlines()[-1] == "1"


def test_telemetry_is_switched_off_even_if_the_learner_environment_says_otherwise():
    code = "from funground_ml import _runtime; _runtime._onnxruntime(); import os; print(os.environ['ORT_DISABLE_TELEMETRY'])"
    done = _run(code, ORT_DISABLE_TELEMETRY="0")
    assert done.returncode == 0, done.stderr
    assert done.stdout.strip().splitlines()[-1] == "1"


def test_the_core_stub_says_it_is_a_separate_install_when_the_package_is_hidden():
    code = (
        "import sys\n"
        "sys.modules['funground_ml'] = None\n"
        "try:\n"
        "    from funground import ml\n"
        "except ImportError as error:\n"
        "    print(str(error)); print(error.__suppress_context__)\n"
    )
    done = _run(code)
    assert done.returncode == 0, done.stderr
    lines = done.stdout.strip().splitlines()
    assert lines[-2] == "The models library is a separate install: run `python -m pip install funground-ml`"
    assert lines[-1] == "True"                                        # raised from None: no confusing chain


def test_the_core_stub_passes_the_names_on():
    from funground import ml

    assert ml.pose is funground_ml.pose and ml.hand is funground_ml.hand and ml.person is funground_ml.person
    assert ml.words is funground_ml.words
    assert ml.__all__ == ["pose", "hand", "person", "words"]
    assert "ml" not in f._PUBLIC_NAMES                                 # the naming trap: no public function is called ml


# ---- the person's mask (S-233)
def test_a_one_file_task_downloads_it_under_its_kept_name_and_gives_it_the_role_model(monkeypatch, clean_fetch, capsys):
    import hashlib

    data = b"m" * 1500
    model = _models.Model("person_mask", "onnx-community/test", "0" * 40, "onnx/model.onnx", len(data),
                          hashlib.sha256(data).hexdigest(), "Apache-2.0", kept_as="selfie.onnx")
    monkeypatch.setattr(_fetch, "MODELS", {**_models.MODELS, "person_mask": model})
    asked = _opener(monkeypatch, {model.url: data})
    paths = _fetch.ensure("person", None, "ml.person()")
    assert list(paths) == ["model"] and Path(paths["model"]) == clean_fetch / "selfie.onnx"
    assert Path(paths["model"]).read_bytes() == data and asked == [model.url]
    assert "Downloading the person model, 1 MB, once." in capsys.readouterr().out
    _fetch.ensure("person", None, "ml.person()")
    assert len(asked) == 1                                              # the kept copy is found by its kept name


class _Selfie:
    """Stands for the selfie model: it records what it was given and answers with a mask, 0 on the left, 1 on the right."""

    def __init__(self, mask=None) -> None:
        self.inputs = []
        self.mask = mask

    def get_inputs(self):
        return [type("Input", (), {"name": "pixel_values"})()]

    def run(self, outputs, feed):
        import numpy as np

        x = feed["pixel_values"]
        self.inputs.append(x)
        if self.mask is not None:
            return [self.mask(x)]
        alphas = np.zeros((1, 1, 256, 256), np.float32)
        alphas[..., 128:] = 1.0
        return [alphas]


def _constant(value: float):
    """A stand-in model's answer: the same mask value everywhere."""
    def answer(x):
        import numpy as np

        return np.full((1, 1, 256, 256), value, np.float32)

    return answer


@pytest.fixture
def selfie(monkeypatch):
    from funground_ml import _runtime

    model = _Selfie()
    monkeypatch.setattr(_fetch, "ensure", lambda task, base, who: {"model": "unused"})
    monkeypatch.setattr(_runtime, "session", lambda path: model)
    return model


def _alphas(picture):
    snap = picture._snapshot()
    return snap.pixels[3::4], snap.phys_width, snap.phys_height


def test_the_person_is_a_new_picture_of_the_sources_size_with_the_masks_alpha(selfie):
    from funground.picture import Picture

    source = solid_picture(512, 8)                                          # twice the mask's width: its edge is smoothed
    cut = funground_ml.person(source)
    assert isinstance(cut, Picture) and cut is not source
    assert (cut.width, cut.height) == (512, 8)
    alphas, width, height = _alphas(cut)
    assert (width, height) == (512, 8) and len(alphas) == 512 * 8
    row = alphas[3 * 512:4 * 512]
    assert row[:255] == bytes(255) and row[257:] == bytes([255]) * 255      # see-through on the left, solid on the right
    assert 0 < row[255] < row[256] < 255                                    # and a soft edge between, not a step
    assert _alphas(source)[0] == bytes([255]) * (512 * 8)                   # the source is not changed


def test_the_colours_stay_the_sources_and_go_with_the_alpha_premultiplied(selfie):
    cut = funground_ml.person(solid_picture(512, 8, blue=200))              # blue 200, green 90, red 120
    pixels = cut._snapshot().pixels
    right = (3 * 512 + 500) * 4
    assert tuple(pixels[right:right + 4]) == (200, 90, 120, 255)            # solid: the source's own pixel
    left = (3 * 512 + 2) * 4
    assert tuple(pixels[left:left + 4]) == (0, 0, 0, 0)
    edge = (3 * 512 + 255) * 4
    b, g, r, a = pixels[edge:edge + 4]
    assert 0 < a < 255 and max(abs(b - round(200 * a / 255)), abs(g - round(90 * a / 255)), abs(r - round(120 * a / 255))) <= 1


def test_the_mask_is_not_thresholded(selfie):
    selfie.mask = _constant(0.4)
    alphas, _, _ = _alphas(funground_ml.person(solid_picture()))
    assert set(alphas) == {102}                                              # 0.4 of 255, kept as it is


def test_a_picture_with_nobody_in_it_is_see_through_everywhere_and_is_not_none(selfie):
    selfie.mask = _constant(0.0)
    cut = funground_ml.person(solid_picture(40, 30))
    assert cut is not None and set(cut._snapshot().pixels) == {0}


def test_an_empty_transparent_picture_stays_see_through_under_a_full_mask(selfie):
    selfie.mask = _constant(1.0)
    f.size(100, 100)
    empty = f.create_graphics(50, 40)
    assert set(funground_ml.person(empty)._snapshot().pixels) == {0}


def test_the_model_gets_the_whole_picture_stretched_to_256_square_scaled_to_0_1(selfie):
    funground_ml.person(solid_picture(64, 48, blue=51))
    x = selfie.inputs[0]
    assert x.shape == (1, 3, 256, 256) and x.dtype.name == "float32"
    assert x[0, 0, 100, 100] == pytest.approx(120 / 255, abs=1e-6)           # channels first: red, green, blue
    assert x[0, 1, 0, 255] == pytest.approx(90 / 255, abs=1e-6) and x[0, 2, 255, 0] == pytest.approx(51 / 255, abs=1e-6)


def test_a_high_density_picture_gives_a_picture_with_the_same_logical_size_and_scale(selfie):
    from funground.picture import Picture

    source = Picture(20, 10, 2.0, "photo")
    source._write_pixels(bytes([40, 120, 200, 255]) * (40 * 20))
    cut = funground_ml.person(source)
    snap = cut._snapshot()
    assert (cut.width, cut.height, snap.phys_width, snap.phys_height, snap.scale) == (20, 10, 40, 20, 2.0)


def test_the_same_picture_comes_twice_in_a_frame_and_a_new_one_for_a_new_frame(selfie):
    picture = solid_picture()
    camera = FakeCamera(picture)
    first = funground_ml.person(camera)
    assert funground_ml.person(camera) is first and len(selfie.inputs) == 1       # the model ran once
    picture._write_pixels(bytes([9, 9, 9, 255]) * (64 * 48))                       # a new frame
    assert funground_ml.person(camera) is not first and len(selfie.inputs) == 2


def test_a_mirrored_camera_is_not_swapped_for_the_person(selfie):
    plain, mirrored = funground_ml.person(FakeCamera(solid_picture(), mirror=False)), funground_ml.person(FakeCamera(solid_picture(), mirror=True))
    assert plain._snapshot().pixels == mirrored._snapshot().pixels               # the mask is in the picture's own pixels


def test_person_says_what_it_needs_when_given_something_else():
    with pytest.raises(TypeError, match=r"ml\.person\(\) needs a camera from camera\.open\(\) or a picture from f\.load_image\(\), not str"):
        funground_ml.person("a.png")
