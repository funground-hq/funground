"""Capability registry and learner-facing errors (S-021)."""
from __future__ import annotations

import pytest

import playground as p
from playground import api, ir
from playground.capabilities import EXTRA_FOR, Capability, PlaygroundError
from playground.sketch import Sketch


class NoRasterRenderer:
    name = "toy"
    capabilities = frozenset()

    def attach(self, target):
        pass

    def render(self, frame):
        pass


def test_missing_capability_fails_at_size_not_mid_loop():
    api.use_sketch(Sketch(renderer=NoRasterRenderer()))
    with pytest.raises(PlaygroundError) as e:
        p.size(100, 100)
    msg = str(e.value)
    assert "Drawing shapes" in msg and "basic 2D shapes" in msg and "toy" in msg


def test_message_names_the_extra_when_one_exists(monkeypatch):
    monkeypatch.setitem(EXTRA_FOR, Capability.RASTER_2D, "design")
    api.use_sketch(Sketch(renderer=NoRasterRenderer()))
    with pytest.raises(PlaygroundError, match=r"pip install playground\[design\]"):
        p.size(100, 100)


def test_run_without_size_also_checks_capabilities():
    api.use_sketch(Sketch(renderer=NoRasterRenderer()))
    with pytest.raises(PlaygroundError):
        api.active_sketch().run_namespace({"draw": lambda: None}, max_frames=1)


def test_legacy_renderer_declares_raster_only():
    from playground.renderers.legacy_pygame import LegacyPygameRenderer

    assert LegacyPygameRenderer.capabilities == frozenset({Capability.RASTER_2D})


def test_playground_error_is_a_runtime_error():
    assert issubclass(PlaygroundError, RuntimeError)


def test_legacy_renderer_refuses_unknown_ops_loudly():
    """An op the legacy renderer cannot draw is a bug, not silence (deleted with it in S-026)."""
    from playground.renderers.legacy_pygame import LegacyPygameRenderer

    import pygame

    r = LegacyPygameRenderer()
    r.attach(pygame.Surface((10, 10)))
    with pytest.raises(NotImplementedError, match="Save"):
        r.render(ir.Frame([ir.Save()]))
