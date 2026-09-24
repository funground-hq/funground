"""The Renderer protocol for the v0.5 primitive set.

Sprint 1 boundary: the sketch validates arguments, resolves colours and owns
the GraphicsState; a renderer only paints. Sprint 2 replaces these per-primitive
methods with a single ``render(ops)`` over the draw-op IR (story S-018/S-019).
"""
from __future__ import annotations

from typing import Any, Protocol

from ..color import Color
from ..state import GraphicsState


class Renderer(Protocol):
    def attach(self, target: Any) -> None:
        """Bind to the platform's native drawing target."""

    def background(self, color: Color) -> None: ...
    def circle(self, x: float, y: float, diameter: float, state: GraphicsState) -> None: ...
    def ellipse(self, x: float, y: float, width: float, height: float, state: GraphicsState) -> None: ...
    def rect(self, x: float, y: float, width: float, height: float, state: GraphicsState) -> None: ...
    def line(self, x1: float, y1: float, x2: float, y2: float, state: GraphicsState) -> None: ...
    def point(self, x: float, y: float, state: GraphicsState) -> None: ...
    def text(self, message: str, x: float, y: float, color: Color, state: GraphicsState) -> None: ...
