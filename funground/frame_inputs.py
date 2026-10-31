"""Inputs that the sketch serves each frame, such as a camera (ADR-007, S-247).

The core never imports a library. A library that has a live input, such as the camera, registers two functions here
when it is imported: ``take(sketch)``, which the sketch calls once before each ``draw()`` (so everything in one frame
sees the same input, like the mouse; contract I4), and ``stop()``, which the sketch calls when it ends. With no
library imported, the lists are empty and the sketch does nothing. This is not learner API.
"""
from __future__ import annotations

from collections.abc import Callable

_inputs: list[tuple[Callable, Callable]] = []


def register(take: Callable, stop: Callable) -> None:
    """Add an input. Registering the same pair twice has no effect."""
    pair = (take, stop)
    if pair not in _inputs:
        _inputs.append(pair)


def take_all(sketch) -> None:
    """Call every input's ``take(sketch)``. The sketch calls this before each draw()."""
    for take, _ in list(_inputs):
        take(sketch)


def stop_all() -> None:
    """Call every input's ``stop()``. The sketch calls this when it ends."""
    for _, stop in list(_inputs):
        stop()
