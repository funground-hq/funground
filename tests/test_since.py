"""Release markers (S-229, D-116): which release each public name arrives in.

funground/released_names.json freezes the public API of each release (tools/make_released_names.py). A name in
the first release shows nothing; a later one is marked "Since 0.2" in the API reference, completions.json and
llms.txt, and by hand in the Quick Reference, the guide and (by tools/make_gallery.py) the gallery.
"""
from __future__ import annotations

import importlib.util
import json
import re
import subprocess
import sys

import pytest

import funground
from conftest import ROOT
from funground.imaging import FILTER_KINDS

sys.path.insert(0, str(ROOT / "tools"))
import since  # noqa: E402

CANDIDATE = "v0.1.0"


def load(name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "tools" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def completions() -> dict:
    return json.loads((ROOT / "funground" / "completions.json").read_text(encoding="utf-8"))


def read(path) -> str:
    return path.read_text(encoding="utf-8").replace("\r\n", "\n")


def test_the_first_release_is_listed():
    data = json.loads((ROOT / "funground" / "released_names.json").read_text(encoding="utf-8"))
    assert "0.1.0" in data
    assert "circle" in data["0.1.0"]["names"]
    assert "remove_color" not in data["0.1.0"]["classes"]["Picture"]


def test_no_public_name_is_the_name_of_a_helper():
    # A submodule must never have the name of a public function (the naming trap).
    assert not {"since", "released_names"} & set(funground._PUBLIC_NAMES)


def test_later_names_say_so_and_earlier_ones_do_not():
    names = {e["name"]: e for e in completions()["names"]}
    assert "camera" not in names and "load_clip" not in names       # the camera is a library now (S-247)
    assert "since" not in names["circle"]
    classes = completions()["classes"]
    members = {m["name"]: m for m in classes["Picture"]["members"]}
    assert members["remove_color"]["since"] == "0.2"
    assert members["remove_background"]["since"] == "0.2"
    assert "since" not in members["copy"]
    assert classes["Camera"]["since"] == "0.2"
    assert "since" not in classes["Picture"]


def test_every_later_entry_in_completions_has_the_upcoming_version():
    data = completions()
    marked = [e for e in data["names"] if "since" in e]
    marked += [m for c in data["classes"].values() for m in c["members"] if "since" in m]
    assert marked
    assert {e["since"] for e in marked} == {since.upcoming()}


def test_the_later_option_word_exists():
    for function, arguments in since.LATER_WORDS.items():
        for argument, words in arguments.items():
            for word in words:
                assert word in FILTER_KINDS, f"{function}({argument}): {word!r} is no longer accepted, remove it from LATER_WORDS"
    options = {o["word"]: o for o in completions()["names"][[e["name"] for e in completions()["names"]].index("filter")]["options"]["kind"]}
    assert options["edges"]["since"] == "0.2"


def test_the_api_reference_and_llms_say_so():
    api = read(ROOT / "docs" / "reference" / "API.md")
    for anchor in ("cls-Camera", "cls-Picture-remove_color"):
        section = api.split(f'<a id="{anchor}"></a>')[1].split("<a id=")[0]
        assert since.api_badge("0.2") in section.split("```")[0]          # the badge, before the signature
    library = api.split('<a id="the-camera-library"></a>')[1].split("<a id=")[0]      # a library says its own history
    assert "New in 0.2." in library
    circle = api.split('<a id="fn-circle"></a>')[1].split("<a id=")[0]
    assert "Since 0" not in circle
    assert "Since 0.2." in read(ROOT / "llms-full.txt")
    assert "Since 0.2." in read(ROOT / "docs" / "reference" / "llms_rules.md")


def test_the_tool_checks_what_a_release_contains():
    # Every name that completions.json marks is in no release; every unmarked one is in the first.
    first = since.released()["0.1.0"]
    names = {e["name"]: e for e in completions()["names"]}
    for name, entry in names.items():
        assert ("since" in entry) == (name not in first["names"]), name


def test_every_quick_reference_row_for_a_later_name_has_the_marker():
    data = completions()
    builder = {m["name"]: m["since"] for m in data["classes"]["PathBuilder"]["members"] if "since" in m}
    missing = []
    for number, line in enumerate(read(ROOT / "docs" / "reference" / "Quick_Reference.md").split("\n"), 1):
        if not line.startswith("|"):
            continue
        needs = since.later_use(line)
        lead = re.match(r"\|\s*`\.(\w+)\(", line)
        if lead and lead.group(1) in builder:
            needs = builder[lead.group(1)]
        if needs and since.row_marker(needs) not in line:
            missing.append(f"line {number}: add {since.row_marker(needs)} to {line[:60]}")
    assert not missing, "\n".join(missing)


def guide_sections():
    for path in sorted((ROOT / "docs" / "guide").rglob("*.md")):
        for section in since.sections(read(path)):
            yield path.relative_to(ROOT).as_posix(), section


def test_every_guide_section_using_a_later_name_has_the_marker_line():
    missing = []
    for path, section in guide_sections():
        needs = section.needs()
        if needs and section.first_line != since.marker(needs):
            missing.append(f"{path}:{section.line} {section.heading}: put this line under the heading:\n  {since.marker(needs)}")
    assert not missing, "\n".join(missing)


def test_every_guide_table_row_naming_a_later_name_has_the_row_marker():
    missing = [f"{path}:{section.line} add {since.row_marker(v)} to {row[:60]}"
               for path, section in guide_sections() for row, v in section.rows()
               if since.row_marker(v) not in row and section.needs() != v]       # a marked section covers its rows
    assert not missing, "\n".join(missing)


def test_no_guide_section_has_a_stale_marker():
    stale = []
    for path, section in guide_sections():
        if section.first_line.startswith("> **Since ") and not section.needs():
            stale.append(f"{path}:{section.line} {section.heading}")
    assert not stale, "these sections have the marker but use no later name: " + ", ".join(stale)


def test_the_camera_section_and_the_gallery_are_marked():
    camera = [s for p, s in guide_sections() if s.heading == "### The camera"]
    assert camera and camera[0].first_line == since.marker("0.2")
    gallery = read(ROOT / "docs" / "gallery" / "README.md")
    assert since.marker("0.2") in gallery
    assert gallery == load("make_gallery").build_index()


def test_the_sections_helper_ignores_headings_in_code():
    text = "## A\n\n```py\n# not a heading\n```\n\n### B\nf.camera()\n"
    found = since.sections(text)
    assert [s.heading for s in found] == ["## A", "### B"]
    assert found[0].code and not found[0].needs()


def test_running_the_tool_again_reproduces_the_file():
    try:
        known = subprocess.run(["git", "cat-file", "-e", f"{CANDIDATE}^{{commit}}"], cwd=ROOT, capture_output=True).returncode == 0
    except OSError:
        known = False
    if not known:
        pytest.skip(f"git or commit {CANDIDATE} is not available")
    tool = load("make_released_names")
    stored = (ROOT / "funground" / "released_names.json").read_bytes().decode("utf-8")
    again = tool.released_text("0.1.0", CANDIDATE, json.loads(stored))
    assert again == stored, "run: .venv/Scripts/python tools/make_released_names.py --ref v0.1.0 --version 0.1.0"
