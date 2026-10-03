"""The frozen v0.5 public API, as an executable contract.

If any of these fail, learner-visible behaviour has changed. Change the
expectation here only as a deliberate, documented decision.
"""
from __future__ import annotations

import inspect

import funground as p

V05_FUNCTIONS = {
    "background": "(color: 'Color', *more: 'float') -> 'None'",
    "circle": "(x: 'float', y: 'float', diameter: 'float') -> 'None'",
    "constrain": "(value: 'float', low: 'float', high: 'float') -> 'float'",
    "distance": "(x1: 'float', y1: 'float', x2: 'float', y2: 'float') -> 'float'",
    "ellipse": "(x: 'float', y: 'float', width: 'float', height: 'float') -> 'None'",
    "fill": "(color: 'Color', *more: 'float') -> 'None'",
    "key_down": "(key: 'str | int') -> 'bool'",
    "line": "(x1: 'float', y1: 'float', x2: 'float', y2: 'float') -> 'None'",
    "no_fill": "() -> 'None'",
    "no_stroke": "() -> 'None'",
    "point": "(x: 'float', y: 'float') -> 'None'",
    "random": "(low: 'float' = 1.0, high: 'float | None' = None) -> 'float'",
    "rect": "(x: 'float', y: 'float', width: 'float', height: 'float', *radii: 'float') -> 'None'",
    "size": "(width: 'int', height: 'int', *, title: 'str' = 'funground', fps: 'int' = 60) -> 'None'",
    "stop": "() -> 'None'",
    "stroke": "(color: 'Color', *more: 'float') -> 'None'",
    "stroke_width": "(pixels: 'int') -> 'None'",
    "text": "(message: 'object', x: 'float', y: 'float', color: 'Color | None' = None) -> 'None'",
    "text_size": "(size: 'int') -> 'None'",
}

# Additive since v0.5 (Phase 0). Listed separately so the v0.5 set above stays
# an exact record of what Session 1 learners were given.
ADDED_FUNCTIONS = {
    "random_seed": "(seed: 'int | None' = None) -> 'None'",
    "run": "(*, fps: 'int | None' = None, max_frames: 'int | None' = None) -> 'None'",
    "save": "(path: 'str', *, text: 'str' = 'live') -> 'None'",
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
    "square": "(x: 'float', y: 'float', size: 'float', *radii: 'float') -> 'None'",
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
    # S-049 text alignment and metrics
    "text_align": "(horizontal: 'str', vertical: 'str | None' = None) -> 'None'",
    "text_ascent": "() -> 'float'",
    "text_descent": "() -> 'float'",
    # S-053 multi-line text and text boxes
    "text_box": "(message: 'object', x: 'float', y: 'float', width: 'float', height: 'float | None' = None, color: 'Color | None' = None) -> 'str | FormattedString'",
    "text_leading": "(leading: 'float | None') -> 'None'",
    # S-050 gradients
    "linear_gradient": "(x1: 'float', y1: 'float', x2: 'float', y2: 'float', colors, stops=None)",
    "radial_gradient": "(x: 'float', y: 'float', radius: 'float', colors, stops=None)",
    # S-051 blend modes, opacity, shadow
    "blend_mode": "(mode: 'str') -> 'None'",
    "opacity": "(amount: 'float') -> 'None'",
    "shadow": "(x_offset: 'float', y_offset: 'float', blur: 'float' = 5, color: 'Color' = (0, 0, 0, 128)) -> 'None'",
    "no_shadow": "() -> 'None'",
    # S-056 frame sequences
    "save_frames": "(pattern: 'str', count: 'int') -> 'None'",
    # S-057 window control
    "resize_canvas": "(width: 'int', height: 'int') -> 'None'",
    "full_screen": "() -> 'None'",
    "cursor": "(kind: 'str' = 'arrow') -> 'None'",
    "no_cursor": "() -> 'None'",
    # S-054 fonts and styles
    "load_font": "(path: 'str')",
    "text_font": "(font, size: 'float | None' = None) -> 'None'",
    "text_style": "(style: 'str') -> 'None'",
    # S-052 off-screen graphics
    "create_graphics": "(width: 'int', height: 'int') -> 'Picture'",
    "image": "(picture, x: 'float', y: 'float', width: 'float | None' = None, height: 'float | None' = None, sx: 'float | None' = None, sy: 'float | None' = None, sw: 'float | None' = None, sh: 'float | None' = None) -> 'None'",
    # S-076 script mode
    "show": "() -> 'None'",
    # S-077 images
    "load_image": "(path: 'str') -> 'Picture'",
    # S-092 SVG import
    "load_svg": "(path: 'str') -> 'Picture'",
    "svg_paths": "(path: 'str') -> 'list[PathBuilder]'",
    # S-098 sound
    "load_sound": "(path: 'str')",
    # S-110 making sound
    "create_sound": "(samples, rate: 'int' = 44100)",
    "tone": "(frequency: 'float', seconds: 'float', wave: 'str' = 'sine', volume: 'float' = 1, attack: 'float' = 0.01, release: 'float' = 0.05)",
    "note": "(name: 'str', seconds: 'float', wave: 'str' = 'sine', volume: 'float' = 1, attack: 'float' = 0.01, release: 'float' = 0.05)",
    "pluck": "(name_or_frequency, seconds: 'float', volume: 'float' = 1)",
    "melody": "(text: 'str', tempo: 'float' = 120, wave: 'str' = 'sine', sa: 'str | None' = None, tuning: 'str' = 'equal')",
    "sequence": "(*sounds)",
    "mix": "(*sounds)",
    "note_to_frequency": "(name: 'str', sa: 'str | None' = None) -> 'float'",
    "frequency_to_note": "(hz: 'float', sa: 'str | None' = None) -> 'str'",
    # S-108 microphone
    "microphone": "(name: 'str | None' = None)",
    "microphones": "() -> 'list[str]'",
    # S-115 ragas
    "ragas": "() -> 'list[str]'",
    "raga": "(name: 'str')",
    "talas": "() -> 'list[str]'",
    "tala_info": "(name: 'str')",
    "tala": "(name: 'str', tempo: 'float' = 80, cycles: 'int' = 1)",
    "drone": "(sa, seconds: 'float', pattern: 'str' = \"P S' S' S\")",
    "match_ragas": "(histogram) -> 'list[tuple[str, float]]'",
    # S-090 tracking, features, variations
    "text_tracking": "(pixels: 'float') -> 'None'",
    "text_features": "(**features: 'bool') -> 'None'",
    "font_variations": "(**axes: 'float') -> 'None'",
    # S-091 formatted text
    "FormattedString": "() -> 'None'",
    # S-088 text as a path
    "text_path": "(message: 'object', x: 'float', y: 'float') -> 'PathBuilder'",
    # S-104/S-106 text to points, font information
    "text_to_points": "(message: 'object', x: 'float', y: 'float', spacing: 'float' = 5) -> 'list[tuple[float, float]]'",
    "current_font": "() -> 'Font'",
    # S-102 fallback
    "text_fallback": "(*fonts) -> 'None'",
    "system_font": "(name: 'str')",
    # S-100 motion
    "save_gif": "(path: 'str', seconds: 'float') -> 'None'",
    "save_movie": "(path: 'str', seconds: 'float') -> 'None'",
    "frame_duration": "(seconds: 'float') -> 'None'",
    # S-095 layers
    "layer": "(name: 'str') -> 'Picture'",
    "hide_layer": "(name: 'str') -> 'None'",
    "show_layer": "(name: 'str') -> 'None'",
    # S-101 controls
    "create_slider": "(low: 'float', high: 'float', value: 'float | None' = None, step: 'float | None' = None, label: 'str | None' = None) -> 'Slider'",
    "create_checkbox": "(label: 'str', checked: 'bool' = False) -> 'Checkbox'",
    "create_button": "(label: 'str') -> 'Button'",
    # S-084 pages
    "new_page": "(width: 'int | str | None' = None, height: 'int | None' = None) -> 'None'",
    "page_count": "() -> 'int'",
    "page_size": "(name: 'str', landscape: 'bool' = False) -> 'tuple[int, int]'",
    # S-081 drawing modes
    "rect_mode": "(mode: 'str') -> 'None'",
    "ellipse_mode": "(mode: 'str') -> 'None'",
    "image_mode": "(mode: 'str') -> 'None'",
    # S-082 colour mode
    "color_mode": "(mode: 'str', max1: 'float | None' = None, max2: 'float | None' = None, max3: 'float | None' = None, max_alpha: 'float | None' = None) -> 'None'",
    # S-078 tint and image parts (image's signature is under S-052)
    "tint": "(color, *more: 'float') -> 'None'",
    "no_tint": "() -> 'None'",
    # S-107 erase
    "erase": "(fill_strength: 'float' = 255, stroke_strength: 'float' = 255) -> 'None'",
    "no_erase": "() -> 'None'",
    # S-079 pixels
    "get": "(x: 'float', y: 'float', w: 'float | None' = None, h: 'float | None' = None)",
    "set": "(x: 'float', y: 'float', color, *more: 'float') -> 'None'",
    "load_pixels": "() -> 'None'",
    "update_pixels": "() -> 'None'",
    # S-080 copy, resize, mask, filters (the picture methods copy/resize/mask/filter are in test_filters.py)
    "filter": "(kind: 'str', value: 'float | None' = None) -> 'None'",
}

# D-016 renamed mouse_pressed -> is_mouse_pressed (approved change to the v0.5 contract);
# S-045 added pmouse_x/y, mouse_button, key, key_code and is_key_pressed.
LIVE_VALUES = {"width", "height", "mouse_x", "mouse_y", "is_mouse_pressed", "pmouse_x", "pmouse_y",
               "mouse_button", "key", "key_code", "is_key_pressed", "frame_count", "delta_time", "pixels"}


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
