"""pygame-ce implementation of the Platform protocol.

The only module besides ``renderers/pygame2d.py`` allowed to import pygame
(enforced by tests/test_boundaries.py).
"""
from __future__ import annotations

import pygame

from .base import KEY_NAMES, InputState

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


class PygamePlatform:
    def __init__(self) -> None:
        self._screen: pygame.Surface | None = None
        self._clock: pygame.time.Clock | None = None

    # ---- window
    def open_window(self, width: int, height: int, title: str) -> pygame.Surface:
        pygame.display.init()
        self._screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption(title)
        return self._screen

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
        return InputState(x, y, any(pygame.mouse.get_pressed(3)))

    def key_down(self, key: str | int) -> bool:
        return bool(pygame.key.get_pressed()[key_code(key)])

    def present(self) -> None:
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
