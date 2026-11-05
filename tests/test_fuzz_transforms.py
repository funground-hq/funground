"""Regressions found by the API fuzz spike (spikes/20_api_fuzz): calls a beginner can write that hung
or put nan into a saved file. Each must finish quickly, and either draw or raise a learner error."""
from __future__ import annotations

import pytest

import funground as f


@pytest.mark.parametrize("call", [
    lambda: f.translate(float("nan"), 0),
    lambda: f.translate(0, float("inf")),
    lambda: f.rotate(float("nan")),
    lambda: f.rotate(float("inf")),
    lambda: f.scale(float("nan")),
    lambda: f.scale(2, float("inf")),
    lambda: f.shear_x(float("nan")),
    lambda: f.apply_matrix(1, 0, 0, 1, float("nan"), 0),
])
def test_a_transform_with_nan_or_inf_is_refused_with_a_sentence(canvas, call):
    with pytest.raises(ValueError, match=r"^f\.\w+\(\): .*finite number"):
        call()


def test_nan_translate_never_reaches_a_saved_svg(canvas, tmp_path):
    try:
        f.translate(float("nan"), 0)
    except ValueError:
        pass
    f.circle(50, 50, 20)
    out = tmp_path / "out.svg"
    f.save(str(out))
    assert "nan" not in out.read_text(encoding="utf-8").lower()
