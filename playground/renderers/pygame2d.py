"""pygame.draw implementation of the Renderer protocol.

Reproduces v0.5 pixel-for-pixel (contract rows C6 rounding, S4 inside strokes,
S2 alpha dropped, T1–T3 text) so the Sprint-0 goldens stay byte-identical.
"""
from __future__ import annotations

import pygame

from ..color import Color
from ..state import GraphicsState


class PygameRenderer:
    def __init__(self) -> None:
        self._surface: pygame.Surface | None = None
        self._fonts: dict[int, pygame.font.Font] = {}

    def attach(self, target: pygame.Surface) -> None:
        self._surface = target
        self._fonts.clear()

    def _s(self) -> pygame.Surface:
        if self._surface is None:
            raise RuntimeError("renderer has no target")
        return self._surface

    def background(self, color: Color) -> None:
        self._s().fill(color.rgba)

    def circle(self, x, y, diameter, state: GraphicsState) -> None:
        radius = max(0.0, diameter / 2)
        center = (round(x), round(y))
        if state.fill is not None:
            pygame.draw.circle(self._s(), state.fill.rgba, center, radius)
        if state.stroke is not None and radius >= 1:
            pygame.draw.circle(self._s(), state.stroke.rgba, center, radius, width=state.stroke_width)

    def ellipse(self, x, y, width, height, state: GraphicsState) -> None:
        r = pygame.Rect(0, 0, max(0, round(width)), max(0, round(height)))
        r.center = (round(x), round(y))
        if state.fill is not None:
            pygame.draw.ellipse(self._s(), state.fill.rgba, r)
        if state.stroke is not None:
            pygame.draw.ellipse(self._s(), state.stroke.rgba, r, width=state.stroke_width)

    def rect(self, x, y, width, height, state: GraphicsState) -> None:
        r = pygame.Rect(round(x), round(y), round(width), round(height))
        if state.fill is not None:
            pygame.draw.rect(self._s(), state.fill.rgba, r)
        if state.stroke is not None:
            pygame.draw.rect(self._s(), state.stroke.rgba, r, width=state.stroke_width)

    def line(self, x1, y1, x2, y2, state: GraphicsState) -> None:
        if state.stroke is not None:
            pygame.draw.line(self._s(), state.stroke.rgba, (x1, y1), (x2, y2), state.stroke_width)

    def point(self, x, y, state: GraphicsState) -> None:
        if state.stroke is not None:
            pygame.draw.circle(
                self._s(), state.stroke.rgba, (round(x), round(y)), max(1, state.stroke_width // 2)
            )

    def text(self, message: str, x, y, color: Color, state: GraphicsState) -> None:
        font = self._fonts.get(state.text_size)
        if font is None:
            pygame.font.init()
            font = self._fonts[state.text_size] = pygame.font.Font(None, state.text_size)
        self._s().blit(font.render(message, True, color.rgba), (x, y))
