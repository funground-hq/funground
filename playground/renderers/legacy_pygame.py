"""LegacyPygameRenderer: v0.5's pygame.draw calls, driven by the IR (story S-019).

Reproduces v0.5 pixel-for-pixel (contract rows C6 rounding, S4 inside strokes,
S2 alpha dropped, T1-T3 text) so the Sprint-0 goldens stay byte-identical.
Named *legacy* because it is deleted once the vector renderer passes the
sample suite (D-008); do not extend it.
"""
from __future__ import annotations

import pygame

from .. import ir
from ..capabilities import Capability


class LegacyPygameRenderer:
    name = "legacy pygame"
    capabilities = frozenset({Capability.RASTER_2D})

    def __init__(self) -> None:
        self._surface: pygame.Surface | None = None
        self._fonts: dict[int, pygame.font.Font] = {}

    def attach(self, target: pygame.Surface | None) -> None:
        self._surface = target
        self._fonts.clear()

    def _s(self) -> pygame.Surface:
        if self._surface is None:
            raise RuntimeError("renderer has no target")
        return self._surface

    # ---- entry point
    def render(self, frame: ir.Frame) -> None:
        for op in frame:
            handler = self._HANDLERS.get(type(op))
            if handler is None:
                raise NotImplementedError(f"{self.name} renderer cannot draw {type(op).__name__}")
            handler(self, op)

    # ---- per-op drawing, verbatim from v0.5 _core.py
    def _clear(self, op: ir.Clear) -> None:
        self._s().fill(op.color.rgba)

    def _circle(self, op: ir.Circle) -> None:
        st = op.style
        radius = max(0.0, op.diameter / 2)
        center = (round(op.x), round(op.y))
        if st.fill is not None:
            pygame.draw.circle(self._s(), st.fill.rgba, center, radius)
        if st.stroke is not None and radius >= 1:
            pygame.draw.circle(self._s(), st.stroke.rgba, center, radius, width=st.stroke_width)

    def _ellipse(self, op: ir.Ellipse) -> None:
        st = op.style
        r = pygame.Rect(0, 0, max(0, round(op.width)), max(0, round(op.height)))
        r.center = (round(op.x), round(op.y))
        if st.fill is not None:
            pygame.draw.ellipse(self._s(), st.fill.rgba, r)
        if st.stroke is not None:
            pygame.draw.ellipse(self._s(), st.stroke.rgba, r, width=st.stroke_width)

    def _rect(self, op: ir.Rect) -> None:
        st = op.style
        r = pygame.Rect(round(op.x), round(op.y), round(op.width), round(op.height))
        if st.fill is not None:
            pygame.draw.rect(self._s(), st.fill.rgba, r)
        if st.stroke is not None:
            pygame.draw.rect(self._s(), st.stroke.rgba, r, width=st.stroke_width)

    def _line(self, op: ir.Line) -> None:
        st = op.style
        if st.stroke is not None:
            pygame.draw.line(self._s(), st.stroke.rgba, (op.x1, op.y1), (op.x2, op.y2), st.stroke_width)

    def _point(self, op: ir.Point) -> None:
        st = op.style
        if st.stroke is not None:
            pygame.draw.circle(
                self._s(), st.stroke.rgba, (round(op.x), round(op.y)), max(1, st.stroke_width // 2)
            )

    def _text(self, op: ir.Text) -> None:
        font = self._fonts.get(op.style.text_size)
        if font is None:
            pygame.font.init()
            font = self._fonts[op.style.text_size] = pygame.font.Font(None, op.style.text_size)
        self._s().blit(font.render(op.text, True, op.color.rgba), (op.x, op.y))

    _HANDLERS = {
        ir.Clear: _clear,
        ir.Circle: _circle,
        ir.Ellipse: _ellipse,
        ir.Rect: _rect,
        ir.Line: _line,
        ir.Point: _point,
        ir.Text: _text,
    }
