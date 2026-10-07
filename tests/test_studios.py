"""Studios (S-132): six compositions, each written twice, draw the same picture.

Each studio is a gallery example in examples/gallery/studios/NN_name.py, written with the studio
vocabulary (Ground, Area and Grid, Mark, Play), and a "before" version in
examples/studios/NN_name_before.py that draws the same picture with what funground had before it.
Both are printed in full in docs/guide/19_studios.md. These tests render both versions headless
and compare the pictures, check that the guide prints the files exactly, and check that the poster
series keeps its versions next to the sketch, never in the repository.
"""
from __future__ import annotations

import inspect
import json
import re
import shutil
from pathlib import Path

import pytest

import funground
from funground import api
from funground.platform.base import InputEvent
from funground.platform.headless import HeadlessPlatform
from funground.sketch import Sketch

from conftest import ROOT, reset_funground, run_sketch

AFTER = ROOT / "examples" / "gallery" / "studios"
BEFORE = ROOT / "examples" / "studios"
CHAPTER = ROOT / "docs" / "guide" / "19_studios.md"
STUDIOS = sorted(AFTER.glob("[0-9][0-9]_*.py"))

# The pairs that are not pixel-equal, and why. Both differences come from contract K1: a mark's bounds
# are conservative, rounded out to 1/32 of a unit, while the before versions measure exactly.
NEAR = {
    "05_text_as_geometry": "each version is fitted by its mark's bounds, which may be up to 1/32 unit larger "
                           "on a side than the path's exact bounds() that the before version uses",
    "06_poster_series": "anchor='center' uses the spot mark's bounds, rounded out by 1/32 unit on one side, "
                        "so each spot sits up to 1/64 unit (scaled) from where the before version puts it",
}
MAX_CHANNEL = 32        # no pixel differs by more than this in any channel (of 255): edge anti-aliasing only
MAX_MEAN = 0.1          # mean difference per channel over the whole picture


@pytest.fixture(autouse=True)
def _scratch(tmp_path, monkeypatch):
    """Every run writes (if at all) into a throwaway folder, with no window and no sound."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("FUNGROUND_HEADLESS", "1")


def before_of(path: Path) -> Path:
    return BEFORE / f"{path.stem}_before.py"


def code_of(path: Path) -> str:
    """The file without its docstring: what the guide prints."""
    return path.read_text(encoding="utf-8").split('"""', 2)[2].lstrip("\n")


def test_six_studios_each_with_a_before_version():
    assert [p.stem for p in STUDIOS] == ["01_placement", "02_proximity", "03_rhythm", "04_boolean_shapes",
                                         "05_text_as_geometry", "06_poster_series"]
    assert sorted(BEFORE.glob("*.py")) == sorted(before_of(p) for p in STUDIOS)


@pytest.mark.parametrize("after", STUDIOS, ids=lambda p: p.stem)
def test_both_versions_draw_the_same_picture(after: Path):
    (size_a, a) = run_sketch(after, frames=3)
    reset_funground()
    (size_b, b) = run_sketch(before_of(after), frames=3)
    assert size_a == size_b
    if after.stem not in NEAR:
        assert a == b, f"{after.stem}: the two versions draw different pictures"
        return
    diffs = [abs(x - y) for x, y in zip(a, b)]
    assert any(diffs), f"{after.stem} is now pixel-equal: remove it from NEAR"
    assert max(diffs) <= MAX_CHANNEL, f"{after.stem}: a pixel differs by {max(diffs)} ({NEAR[after.stem]})"
    assert sum(diffs) / len(diffs) <= MAX_MEAN, f"{after.stem}: the pictures differ too much ({NEAR[after.stem]})"


def test_the_guide_prints_both_versions_exactly():
    blocks = re.findall(r"```python\n(.*?)```", CHAPTER.read_text(encoding="utf-8"), re.S)
    for path in [*STUDIOS, *map(before_of, STUDIOS)]:
        assert code_of(path) in blocks, f"docs/guide/19_studios.md does not print {path.name} as it is"
    assert len(blocks) == 2 * len(STUDIOS)


class KeyAt(HeadlessPlatform):
    """A headless window where one key is pressed before frame *at*."""

    def __init__(self, at: int, key: str) -> None:
        super().__init__()
        self.at, self.key, self.polls = at, key, 0

    def poll(self):
        if self.polls == self.at:
            self.post(InputEvent("key_pressed", key=self.key, key_code=ord(self.key)))
        self.polls += 1
        return super().poll()


def run_copy(source: Path, folder: Path, monkeypatch) -> None:
    """Run a copy of *source* in *folder*, pressing K before frame 2."""
    copy = folder / source.name
    shutil.copy(source, copy)
    sketch = api.use_sketch(Sketch(platform=KeyAt(2, "k")))

    def harness_run(**_):
        sketch.run_namespace(inspect.currentframe().f_back.f_globals, max_frames=4)

    monkeypatch.setattr(funground, "run", harness_run)
    namespace = {"__name__": "__main__", "__file__": str(copy)}
    exec(compile(copy.read_text(encoding="utf-8"), str(copy), "exec"), namespace)


def test_k_keeps_the_poster_sheet_next_to_the_sketch(tmp_path, monkeypatch):
    run_copy(AFTER / "06_poster_series.py", tmp_path, monkeypatch)
    studio = tmp_path / "studio"
    record = json.loads((studio / "001.json").read_text(encoding="utf-8"))
    assert record["note"] == "the series so far" and record["settings"] == {"events": 4}
    assert record["seed"] == 2026 and record["seed_chosen_by"] == "you"
    assert (studio / "001.png").read_bytes()[:4] == b"\x89PNG"
    assert (studio / "001.py").read_text(encoding="utf-8") == (AFTER / "06_poster_series.py").read_text(encoding="utf-8")
    assert not (AFTER / "studio").exists()


def test_k_saves_the_before_sheet_and_its_note_in_the_current_folder(tmp_path, monkeypatch):
    run_copy(before_of(AFTER / "06_poster_series.py"), tmp_path, monkeypatch)
    assert (tmp_path / "sheet_001.png").read_bytes()[:4] == b"\x89PNG"
    assert json.loads((tmp_path / "sheet_001.json").read_text(encoding="utf-8"))["seed"] == 2026
    assert not list(BEFORE.glob("sheet_*"))
