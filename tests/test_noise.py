"""Noise (S-047, contract H4): p5.js's algorithm and seeding, value for value."""
from __future__ import annotations

import pytest

import funground as p

# Reference values computed by p5.js's noise/noiseSeed algorithm (run in Node during S-047).
P5_SEED_42 = [((0,), 0.236574), ((0.5,), 0.202788), ((1.3, 2.7), 0.463387), ((0.1, 0.2, 0.3), 0.312246)]


def test_seeded_noise_matches_p5_values():
    p.noise_seed(42)
    for args, expected in P5_SEED_42:
        assert p.noise(*args) == pytest.approx(expected, abs=1e-6)


def test_same_seed_same_field_and_random_seed_does_not_touch_it():
    p.noise_seed(7)
    first = [p.noise(i * 0.1, 3.3) for i in range(20)]
    p.random_seed(123)                       # must not change noise
    p.noise_seed(7)
    assert [p.noise(i * 0.1, 3.3) for i in range(20)] == first


def test_values_stay_between_0_and_1_and_change_smoothly():
    p.noise_seed(1)
    values = [p.noise(i * 0.01, 5.5, 0.25) for i in range(2000)]
    assert all(0 <= v <= 1 for v in values)
    assert max(abs(a - b) for a, b in zip(values, values[1:])) < 0.05


def test_negative_inputs_mirror_like_p5():
    p.noise_seed(3)
    assert p.noise(-1.5, -2.25) == p.noise(1.5, 2.25)


def test_noise_detail_changes_the_field():
    p.noise_seed(9)
    rich = p.noise(0.37, 0.61)
    p.noise_detail(1)
    assert p.noise(0.37, 0.61) != rich
    p.noise_detail(4, 0.5)
    assert p.noise(0.37, 0.61) == rich


@pytest.mark.parametrize("args", [(0,), (2, 0), (2, 1.5), (2, -0.1)])
def test_noise_detail_rejects_bad_values(args):
    with pytest.raises(ValueError):
        p.noise_detail(*args)
