"""The sentence for nan and infinity (D-130): it does not call nan a number, or guess how the value was made."""
from __future__ import annotations

import pytest

import funground as f


def test_nan_is_said_to_be_not_a_number(canvas):
    with pytest.raises(ValueError) as caught:
        f.rotate(float("nan"))
    assert str(caught.value) == ('f.rotate(): angle came out as "not a number" (nan), so it cannot be used. '
                                 "Check how angle was worked out.")


def test_infinity_is_named(canvas):
    with pytest.raises(ValueError) as caught:
        f.rotate(float("inf"))
    assert str(caught.value) == ("f.rotate(): angle came out as infinity (inf), so it cannot be used. "
                                 "Check how angle was worked out.")


def test_minus_infinity_is_named(canvas):
    with pytest.raises(ValueError, match=r"came out as minus infinity \(-inf\)"):
        f.rotate(float("-inf"))


@pytest.mark.parametrize("call", [
    lambda: f.rotate(float("nan")),
    lambda: f.circle(0, 0, float("inf")),
    lambda: f.linear_gradient(float("nan"), 0, 200, 0, ["red", "blue"]),
    lambda: f.arc(0, 0, 10, 10, float("inf"), 90),
])
def test_no_sentence_says_finite_or_sum(canvas, call):
    with pytest.raises(ValueError) as caught:
        call()
    message = str(caught.value)
    assert "finite" not in message and "sum" not in message
