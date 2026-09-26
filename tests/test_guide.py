"""User Guide (S-069): every complete example runs exactly as printed; links resolve.

Convention: a ```python block is a complete sketch (it must call f.run()) and is run
headless here; a ```py block is a fragment, shown but not run.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

from conftest import ROOT, run_sketch

GUIDE = ROOT / "docs" / "guide"
CHAPTERS = sorted(GUIDE.glob("[0-9][0-9]_*.md"))
BLOCK = re.compile(r"```python\n(.*?)```", re.S)


def _runnable_blocks():
    for chapter in CHAPTERS:
        for i, match in enumerate(BLOCK.finditer(chapter.read_text(encoding="utf-8")), 1):
            yield pytest.param(chapter, match.group(1), id=f"{chapter.stem}#{i}")


def test_guide_has_a_table_of_contents_listing_every_chapter():
    toc = (GUIDE / "README.md").read_text(encoding="utf-8")
    assert len(CHAPTERS) >= 15
    for chapter in CHAPTERS:
        assert f"({chapter.name})" in toc, f"{chapter.name} missing from docs/guide/README.md"


@pytest.mark.parametrize("chapter, code", list(_runnable_blocks()))
def test_complete_examples_run_as_printed(chapter, code, tmp_path, monkeypatch):
    assert "f.run(" in code, "a ```python block must be a complete sketch; use ```py for fragments"
    monkeypatch.chdir(tmp_path)               # examples that f.save() write here
    sketch = tmp_path / "example.py"
    sketch.write_text(code, encoding="utf-8")
    (w, h), data = run_sketch(sketch, frames=3)
    assert len(data) == w * h * 3


def test_relative_links_and_images_resolve():
    broken = []
    for page in [GUIDE / "README.md", *CHAPTERS]:
        for target in re.findall(r"\]\(([^)#:]+)\)", page.read_text(encoding="utf-8")):
            if not (page.parent / target).resolve().exists():
                broken.append(f"{page.name}: {target}")
    assert not broken, "broken links: " + ", ".join(broken)
