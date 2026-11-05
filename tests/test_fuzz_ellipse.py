"""Regressions found by the API fuzz spike (spikes/20_api_fuzz): calls a beginner can write that hung
or put nan into a saved file. Each must finish quickly, and either draw or raise a learner error."""
from __future__ import annotations

import pytest

import funground as f


@pytest.mark.parametrize("call", [
    lambda: f.circle(100, 50, float("inf")),
    lambda: f.ellipse(100, 50, float("inf"), 20),
    lambda: f.ellipse(100, 50, 20, -float("inf")),
])
def test_an_infinite_circle_is_refused_rather_than_stalling_the_pdf(canvas, call):
    with pytest.raises(ValueError, match=r"^f\.(circle|ellipse)\(\): .* came out as "):
        call()
