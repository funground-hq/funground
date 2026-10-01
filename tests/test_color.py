"""Contract row S1: every colour form the Quick Reference documents parses to the same RGBA."""
from __future__ import annotations

import pytest

from funground._colornames import NAMED_COLORS
from funground.color import BLACK, WHITE, Color


@pytest.mark.parametrize(
    "value, expected",
    [
        ("tomato", (255, 99, 71, 255)),
        ("Tomato", (255, 99, 71, 255)),
        ("navy", (0, 0, 128, 255)),
        ("gray25", (64, 64, 64, 255)),
        ("darkslategrey", (47, 79, 79, 255)),
        ("aqua", (0, 255, 255, 255)),
        ((255, 0, 0), (255, 0, 0, 255)),
        ((0, 180, 100), (0, 180, 100, 255)),
        ([120, 80, 200], (120, 80, 200, 255)),
        ((0, 0, 255, 64), (0, 0, 255, 64)),
        ("#F05A45", (0xF0, 0x5A, 0x45, 255)),
        ("#203040", (0x20, 0x30, 0x40, 255)),
        ("#FF634780", (255, 99, 71, 128)),
        ("0xFF6347", (255, 99, 71, 255)),
        ("0xFF634780", (255, 99, 71, 128)),
        (Color(1, 2, 3, 4), (1, 2, 3, 4)),
    ],
)
def test_documented_forms_parse(value, expected):
    assert Color.parse(value).rgba == expected


def test_named_table_matches_pygame_ce():
    pygame = pytest.importorskip("pygame")
    from pygame.colordict import THECOLORS

    assert NAMED_COLORS == {k: tuple(v) for k, v in THECOLORS.items()}


def test_backend_compatible_forms_still_work():
    """v0.5 forwarded anything pygame accepted; the frozen API keeps those forms (contract S1)."""
    pygame = pytest.importorskip("pygame")
    # pygame.Color objects, via duck-typed r/g/b/a - no pygame import in color.py
    assert Color.parse(pygame.Color("tomato")).rgba == (255, 99, 71, 255)
    assert Color.parse(pygame.Color(1, 2, 3, 4)).rgba == (1, 2, 3, 4)
    # a single number is a grey, not a packed colour (S16, D-032); the string forms stay
    assert Color.parse(128).rgba == (128, 128, 128, 255)
    assert Color.parse(255).rgba == (255, 255, 255, 255)
    assert Color.parse("0xFF634780").rgba == (255, 99, 71, 128)
    with pytest.raises(ValueError):
        Color.parse(0x1_0000_0000)


def test_aliases_are_identical():
    assert Color.parse("aqua") == Color.parse("cyan")
    assert Color.parse("fuchsia") == Color.parse("magenta")
    assert Color.parse("gray") == Color.parse("grey")


@pytest.mark.parametrize("bad", ["banana", "#12345", "#GGGGGG", (1,), (1, 2, 3, 4, 5), (1, 256), (256, 0, 0), (-1, 0, 0), (256.0, 0, 0), (float("nan"), 0, 0), None, (True, 0, 0), object()])
def test_invalid_forms_raise_learner_readable_error(bad):
    with pytest.raises(ValueError) as e:
        Color.parse(bad)
    assert "colour" in str(e.value)


def test_constants():
    assert WHITE.rgb == (255, 255, 255) and BLACK.rgb == (0, 0, 0)
    assert WHITE.a == 255


def test_color_is_immutable_and_hashable():
    c = Color(1, 2, 3)
    with pytest.raises(AttributeError):
        c.r = 5  # type: ignore[misc]
    assert len({c, Color(1, 2, 3)}) == 1


@pytest.mark.parametrize("value, expected", [
    ((211.8, 10.5, 255.0), (211, 10, 255, 255)),
    ((255.99, 0, 0), (255, 0, 0, 255)),
    ((-0.5, 0, 0), (0, 0, 0, 255)),
    ((0, 0, 0, 127.9), (0, 0, 0, 127)),
])
def test_fractional_components_are_truncated_like_v05(value, expected):
    """v0.5 passed tuples to pygame-ce, which truncates; computed colours must keep working."""
    pygame = pytest.importorskip("pygame")
    assert Color.parse(value).rgba == expected == tuple(pygame.Color(value))
