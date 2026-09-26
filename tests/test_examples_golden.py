"""Every Session-1 sketch runs unchanged, headless, and renders what it did before.

Golden PNGs live in tests/golden/. They are exact-match because the renderer is
still pygame on every platform; when a second rasteriser arrives, this becomes
a tolerance comparison (or an op-list comparison - see the architecture review).

Regenerate deliberately with:  FUNGROUND_UPDATE_GOLDENS=1 pytest tests/test_examples_golden.py
Golden comparison is skipped on platforms other than the one that produced the
goldens (font rasterisation differs); those platforms still run every sketch.
"""
from __future__ import annotations

import os
import platform
from pathlib import Path

import pygame
import pytest

from conftest import EXAMPLES, GOLDEN, run_sketch, surface_from_frame

SKETCHES = sorted(EXAMPLES.glob("*.py"))
# Their output depends on wall-clock timing, so they are smoke-tested only.
TIME_DEPENDENT = {"11_delta_time.py"}
GOLDEN_PLATFORM = "Windows"
UPDATE = os.environ.get("FUNGROUND_UPDATE_GOLDENS") == "1"


def test_sample_suite_is_present():
    assert len(SKETCHES) >= 12


@pytest.mark.parametrize("sketch", SKETCHES, ids=lambda s: s.name)
def test_sketch_runs_unchanged_headless(sketch: Path):
    (w, h), data = run_sketch(sketch, frames=30)
    assert (w, h) in {(640, 400), (640, 480)}
    assert len(data) == w * h * 3


@pytest.mark.parametrize(
    "sketch", [s for s in SKETCHES if s.name not in TIME_DEPENDENT], ids=lambda s: s.name
)
def test_sketch_matches_golden(sketch: Path, tmp_path: Path):
    frame = run_sketch(sketch, frames=30)
    golden = GOLDEN / f"{sketch.stem}.png"
    actual = surface_from_frame(frame)

    if UPDATE or not golden.exists():
        GOLDEN.mkdir(exist_ok=True)
        pygame.image.save(actual, str(golden))
        pytest.skip(f"golden written: {golden.name}")

    if platform.system() != GOLDEN_PLATFORM:
        pytest.skip(f"goldens were produced on {GOLDEN_PLATFORM}")

    expected = pygame.image.load(str(golden))
    same = pygame.image.tobytes(expected, "RGB") == frame[1]
    if not same:
        out = GOLDEN / "_actual"
        out.mkdir(exist_ok=True)
        pygame.image.save(actual, str(out / golden.name))
    assert same, f"{sketch.name} differs from golden; actual saved to tests/golden/_actual/"
