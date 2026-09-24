"""Shared fixtures for the Playground regression suite.

Everything runs headless: the SDL dummy video/audio drivers are selected
before pygame is imported, so the suite works in CI without a display.
"""
from __future__ import annotations

import inspect
import os
import sys
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import pygame  # noqa: E402
import pytest  # noqa: E402

import playground  # noqa: E402
from playground import _core  # noqa: E402

EXAMPLES = ROOT / "examples" / "session1"
GOLDEN = ROOT / "tests" / "golden"


def reset_playground() -> None:
    """Put the module-level v0.5 state back to its defaults between tests."""
    _core._state = _core._State()
    _core._style = _core._Style()
    _core._screen = None
    _core._clock = None
    _core._last_frame = None
    _core.random_seed(0)


@pytest.fixture(autouse=True)
def _fresh_state():
    reset_playground()
    yield
    if pygame.get_init():
        pygame.quit()
    reset_playground()


@pytest.fixture
def canvas():
    """A live 200x100 drawing surface for pixel-level semantic tests."""
    pygame.init()
    playground.size(200, 100)
    return _core._surface()


def run_sketch(path: Path, frames: int = 30, fps: int = 1000):
    """Execute a learner sketch file unchanged, stopping after *frames*.

    The sketch calls ``p.run()`` itself; we swap in a wrapper that forwards the
    sketch's own globals to ``_core._run_namespace`` with ``max_frames`` set.
    Returns ``((width, height), rgb_bytes)`` of the final frame.
    """
    source = path.read_text(encoding="utf-8")
    namespace: dict[str, object] = {"__name__": "__sketch__", "__file__": str(path)}

    def harness_run(*, fps=fps, max_frames=frames):
        caller = inspect.currentframe().f_back
        _core._run_namespace(caller.f_globals, fps=fps, max_frames=max_frames)

    original = playground.run
    playground.run = harness_run
    try:
        exec(compile(source, str(path), "exec"), namespace)
    finally:
        playground.run = original

    assert _core._last_frame is not None, "sketch did not reach max_frames"
    return _core._last_frame


def surface_from_frame(frame) -> pygame.Surface:
    size, data = frame
    return pygame.image.frombuffer(data, size, "RGB")
