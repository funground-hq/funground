"""The gallery in the package (S-103, D-049, contract R18)."""
from __future__ import annotations

import ast
import importlib.util
import os
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

from funground import gallery
from funground.gallery import Locations, copy_example, data_files, free_name, list_examples, locate

from conftest import ROOT, run_sketch

SOURCE_EXAMPLES = ROOT / "examples" / "gallery"
SOURCE_IMAGES = ROOT / "docs" / "gallery" / "images"


def _env():
    env = dict(os.environ)
    env["PYTHONPATH"] = str(ROOT) + os.pathsep + env.get("PYTHONPATH", "")
    env["FUNGROUND_HEADLESS"] = "1"
    return env


# ---- the locator
def test_a_checkout_finds_every_example_and_its_picture():
    where = locate()
    assert not where.installed
    assert where.examples == SOURCE_EXAMPLES
    assert where.images == SOURCE_IMAGES
    found = list_examples(where.examples)
    assert len(found) >= 60
    for path in found:
        assert (where.images / f"{gallery.example_id(path)}.png").is_file(), path


def _fake_install(root: Path) -> Path:
    """The layout the wheel makes: funground/examples/<area>/... and funground/gallery_images/."""
    package = root / "funground"
    for path in list_examples(SOURCE_EXAMPLES):
        target = package / "examples" / path.parent.name / path.name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(path.read_bytes())
        for data in data_files(path):
            place = package / "examples" / data.relative_to(SOURCE_EXAMPLES)
            place.parent.mkdir(parents=True, exist_ok=True)
            place.write_bytes(data.read_bytes())
        picture = package / "gallery_images" / f"{gallery.example_id(path)}.png"
        picture.parent.mkdir(parents=True, exist_ok=True)
        picture.write_bytes(b"png")
    return package


def test_an_installed_layout_is_found_beside_the_module(tmp_path):
    package = _fake_install(tmp_path)
    where = locate(package)
    assert where.installed
    assert where.examples == package / "examples" and where.images == package / "gallery_images"
    installed = list_examples(where.examples)
    assert [(p.parent.name, p.name) for p in installed] == [(p.parent.name, p.name) for p in list_examples(SOURCE_EXAMPLES)]
    assert all((where.images / f"{gallery.example_id(p)}.png").is_file() for p in installed)


def test_an_installed_example_keeps_its_data_files_next_to_it(tmp_path):
    where = locate(_fake_install(tmp_path))
    photo = next(p for p in list_examples(where.examples) if p.name == "01_load_image.py")
    assert [d.name for d in data_files(photo)] == ["photo.jpg"]


def test_the_make_gallery_tool_and_the_browser_agree_on_the_examples():
    spec = importlib.util.spec_from_file_location("make_gallery_agree", ROOT / "tools" / "make_gallery.py")
    tool = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tool)
    assert tool.examples() == list_examples(locate().examples)
    assert tool.AREAS is gallery.AREAS                      # one source of truth
    assert tool.title_and_description is gallery.title_and_description


def test_the_old_tool_path_still_starts_the_package_browser():
    spec = importlib.util.spec_from_file_location("old_browser_path", ROOT / "tools" / "gallery_browser.py")
    wrapper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(wrapper)
    assert wrapper.main is gallery.main


# ---- copy to folder
def test_copy_writes_the_example_and_its_data_and_never_overwrites(tmp_path):
    photo = SOURCE_EXAMPLES / "images" / "01_load_image.py"
    first, written, kept = copy_example(photo, tmp_path)
    assert first == tmp_path / "01_load_image.py" and first.read_bytes() == photo.read_bytes()
    assert written == [tmp_path / "data" / "photo.jpg"] and written[0].is_file() and not kept
    first.write_text("my own work", encoding="utf-8")
    second, written2, kept2 = copy_example(photo, tmp_path)
    assert second == tmp_path / "01_load_image_2.py"
    assert first.read_text(encoding="utf-8") == "my own work"          # never overwritten
    assert not written2 and kept2 == [tmp_path / "data" / "photo.jpg"]
    third, _, _ = copy_example(photo, tmp_path)
    assert third.name == "01_load_image_3.py"


def test_free_name_skips_taken_names(tmp_path):
    (tmp_path / "a.py").write_text("x")
    (tmp_path / "a_2.py").write_text("x")
    assert free_name(tmp_path, "a.py") == tmp_path / "a_3.py"
    assert free_name(tmp_path, "b.py") == tmp_path / "b.py"


def test_a_copied_example_with_data_runs_from_its_new_folder(tmp_path):
    target, _, _ = copy_example(SOURCE_EXAMPLES / "images" / "01_load_image.py", tmp_path)
    (w, h), data = run_sketch(target, frames=2)           # its "data/photo.jpg" is found next to the copy
    assert len(data) == w * h * 3


# ---- running without a window
def test_list_works_headless():
    done = subprocess.run([sys.executable, "-m", "funground.gallery", "--list"], cwd=ROOT, env=_env(),
                          capture_output=True, text=True, timeout=120)
    assert done.returncode == 0, done.stderr
    lines = done.stdout.strip().splitlines()
    assert len(lines) == len(list_examples(locate().examples))
    assert lines[0].startswith("basics-")


def test_import_funground_does_not_import_the_gallery():
    done = subprocess.run([sys.executable, "-c", "import sys, funground; assert 'funground.gallery' not in sys.modules"],
                          cwd=ROOT, env=_env(), capture_output=True, text=True, timeout=120)
    assert done.returncode == 0, done.stderr


def test_the_gallery_module_imports_only_the_standard_library_and_funground():
    tree = ast.parse((ROOT / "funground" / "gallery.py").read_text(encoding="utf-8"))
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            names.add(node.module.split(".")[0])
    assert names <= set(sys.stdlib_module_names) | {"funground"}, names


# ---- the wheel
def test_the_wheel_carries_the_examples_pictures_and_licence(tmp_path):
    built = subprocess.run([sys.executable, "-m", "build", "--wheel", "--outdir", str(tmp_path)], cwd=ROOT,
                           capture_output=True, text=True, timeout=600)
    if built.returncode != 0 and ("No matching distribution" in built.stdout + built.stderr
                                  or "Connection" in built.stdout + built.stderr):
        pytest.skip("cannot fetch the build tools here (offline)")
    assert built.returncode == 0, built.stdout[-2000:] + built.stderr[-2000:]
    wheel = next(tmp_path.glob("funground-*.whl"))
    names = set(zipfile.ZipFile(wheel).namelist())
    for path in list_examples(SOURCE_EXAMPLES):
        rel = path.relative_to(SOURCE_EXAMPLES).as_posix()
        assert f"funground/examples/{rel}" in names, rel
        assert f"funground/gallery_images/{gallery.example_id(path)}.png" in names, rel
    # every data or font file beside an example is shipped too (a new data folder must be added to pyproject.toml)
    extra = [p for p in SOURCE_EXAMPLES.rglob("*") if p.is_file() and p.suffix != ".py" and "__pycache__" not in p.parts]
    assert extra
    for p in extra:
        assert f"funground/examples/{p.relative_to(SOURCE_EXAMPLES).as_posix()}" in names, p
    assert any(n.endswith("licenses/examples/LICENSE") for n in names)
    assert "funground/gallery.py" in names
    assert not any(n.endswith(".pyc") for n in names)
