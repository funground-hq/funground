"""pygame-ce implementation of the Platform protocol.

The only module in the package allowed to import pygame (tests/test_boundaries.py).
pygame supplies the window, events, input, timing and the blit of a finished
frame; it draws nothing (D-008).
"""
from __future__ import annotations

import os
import sys

import pygame

from .base import KEY_NAMES, InputState, Pixels

_NAMED_KEYS = {
    "left": pygame.K_LEFT,
    "right": pygame.K_RIGHT,
    "up": pygame.K_UP,
    "down": pygame.K_DOWN,
    "space": pygame.K_SPACE,
    "enter": pygame.K_RETURN,
    "escape": pygame.K_ESCAPE,
}
assert set(_NAMED_KEYS) == set(KEY_NAMES)


def key_code(key: str | int) -> int:
    """Map a Playground key name / character / backend code to a pygame key code."""
    if isinstance(key, int):
        return key
    lowered = key.lower()
    if lowered in _NAMED_KEYS:
        return _NAMED_KEYS[lowered]
    if len(lowered) == 1:
        return pygame.key.key_code(lowered)
    raise ValueError(f"unknown key name: {key!r}")


def detect_backing_scale() -> float:
    """Physical pixels per logical pixel (contract C3, story S-024).

    PLAYGROUND_BACKING_SCALE overrides (tests, unusual setups). The dummy video
    driver has no display, so it is always 1.0. On Windows the process declares
    per-monitor DPI awareness so the OS stops bitmap-stretching the window and
    we can render at physical resolution instead.
    """
    forced = os.environ.get("PLAYGROUND_BACKING_SCALE")
    if forced:
        return max(0.5, float(forced))
    if os.environ.get("SDL_VIDEODRIVER", "").lower() == "dummy":
        return 1.0
    if sys.platform == "win32":
        try:
            import ctypes

            try:
                ctypes.windll.shcore.SetProcessDpiAwareness(2)  # PROCESS_PER_MONITOR_DPI_AWARE
            except OSError:
                pass  # already set for this process; keep whatever it is
            return ctypes.windll.user32.GetDpiForSystem() / 96.0
        except Exception:
            return 1.0
    return 1.0  # macOS/Linux HiDPI: follow-up story; SDL reports logical sizes there


class PygamePlatform:
    def __init__(self) -> None:
        self._screen: pygame.Surface | None = None
        self._clock: pygame.time.Clock | None = None
        self._scale = 1.0

    @property
    def backing_scale(self) -> float:
        return self._scale

    # ---- window
    def open_window(self, width: int, height: int, title: str) -> tuple[int, int]:
        self._scale = detect_backing_scale()
        pygame.display.init()
        physical = (round(width * self._scale), round(height * self._scale))
        self._screen = pygame.display.set_mode(physical)
        pygame.display.set_caption(title)
        return physical

    @property
    def target(self) -> pygame.Surface | None:
        return self._screen

    # ---- loop services
    def start(self) -> None:
        pygame.init()
        self._clock = pygame.time.Clock()

    def poll(self) -> bool:
        keep_running = True
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                keep_running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                keep_running = False
        return keep_running

    def input_state(self) -> InputState:
        x, y = pygame.mouse.get_pos()
        s = self._scale
        return InputState(round(x / s), round(y / s), any(pygame.mouse.get_pressed(3)))

    def key_down(self, key: str | int) -> bool:
        return bool(pygame.key.get_pressed()[key_code(key)])

    def present(self, pixels: Pixels) -> None:
        if self._screen is None:
            raise RuntimeError("no window to present to")
        image = pygame.image.frombuffer(pixels.data, (pixels.width, pixels.height), pixels.format)
        self._screen.blit(image, (0, 0))
        pygame.display.flip()

    def tick(self, fps: int) -> float:
        if self._clock is None:
            self._clock = pygame.time.Clock()
        return self._clock.tick(fps) / 1000.0

    def capture(self) -> tuple[tuple[int, int], bytes]:
        if self._screen is None:
            raise RuntimeError("no window to capture")
        return (self._screen.get_size(), pygame.image.tobytes(self._screen, "RGB"))

    def close(self) -> None:
        # The display surface dies with pygame.quit(); forget it so a later
        # run creates a fresh window (v0.5 defect, fixed in Sprint 0).
        pygame.quit()
        self._screen = None
        self._clock = None
