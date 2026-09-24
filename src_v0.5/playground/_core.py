"""Core implementation for the playground teaching wrapper."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import inspect
import math
import random as _random
from typing import TypeAlias

import pygame

Color: TypeAlias = pygame.typing.ColorLike


@dataclass
class _Style:
    fill: Color | None = "white"
    stroke: Color | None = "black"
    stroke_width: int = 1
    text_size: int = 20


@dataclass
class _State:
    width: int = 640
    height: int = 480
    mouse_x: int = 0
    mouse_y: int = 0
    mouse_pressed: bool = False
    frame_count: int = 0
    delta_time: float = 0.0
    fps: int = 60
    title: str = "playground"
    running: bool = False


_state = _State()
_style = _Style()
_screen: pygame.Surface | None = None
_clock: pygame.time.Clock | None = None


def size(width: int, height: int, *, title: str = "playground", fps: int = 60) -> None:
    """Create or resize the sketch window."""
    global _screen

    if width <= 0 or height <= 0:
        raise ValueError("width and height must be positive")
    if fps <= 0:
        raise ValueError("fps must be positive")

    _state.width = int(width)
    _state.height = int(height)
    _state.fps = int(fps)
    _state.title = title

    _screen = pygame.display.set_mode((_state.width, _state.height))
    pygame.display.set_caption(_state.title)


def background(color: Color) -> None:
    _surface().fill(color)


def fill(color: Color) -> None:
    _style.fill = color


def no_fill() -> None:
    _style.fill = None


def stroke(color: Color) -> None:
    _style.stroke = color


def no_stroke() -> None:
    _style.stroke = None


def stroke_width(pixels: int) -> None:
    if pixels < 1:
        raise ValueError("stroke width must be at least 1")
    _style.stroke_width = int(pixels)


def circle(x: float, y: float, diameter: float) -> None:
    radius = max(0.0, diameter / 2)
    center = (round(x), round(y))

    if _style.fill is not None:
        pygame.draw.circle(_surface(), _style.fill, center, radius)
    if _style.stroke is not None and radius >= 1:
        pygame.draw.circle(
            _surface(),
            _style.stroke,
            center,
            radius,
            width=_style.stroke_width,
        )


def ellipse(x: float, y: float, width: float, height: float) -> None:
    """Draw an ellipse centered at (x, y)."""
    rect_value = pygame.Rect(0, 0, max(0, round(width)), max(0, round(height)))
    rect_value.center = (round(x), round(y))

    if _style.fill is not None:
        pygame.draw.ellipse(_surface(), _style.fill, rect_value)
    if _style.stroke is not None:
        pygame.draw.ellipse(
            _surface(),
            _style.stroke,
            rect_value,
            width=_style.stroke_width,
        )


def rect(x: float, y: float, width: float, height: float) -> None:
    """Draw a rectangle from its top-left corner."""
    rect_value = pygame.Rect(round(x), round(y), round(width), round(height))

    if _style.fill is not None:
        pygame.draw.rect(_surface(), _style.fill, rect_value)
    if _style.stroke is not None:
        pygame.draw.rect(
            _surface(),
            _style.stroke,
            rect_value,
            width=_style.stroke_width,
        )


def line(x1: float, y1: float, x2: float, y2: float) -> None:
    if _style.stroke is not None:
        pygame.draw.line(
            _surface(),
            _style.stroke,
            (x1, y1),
            (x2, y2),
            _style.stroke_width,
        )


def point(x: float, y: float) -> None:
    if _style.stroke is not None:
        pygame.draw.circle(
            _surface(),
            _style.stroke,
            (round(x), round(y)),
            max(1, _style.stroke_width // 2),
        )


def text_size(size: int) -> None:
    if size <= 0:
        raise ValueError("text size must be positive")
    _style.text_size = int(size)


def text(message: object, x: float, y: float, color: Color | None = None) -> None:
    pygame.font.init()
    font = pygame.font.Font(None, _style.text_size)
    chosen = color if color is not None else (_style.fill or _style.stroke or "white")
    image = font.render(str(message), True, chosen)
    _surface().blit(image, (x, y))


def random(low: float = 1.0, high: float | None = None) -> float:
    """random(10) -> 0..10; random(5, 10) -> 5..10."""
    if high is None:
        high = low
        low = 0.0
    return _random.uniform(low, high)


def constrain(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def distance(x1: float, y1: float, x2: float, y2: float) -> float:
    return math.hypot(x2 - x1, y2 - y1)


def key_down(key: str | int) -> bool:
    """Return whether a key is held, e.g. key_down('left') or key_down('a')."""
    return bool(pygame.key.get_pressed()[_key_code(key)])


def stop() -> None:
    _state.running = False


def run(*, fps: int | None = None) -> None:
    """Run standardized setup() and draw() functions from the calling script.

    setup() is optional; draw() is required. Neither is passed as an argument.
    """
    global _clock

    caller = inspect.currentframe()
    if caller is None or caller.f_back is None:
        raise RuntimeError("Could not find the sketch that called p.run().")

    setup, draw = _sketch_functions(caller.f_back.f_globals)

    pygame.init()
    _clock = pygame.time.Clock()
    _state.running = True
    _state.frame_count = 0
    _state.delta_time = 0.0

    if fps is not None:
        if fps <= 0:
            raise ValueError("fps must be positive")
        _state.fps = int(fps)

    # setup() usually calls size(). A default canvas keeps setup() optional.
    if setup is not None:
        setup()
    if _screen is None:
        size(_state.width, _state.height, title=_state.title, fps=_state.fps)

    try:
        while _state.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    _state.running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    _state.running = False

            _state.mouse_x, _state.mouse_y = pygame.mouse.get_pos()
            _state.mouse_pressed = any(pygame.mouse.get_pressed(3))

            draw()
            pygame.display.flip()

            _state.frame_count += 1
            _state.delta_time = _clock.tick(_state.fps) / 1000.0
    finally:
        _state.running = False
        pygame.quit()


def live_value(name: str) -> object:
    """Return one of the public live sketch values."""
    if name not in {
        "width",
        "height",
        "mouse_x",
        "mouse_y",
        "mouse_pressed",
        "frame_count",
        "delta_time",
    }:
        raise AttributeError(name)
    return getattr(_state, name)


def _sketch_functions(
    namespace: dict[str, object],
) -> tuple[Callable[[], None] | None, Callable[[], None]]:
    setup = namespace.get("setup")
    draw = namespace.get("draw")

    if setup is not None and not callable(setup):
        raise TypeError("setup must be a function")
    if draw is None:
        raise RuntimeError("Define a draw() function before calling p.run().")
    if not callable(draw):
        raise TypeError("draw must be a function")

    return setup, draw


def _surface() -> pygame.Surface:
    if _screen is None:
        raise RuntimeError("No drawing window yet. Call p.size(...) first.")
    return _screen


def _key_code(key: str | int) -> int:
    if isinstance(key, int):
        return key

    names = {
        "left": pygame.K_LEFT,
        "right": pygame.K_RIGHT,
        "up": pygame.K_UP,
        "down": pygame.K_DOWN,
        "space": pygame.K_SPACE,
        "enter": pygame.K_RETURN,
        "escape": pygame.K_ESCAPE,
    }

    lowered = key.lower()
    if lowered in names:
        return names[lowered]
    if len(lowered) == 1:
        return pygame.key.key_code(lowered)
    raise ValueError(f"unknown key name: {key!r}")
