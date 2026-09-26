"""Mapping, interpolation and random helpers (S-046, contract H3)."""
from __future__ import annotations

import pytest

import funground as p


def test_map_range():
    assert p.map_range(5, 0, 10, 0, 100) == 50
    assert p.map_range(0, 0, 10, 100, 0) == 100             # reversed target range
    assert p.map_range(20, 0, 10, 0, 100) == 200            # extrapolates by default
    assert p.map_range(20, 0, 10, 0, 100, clamp=True) == 100
    assert p.map_range(-5, 0, 10, 100, 0, clamp=True) == 100
    with pytest.raises(ValueError):
        p.map_range(1, 3, 3, 0, 1)


def test_lerp_norm_mag():
    assert p.lerp(10, 20, 0.25) == 12.5
    assert p.lerp(10, 20, 0) == 10 and p.lerp(10, 20, 1) == 20
    assert p.norm(15, 10, 20) == 0.5
    assert p.mag(3, 4) == 5
    with pytest.raises(ValueError):
        p.norm(1, 2, 2)


def test_map_range_does_not_shadow_builtins():
    import builtins

    import funground

    assert "map" not in funground.__all__ and builtins.map is map


def test_random_gaussian_and_choice_are_repeatable_with_the_seed():
    p.random_seed(3)
    first = ([p.random_gaussian(10, 2) for _ in range(5)], [p.random_choice("abcde") for _ in range(5)], p.random(1))
    p.random_seed(3)
    again = ([p.random_gaussian(10, 2) for _ in range(5)], [p.random_choice("abcde") for _ in range(5)], p.random(1))
    assert first == again


def test_random_gaussian_centres_on_the_mean():
    p.random_seed(1)
    values = [p.random_gaussian(50, 5) for _ in range(2000)]
    mean = sum(values) / len(values)
    assert 49 < mean < 51
    within = sum(1 for v in values if 45 <= v <= 55) / len(values)
    assert 0.6 < within < 0.75                               # about two thirds within one sd
    with pytest.raises(ValueError):
        p.random_gaussian(0, -1)


def test_random_choice():
    p.random_seed(2)
    assert p.random_choice(["only"]) == "only"
    assert p.random_choice((1, 2, 3)) in (1, 2, 3)
    with pytest.raises(ValueError):
        p.random_choice([])
