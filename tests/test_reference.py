"""Quick Reference v0.6 (story S-030): the document is produced by the code it documents.

Acceptance line of the story: every name in ``funground.__all__`` appears in the
reference with a runnable example. The runnable examples are the sketches in
examples/reference/, embedded verbatim in the markdown; the pictures are made
from them by tools/make_reference_images.py.
"""
from __future__ import annotations

import importlib.util
import re
import struct
from pathlib import Path

import pytest

import funground

from conftest import ROOT

REFERENCE = ROOT / "docs" / "reference" / "Quick_Reference.md"
IMAGES = ROOT / "docs" / "reference" / "images"
SKETCHES = sorted((ROOT / "examples" / "reference").glob("*.py"))
TOOL = ROOT / "tools" / "make_reference_images.py"


def _tool():
    spec = importlib.util.spec_from_file_location("make_reference_images", TOOL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _png_size(data: bytes) -> tuple[int, int]:
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    return struct.unpack(">II", data[16:24])


@pytest.fixture(scope="module")
def reference_text() -> str:
    return REFERENCE.read_text(encoding="utf-8")


def test_reference_sketches_are_present():
    assert len(SKETCHES) >= 11


def test_every_public_name_is_documented(reference_text):
    missing = [name for name in funground.__all__ if f"f.{name}" not in reference_text]
    assert not missing, f"names in funground.__all__ absent from the Quick Reference: {missing}"
    # The reference must state the version it documents (follows S-070 / releases).
    assert funground.__version__ in reference_text and "f.__version__" in reference_text


@pytest.mark.parametrize("sketch", SKETCHES, ids=lambda s: s.name)
def test_every_reference_sketch_is_embedded_verbatim(sketch: Path, reference_text):
    source = sketch.read_text(encoding="utf-8").strip()
    assert source in reference_text, f"{sketch.name} is not embedded verbatim in the reference"
    assert f"images/{sketch.stem}.png" in reference_text


def test_every_referenced_image_exists(reference_text):
    refs = re.findall(r"!\[[^\]]*\]\(([^)]+)\)", reference_text)
    assert refs, "the reference has no pictures"
    for ref in refs:
        path = REFERENCE.parent / ref
        assert path.exists(), f"missing image {ref}"
        assert _png_size(path.read_bytes()) == (640, 400), ref


@pytest.mark.parametrize("sketch", SKETCHES, ids=lambda s: s.name)
def test_reference_sketch_renders_headless_through_the_tool(sketch: Path, tmp_path: Path):
    out = _tool().render(sketch, tmp_path / f"{sketch.stem}.png", frames=3)
    assert _png_size(out.read_bytes()) == (640, 400)
