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
    "saved_state": "() -> 'AbstractContextManager[None]'",
    "radians": "(degrees: 'float') -> 'float'",
    "degrees": "(radians: 'float') -> 'float'",
    # Sprint 4, S-028: shapes, paths and clipping (contract F3).
    "begin_shape": "() -> 'None'",
    "vertex": "(x: 'float', y: 'float') -> 'None'",
    "end_shape": "(close: 'bool' = False) -> 'None'",
    "path": "() -> 'PathBuilder'",
    "draw_path": "(path: 'PathBuilder') -> 'None'",
    "clip": "(path: 'PathBuilder') -> 'None'",
    # Sprint 4, S-037: text measurement (contract T6).
    "text_width": "(message: 'object') -> 'float'",
    # Sprint 5, S-041: more shapes, clear, no_clip (contract F5-F7).
    "square": "(x: 'float', y: 'float', size: 'float') -> 'None'",
    "triangle": "(x1: 'float', y1: 'float', x2: 'float', y2: 'float', x3: 'float', y3: 'float') -> 'None'",
    "quad": "(x1: 'float', y1: 'float', x2: 'float', y2: 'float', x3: 'float', y3: 'float', x4: 'float', y4: 'float') -> 'None'",
    "polygon": "(points: 'list[tuple[float, float]]') -> 'None'",
    "arc": "(x: 'float', y: 'float', width: 'float', height: 'float', start: 'float', stop: 'float', mode: 'str' = 'open') -> 'None'",
    "clear": "() -> 'None'",
    "no_clip": "() -> 'None'",
    # Sprint 5, S-042: stroke styles and smoothing (contract S11, C6).
    "stroke_cap": "(cap: 'str') -> 'None'",
    "stroke_join": "(join: 'str') -> 'None'",
    "miter_limit": "(limit: 'float') -> 'None'",
    "stroke_dash": "(pattern: 'float | list[float]', offset: 'float' = 0) -> 'None'",
    "no_dash": "() -> 'None'",
    "no_smooth": "() -> 'None'",
    "smooth": "() -> 'None'",
    # Sprint 5, S-043: shear and matrices (contract F8).
    "shear_x": "(degrees: 'float') -> 'None'",
    "shear_y": "(degrees: 'float') -> 'None'",
    "apply_matrix": "(a: 'float', b: 'float', c: 'float', d: 'float', e: 'float', f: 'float') -> 'None'",
    "reset_matrix": "() -> 'None'",
    # Sprint 5, S-074: curve vocabulary aligned with Processing (D-018, contract F3/F9).
    "bezier_vertex": "(cx1: 'float', cy1: 'float', cx2: 'float', cy2: 'float', x: 'float', y: 'float') -> 'None'",
    "quadratic_vertex": "(cx: 'float', cy: 'float', x: 'float', y: 'float') -> 'None'",
    "curve_vertex": "(x: 'float', y: 'float') -> 'None'",
    "curve_tightness": "(tightness: 'float') -> 'None'",
    "begin_contour": "() -> 'None'",
    "end_contour": "() -> 'None'",
    "bezier": "(x1: 'float', y1: 'float', cx1: 'float', cy1: 'float', cx2: 'float', cy2: 'float', x2: 'float', y2: 'float') -> 'None'",
    "curve": "(x1: 'float', y1: 'float', x2: 'float', y2: 'float', x3: 'float', y3: 'float', x4: 'float', y4: 'float') -> 'None'",
    "bezier_point": "(a: 'float', b: 'float', c: 'float', d: 'float', t: 'float') -> 'float'",
    "bezier_tangent": "(a: 'float', b: 'float', c: 'float', d: 'float', t: 'float') -> 'float'",
    "curve_point": "(a: 'float', b: 'float', c: 'float', d: 'float', t: 'float') -> 'float'",
    "curve_tangent": "(a: 'float', b: 'float', c: 'float', d: 'float', t: 'float') -> 'float'",
    # Sprint 5, S-046: mapping, interpolation and random helpers (contract H3).
    "random_gaussian": "(mean: 'float' = 0.0, sd: 'float' = 1.0) -> 'float'",
    "random_choice": "(items)",
    "map_range": "(value: 'float', start1: 'float', stop1: 'float', start2: 'float', stop2: 'float', clamp: 'bool' = False) -> 'float'",
    "lerp": "(start: 'float', stop: 'float', amount: 'float') -> 'float'",
    "norm": "(value: 'float', start: 'float', stop: 'float') -> 'float'",
    "mag": "(x: 'float', y: 'float') -> 'float'",
    # Sprint 5, S-047: noise (contract H4).
    "noise": "(x: 'float', y: 'float' = 0.0, z: 'float' = 0.0) -> 'float'",
    "noise_seed": "(seed: 'int') -> 'None'",
    "noise_detail": "(octaves: 'int', falloff: 'float | None' = None) -> 'None'",
    # Sprint 5, S-048: loop control and the clock (contract R10).
    "exit": "() -> 'None'",
    "no_loop": "() -> 'None'",
    "loop": "() -> 'None'",
    "redraw": "() -> 'None'",
    "is_looping": "() -> 'bool'",
    "millis": "() -> 'int'",
    "frame_rate": "() -> 'float'",
    "second": "() -> 'int'",
    "minute": "() -> 'int'",
    "hour": "() -> 'int'",
    "day": "() -> 'int'",
    "month": "() -> 'int'",
    "year": "() -> 'int'",
    # Sprint 5, S-044: colour constructors and colour objects (D-017 = C, contract S12).
    "color": "(*values)",
    "hsb": "(hue: 'float', saturation: 'float', brightness: 'float', alpha: 'float' = 255)",
    "hsl": "(hue: 'float', saturation: 'float', lightness: 'float', alpha: 'float' = 255)",
    "lerp_color": "(c1: 'Color', c2: 'Color', amount: 'float')",
    # S-055 Vector
    "Vector": "(x: 'float' = 0.0, y: 'float' = 0.0) -> 'None'",
}

# D-016 renamed mouse_pressed -> is_mouse_pressed (approved change to the v0.5 contract);
# S-045 added pmouse_x/y, mouse_button, key, key_code and is_key_pressed.
LIVE_VALUES = {"width", "height", "mouse_x", "mouse_y", "is_mouse_pressed", "pmouse_x", "pmouse_y",
               "mouse_button", "key", "key_code", "is_key_pressed", "frame_count", "delta_time"}


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
