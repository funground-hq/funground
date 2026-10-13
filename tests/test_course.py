"""Course pages, examples and learner download remain usable together."""
from __future__ import annotations

import re
import zipfile

import pytest

from conftest import ROOT, run_sketch

COURSE = ROOT / "docs" / "course"
PAGES = sorted(COURSE.glob("*.md"))
EXAMPLES = sorted((ROOT / "examples" / "course").glob("[0-9][0-9]_*.py"))
FENCE = chr(96) * 3


def _complete_blocks():
    for page in PAGES:
        pattern = FENCE + r"python\n(.*?)" + FENCE
        for number, code in enumerate(re.findall(pattern, page.read_text(encoding="utf-8"), re.S), 1):
            yield pytest.param(code, id=f"{page.stem}#{number}")


@pytest.mark.parametrize("code", list(_complete_blocks()))
def test_course_complete_code_runs_as_printed(code, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    script = tmp_path / "lesson.py"
    script.write_text(code, encoding="utf-8")
    (width, height), pixels = run_sketch(script, frames=3)
    assert len(pixels) == width * height * 3


@pytest.mark.parametrize("script", EXAMPLES, ids=lambda p: p.stem)
def test_downloadable_course_sketch_runs_and_exports(script, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (width, height), pixels = run_sketch(script, frames=3)
    assert len(pixels) == width * height * 3
    assert list(tmp_path.glob("*.png")), f"{script.name} did not export its result"


def test_course_local_links_and_images_resolve():
    broken = []
    for page in [*PAGES, ROOT / "docs/README.md", ROOT / "docs/creative-curriculum.md",
                 ROOT / "examples/course/README.md"]:
        for target in re.findall(r"\]\(([^)]+)\)", page.read_text(encoding="utf-8")):
            if "://" in target or target.startswith("#"):
                continue
            local = target.split("#", 1)[0]
            if not (page.parent / local).resolve().exists():
                broken.append(f"{page.relative_to(ROOT)}: {target}")
    assert not broken, "\n".join(broken)


@pytest.mark.parametrize("archive_name, lesson_limit", [
    ("first_two_lessons.zip", 2),
    ("course_sketches.zip", 11),
])
def test_download_bundle_matches_the_source_sketches(archive_name, lesson_limit):
    archive = COURSE / "downloads" / archive_name
    selected = [p for p in EXAMPLES if int(p.name[:2]) <= lesson_limit]
    with zipfile.ZipFile(archive) as bundle:
        for script in selected:
            assert bundle.read(script.name) == script.read_bytes()
        assert {name for name in bundle.namelist() if name.endswith(".py")} == {p.name for p in selected}
        assert bundle.read("LICENSE") == (ROOT / "examples/LICENSE").read_bytes()
