"""The Platform protocol: what funground needs from an OS/window layer.

funground owns the sketch loop; a platform supplies window creation, event
pumping, input sampling, frame pacing and presentation of a finished frame.
Nothing here mentions a concrete library.

Coordinates: the sketch works in *logical* pixels (contract C2/C3). A platform
reports `backing_scale` (physical pixels per logical pixel); the window and the
renderer's surface are physical, input is reported in logical units.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

# Key names funground understands (contract row I2). Single characters and
# backend key codes are also accepted and passed to the platform.
KEY_NAMES = ("left", "right", "up", "down", "space", "enter", "escape")

# Mouse pointer shapes for f.cursor() (S-057): p5's ARROW, CROSS, HAND, MOVE, TEXT, WAIT.
CURSOR_KINDS = ("arrow", "cross", "hand", "move", "text", "wait")


@dataclass(frozen=True, slots=True)
class InputState:
    mouse_x: int = 0
    mouse_y: int = 0
    mouse_pressed: bool = False        # any of the first three buttons held (f.is_mouse_pressed)
    key_pressed: bool = False          # any key held (f.is_key_pressed)


# Event kinds, named after the learner callbacks they trigger (contract I3, D-016).
EVENT_KINDS = ("mouse_pressed", "mouse_released", "mouse_moved", "mouse_dragged", "mouse_wheel",
               "key_pressed", "key_released", "key_typed")
MOUSE_BUTTONS = ("left", "center", "right")


@dataclass(frozen=True, slots=True)
class InputEvent:
    """One input event, in logical coordinates, delivered in the order it happened."""

    kind: str
    x: int = 0
    y: int = 0
    button: str | None = None          # "left" | "center" | "right" for mouse button events
    key: str | None = None             # a character ("a", "A", "7", " ") or a name ("left", "enter", "f1")
    key_code: int | None = None        # the backend's key code
    delta: float = 0.0                 # mouse wheel: positive when scrolling down/towards you


@dataclass(frozen=True, slots=True)
class Pixels:
    """A finished frame handed from renderer to platform: raw bytes + layout."""

    data: object            # bytes-like, row-major, no padding
    width: int
    height: int
    format: str = "BGRA"    # pygame.image.frombuffer format name


class Platform(Protocol):
    @property
    def backing_scale(self) -> float:
        """Physical pixels per logical pixel for the open window (1.0 until open_window)."""

    def open_window(self, width: int, height: int, title: str) -> tuple[int, int]:
        """Create or resize the window for a *logical* size; return the physical size."""

    def open_full_screen(self, title: str) -> tuple[int, int]:
        """Make the window fill the display; return the physical size (S-057)."""

    def set_cursor(self, kind: str | None) -> None:
        """Show a CURSOR_KINDS pointer over the window, or hide it for None (S-057)."""

    def start(self) -> None:
        """Called once by the sketch loop before setup()."""

    def poll(self) -> bool:
        """Pump OS events. Return True if the sketch should keep running."""

    def events(self) -> list[InputEvent]:
        """The input events gathered by the last poll(), oldest first."""

    def input_state(self) -> InputState:
        """Mouse position in logical pixels, button state."""

    def key_down(self, key: str | int) -> bool:
        """key is a KEY_NAMES entry (lower-case), a single character, or a backend code."""

    def present(self, pixels: Pixels) -> None:
        """Show a finished frame."""

    def tick(self, fps: int) -> float:
        """Wait for the frame budget; return seconds since the previous tick."""

    def capture(self) -> tuple[tuple[int, int], bytes]:
        """Return ((width, height), RGB bytes) of the last presented frame."""

    def close(self) -> None:
        """Destroy the window and release platform resources."""
