"""Regressions found by the API fuzz spike (spikes/20_api_fuzz): calls a beginner can write that hung
or put nan into a saved file. Each must finish quickly, and either draw or raise a learner error."""
from __future__ import annotations

import pytest

import funground as f


@pytest.mark.parametrize("pattern", [float("nan"), float("inf"), [4, float("nan")]])
def test_a_dash_with_nan_or_inf_is_refused_before_it_breaks_the_pdf(canvas, pattern):
    with pytest.raises(ValueError, match=r"^f\.stroke_dash\(\)"):
        f.stroke_dash(pattern)
