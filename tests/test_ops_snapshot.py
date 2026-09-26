"""IR snapshots: every Session-1 sketch asks for exactly the ops it did before (S-020).

This is the primary cross-backend contract (PROCESS test hierarchy). The
snapshot is the op list of the *final* frame of a 30-frame headless run,
serialised to JSON. It is platform-independent by construction: no pixels,
no fonts, no anti-aliasing - just what the learner's code requested.

Regenerate deliberately:  FUNGROUND_UPDATE_SNAPSHOTS=1 pytest tests/test_ops_snapshot.py
A failure writes the actual ops to tests/snapshots/_actual/<sketch>.json.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from conftest import EXAMPLES, run_sketch
from funground import api, ir

SNAPSHOTS = Path(__file__).resolve().parent / "snapshots"
SKETCHES = sorted(EXAMPLES.glob("*.py"))
TIME_DEPENDENT = {"11_delta_time.py"}  # positions depend on wall-clock delta_time
UPDATE = os.environ.get("FUNGROUND_UPDATE_SNAPSHOTS") == "1"


def _dump(ops) -> str:
    return json.dumps(ir.Frame(list(ops)).to_jsonable(), indent=1, sort_keys=True) + "\n"


@pytest.mark.parametrize(
    "sketch", [s for s in SKETCHES if s.name not in TIME_DEPENDENT], ids=lambda s: s.name
)
def test_sketch_ops_match_snapshot(sketch: Path):
    run_sketch(sketch, frames=30)
    ops = api.active_sketch().last_ops
    assert ops is not None and len(ops) > 0
    actual = _dump(ops)
    snap = SNAPSHOTS / f"{sketch.stem}.json"

    if UPDATE or not snap.exists():
        SNAPSHOTS.mkdir(exist_ok=True)
        snap.write_text(actual, encoding="utf-8")
        pytest.skip(f"snapshot written: {snap.name}")

    expected = snap.read_text(encoding="utf-8")
    if actual != expected:
        out = SNAPSHOTS / "_actual"
        out.mkdir(exist_ok=True)
        (out / snap.name).write_text(actual, encoding="utf-8")
    assert actual == expected, f"{sketch.name}: op list differs; actual saved to tests/snapshots/_actual/"


def test_snapshot_round_trips_as_ir():
    """A stored snapshot can be loaded back into ops - the replay path exporters will use."""
    for snap in SNAPSHOTS.glob("*.json"):
        frame = ir.Frame.from_jsonable(json.loads(snap.read_text(encoding="utf-8")))
        assert len(frame) > 0
        assert all(isinstance(op, ir.Op) for op in frame)


def test_every_sketch_begins_its_frame_with_background_except_trails():
    """Documents a Session-1 convention: draw() clears first. (12_default_window too.)"""
    for sketch in SKETCHES:
        if sketch.name in TIME_DEPENDENT:
            continue
        run_sketch(sketch, frames=2)
        first = api.active_sketch().last_ops[0]
        assert isinstance(first, ir.Clear), sketch.name
