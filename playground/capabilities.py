"""Capability identifiers and learner-facing errors (story S-021).

A renderer declares a frozenset of Capability; a feature that needs one the
selected renderer lacks fails at p.size()/p.run() - never mid-loop - with a
message that names the feature and what to install (contract R9).
"""
from __future__ import annotations

from enum import Enum


class Capability(Enum):
    RASTER_2D = "basic 2D shapes"
    ALPHA = "translucent colours"
    ANTIALIAS = "smooth edges"
    TRANSFORMS = "translate/rotate/scale"
    VECTOR_PATHS = "paths and curves"
    CLIP_PATH = "clipping to a shape"
    GRADIENTS = "gradients"
    TEXT_OUTLINES = "bundled-font text"
    PNG_EXPORT = "saving PNG"
    PDF_EXPORT = "saving PDF"
    SVG_EXPORT = "saving SVG"


# Which pip extra provides a capability the base install lacks. Filled in as
# extras appear (Sprint 3+); the base install covers RASTER_2D only today.
EXTRA_FOR: dict[Capability, str] = {}


class PlaygroundError(RuntimeError):
    """A clear, learner-facing error raised by Playground itself."""


class PlaygroundWarning(UserWarning):
    """A learner-facing warning: something was fixed up rather than crashing mid-lesson."""


def missing_capability(cap: Capability, feature: str, renderer_name: str) -> PlaygroundError:
    extra = EXTRA_FOR.get(cap)
    hint = f" Install it with:  pip install playground[{extra}]" if extra else ""
    return PlaygroundError(
        f"{feature} needs {cap.value}, which the {renderer_name} renderer cannot do.{hint}"
    )
