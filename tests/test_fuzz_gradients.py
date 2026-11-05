"""Regressions found by the API fuzz spike (spikes/20_api_fuzz): calls a beginner can write that hung
or put nan into a saved file. Each must finish quickly, and either draw or raise a learner error."""
from __future__ import annotations

import pytest

import funground as f


@pytest.mark.parametrize("call", [
    lambda: f.linear_gradient(float("nan"), 0, 200, 0, ["red", "blue"]),
    lambda: f.linear_gradient(0, 0, float("inf"), 0, ["red", "blue"]),
    lambda: f.radial_gradient(320, float("nan"), 300, ["white", "navy"]),
    lambda: f.radial_gradient(320, 200, float("inf"), ["white", "navy"]),
])
def test_a_gradient_with_nan_or_inf_is_refused_with_a_sentence(canvas, call):
    with pytest.raises(ValueError, match=r"gradient needs finite numbers"):
        call()
