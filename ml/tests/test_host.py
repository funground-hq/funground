"""Tests of the host path of funground-ml: the models run in a web page (S-232). No browser, no model file, no network."""
from __future__ import annotations

import os
import subprocess
import sys

import pytest

import funground_ml
from funground import host_services
from funground.platform.browser_models import HostModels, MaskResult, PointsResult
from funground_ml import _results

from conftest import ROOT, FakeCamera, solid_picture


def _pairs(n):
    """The flat x, y list of n points; the point numbered i is at (i, 2i)."""
    return [v for i in range(n) for v in (float(i), float(i) * 2)]


class Page:
    """Stands for the page: it records what the models were asked, and answers when the test says so."""

    def __init__(self) -> None:
        self.asked: list[tuple[str, dict]] = []
        self.models = HostModels(lambda command, fields: self.asked.append((command, fields)))

    def requests(self):
        return [fields for command, fields in self.asked if command == "request"]


@pytest.fixture
def page():
    stand_in = Page()
    host_services.models = stand_in.models
    try:
        yield stand_in
    finally:
        host_services.models = None


# ---- HostModels on its own
def test_there_is_no_result_before_the_first_push():
    models = HostModels(lambda command, fields: None)
    assert models.latest("pose", 1) is None


def test_the_latest_result_is_what_was_pushed_last():
    models = HostModels(lambda command, fields: None)
    models.request("pose", 7, bytes(16), 2, 2)
    models.push("pose", 7, _pairs(33), 0.9, 2, 2)
    first = models.latest("pose", 7)
    assert first.score == 0.9 and len(first.points) == 33 and first.points[3] == (3.0, 6.0)
    models.request("pose", 7, bytes(16), 2, 2)
    models.push("pose", 7, None, 0.0, 2, 2)
    assert models.latest("pose", 7).points is None          # "nobody" is a result too
    assert models.latest("hand", 7) is None and models.latest("pose", 8) is None      # each task and source has its own


def test_one_request_is_in_flight_for_each_task_and_source():
    asked = []
    models = HostModels(lambda command, fields: asked.append(command))
    assert models.request("pose", 1, bytes(16), 2, 2) is True
    assert models.request("pose", 1, bytes(16), 2, 2) is False              # dropped, not queued
    assert models.request("hand", 1, bytes(16), 2, 2) is True               # another task
    assert models.request("pose", 2, bytes(16), 2, 2) is True               # another source
    assert asked == ["request"] * 3
    models.push("pose", 1, None, 0.0, 2, 2)
    assert models.request("pose", 1, bytes(16), 2, 2) is True               # free again once the answer is in
    assert asked == ["request"] * 4


def test_a_dropped_picture_is_not_kept_for_later():
    seen = []
    models = HostModels(lambda command, fields: seen.append(fields.get("pixels")))
    models.request("pose", 1, b"\x01" * 16, 2, 2)
    models.request("pose", 1, b"\x02" * 16, 2, 2)
    models.push("pose", 1, None, 0.0, 2, 2)
    assert seen == [b"\x01" * 16]                                           # the second picture is gone


def test_a_result_nobody_asked_for_is_ignored():
    models = HostModels(lambda command, fields: None)
    models.push("pose", 5, _pairs(33), 0.9, 2, 2)
    assert models.latest("pose", 5) is None and models.generation == 0


def test_a_wrong_sized_picture_or_odd_points_are_refused():
    models = HostModels(lambda command, fields: None)
    with pytest.raises(ValueError, match="width \\* height \\* 4"):
        models.request("pose", 1, bytes(10), 2, 2)
    models.request("pose", 1, bytes(16), 2, 2)
    with pytest.raises(ValueError, match="x, y pairs"):
        models.push("pose", 1, [1.0, 2.0, 3.0], 0.9, 2, 2)


def test_without_a_callback_nothing_is_asked_and_there_is_never_a_result():
    models = HostModels()
    assert models.busy("pose", 1) and models.request("pose", 1, bytes(16), 2, 2) is False
    assert models.latest("pose", 1) is None


def test_close_forgets_everything_and_tells_the_page_once():
    asked = []
    models = HostModels(lambda command, fields: asked.append(command))
    models.close()
    assert asked == []                                                      # nothing was asked, so nothing to tell
    models.request("pose", 1, bytes(16), 2, 2)
    models.push("pose", 1, None, 0.0, 2, 2)
    models.close()
    models.close()
    assert asked == ["request", "close"]
    assert models.latest("pose", 1) is None


def test_a_task_the_page_cannot_run_prints_once_and_is_not_asked_again(capsys):
    asked = []
    models = HostModels(lambda command, fields: asked.append(command))
    models.request("pose", 1, bytes(16), 2, 2)
    models.unavailable("pose", "Could not download the pose model.")
    models.unavailable("pose", "Could not download the pose model.")
    assert capsys.readouterr().out == "Could not download the pose model.\n"
    assert models.request("pose", 1, bytes(16), 2, 2) is False and asked == ["request"]
    assert models.request("hand", 1, bytes(16), 2, 2) is True               # the hand is another task


def test_a_mask_result_is_a_result_of_its_own_kind():
    models = HostModels(lambda command, fields: None)
    models.request("person", 3, bytes(16), 2, 2)
    models.push_mask("person", 3, bytes([0, 64, 128, 255]), 2, 2, 640, 480)
    found = models.latest("person", 3)
    assert isinstance(found, MaskResult) and not isinstance(found, PointsResult)
    assert found == MaskResult(bytes([0, 64, 128, 255]), 2, 2, 640, 480) and models.generation == 1
    models.request("pose", 3, bytes(16), 2, 2)
    models.push("pose", 3, None, 0.0, 2, 2)
    assert isinstance(models.latest("pose", 3), PointsResult)               # points stay points


def test_a_mask_is_taken_as_bytes_from_any_buffer_and_a_wrong_length_is_refused():
    models = HostModels(lambda command, fields: None)
    models.request("person", 1, bytes(16), 2, 2)
    models.push_mask("person", 1, bytearray([1, 2, 3, 4]), 2, 2, 2, 2)
    assert models.latest("person", 1).mask == bytes([1, 2, 3, 4])
    models.request("person", 1, bytes(16), 2, 2)
    with pytest.raises(ValueError, match="mask_width \\* mask_height"):
        models.push_mask("person", 1, bytes(5), 2, 2, 2, 2)
    models.request("person", 2, bytes(16), 2, 2)
    with pytest.raises(ValueError, match="mask_width \\* mask_height"):
        models.push_mask("person", 2, b"", 0, 0, 2, 2)


def test_a_mask_nobody_asked_for_is_ignored():
    models = HostModels(lambda command, fields: None)
    models.push_mask("person", 5, bytes(4), 2, 2, 2, 2)
    assert models.latest("person", 5) is None and models.generation == 0


# ---- ml.pose and ml.hand on the host path
def test_pose_is_none_until_the_first_result_arrives(page):
    camera = FakeCamera(solid_picture())
    assert funground_ml.pose(camera) is None
    assert len(page.requests()) == 1
    request = page.requests()[0]
    assert (request["task"], request["width"], request["height"]) == ("pose", 64, 48)
    assert len(request["pixels"]) == 64 * 48 * 4
    assert funground_ml.pose(camera) is None                                # still waiting: no second request


def test_the_picture_is_sent_as_opaque_rgba(page):
    camera = FakeCamera(solid_picture(2, 1, blue=10))                       # blue 10, green 90, red 120
    funground_ml.pose(camera)
    assert page.requests()[0]["pixels"] == bytes([120, 90, 10, 255]) * 2


def test_a_result_gives_a_body_and_the_same_one_twice_in_a_frame(page):
    camera = FakeCamera(solid_picture(), mirror=False)
    funground_ml.pose(camera)
    key = page.requests()[0]["key"]
    page.models.push("pose", key, _pairs(33), 0.8, 64, 48)
    first = funground_ml.pose(camera)
    assert isinstance(first, _results.Body) and first.score == 0.8
    assert (first.left_wrist.x, first.left_wrist.y) == (15.0, 30.0)
    assert funground_ml.pose(camera) is first                               # the same answer, no more work
    assert len(page.requests()) == 1


def test_a_still_picture_gets_its_answer_when_it_arrives_without_a_second_request(page):
    picture = solid_picture()
    assert funground_ml.pose(picture) is None
    key = page.requests()[0]["key"]
    page.models.push("pose", key, _pairs(33), 0.8, 64, 48)
    assert funground_ml.pose(picture) is not None
    assert funground_ml.pose(picture) is not None
    assert len(page.requests()) == 1                                        # the picture did not change


def test_the_next_frame_asks_again_and_may_still_show_the_older_result(page):
    camera = FakeCamera(solid_picture(), mirror=False)
    funground_ml.pose(camera)
    key = page.requests()[0]["key"]
    page.models.push("pose", key, _pairs(33), 0.8, 64, 48)
    old = funground_ml.pose(camera)
    camera.picture = solid_picture(blue=50)                                 # a new frame
    behind = funground_ml.pose(camera)
    assert len(page.requests()) == 2                                        # the new frame was sent
    assert (behind.nose.x, behind.nose.y) == (old.nose.x, old.nose.y)       # the older answer until the next arrives


def test_nobody_found_gives_none(page):
    picture = solid_picture()
    funground_ml.hand(picture)
    page.models.push("hand", page.requests()[0]["key"], None, 0.0, 64, 48)
    assert funground_ml.hand(picture) is None


def test_a_mirrored_camera_swaps_the_sides_in_python(page):
    plain, mirrored = FakeCamera(solid_picture(), mirror=False), FakeCamera(solid_picture(), mirror=True)
    funground_ml.pose(plain)
    funground_ml.pose(mirrored)
    for request in page.requests():
        page.models.push("pose", request["key"], _pairs(33), 0.9, 64, 48)
    a, b = funground_ml.pose(plain), funground_ml.pose(mirrored)
    assert a.left_wrist.x == 15.0 and b.left_wrist.x == 16.0 and b.right_wrist.x == 15.0
    assert b.nose.x == a.nose.x


def test_points_are_scaled_from_the_size_the_page_used_to_logical_pixels(page):
    picture = solid_picture(64, 48)
    funground_ml.hand(picture)
    page.models.push("hand", page.requests()[0]["key"], _pairs(21), 0.95, 128, 96)      # the page worked on twice the size
    palm = funground_ml.hand(picture)
    assert isinstance(palm, _results.Hand)
    assert (palm.index_finger_tip.x, palm.index_finger_tip.y) == (8.0 * 64 / 128, 16.0 * 48 / 96)


def test_a_task_that_is_unavailable_gives_none_and_prints_one_line(page, capsys):
    picture = solid_picture()
    funground_ml.pose(picture)
    page.models.unavailable("pose", "Could not download the pose model.")
    assert funground_ml.pose(picture) is None and funground_ml.pose(FakeCamera(solid_picture())) is None
    assert capsys.readouterr().out == "Could not download the pose model.\n"


def test_a_source_that_is_not_a_camera_or_picture_is_still_a_type_error(page):
    with pytest.raises(TypeError, match="needs a camera"):
        funground_ml.pose("not a picture")


# ---- ml.person on the host path
def _alphas(picture):
    return picture._snapshot().pixels[3::4]


def test_person_is_none_until_the_first_mask_arrives_and_then_a_picture_cut_out_by_it(page):
    camera = FakeCamera(solid_picture(512, 8))
    assert funground_ml.person(camera) is None
    request = page.requests()[0]
    assert (request["task"], request["width"], request["height"]) == ("person", 512, 8)
    assert funground_ml.person(camera) is None and len(page.requests()) == 1       # waiting: no second request
    page.models.push_mask("person", request["key"], bytes(128) + bytes([255]) * 128, 256, 1, 512, 8)
    cut = funground_ml.person(camera)
    assert (cut.width, cut.height) == (512, 8)
    alphas = _alphas(cut)
    assert alphas[:255] == bytes(255) and alphas[257:512] == bytes([255]) * 255 and 0 < alphas[255] < alphas[256] < 255
    assert funground_ml.person(camera) is cut                                       # the same picture twice in a frame
    assert len(page.requests()) == 1


def test_a_new_frame_is_cut_out_by_the_older_mask_until_the_next_one_arrives(page):
    camera = FakeCamera(solid_picture(64, 48, blue=10))
    funground_ml.person(camera)
    key = page.requests()[0]["key"]
    page.models.push_mask("person", key, bytes([255]) * 4, 2, 2, 64, 48)
    old = funground_ml.person(camera)
    camera.picture._write_pixels(bytes([200, 90, 120, 255]) * (64 * 48))            # a new frame, the same size
    behind = funground_ml.person(camera)
    assert len(page.requests()) == 2                                                # the new frame was sent
    assert behind is not old and behind._snapshot().pixels[:4] == bytes([200, 90, 120, 255])    # this frame's pixels, the old mask


def test_a_mask_for_a_picture_of_another_size_still_covers_the_whole_picture(page):
    picture = solid_picture(64, 48)
    funground_ml.person(picture)
    page.models.push_mask("person", page.requests()[0]["key"], bytes([255]) * 16, 4, 4, 32, 24)   # the page saw half the size
    assert set(_alphas(funground_ml.person(picture))) == {255}


def test_person_in_a_page_gives_the_same_picture_as_the_same_mask_on_the_desktop_path(page):
    camera = FakeCamera(solid_picture(512, 8, blue=70), mirror=False)
    funground_ml.person(camera)
    mask = bytes(range(256))
    page.models.push_mask("person", page.requests()[0]["key"], mask, 256, 1, 512, 8)
    assert funground_ml.person(camera)._snapshot().pixels == camera.picture._masked_copy(mask, 256, 1)._snapshot().pixels


def test_a_person_task_that_is_unavailable_gives_none_and_prints_one_line(page, capsys):
    picture = solid_picture()
    funground_ml.person(picture)
    page.models.unavailable("person", "Could not download the person model.")
    assert funground_ml.person(picture) is None
    assert capsys.readouterr().out == "Could not download the person model.\n"
    assert funground_ml.pose(picture) is None and len(page.requests()) == 2          # the pose task is another task


# ---- what a page does not load
def _run(code: str):
    env = dict(os.environ, FUNGROUND_HEADLESS="1")
    return subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=300, env=env, cwd=str(ROOT))


def test_the_host_path_imports_no_numpy_pillow_or_desktop_module():
    code = (
        "import sys\n"
        "sys.path.insert(0, 'ml/tests')\n"
        "from funground import host_services\n"
        "from funground.platform.browser_models import HostModels\n"
        "from conftest import FakeCamera, solid_picture\n"
        "from funground import ml\n"
        "page = []\n"
        "host_services.models = HostModels(lambda command, fields: page.append((command, fields)))\n"
        "camera = FakeCamera(solid_picture())\n"
        "assert ml.pose(camera) is None and ml.hand(camera) is None and ml.person(camera) is None\n"
        "host_services.models.push('pose', page[0][1]['key'], [float(i) for i in range(66)], 0.9, 64, 48)\n"
        "assert ml.pose(camera) is not None\n"
        "host_services.models.push_mask('person', page[2][1]['key'], bytes([255]) * 16, 4, 4, 64, 48)\n"
        "assert ml.person(camera) is not None\n"
        "gone = [name for name in ('onnxruntime', 'numpy', 'PIL', 'funground_ml._runtime', 'funground_ml._glue',\n"
        "                          'funground_ml._fetch') if name in sys.modules]\n"
        "print('imported:', gone)\n"
    )
    done = _run(code)
    assert done.returncode == 0, done.stderr
    assert done.stdout.strip().splitlines()[-1] == "imported: []"


def test_importing_the_library_loads_no_numpy_or_pillow():
    done = _run("import sys; import funground_ml; print([n for n in ('numpy', 'PIL', 'onnxruntime') if n in sys.modules])")
    assert done.returncode == 0, done.stderr
    assert done.stdout.strip().splitlines()[-1] == "[]"


# ---- the Session hands the models over
def test_a_session_supplies_the_models_for_its_run_and_takes_them_away():
    from funground.web import Session

    asked = []
    session = Session(64, 48, on_models=lambda command, fields: asked.append((command, fields)))
    assert host_services.models is not None
    session.start(
        "import funground as f\n"
        "from funground import ml\n"
        "f.size(64, 48)\n"
        "g = f.create_graphics(32, 24)\n"
        "def draw():\n"
        "    print('body', ml.pose(g))\n"
        "f.run()\n"
    )
    session.step(0.0)
    request = next(fields for command, fields in asked if command == "request")
    assert (request["task"], request["width"], request["height"]) == ("pose", 32, 24)
    session.push_models("pose", request["key"], _pairs(33), 0.9, 32, 24)
    session.step(1.0)
    session.push_models_mask("person", request["key"], bytes(4), 2, 2, 32, 24)         # nothing asked for it: ignored
    session.models_unavailable("hand", "no hand model today")
    session.stop()
    assert host_services.models is None
    assert asked[-1][0] == "close"
