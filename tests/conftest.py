"""Shared fixtures for the funground regression suite.

Everything runs headless: the SDL dummy video/audio drivers are selected
before pygame is imported, so the suite works in CI without a display.
"""
from __future__ import annotations

import inspect
import math
import os
import sys
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import pygame  # noqa: E402
import pytest  # noqa: E402

import funground  # noqa: E402
from funground import api  # noqa: E402
from funground.sketch import Sketch  # noqa: E402

EXAMPLES = ROOT / "examples" / "session1"
GOLDEN = ROOT / "tests" / "golden"


def reset_funground() -> Sketch:
    """Give the public API a fresh Sketch between tests."""
    sketch = api.use_sketch(Sketch())
    sketch.random_seed(0)
    return sketch


@pytest.fixture(autouse=True)
def _fresh_state():
    reset_funground()
    yield
    if pygame.get_init():
        pygame.quit()
    reset_funground()


@pytest.fixture
def sketch() -> Sketch:
    return api.active_sketch()


class LiveCanvas:
    """Pixel access that first draws whatever the sketch has recorded.

    A top-level ``f.size()`` makes a script canvas (S-076): no window, ops kept, pixels on a
    Cairo surface. Drawing calls append IR ops; pixels exist only after they are flushed onto
    that surface, so semantic tests read through this wrapper instead of the raw surface.
    """

    def __init__(self, sketch: Sketch) -> None:
        self._sketch = sketch

    def _pixels(self):
        self._sketch._script_flush()
        return self._sketch._renderer.pixels()

    def get_at(self, pos):
        px = self._pixels()
        i = (pos[1] * px.width + pos[0]) * 4
        b, g, r, a = bytes(px.data)[i:i + 4]
        return pygame.Color(r, g, b, a)

    def get_size(self):
        px = self._pixels()
        return (px.width, px.height)


class FrameCanvas(LiveCanvas):
    """Like LiveCanvas, but the sketch has a real (dummy-driver) window and works frame by frame,
    as a running sketch does: rendering ends the frame, so a transform or an open push() does not
    carry into the next one. A top-level f.size() no longer gives this (S-076); a running sketch's
    setup() does, and this reproduces it for the tests of frame behaviour."""

    def get_at(self, pos):
        self._sketch._render()
        return self._sketch._platform.target.get_at(pos)

    def get_size(self):
        return self._sketch._platform.target.get_size()


def open_frame_window(width: int, height: int) -> Sketch:
    """Open the active sketch's window the way a running sketch's f.size() does."""
    sketch = api.active_sketch()
    sketch.width, sketch.height = width, height
    pygame.init()
    pw, ph = sketch._platform.open_window(width, height, sketch.title)
    sketch._attach(pw, ph)
    return sketch


@pytest.fixture
def frame_canvas():
    """A live 200x100 window that renders frame by frame (see FrameCanvas)."""
    return FrameCanvas(open_frame_window(200, 100))


@pytest.fixture
def canvas():
    """A live 200x100 drawing surface for pixel-level semantic tests."""
    pygame.init()
    funground.size(200, 100)
    return LiveCanvas(api.active_sketch())


def run_sketch(path: Path, frames: int = 30, fps: int = 1000):
    """Execute a learner sketch file unchanged, stopping after *frames*.

    The sketch calls ``f.run()`` itself; we swap in a wrapper that forwards the
    sketch's own globals to ``Sketch.run_namespace`` with ``max_frames`` set.
    Returns ``((width, height), rgb_bytes)`` of the final frame.
    """
    source = path.read_text(encoding="utf-8")
    namespace: dict[str, object] = {"__name__": "__sketch__", "__file__": str(path)}

    def harness_run(*, fps=fps, max_frames=frames):
        caller = inspect.currentframe().f_back
        api.active_sketch().run_namespace(caller.f_globals, fps=fps, max_frames=max_frames)

    def harness_show():
        pass            # a script's f.show() would wait for a window to be closed (S-076)

    original_run, original_show = funground.run, funground.show
    funground.run, funground.show = harness_run, harness_show
    try:
        exec(compile(source, str(path), "exec"), namespace)
    finally:
        funground.run, funground.show = original_run, original_show

    active = api.active_sketch()
    if active.last_frame is None and active._script:
        return script_frame(active)
    frame = active.last_frame
    assert frame is not None, "sketch did not reach max_frames"
    return frame


def script_frame(sketch: Sketch):
    """A script (S-076) never calls f.run(): its frame is the finished canvas, and its ops are
    everything it drew. Same shape as a sketch's ``last_frame`` / ``last_ops`` (S-076)."""
    from funground.platform.headless import HeadlessPlatform

    sketch._script_flush()
    sketch.last_ops = sketch.frame.ops
    platform = HeadlessPlatform()
    platform.present(sketch._view_pixels())       # with its layers composited, as f.show() and saves see it
    return platform.capture()


def surface_from_frame(frame) -> pygame.Surface:
    size, data = frame
    return pygame.image.frombuffer(data, size, "RGB")


def assert_json_documents_close(
    actual, expected, *, rel_tol: float = 1e-12, abs_tol: float = 1e-9
) -> None:
    """Compare two parsed JSON documents, tolerating last-digit float noise (S-039).

    Dicts need the same keys, lists the same length; strings, bools, ``None`` and ints
    compare exactly. Floats compare with ``math.isclose`` - a few units in the last place
    for the coordinate sizes funground uses. An int on one side and a float on the other
    with the same value still fails: untouched numbers stay ints in our snapshots.

    Raises ``AssertionError`` naming the JSON path (``$.foo[2].bar``) of the first
    difference.
    """

    def walk(a, b, path: str) -> None:
        # bool is a subclass of int, so check it first.
        if isinstance(a, bool) or isinstance(b, bool):
            if type(a) is not type(b) or a != b:
                raise AssertionError(f"{path}: {a!r} != {b!r}")
        elif isinstance(a, float) or isinstance(b, float):
            if type(a) is not type(b):
                raise AssertionError(f"{path}: {a!r} != {b!r} (int vs float)")
            if not math.isclose(a, b, rel_tol=rel_tol, abs_tol=abs_tol):
                raise AssertionError(f"{path}: {a!r} != {b!r}")
        elif isinstance(a, dict):
            if not isinstance(b, dict):
                raise AssertionError(f"{path}: {a!r} != {b!r}")
            if a.keys() != b.keys():
                raise AssertionError(f"{path}: keys differ: {sorted(a)} != {sorted(b)}")
            for key in a:
                walk(a[key], b[key], f"{path}.{key}")
        elif isinstance(a, list):
            if not isinstance(b, list):
                raise AssertionError(f"{path}: {a!r} != {b!r}")
            if len(a) != len(b):
                raise AssertionError(f"{path}: length differs: {len(a)} != {len(b)}")
            for i, (x, y) in enumerate(zip(a, b)):
                walk(x, y, f"{path}[{i}]")
        else:
            if a != b:
                raise AssertionError(f"{path}: {a!r} != {b!r}")

    walk(actual, expected, "$")
