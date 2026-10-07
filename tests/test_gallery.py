"""Examples Gallery (S-068): every example runs, is pinned, and together they cover the API.

Goldens live in tests/golden/gallery/, IR snapshots in tests/snapshots/gallery/, both
named '<area>-<stem>'. Same policy as the Session-1 suite: exact goldens on the golden
platform only, snapshots everywhere; time-dependent examples are smoke-tested only.
Write new goldens/snapshots by running the suite once; never edit them by hand.
"""
from __future__ import annotations

import importlib.util
import json
import os
import platform
import re
from pathlib import Path

import pygame
import pytest

import funground
from funground import api, ir

from conftest import GOLDEN, ROOT, assert_json_documents_close, run_sketch, surface_from_frame

TOOL = ROOT / "tools" / "make_gallery.py"
_spec = importlib.util.spec_from_file_location("make_gallery", TOOL)
gallery = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gallery)

EXAMPLES = gallery.examples()
DETERMINISTIC = [e for e in EXAMPLES if not gallery.is_time_dependent(e)]
GALLERY_GOLDEN = GOLDEN / "gallery"
GALLERY_SNAPSHOTS = ROOT / "tests" / "snapshots" / "gallery"
GOLDEN_PLATFORM = "Windows"

# Public names not yet shown by any example. This list may only shrink: the test below
# fails if a listed name is now covered, and S-072 (release 0.1) requires it empty.
# S-132: Ground and Mark get their gallery examples with the studios (Sprint 16).
NOT_YET_IN_GALLERY: set[str] = {"grid", "ground", "inch", "mm", "mark", "variations", "keep", "play"}


@pytest.fixture(autouse=True)
def _scratch_cwd(tmp_path, monkeypatch):
    """Examples that f.save() write into a throwaway directory, never the repo. They also run with no
    sound device and a silent microphone: a test must not open the real microphone (two examples that
    do, in one process, made the suite hang at the second one)."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("FUNGROUND_HEADLESS", "1")


def test_gallery_exists_and_every_example_has_a_docstring():
    assert len(EXAMPLES) >= 15
    for path in EXAMPLES:
        title, description = gallery.title_and_description(path)
        assert title != path.stem and description, f"{path.name} needs a docstring: title line + description"


@pytest.mark.parametrize("path", EXAMPLES, ids=gallery.example_id)
def test_example_runs_headless(path: Path):
    (w, h), data = run_sketch(path, frames=30)
    assert len(data) == w * h * 3


@pytest.mark.parametrize("path", DETERMINISTIC, ids=gallery.example_id)
def test_example_matches_golden(path: Path):
    frame = run_sketch(path, frames=30)
    golden = GALLERY_GOLDEN / f"{gallery.example_id(path)}.png"
    if not golden.exists():
        GALLERY_GOLDEN.mkdir(parents=True, exist_ok=True)
        pygame.image.save(surface_from_frame(frame), str(golden))
        pytest.skip(f"golden written: {golden.name}")
    if platform.system() != GOLDEN_PLATFORM:
        pytest.skip(f"goldens were produced on {GOLDEN_PLATFORM}")
    same = pygame.image.tobytes(pygame.image.load(str(golden)), "RGB") == frame[1]
    if not same:
        actual = GOLDEN / "_actual"
        actual.mkdir(exist_ok=True)
        pygame.image.save(surface_from_frame(frame), str(actual / golden.name))
    assert same, f"{path.name} differs from its golden; actual saved to tests/golden/_actual/"


@pytest.mark.parametrize("path", DETERMINISTIC, ids=gallery.example_id)
def test_example_ops_match_snapshot(path: Path):
    run_sketch(path, frames=30)
    actual = json.dumps(ir.Frame(list(api.active_sketch().last_ops)).to_jsonable(), indent=1, sort_keys=True) + "\n"
    snap = GALLERY_SNAPSHOTS / f"{gallery.example_id(path)}.json"
    if not snap.exists():
        GALLERY_SNAPSHOTS.mkdir(parents=True, exist_ok=True)
        snap.write_text(actual, encoding="utf-8", newline="\n")
        pytest.skip(f"snapshot written: {snap.name}")
    expected = snap.read_text(encoding="utf-8")
    if actual != expected:
        out = ROOT / "tests" / "snapshots" / "_actual"
        out.mkdir(parents=True, exist_ok=True)
        (out / snap.name).write_text(actual, encoding="utf-8")
    try:
        assert_json_documents_close(json.loads(actual), json.loads(expected))
    except AssertionError as exc:
        raise AssertionError(
            f"{path.name}: op list differs from its snapshot; actual saved to tests/snapshots/_actual/: {exc}"
        ) from exc


def _names_used() -> set[str]:
    used = set()
    for path in EXAMPLES:
        used |= set(re.findall(r"\bf\.([A-Za-z_]+)\b", path.read_text(encoding="utf-8")))
    return used


def test_every_public_name_is_shown_by_an_example():
    """D-015, D-019: release 0.1 ships a gallery that highlights every feature."""
    public = set(funground.__all__)
    uncovered = public - _names_used()
    unexpected = uncovered - NOT_YET_IN_GALLERY
    assert not unexpected, f"public names with no gallery example: {sorted(unexpected)}"
    stale = NOT_YET_IN_GALLERY & (_names_used() | (NOT_YET_IN_GALLERY - public))
    assert not stale, f"now covered or no longer public - remove from NOT_YET_IN_GALLERY: {sorted(stale)}"


def test_index_is_up_to_date():
    index = gallery.INDEX
    assert index.exists(), "run: python tools/make_gallery.py"
    assert index.read_text(encoding="utf-8") == gallery.build_index(), "run: python tools/make_gallery.py --index"


def test_showcase_is_up_to_date():
    showcase = gallery.SHOWCASE
    assert showcase.exists(), "run: python tools/make_gallery.py --index"
    assert showcase.read_text(encoding="utf-8") == gallery.build_showcase(), "run: python tools/make_gallery.py --index"
    assert 10 <= len(gallery.SHOWCASE_PICKS) <= 12
    assert all((gallery.IMAGES / f"{ident}.png").exists() for ident, _ in gallery.SHOWCASE_PICKS)


def test_every_example_has_a_gallery_image():
    missing = [gallery.example_id(p) for p in EXAMPLES if not (gallery.IMAGES / f"{gallery.example_id(p)}.png").exists()]
    assert not missing, f"run: python tools/make_gallery.py  (missing images: {missing})"
