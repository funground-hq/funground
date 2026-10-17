"""Camera input (S-172; contracts I4 and I5; D-089).

The real camera is never opened here. The desktop tests replace `camera_input._camera_module` with a fake
`pygame.camera` that hands out real pygame surfaces, so the desktop device's scaling, mirroring and conversion run for
real. The browser tests use a Session with a fake page that pushes RGBA frames.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pygame
import pytest

import funground as f
from funground import api, camera_input as ci, ir
from funground.picture import Picture
from funground.platform.headless import HeadlessPlatform
from funground.sketch import Sketch
from funground.web import Session

ROOT = Path(__file__).resolve().parent.parent
NATIVE = (16, 8)                  # what the fake device really delivers; the tests ask for 8 x 4


def frame_surface(n: int, size=NATIVE) -> pygame.Surface:
    """Frame number n: red 10 * n on the left half, blue on the right half."""
    surface = pygame.Surface(size, 0, 24)
    surface.fill((0, 0, 200))
    surface.fill((10 * n, 0, 0), (0, 0, size[0] // 2, size[1]))
    return surface


class FakeCamera:
    """pygame.camera.Camera: every query_image() is a new frame, numbered from 1."""

    def __init__(self, module, name, size):
        self.module, self.name, self.size = module, name, size
        self.running = False
        self.count = 0

    def start(self):
        if self.module.fail_to_open:
            raise OSError(self.module.fail_to_open)
        self.running = True

    def stop(self):
        self.running = False

    def query_image(self):
        return self.running and not self.module.silent

    def get_image(self):
        self.count += 1
        return frame_surface(self.count, self.module.native)


class FakeCameraModule:
    def __init__(self, names):
        self.names = names
        self.native = NATIVE
        self.opened: list[FakeCamera] = []
        self.silent = False
        self.fail_to_open = ""

    def init(self):
        pass

    def list_cameras(self):
        return list(self.names)

    def Camera(self, name, size):         # noqa: N802 (pygame's name)
        camera = FakeCamera(self, name, size)
        self.opened.append(camera)
        return camera


@pytest.fixture
def desk(monkeypatch):
    """Two fake cameras on a desktop that is not a Mac."""
    module = FakeCameraModule(["Fake webcam", "Other camera"])
    monkeypatch.setattr(ci, "_camera_module", lambda: module)
    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.delenv("FUNGROUND_HEADLESS", raising=False)
    return module


def run(draw, frames=3, setup=None, fps=None):
    """Run a small sketch for some frames on the headless platform; return the Sketch."""
    sketch = api.use_sketch(Sketch(platform=HeadlessPlatform()))

    def default_setup():
        f.size(8, 4)

    sketch.run_namespace({"setup": setup or default_setup, "draw": draw}, max_frames=frames, fps=fps)
    return sketch


def rgb(x, y):
    c = f.get(x, y)
    return (c.r, c.g, c.b)


def at(picture, x, y):
    c = picture.get(x, y)
    return (c.r, c.g, c.b)


# ---- finding cameras

def test_cameras_lists_the_device_names(desk):
    assert f.cameras() == ["Fake webcam", "Other camera"]


def test_cameras_is_empty_when_headless_and_on_a_mac(desk, monkeypatch):
    monkeypatch.setattr(sys, "platform", "darwin")
    assert f.cameras() == []
    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setenv("FUNGROUND_HEADLESS", "1")
    assert f.cameras() == []


def test_camera_picks_the_first_or_the_one_with_the_name(desk):
    assert f.camera()._device_name == "Fake webcam"
    assert f.camera("other")._device_name == "Other camera"


def test_a_name_that_matches_none_is_a_runtime_error(desk):
    with pytest.raises(RuntimeError, match="'nope'.*Fake webcam.*Other camera"):
        f.camera("nope")


def test_no_camera_is_a_runtime_error(desk):
    desk.names = []
    with pytest.raises(RuntimeError, match="no camera was found"):
        f.camera()


def test_a_bad_name_is_a_value_error(desk):
    with pytest.raises(ValueError, match="name must be text"):
        f.camera(3)
    with pytest.raises(ValueError, match="name must be text"):
        f.camera("")


def test_a_mac_desktop_says_to_use_the_website(desk, monkeypatch):
    monkeypatch.setattr(sys, "platform", "darwin")
    with pytest.raises(RuntimeError, match="Windows and Linux.*website"):
        f.camera()


def test_nothing_opens_until_start(desk):
    cam = f.camera()
    assert desk.opened == [] and not cam.is_ready()
    cam.start()
    assert [c.size for c in desk.opened] == [(640, 480)] and desk.opened[0].running


def test_a_camera_that_cannot_be_opened_is_a_runtime_error_at_start(desk):
    desk.fail_to_open = "busy"
    cam = f.camera()
    with pytest.raises(RuntimeError, match="could not be opened.*busy"):
        cam.start()
    assert not cam.is_ready()


def test_start_checks_its_arguments(desk):
    cam = f.camera()
    for bad in (0, -3, 2.5, "big", True):
        with pytest.raises(ValueError, match="width must be a whole number above 0"):
            cam.start(bad, 4)
    with pytest.raises(ValueError, match="mirror"):
        cam.start(8, 4, mirror="yes")


# ---- headless

def test_a_headless_camera_opens_nothing_and_is_never_ready(desk, monkeypatch):
    monkeypatch.setenv("FUNGROUND_HEADLESS", "1")
    cam = f.camera()
    seen = []

    def draw():
        f.background("white")
        f.image(cam, 0, 0)
        seen.append((cam.is_ready(), rgb(1, 1)))

    def setup():
        f.size(8, 4)
        cam.start(8, 4)

    run(draw, setup=setup)
    assert desk.opened == []
    assert seen == [(False, (255, 255, 255))] * 3


# ---- the frame

def test_image_draws_the_frame_scaled_and_mirrored(desk):
    cam = f.camera()
    seen = []

    def setup():
        f.size(8, 4)
        cam.start(8, 4)

    def draw():
        f.image(cam, 0, 0)
        seen.append((cam.is_ready(), rgb(1, 1), rgb(6, 1)))

    run(draw, setup=setup)
    assert (cam.width, cam.height) == (8, 4)
    # mirrored: frame 1 is red on the left, so blue is now on the left
    assert seen[0] == (True, (0, 0, 200), (10, 0, 0))
    assert seen[1][2] == (20, 0, 0) and seen[2][2] == (30, 0, 0)       # a new frame before each draw


def test_image_draws_the_frame_unmirrored(desk):
    cam = f.camera()
    seen = []

    def setup():
        f.size(8, 4)
        cam.start(8, 4, mirror=False)

    def draw():
        f.image(cam, 0, 0)
        seen.append((rgb(1, 1), rgb(6, 1)))

    run(draw, setup=setup, frames=1)
    assert seen == [((10, 0, 0), (0, 0, 200))]


def test_image_takes_the_tint_the_size_and_the_image_mode(desk):
    cam = f.camera()

    def setup():
        f.size(8, 4)
        cam.start(8, 4, mirror=False)

    def draw():
        f.background("white")
        f.image_mode("center")
        f.image(cam, 4, 2, 4, 2)
        assert rgb(0, 0) == (255, 255, 255)           # the image is 4 x 2 in the middle
        assert rgb(3, 1) == (10, 0, 0)

    run(draw, setup=setup, frames=1)


def test_a_frame_is_scaled_to_the_asked_size_from_any_native_size(desk):
    desk.native = (4, 2)
    cam = f.camera()
    cam.start(8, 4, mirror=False)
    sketch = run(lambda: None, setup=lambda: f.size(8, 4), frames=1)
    assert cam.is_ready() is False                    # the sketch ended, so the camera was let go
    cam.start(8, 4, mirror=False)
    ci.take_frames(sketch)
    picture = cam.picture()
    assert (picture.width, picture.height) == (8, 4)
    assert at(picture, 0, 0) == (10, 0, 0) and at(picture, 7, 3) == (0, 0, 200)


def test_picture_is_black_before_the_first_frame(desk):
    cam = f.camera()
    cam.start(8, 4)
    desk.silent = True
    f.size(8, 4)
    picture = cam.picture()
    assert (picture.width, picture.height) == (8, 4)
    assert {at(picture, x, y) for x in range(8) for y in range(4)} == {(0, 0, 0)}
    assert picture.get(0, 0).a == 255
    assert not cam.is_ready()


def test_image_draws_nothing_before_the_first_frame(desk):
    desk.silent = True
    cam = f.camera()

    def setup():
        f.size(8, 4)
        cam.start(8, 4)

    def draw():
        f.background("white")
        f.image(cam, 0, 0)
        assert rgb(1, 1) == (255, 255, 255)

    run(draw, setup=setup)


def test_picture_is_an_independent_copy(desk):
    cam = f.camera()
    pictures = []

    def setup():
        f.size(8, 4)
        cam.start(8, 4, mirror=False)

    def draw():
        shot = cam.picture()
        shot.set(1, 1, "white")                        # change the copy...
        pictures.append(shot)
        assert at(cam.picture(), 1, 1) != (255, 255, 255)   # ...not the camera

    run(draw, setup=setup)
    assert len({id(p) for p in pictures}) == 3 and all(isinstance(p, Picture) for p in pictures)
    # an earlier copy keeps its frame while the camera goes on (frame 1 had red 10 on the left)
    assert at(pictures[0], 2, 2) == (10, 0, 0)
    assert at(pictures[2], 2, 2) == (30, 0, 0)


def test_the_frame_is_taken_once_before_each_draw(desk):
    cam = f.camera()
    pairs = []

    def setup():
        f.size(8, 4)
        cam.start(8, 4, mirror=False)

    def draw():
        first = at(cam.picture(), 2, 2)
        f.image(cam, 0, 0)
        pairs.append((first, at(cam.picture(), 2, 2), rgb(2, 2)))

    run(draw, setup=setup)
    assert all(a == b and a[:3] == c for a, b, c in pairs)
    assert [p[0][0] for p in pairs] == [10, 20, 30]


def test_the_camera_is_one_picture_with_a_new_version_each_frame(desk):
    cam = f.camera()
    seen = []

    def setup():
        f.size(8, 4)
        cam.start(8, 4)

    def draw():
        f.image(cam, 0, 0)
        f.image(cam, 4, 0)
        images = [op for op in api.active_sketch().frame.ops if isinstance(op, ir.Image)]
        seen.append([(op.source, op.version) for op in images])

    run(draw, setup=setup)
    names = {name for frame in seen for name, _ in frame}
    versions = [frame[0][1] for frame in seen]
    assert len(names) == 1                              # one picture...
    assert seen[0][0] == seen[0][1]                     # ...the same frame in both places...
    assert len(set(versions)) == 3                      # ...and new content each frame


def test_save_writes_a_png_of_the_frame(desk, tmp_path):
    cam = f.camera()
    path = tmp_path / "me.png"

    def setup():
        f.size(8, 4)
        cam.start(8, 4, mirror=False)

    run(lambda: cam.save(str(path)) if f.frame_count == 1 else None, setup=setup, frames=2)
    saved = f.load_image(str(path))
    assert (saved.width, saved.height) == (8, 4)
    assert at(saved, 1, 1) == (20, 0, 0) and at(saved, 6, 1) == (0, 0, 200)


def test_save_writes_a_jpg_and_refuses_other_endings(desk, tmp_path):
    pytest.importorskip("PIL")
    cam = f.camera()
    f.size(8, 4)
    cam.start(8, 4)
    cam.save(str(tmp_path / "me.jpg"))
    assert (tmp_path / "me.jpg").read_bytes()[:2] == b"\xff\xd8"
    with pytest.raises(ValueError, match=r"\.png, \.jpg or \.jpeg"):
        cam.save(str(tmp_path / "me.bmp"))


def test_stop_lets_the_camera_go(desk):
    cam = f.camera()
    cam.start(8, 4)
    assert desk.opened[0].running
    cam.stop()
    assert not desk.opened[0].running and not cam.is_ready()
    cam.stop()                                          # again: nothing happens


def test_the_end_of_the_sketch_stops_the_camera(desk):
    cam = f.camera()

    def setup():
        f.size(8, 4)
        cam.start(8, 4)

    sketch = run(lambda: None, setup=setup, frames=2)
    sketch.finish()
    assert not desk.opened[0].running and not cam.is_ready()


# ---- clips

def test_record_keeps_one_frame_per_drawn_frame(desk):
    cam = f.camera()
    clips = []

    def setup():
        f.size(8, 4)
        cam.start(8, 4, mirror=False)

    def draw():
        if f.frame_count == 1:
            clips.append(cam.record(0.5))              # 0.5 s at 10 frames a second

    run(draw, setup=setup, frames=10, fps=10)
    clip = clips[0]
    assert clip.fps == 10 and clip.done and len(clip) == 5
    first, last = clip.frame(0), clip.frame(-1)
    assert at(first, 1, 1) == (30, 0, 0)    # the recording starts with the frame after the call (frame 3)
    assert at(last, 1, 1) == (70, 0, 0)
    assert at(clip.frame(4), 1, 1) == at(last, 1, 1)
    assert (first.width, first.height) == (8, 4) and first is not clip.frame(0)


def test_a_clip_grows_and_stops_when_full(desk):
    cam = f.camera()
    lengths = []

    def setup():
        f.size(8, 4)
        cam.start(8, 4)

    def draw():
        if f.frame_count == 0:
            lengths.append(cam.record(0.3))
        lengths.append(len(lengths[0]))

    run(draw, setup=setup, frames=8, fps=10)
    assert lengths[1:] == [0, 1, 2, 3, 3, 3, 3, 3]
    assert lengths[0].done


def test_a_clip_that_is_not_ready_holds_nothing(desk):
    desk.silent = True
    cam = f.camera()

    def setup():
        f.size(8, 4)
        cam.start(8, 4)

    clips = []
    run(lambda: clips.append(cam.record(1)) if not clips else None, setup=setup, frames=3, fps=10)
    assert len(clips[0]) == 0 and clips[0].done            # the sketch's end stopped the camera, so it is over


def test_frame_index_errors(desk):
    cam = f.camera()
    f.size(8, 4)
    cam.start(8, 4)
    clip = cam.record(1)
    with pytest.raises(IndexError, match="0 frames"):
        clip.frame(0)
    with pytest.raises(IndexError):
        clip.frame(-1)
    sketch = api.active_sketch()
    for _ in range(2):
        ci.take_frames(sketch)
    assert len(clip) == 2
    clip.frame(1), clip.frame(-2)
    for bad in (2, -3):
        with pytest.raises(IndexError, match="2 frames"):
            clip.frame(bad)
    with pytest.raises(TypeError):
        clip.frame(0.5)


def test_pause_and_resume_leave_the_paused_frames_out(desk):
    cam = f.camera()
    f.size(8, 4)
    cam.start(8, 4)
    clip = cam.record(5)
    sketch = api.active_sketch()
    ci.take_frames(sketch)
    clip.pause()
    assert clip.is_paused()
    for _ in range(4):
        ci.take_frames(sketch)
    assert len(clip) == 1 and not clip.done              # paused: nothing kept, and not over
    clip.resume()
    ci.take_frames(sketch)
    assert len(clip) == 2 and not clip.is_paused()


def test_clip_stop_ends_the_recording_and_keeps_the_camera_on(desk):
    cam = f.camera()
    f.size(8, 4)
    cam.start(8, 4)
    clip = cam.record(5)
    sketch = api.active_sketch()
    for _ in range(3):
        ci.take_frames(sketch)
    clip.stop()
    assert clip.done and len(clip) == 3
    ci.take_frames(sketch)
    assert len(clip) == 3 and cam.is_ready()            # nothing more is kept, and the camera still gives frames


def test_stop_ends_a_recording_early_and_what_was_kept_stays(desk):
    cam = f.camera()
    f.size(8, 4)
    cam.start(8, 4)
    clip = cam.record(5)
    sketch = api.active_sketch()
    ci.take_frames(sketch)
    ci.take_frames(sketch)
    cam.stop()
    assert len(clip) == 2 and clip.done                    # over, though not full, so a sketch waiting on done saves
    cam.start(8, 4)
    ci.take_frames(sketch)
    assert len(clip) == 2


def test_record_needs_a_started_camera(desk):
    cam = f.camera()
    f.size(8, 4)
    with pytest.raises(RuntimeError, match=r"Call cam.start\(\) first"):
        cam.record(1)


def test_the_clip_cap_names_the_memory(desk):
    cam = f.camera()
    f.size(8, 4)
    cam.start(640, 480)
    with pytest.raises(ValueError, match=r"at most 10 seconds.*640 x 480.*60 frames a second.*about 774 MB"):
        cam.record(10.5 * 1)
    for bad in (0, -1, True, "3", None, float("nan")):
        with pytest.raises(ValueError, match="more than 0 and at most 10"):
            cam.record(bad)
    cam.record(10)                                      # the cap itself is allowed


def test_clip_save_writes_a_readable_gif(desk, tmp_path):
    pytest.importorskip("PIL")
    from PIL import Image

    cam = f.camera()
    clips = []

    def setup():
        f.size(8, 4)
        cam.start(8, 4, mirror=False)

    def draw():
        if not clips:
            clips.append(cam.record(0.4))

    run(draw, setup=setup, frames=8, fps=10)
    path = tmp_path / "me.gif"
    clips[0].save(str(path))
    with Image.open(path) as gif:
        assert gif.size == (8, 4) and gif.n_frames == 4
        assert gif.info["loop"] == 0


def test_clip_save_errors(desk, tmp_path):
    cam = f.camera()
    f.size(8, 4)
    cam.start(8, 4)
    clip = cam.record(1)
    with pytest.raises(ValueError, match="no frames yet"):
        clip.save(str(tmp_path / "me.gif"))
    ci.take_frames(api.active_sketch())
    for bad in ("me.avi", "me", "me.png"):
        with pytest.raises(ValueError, match=r"must end in \.gif or \.mp4"):
            clip.save(str(tmp_path / bad))
    assert not list(tmp_path.iterdir())


# ---- the desktop module in a program that has no pygame camera (the boundary also checks the import)

def test_pygame_is_not_imported_by_importing_funground():
    script = ("import sys; sys.path.insert(0, sys.argv[1])\nimport funground\n"
              "assert 'pygame.camera' not in sys.modules\nprint('ok')")
    done = subprocess.run([sys.executable, "-I", "-c", script, str(ROOT)], capture_output=True, text=True, timeout=300,
                          env={**os.environ, "FUNGROUND_HEADLESS": "1"})
    assert done.returncode == 0 and "ok" in done.stdout, done.stderr


# ---- the browser: a Session with a page that opens the camera and pushes frames

class Page:
    """The page: keeps the camera commands and pushes RGBA frames."""

    def __init__(self):
        self.commands: list[tuple[str, dict]] = []
        self.session = None

    def on_camera(self, command, fields):
        self.commands.append((command, dict(fields)))

    def names(self):
        return [c[0] for c in self.commands]

    def push(self, n, size=(8, 4)):
        """Frame n at this size: red 10 * n on the left half, blue on the right half, as RGBA."""
        w, h = size
        pixels = bytearray()
        for _ in range(h):
            for x in range(w):
                pixels += bytes((10 * n, 0, 0, 255)) if x < w // 2 else bytes((0, 0, 200, 255))
        self.session.push_camera(bytes(pixels), w, h)


SOURCE = """
import funground as f
cam = f.camera()
def setup():
    f.size(8, 4)
    cam.start(8, 4)
def draw():
    f.image(cam, 0, 0)
f.run()
"""


NO_CAMERA = """
import funground as f
def setup():
    f.size(8, 4)
def draw():
    pass
f.run()
"""


@pytest.fixture
def page():
    page = Page()
    page.session = Session(8, 4, on_camera=page.on_camera)
    yield page
    page.session.stop()


def test_the_page_is_told_to_start_stop_and_close(page):
    page.session.start(SOURCE)
    assert page.commands == [("start", {"width": 8, "height": 4})]
    page.session.stop()
    assert page.names() == ["start", "stop", "close"]
    assert page.commands[1:] == [("stop", {}), ("close", {})]


def test_a_pushed_frame_is_drawn_mirrored(page):
    page.session.start(SOURCE)
    page.session.step(0.0)
    assert rgb(1, 1) == (0, 0, 0)                       # nothing has arrived: nothing is drawn
    page.push(1)
    page.session.step(1.0)
    assert (rgb(1, 1), rgb(6, 1)) == ((0, 0, 200), (10, 0, 0))
    page.push(2)
    page.session.step(2.0)
    assert rgb(6, 1) == (20, 0, 0)


def test_only_the_latest_frame_is_used(page):
    page.session.start(SOURCE)
    for n in (1, 2, 3):
        page.push(n)
    page.session.step(0.0)
    assert rgb(6, 1) == (30, 0, 0)


def test_a_frame_of_another_size_is_scaled(page):
    page.session.start(SOURCE)
    page.push(4, size=(16, 8))
    page.session.step(0.0)
    assert (rgb(1, 1), rgb(6, 1)) == ((0, 0, 200), (40, 0, 0))


def test_a_wrong_sized_frame_is_a_value_error(page):
    page.session.start(SOURCE)
    with pytest.raises(ValueError, match="width \\* height \\* 4"):
        page.session.push_camera(b"\x00" * 10, 8, 4)


def test_frames_are_ignored_until_the_sketch_starts_the_camera(page):
    page.push(1)
    page.session.start(SOURCE)
    page.session.step(0.0)
    assert rgb(6, 1) == (0, 0, 0)


def test_without_on_camera_the_camera_never_becomes_ready():
    session = Session(8, 4)
    try:
        session.start(SOURCE)
        session.push_camera(b"\x80" * (8 * 4 * 4), 8, 4)
        session.step(0.0)
        assert rgb(1, 1) == (0, 0, 0)
        assert not f.camera().is_ready()
    finally:
        session.stop()


def test_camera_unavailable_prints_one_line_for_each_start(page, capsys):
    page.session.start(SOURCE)
    page.session.camera_unavailable("the camera was refused")
    page.session.camera_unavailable("the camera was refused")
    page.session.step(0.0)
    assert capsys.readouterr().out == "The camera is not available: the camera was refused.\n"
    assert rgb(1, 1) == (0, 0, 0)
    page.session.stop()
    page.session.camera_unavailable("again")             # the run is over: nothing more to say
    assert capsys.readouterr().out == ""


def test_the_browser_choose_the_camera_and_mp4_is_refused(page, tmp_path):
    page.session.start(SOURCE)
    assert f.cameras() == []
    with pytest.raises(RuntimeError, match="only works in the desktop version"):
        f.camera("USB")
    page.push(1)
    page.session.step(0.0)
    cam = f.camera()
    cam.start(8, 4)
    clip = cam.record(1)
    ci.take_frames(api.canvas_sketch())
    with pytest.raises(ValueError, match=r"must end in \.gif, not"):
        clip.save(str(tmp_path / "me.mp4"))


def test_a_browser_clip_is_saved_as_a_gif(page, tmp_path):
    pytest.importorskip("PIL")
    page.session.start(NO_CAMERA)
    cam = f.camera()
    cam.start(8, 4)
    clip = cam.record(0.2)
    for n in (1, 2, 3):
        page.push(n)
        ci.take_frames(api.canvas_sketch())
    assert len(clip) == 3
    clip.save(str(tmp_path / "me.gif"))
    assert (tmp_path / "me.gif").stat().st_size > 0


def test_a_session_runs_without_pygame_camera_or_pygame():
    script = (
        "import sys; sys.path.insert(0, sys.argv[1])\n"
        "import funground as f\n"
        "from funground.web import Session\n"
        "got = []\n"
        "s = Session(8, 4, on_camera=lambda c, fields: got.append(c))\n"
        "s.start('import funground as f\\ncam = f.camera()\\n"
        "def setup():\\n    f.size(8, 4)\\n    cam.start(8, 4)\\n"
        "def draw():\\n    f.image(cam, 0, 0)\\nf.run()\\n')\n"
        "s.push_camera(bytes([9, 9, 9, 255]) * 32, 8, 4)\n"
        "s.step(0.0); s.step(1.0)\n"
        "s.stop()\n"
        "assert 'pygame' not in sys.modules, 'pygame was imported'\n"
        "print(','.join(got))\n")
    done = subprocess.run([sys.executable, "-I", "-c", script, str(ROOT)], capture_output=True, text=True, timeout=300,
                          env={**os.environ, "FUNGROUND_HEADLESS": "1"})
    assert done.returncode == 0, done.stderr
    assert done.stdout.strip() == "start,stop,close"


# ---- loading a clip (S-220, D-109)
def test_a_saved_take_loads_back_as_the_same_clip(desk, tmp_path):
    pytest.importorskip("PIL")
    cam = f.camera()
    clips = []

    def setup():
        f.size(8, 4)
        cam.start(8, 4, mirror=False)

    def draw():
        if not clips:
            clips.append(cam.record(0.4))

    run(draw, setup=setup, frames=8, fps=10)
    path = tmp_path / "take.gif"
    clips[0].save(str(path))
    loaded = f.load_clip(str(path))
    assert loaded.done and len(loaded) == len(clips[0]) == 4
    assert loaded.fps == 10
    picture = loaded.frame(-1)
    assert (picture.width, picture.height) == (8, 4)


def test_a_still_picture_loads_as_one_frame(tmp_path):
    pygame = pytest.importorskip("pygame")
    surface = pygame.Surface((5, 3))
    surface.fill((200, 40, 40))
    path = tmp_path / "still.png"
    pygame.image.save(surface, str(path))
    clip = f.load_clip(str(path))
    assert len(clip) == 1 and clip.done


def test_load_clip_errors(tmp_path):
    with pytest.raises(FileNotFoundError):
        f.load_clip(str(tmp_path / "missing.gif"))
    svg = tmp_path / "shape.svg"
    svg.write_text('<svg xmlns="http://www.w3.org/2000/svg"/>', encoding="utf-8")
    with pytest.raises(ValueError, match="SVG"):
        f.load_clip(str(svg))
    junk = tmp_path / "junk.gif"
    junk.write_bytes(b"not a picture")
    with pytest.raises(ValueError, match="not an animated picture"):
        f.load_clip(str(junk))


def test_the_frame_rate_comes_from_the_middle_delay():
    assert ci._fps_of([100, 100, 100]) == 10
    assert ci._fps_of([40, 40, 2000]) == 25                 # one long pause does not slow the whole clip
    assert ci._fps_of([0, 0]) == 10                         # 0 ms is shown as 100 ms, as browsers do
