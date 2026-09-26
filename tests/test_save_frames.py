"""Frame sequences (S-056): p.save_frames(pattern, count), headless-friendly."""
from __future__ import annotations

import cairo
import pytest

import funground as p
from funground import api
from funground.platform.headless import HeadlessPlatform
from funground.sketch import Sketch

from conftest import ROOT, run_sketch


def run(draw, frames, size=(40, 30)):
    s = api.use_sketch(Sketch(platform=HeadlessPlatform()))
    s.run_namespace({"setup": lambda: p.size(*size), "draw": draw}, max_frames=frames)
    return s


def test_writes_exactly_count_numbered_files_starting_with_this_frame(tmp_path):
    pattern = str(tmp_path / "out" / "f-###.png")        # the folder is created

    def draw():
        p.background((p.frame_count * 10, 0, 0))
        if p.frame_count == 2:
            p.save_frames(pattern, 4)

    run(draw, frames=10)
    files = sorted(f.name for f in (tmp_path / "out").iterdir())
    assert files == ["f-001.png", "f-002.png", "f-003.png", "f-004.png"]
    first = cairo.ImageSurface.create_from_png(str(tmp_path / "out" / "f-001.png"))
    assert bytes(first.get_data())[2] == 20                # red of frame 2: saving starts this frame


def test_a_sequence_longer_than_the_run_just_stops(tmp_path):
    run(lambda: p.save_frames(str(tmp_path / "####.png"), 50) if p.frame_count == 0 else None, frames=3)
    assert sorted(f.name for f in tmp_path.iterdir()) == ["0001.png", "0002.png", "0003.png"]


def test_vector_frames_work_too(tmp_path):
    def draw():
        p.circle(20, 15, 10)
        if p.frame_count == 0:
            p.save_frames(str(tmp_path / "v##.svg"), 2)

    run(draw, frames=5)
    assert sorted(f.name for f in tmp_path.iterdir()) == ["v01.svg", "v02.svg"]


def test_paused_sketches_save_only_frames_they_draw(tmp_path):
    def setup():
        p.size(20, 20)
        p.no_loop()

    def draw():
        p.save_frames(str(tmp_path / "##.png"), 5)

    s = api.use_sketch(Sketch(platform=HeadlessPlatform()))
    s.run_namespace({"setup": setup, "draw": draw}, max_frames=10)
    assert [f.name for f in tmp_path.iterdir()] == ["01.png"]


def test_the_gallery_example_loops_seamlessly(tmp_path, monkeypatch):
    """The example saves 30 frames; frame 31 equals frame 1, so the frames loop without a jump."""
    monkeypatch.chdir(tmp_path)
    api.use_sketch(Sketch(platform=HeadlessPlatform()))
    (w, h), frame_31 = run_sketch(ROOT / "examples/gallery/saving/03_save_frames.py", frames=31)
    frames = sorted((tmp_path / "frames").iterdir())
    assert [f.name for f in frames[:2]] == ["0001.png", "0002.png"] and len(frames) == 30
    first = cairo.ImageSurface.create_from_png(str(frames[0]))
    data, stride = bytes(first.get_data()), first.get_stride()
    rgb_1 = bytes(b for y in range(h) for x in range(w) for b in (data[y * stride + x * 4 + 2],
                                                                    data[y * stride + x * 4 + 1],
                                                                    data[y * stride + x * 4]))
    differing = sum(a != b for a, b in zip(rgb_1, frame_31))
    assert differing < len(rgb_1) * 0.001        # identical up to floating-point edge pixels


def test_mistakes_are_explained():
    api.use_sketch(Sketch(platform=HeadlessPlatform()))
    with pytest.raises(ValueError, match="one run of #"):
        p.save_frames("frame.png", 3)
    with pytest.raises(ValueError, match="one run of #"):
        p.save_frames("##-##.png", 3)
    with pytest.raises(ValueError, match="use one of"):
        p.save_frames("####.gif", 3)
    with pytest.raises(ValueError, match="1 or more"):
        p.save_frames("####.png", 0)
