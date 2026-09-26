"""Capability registry and learner-facing errors (S-021)."""
from __future__ import annotations

import pytest

import funground as p
from funground import api, ir
from funground.capabilities import EXTRA_FOR, Capability, FungroundError
from funground.sketch import Sketch


class NoRasterRenderer:
    name = "toy"
    capabilities = frozenset()

    def attach(self, target):
        pass

    def render(self, frame):
        pass


def test_missing_capability_fails_at_size_not_mid_loop():
    api.use_sketch(Sketch(renderer=NoRasterRenderer()))
    with pytest.raises(FungroundError) as e:
        p.size(100, 100)
    msg = str(e.value)
    assert "Drawing shapes" in msg and "basic 2D shapes" in msg and "toy" in msg


def test_message_names_the_extra_when_one_exists(monkeypatch):
    monkeypatch.setitem(EXTRA_FOR, Capability.RASTER_2D, "design")
    api.use_sketch(Sketch(renderer=NoRasterRenderer()))
    with pytest.raises(FungroundError, match=r"pip install funground\[design\]"):
        p.size(100, 100)


def test_run_without_size_also_checks_capabilities():
    api.use_sketch(Sketch(renderer=NoRasterRenderer()))
    with pytest.raises(FungroundError):
        api.active_sketch().run_namespace({"draw": lambda: None}, max_frames=1)


def test_default_renderer_declares_the_vector_contract():
    from funground.renderers.cairo2d import CairoRenderer
    from funground.sketch import RENDERERS, default_renderer

    assert set(RENDERERS) == {"cairo"}
    assert isinstance(default_renderer(), CairoRenderer)
    assert {Capability.RASTER_2D, Capability.ALPHA, Capability.CLIP_PATH} <= CairoRenderer.capabilities


def test_unknown_renderer_name_is_an_error(monkeypatch):
    from funground.sketch import default_renderer

    monkeypatch.setenv("FUNGROUND_RENDERER", "crayon")
    with pytest.raises(ValueError, match="crayon"):
        default_renderer()


def test_funground_error_is_a_runtime_error():
    assert issubclass(FungroundError, RuntimeError)
