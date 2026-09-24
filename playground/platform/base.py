"""The Platform protocol: what Playground needs from an OS/window layer.

Playground owns the sketch loop; a platform supplies window creation, event
pumping, input sampling, frame pacing and presentation. Nothing here mentions a
concrete library.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

# Key names Playground understands (contract row I2). Single characters and
# backend key codes are also accepted and passed to the platform.
KEY_NAMES = ("left", "right", "up", "down", "space", "enter", "escape")


@dataclass(frozen=True, slots=True)
class InputState:
    mouse_x: int = 0
    mouse_y: int = 0
    mouse_pressed: bool = False


class Platform(Protocol):
    def open_window(self, width: int, height: int, title: str) -> Any:
        """Create or resize the window; return the native drawing target."""

    @property
    def target(self) -> Any:
        """The native drawing target, or None before open_window()."""

    def poll(self) -> bool:
        """Pump OS events. Return True if the sketch should keep running."""

    def input_state(self) -> InputState: ...

    def key_down(self, key: str | int) -> bool:
        """key is a KEY_NAMES entry (lower-case), a single character, or a backend code."""

    def present(self) -> None:
        """Show the frame drawn on the target."""

    def tick(self, fps: int) -> float:
        """Wait for the frame budget; return seconds since the previous tick."""

    def capture(self) -> tuple[tuple[int, int], bytes]:
        """Return ((width, height), RGB bytes) of the current target."""

    def close(self) -> None:
        """Destroy the window and release platform resources."""
