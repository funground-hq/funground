"""The frozen v0.5 public API, as an executable contract.

If any of these fail, learner-visible behaviour has changed. Change the
expectation here only as a deliberate, documented decision.
"""
from __future__ import annotations

import inspect

import playground as p

V05_FUNCTIONS = {
    "background": "(color: 'Color') -> 'None'",
    "circle": "(x: 'float', y: 'float', diameter: 'float') -> 'None'",
    "constrain": "(value: 'float', low: 'float', high: 'float') -> 'float'",
    "distance": "(x1: 'float', y1: 'float', x2: 'float', y2: 'float') -> 'float'",
    "ellipse": "(x: 'float', y: 'float', width: 'float', height: 'float') -> 'None'",
    "fill": "(color: 'Color') -> 'None'",
    "key_down": "(key: 'str | int') -> 'bool'",
    "line": "(x1: 'float', y1: 'float', x2: 'float', y2: 'float') -> 'None'",
    "no_fill": "() -> 'None'",
    "no_stroke": "() -> 'None'",
    "point": "(x: 'float', y: 'float') -> 'None'",
    "random": "(low: 'float' = 1.0, high: 'float | None' = None) -> 'float'",
    "rect": "(x: 'float', y: 'float', width: 'float', height: 'float') -> 'None'",
    "size": "(width: 'int', height: 'int', *, title: 'str' = 'playground', fps: 'int' = 60) -> 'None'",
    "stop": "() -> 'None'",
    "stroke": "(color: 'Color') -> 'None'",
    "stroke_width": "(pixels: 'int') -> 'None'",
    "text": "(message: 'object', x: 'float', y: 'float', color: 'Color | None' = None) -> 'None'",
    "text_size": "(size: 'int') -> 'None'",
}

# Additive since v0.5 (Phase 0). Listed separately so the v0.5 set above stays
# an exact record of what Session 1 learners were given.
ADDED_FUNCTIONS = {
    "random_seed": "(seed: 'int | None' = None) -> 'None'",
    "run": "(*, fps: 'int | None' = None, max_frames: 'int | None' = None) -> 'None'",
    "save": "(path: 'str') -> 'None'",
    # Sprint 4, S-027: transforms and the state stack (contract F1/F2).
    "translate": "(dx: 'float', dy: 'float') -> 'None'",
    "rotate": "(degrees: 'float') -> 'None'",
    "scale": "(sx: 'float', sy: 'float | None' = None) -> 'None'",
    "push": "() -> 'None'",
    "pop": "() -> 'None'",
    "state": "() -> 'AbstractContextManager[None]'",
    "radians": "(degrees: 'float') -> 'float'",
    "degrees": "(radians: 'float') -> 'float'",
    # Sprint 4, S-028: shapes, paths and clipping (contract F3).
    "begin_shape": "() -> 'None'",
    "vertex": "(x: 'float', y: 'float') -> 'None'",
    "curve_vertex": "(cx1: 'float', cy1: 'float', cx2: 'float', cy2: 'float', x: 'float', y: 'float') -> 'None'",
    "end_shape": "(close: 'bool' = False) -> 'None'",
    "path": "() -> 'PathBuilder'",
    "draw_path": "(path: 'PathBuilder') -> 'None'",
    "clip": "(path: 'PathBuilder') -> 'None'",
    # Sprint 4, S-037: text measurement (contract T6).
    "text_width": "(message: 'object') -> 'float'",
}

LIVE_VALUES = {"width", "height", "mouse_x", "mouse_y", "mouse_pressed", "frame_count", "delta_time"}


def _sig(name: str) -> str:
    return str(inspect.signature(getattr(p, name)))


def test_every_v05_function_is_present_with_its_signature():
    for name, expected in V05_FUNCTIONS.items():
        assert callable(getattr(p, name)), name
        assert _sig(name) == expected, f"{name}{_sig(name)} != {name}{expected}"


def test_added_functions_have_expected_signatures():
    for name, expected in ADDED_FUNCTIONS.items():
        assert _sig(name) == expected, f"{name}{_sig(name)} != {name}{expected}"


def test_run_keeps_v05_call_forms():
    # v0.5 documented p.run() and p.run(fps=30); positional fps was never allowed.
    sig = inspect.signature(p.run)
    assert sig.parameters["fps"].kind is inspect.Parameter.KEYWORD_ONLY
    assert sig.parameters["fps"].default is None


def test_public_all_is_exactly_the_contract():
    assert set(p.__all__) == set(V05_FUNCTIONS) | set(ADDED_FUNCTIONS) | LIVE_VALUES


def test_live_values_are_dynamic_module_attributes():
    for name in LIVE_VALUES:
        assert hasattr(p, name), name
    # v0.5 already routes these through module __getattr__ (PEP 562) - they
    # must never become stale copies.
    assert "width" not in vars(p)


def test_unknown_attribute_raises_attribute_error():
    import pytest

    with pytest.raises(AttributeError):
        p.no_such_thing  # noqa: B018


def test_version_is_a_string():
    assert isinstance(p.__version__, str)
