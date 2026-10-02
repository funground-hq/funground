"""GIF and MP4 export (S-100, contract M1, D-048).

ffmpeg is not needed to run these tests: a fake `ffmpeg` program is put first on the PATH. It
records what it was asked to do and how many bytes it was sent. One real-ffmpeg test runs only
when a real ffmpeg is installed.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys

import pytest

import funground as p
from funground import api
from funground.export import motion
from funground.platform.headless import HeadlessPlatform
from funground.sketch import Sketch

PIL = pytest.importorskip("PIL")
from PIL import Image  # noqa: E402

COLOURS = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0)]


def _no_ffmpeg(monkeypatch, tmp_path):
    empty = tmp_path / "empty_path"
    empty.mkdir(exist_ok=True)
    monkeypatch.setenv("PATH", str(empty))
    monkeypatch.setitem(sys.modules, "imageio_ffmpeg", None)   # and no funground[video] either


def _no_pillow(monkeypatch):
    monkeypatch.setitem(sys.modules, "PIL", None)         # `import PIL` now fails


def _pages(colours, size=(24, 16)):
    p.size(*size)
    for number, colour in enumerate(colours):
        if number:
            p.new_page()
        p.background(colour)


def _run_animated(draw, frames, fps=10, size=(24, 16)):
    sketch = api.use_sketch(Sketch(platform=HeadlessPlatform()))
    sketch.run_namespace({"setup": lambda: p.size(*size, fps=fps), "draw": draw}, max_frames=frames)
    return sketch


@pytest.fixture
def fake_ffmpeg(tmp_path, monkeypatch):
    """A program called ffmpeg, first on the PATH. Returns a function that reads what it was given."""
    folder = tmp_path / "fakebin"
    folder.mkdir()
    record = tmp_path / "record.json"
    script = folder / "fake_ffmpeg.py"
    script.write_text(
        "import json, sys\n"
        "data = sys.stdin.buffer.read()\n"
        f"json.dump({{'args': sys.argv[1:], 'bytes': len(data)}}, open({str(record)!r}, 'w'))\n"
        "open(sys.argv[-1], 'wb').write(b'fake')\n",
        encoding="utf-8",
    )
    if os.name == "nt":
        (folder / "ffmpeg.cmd").write_text(f'@echo off\r\n"{sys.executable}" "{script}" %*\r\n', encoding="ascii")
    else:
        launcher = folder / "ffmpeg"
        launcher.write_text(f'#!/bin/sh\nexec "{sys.executable}" "{script}" "$@"\n', encoding="utf-8")
        launcher.chmod(0o755)
    monkeypatch.setenv("PATH", str(folder) + os.pathsep + os.environ.get("PATH", ""))
    return lambda: json.loads(record.read_text(encoding="utf-8"))


# ------------------------------------------------------------------ GIF with Pillow
def test_script_gif_has_a_frame_per_page_with_durations_and_loop(tmp_path):
    out = tmp_path / "x.gif"
    _pages(COLOURS[:3])
    p.save(str(out))
    with Image.open(out) as gif:
        assert gif.n_frames == 3
        assert gif.info["loop"] == 0
        assert gif.size == (24, 16)
        times = []
        for i in range(3):
            gif.seek(i)
            times.append(gif.info["duration"])
        assert times == [100, 100, 100]


def test_frame_duration_changes_apply_to_the_pages_after_it(tmp_path):
    out = tmp_path / "x.gif"
    p.size(24, 16)
    p.background("red")
    p.frame_duration(0.5)
    p.new_page()
    p.background("green")
    p.new_page()
    p.background("blue")
    p.frame_duration(0.014)                       # rounds up to the 20 ms minimum
    p.new_page()
    p.background("white")
    p.save(str(out))
    with Image.open(out) as gif:
        times = []
        for i in range(gif.n_frames):
            gif.seek(i)
            times.append(gif.info["duration"])
    # 0.5 s was set on page 1 and carries on to page 2; 0.014 s was set on page 3 and carries on to page 4
    assert times == [500, 500, 20, 20]


def test_gif_frames_are_the_canvas_pixels(tmp_path):
    out = tmp_path / "x.gif"
    _pages(COLOURS)
    p.save(str(out))
    with Image.open(out) as gif:
        for i, colour in enumerate(COLOURS):
            gif.seek(i)
            assert gif.convert("RGB").getpixel((5, 5)) == colour
            assert gif.convert("RGB").getpixel((23, 15)) == colour


def test_a_see_through_canvas_is_laid_over_white(tmp_path):
    p.size(8, 8)
    p.clear()
    p.fill("black")
    p.rect(0, 0, 4, 8)
    p.new_page()
    p.background("black")
    out = tmp_path / "x.gif"
    p.save(str(out))
    with Image.open(out) as gif:
        first = gif.convert("RGB")
    assert first.getpixel((1, 1)) == (0, 0, 0)
    assert first.getpixel((6, 1)) == (255, 255, 255)


def test_animated_sketch_records_seconds_times_fps_frames(tmp_path):
    out = tmp_path / "anim.gif"

    def draw():
        p.background(COLOURS[p.frame_count % 4])
        if p.frame_count == 1:
            p.save_gif(str(out), 0.5)                 # fps 10 -> 5 frames, starting with the next one

    _run_animated(draw, frames=20, fps=10)
    with Image.open(out) as gif:
        assert gif.n_frames == 5
        gif.seek(0)
        assert gif.convert("RGB").getpixel((3, 3)) == COLOURS[2]       # frame 2 is the first recorded
        assert gif.info["duration"] == 100
        assert gif.info["loop"] == 0


def test_save_gif_in_setup_starts_with_the_first_frame(tmp_path):
    out = tmp_path / "anim.gif"

    def setup():
        p.size(24, 16, fps=10)
        p.save_gif(str(out), 0.3)

    sketch = api.use_sketch(Sketch(platform=HeadlessPlatform()))
    sketch.run_namespace({"setup": setup, "draw": lambda: p.background(COLOURS[p.frame_count % 4])}, max_frames=10)
    with Image.open(out) as gif:
        assert gif.n_frames == 3
        gif.seek(0)
        assert gif.convert("RGB").getpixel((3, 3)) == COLOURS[0]


def test_very_short_recordings_still_take_one_frame(tmp_path):
    out = tmp_path / "one.gif"
    _run_animated(lambda: (p.background("red"), p.save_gif(str(out), 0.001))[1] if p.frame_count == 0 else None,
                  frames=4)
    with Image.open(out) as gif:
        assert gif.n_frames == 1


def test_a_recording_cut_short_by_the_end_of_the_sketch_writes_nothing(tmp_path):
    out = tmp_path / "cut.gif"
    _run_animated(lambda: p.save_gif(str(out), 100) if p.frame_count == 0 else None, frames=3)
    assert not out.exists()


def test_frames_are_logical_size_not_the_backing_scale(tmp_path, monkeypatch):
    monkeypatch.setenv("FUNGROUND_BACKING_SCALE", "2")
    out = tmp_path / "x.gif"
    _pages(COLOURS[:2])
    p.save(str(out))
    with Image.open(out) as gif:
        assert gif.size == (24, 16)
        gif.seek(1)
        assert gif.convert("RGB").getpixel((23, 15)) == COLOURS[1]


# ------------------------------------------------------------------ errors (contract M1)
def test_frame_duration_must_be_above_zero():
    p.size(10, 10)
    for bad in (0, -1, float("inf")):
        with pytest.raises(ValueError, match="above 0"):
            p.frame_duration(bad)
    with pytest.raises(TypeError):
        p.frame_duration("fast")
    with pytest.raises(TypeError):
        p.frame_duration(True)


def test_frame_duration_in_an_animated_sketch_points_to_save_gif():
    def draw():
        p.frame_duration(0.2)

    with pytest.raises(RuntimeError, match="save_gif"):
        _run_animated(draw, frames=1)


def test_save_gif_and_save_movie_need_the_right_extension(tmp_path):
    for call, wrong in ((p.save_gif, "a.mp4"), (p.save_gif, "a.png"), (p.save_movie, "a.gif"), (p.save_movie, "a")):
        with pytest.raises(ValueError, match=r"ending in \.(gif|mp4)"):
            _run_animated(lambda: call(str(tmp_path / wrong), 1), frames=1)


def test_seconds_must_be_a_positive_number(tmp_path):
    for bad in (0, -2):
        with pytest.raises(ValueError, match="above 0"):
            _run_animated(lambda: p.save_gif(str(tmp_path / "a.gif"), bad), frames=1)
    with pytest.raises(TypeError):
        _run_animated(lambda: p.save_gif(str(tmp_path / "a.gif"), "1"), frames=1)


def test_recording_while_recording_is_an_error(tmp_path):
    def draw():
        if p.frame_count == 0:
            p.save_gif(str(tmp_path / "a.gif"), 1)
        if p.frame_count == 1:
            p.save_gif(str(tmp_path / "b.gif"), 1)

    with pytest.raises(RuntimeError, match="another recording"):
        _run_animated(draw, frames=4)


def test_save_gif_in_a_script_is_an_error(tmp_path):
    p.size(10, 10)
    with pytest.raises(RuntimeError, match="animated sketches"):
        p.save_gif(str(tmp_path / "a.gif"), 1)


def test_save_gif_path_in_an_animated_sketch_points_to_save_gif(tmp_path):
    with pytest.raises(ValueError, match=r"save_gif\(path, seconds\)"):
        _run_animated(lambda: p.save(str(tmp_path / "a.gif")), frames=1)
    with pytest.raises(ValueError, match=r"save_movie\(path, seconds\)"):
        _run_animated(lambda: p.save(str(tmp_path / "a.mp4")), frames=1)


def test_pages_of_different_sizes_cannot_be_a_gif(tmp_path):
    p.size(20, 10)
    p.new_page(30, 10)
    with pytest.raises(ValueError, match="same size"):
        p.save(str(tmp_path / "x.gif"))
    assert not (tmp_path / "x.gif").exists()


def test_the_size_error_comes_before_the_encoder_error(tmp_path, monkeypatch):
    _no_pillow(monkeypatch)
    _no_ffmpeg(monkeypatch, tmp_path)
    p.size(20, 10)
    p.new_page(30, 10)
    with pytest.raises(ValueError, match="same size"):
        p.save(str(tmp_path / "x.gif"))


def test_recording_checks_for_an_encoder_straight_away(tmp_path, monkeypatch):
    _no_pillow(monkeypatch)
    _no_ffmpeg(monkeypatch, tmp_path)
    with pytest.raises(RuntimeError, match=r"pip install funground\[extras\]"):
        _run_animated(lambda: p.save_gif(str(tmp_path / "a.gif"), 1), frames=1)


# ------------------------------------------------------------------ without Pillow
def test_no_pillow_and_no_ffmpeg_names_the_extra(tmp_path, monkeypatch):
    _no_pillow(monkeypatch)
    _no_ffmpeg(monkeypatch, tmp_path)
    _pages(COLOURS[:2])
    with pytest.raises(RuntimeError, match=r"pip install funground\[extras\]"):
        p.save(str(tmp_path / "x.gif"))


def test_gif_without_pillow_uses_ffmpeg(tmp_path, monkeypatch, fake_ffmpeg):
    _no_pillow(monkeypatch)
    _pages(COLOURS[:3], size=(20, 10))
    p.save(str(tmp_path / "x.gif"))
    seen = fake_ffmpeg()
    args = seen["args"]
    assert seen["bytes"] == 3 * 20 * 10 * 3
    assert args[args.index("-s") + 1] == "20x10"
    assert args[args.index("-r") + 1] == "10"
    assert args[args.index("-pix_fmt") + 1] == "rgb24"
    assert "palettegen" in args[args.index("-filter_complex") + 1]
    assert args[args.index("-loop") + 1] == "0"
    assert args[-1] == str(tmp_path / "x.gif")
    assert (tmp_path / "x.gif").exists()


# ------------------------------------------------------------------ MP4 with a fake ffmpeg
def test_mp4_command_and_bytes(tmp_path, fake_ffmpeg):
    _pages(COLOURS, size=(24, 16))
    p.save(str(tmp_path / "x.mp4"))
    seen = fake_ffmpeg()
    args = seen["args"]
    assert seen["bytes"] == 4 * 24 * 16 * 3
    assert args[args.index("-c:v") + 1] == "libx264"
    assert args[args.index("-pix_fmt", args.index("-c:v")) + 1] == "yuv420p"
    assert args[args.index("-vf") + 1] == "pad=ceil(iw/2)*2:ceil(ih/2)*2"
    assert args[args.index("-f") + 1] == "rawvideo"
    assert args[args.index("-s") + 1] == "24x16"
    assert args[args.index("-r") + 1] == "10"
    assert args[args.index("-i") + 1] == "-"
    assert args[-1] == str(tmp_path / "x.mp4")
    assert (tmp_path / "x.mp4").read_bytes() == b"fake"


def test_mp4_with_one_frame_time_uses_that_rate(tmp_path, fake_ffmpeg):
    p.size(24, 16)
    p.frame_duration(0.5)                   # set on page 1, it carries on to page 2
    p.background("red")
    p.new_page()
    p.background("blue")
    p.save(str(tmp_path / "x.mp4"))
    args = fake_ffmpeg()["args"]
    assert args[args.index("-r") + 1] == "2"


def test_mp4_with_different_frame_times_repeats_frames_at_a_common_rate(tmp_path, fake_ffmpeg):
    p.size(10, 6)
    p.background("red")                     # 0.1 s
    p.new_page()
    p.frame_duration(0.25)
    p.background("blue")                    # 0.25 s
    p.save(str(tmp_path / "x.mp4"))
    seen = fake_ffmpeg()
    # the page-1 time was 0.1 s when it ended; page 2 changed it to 0.25 s
    # common step 50 ms: 20 per second, 2 copies of page 1 and 5 of page 2
    assert seen["args"][seen["args"].index("-r") + 1] == "20"
    assert seen["bytes"] == 7 * 10 * 6 * 3


def test_odd_sizes_are_sent_as_they_are_and_padded_by_ffmpeg(tmp_path, fake_ffmpeg):
    _pages(COLOURS[:2], size=(25, 15))
    p.save(str(tmp_path / "x.mp4"))
    seen = fake_ffmpeg()
    assert seen["args"][seen["args"].index("-s") + 1] == "25x15"
    assert seen["bytes"] == 2 * 25 * 15 * 3


def test_save_movie_records_frames_at_the_sketch_rate(tmp_path, fake_ffmpeg):
    out = tmp_path / "m.mp4"

    def draw():
        p.background(COLOURS[p.frame_count % 4])
        if p.frame_count == 0:
            p.save_movie(str(out), 1.5)

    _run_animated(draw, frames=40, fps=20)
    seen = fake_ffmpeg()
    assert seen["bytes"] == 30 * 24 * 16 * 3
    assert seen["args"][seen["args"].index("-r") + 1] == "20"
    assert out.exists()


def test_mp4_without_ffmpeg_says_how_to_install_it(tmp_path, monkeypatch):
    _no_ffmpeg(monkeypatch, tmp_path)
    _pages(COLOURS[:2])
    with pytest.raises(RuntimeError) as err:
        p.save(str(tmp_path / "x.mp4"))
    text = str(err.value)
    assert "winget install ffmpeg" in text and "brew install ffmpeg" in text and "apt install ffmpeg" in text
    with pytest.raises(RuntimeError, match="ffmpeg"):
        _run_animated(lambda: p.save_movie(str(tmp_path / "m.mp4"), 1), frames=1)


def test_a_failing_ffmpeg_is_reported(tmp_path, monkeypatch):
    folder = tmp_path / "bad"
    folder.mkdir()
    script = folder / "bad.py"
    script.write_text("import sys\nsys.stdin.buffer.read()\nsys.stderr.write('no such codec')\nsys.exit(1)\n")
    if os.name == "nt":
        (folder / "ffmpeg.cmd").write_text(f'@echo off\r\n"{sys.executable}" "{script}" %*\r\n', encoding="ascii")
    else:
        (folder / "ffmpeg").write_text(f'#!/bin/sh\nexec "{sys.executable}" "{script}" "$@"\n')
        (folder / "ffmpeg").chmod(0o755)
    monkeypatch.setenv("PATH", str(folder) + os.pathsep + os.environ.get("PATH", ""))
    _pages(COLOURS[:2])
    with pytest.raises(RuntimeError, match="no such codec"):
        p.save(str(tmp_path / "x.mp4"))


def test_find_ffmpeg_looks_on_the_path(fake_ffmpeg, tmp_path, monkeypatch):
    assert motion.find_ffmpeg() is not None
    _no_ffmpeg(monkeypatch, tmp_path)
    assert motion.find_ffmpeg() is None


def test_the_video_extra_is_used_when_no_ffmpeg_is_on_the_path(monkeypatch, tmp_path):
    """D-045 = B: imageio-ffmpeg (funground[video]) supplies ffmpeg when the PATH has none."""
    import types
    _no_ffmpeg(monkeypatch, tmp_path)
    fake = types.ModuleType("imageio_ffmpeg")
    fake.get_ffmpeg_exe = lambda: "C:/bundled/ffmpeg.exe"
    monkeypatch.setitem(sys.modules, "imageio_ffmpeg", fake)
    assert motion.find_ffmpeg() == "C:/bundled/ffmpeg.exe"


def test_the_path_comes_before_the_video_extra(fake_ffmpeg, monkeypatch):
    import types
    fake = types.ModuleType("imageio_ffmpeg")
    fake.get_ffmpeg_exe = lambda: "C:/bundled/ffmpeg.exe"
    monkeypatch.setitem(sys.modules, "imageio_ffmpeg", fake)
    assert motion.find_ffmpeg() != "C:/bundled/ffmpeg.exe"


def test_no_ffmpeg_message_names_the_video_extra(monkeypatch, tmp_path):
    _no_ffmpeg(monkeypatch, tmp_path)
    with pytest.raises(RuntimeError, match=r"funground\[video\]"):
        motion.require_encoder("mp4")


@pytest.mark.skipif(motion.find_ffmpeg() is None, reason="no real ffmpeg (PATH or funground[video])")
def test_real_ffmpeg_writes_a_playable_mp4(tmp_path):
    out = tmp_path / "real.mp4"
    _pages(COLOURS, size=(25, 15))
    p.save(str(out))
    assert out.stat().st_size > 0
    probe = subprocess.run([motion.find_ffmpeg(), "-v", "error", "-i", str(out), "-f", "null", "-"],
                           capture_output=True)
    assert probe.returncode == 0


# ------------------------------------------------------------------ helpers and unchanged behaviour
def test_timing_plan():
    assert motion.plan_timing([0.1, 0.1]) == ("10", [1, 1])
    assert motion.plan_timing([0.5]) == ("2", [1])
    assert motion.plan_timing([1 / 60] * 2) == ("60", [1, 1])
    assert motion.plan_timing([0.1, 0.25, 0.3]) == ("20", [2, 5, 6])
    assert motion.gif_milliseconds(0.1) == 100
    assert motion.gif_milliseconds(1 / 60) == 20
    assert motion.gif_milliseconds(0.005) == 20


def test_png_pdf_svg_saves_are_unchanged(tmp_path):
    _pages(COLOURS[:2])
    p.save(str(tmp_path / "a.pdf"))
    p.save(str(tmp_path / "a.png"))
    p.save(str(tmp_path / "a.svg"))
    assert sorted(f.name for f in tmp_path.iterdir()) == ["a.pdf", "a_1.png", "a_1.svg", "a_2.png", "a_2.svg"]
    with pytest.raises(ValueError, match=r"\.png, \.pdf, \.svg"):
        p.save(str(tmp_path / "a.bmp"))
