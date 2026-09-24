"""The Renderer protocol: consume a Frame of IR ops (story S-019).

A renderer never sees a public API call; it sees data. Each renderer declares
the capabilities it can honour so the sketch can refuse unsupported features
up front (story S-021).
"""
from __future__ import annotations

from typing import Any, Protocol

from ..capabilities import Capability
from ..ir import Frame


class Renderer(Protocol):
    capabilities: frozenset[Capability]

    def attach(self, target: Any) -> None:
        """Bind to the platform's native drawing target (None to detach)."""

    def render(self, frame: Frame) -> None:
        """Draw every op in *frame*, in order, onto the attached target."""
