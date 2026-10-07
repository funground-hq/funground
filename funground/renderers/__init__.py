"""The Renderer protocol: consume a Frame of IR ops (stories S-019, S-024).

A renderer never sees a public API call and never touches the window; it
draws a Frame into its own surface and hands the finished pixels back. Each
renderer declares the capabilities it can honour so the sketch can refuse
unsupported features up front (story S-021).
"""
from __future__ import annotations

from typing import Protocol

from ..capabilities import Capability
from ..ir import Frame
from ..platform.base import Pixels


class Renderer(Protocol):
    capabilities: frozenset[Capability]

    def attach(self, width: int, height: int, scale: float = 1.0) -> None:
        """Allocate a surface of *physical* size width x height; draw logical
        coordinates scaled by *scale* (HiDPI). Called again on resize; (0, 0) detaches."""

    def render(self, frame: Frame) -> None:
        """Draw every op in *frame*, in order, onto the surface."""

    def pixels(self) -> Pixels:
        """The surface's current contents, for the platform to present."""

    def ink_bounds(self, ops) -> tuple[float, float, float, float] | None:
        """The area a list of ops would paint, as (x, y, w, h) in their own coordinates, never
        smaller than the ink; None when they paint nothing. Draws nothing (S-132: a mark's bounds)."""
