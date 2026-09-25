"""Backend-neutral graphics state (contract rows S3–S9, T3).

``GraphicsState`` is immutable; a sketch replaces it on every style call and
keeps a stack so ``push()``/``pop()`` and ``with p.saved_state():`` are trivial and
exception-safe.
"""
from __future__ import annotations

from dataclasses import dataclass, replace

from .color import BLACK, WHITE, Color


@dataclass(frozen=True, slots=True)
class GraphicsState:
    fill: Color | None = WHITE
    stroke: Color | None = BLACK
    stroke_width: int = 1
    text_size: int = 20
    # S-042 stroke styles (contract S11). Defaults are the Sprint-3 look (D-004): round/round.
    stroke_cap: str = "round"
    stroke_join: str = "round"
    miter_limit: float = 10.0
    dash: tuple[float, ...] = ()
    dash_offset: float = 0.0
    # S-074: 0 = Catmull-Rom, 1 = straight lines (Processing's curveTightness). Contract F9.
    curve_tightness: float = 0.0

    def with_(self, **changes) -> "GraphicsState":
        return replace(self, **changes)


class StateStack:
    """The current ``GraphicsState`` plus the saved ones beneath it."""

    def __init__(self, initial: GraphicsState | None = None) -> None:
        self.current = initial if initial is not None else GraphicsState()
        self._saved: list[GraphicsState] = []

    def save(self) -> None:
        self._saved.append(self.current)

    def restore(self) -> None:
        if not self._saved:
            raise RuntimeError("restore() called without a matching save()")
        self.current = self._saved.pop()

    @property
    def depth(self) -> int:
        return len(self._saved)

    def unwind(self) -> int:
        """Restore every saved state (end-of-frame safety); return how many were open."""
        count = len(self._saved)
        if count:
            self.current = self._saved[0]
            self._saved.clear()
        return count

    def update(self, **changes) -> GraphicsState:
        self.current = self.current.with_(**changes)
        return self.current
