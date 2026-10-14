"""The list of suggestions for editors (S-195, D-102): funground/completions.json.

tools/make_api_reference.py writes it with the API reference. These tests check that it is current, covers
every public name, links to real places in the reference, and says which words and colours go where.
"""
from __future__ import annotations

import importlib.util
import json
import re
import sys

import funground
from conftest import ROOT

TOOL = ROOT / "tools" / "make_api_reference.py"
FILE = ROOT / "funground" / "completions.json"

_spec = importlib.util.spec_from_file_location("make_api_reference", TOOL)
tool = importlib.util.module_from_spec(_spec)
sys.modules["make_api_reference"] = tool
_spec.loader.exec_module(tool)


def data() -> dict:
    return json.loads(FILE.read_text(encoding="utf-8"))


def entries() -> dict:
    return {e["name"]: e for e in data()["names"]}


def test_the_file_is_in_the_package_and_current():
    assert FILE.exists()
    assert FILE.read_bytes() == tool.completions_text().encode("utf-8"), \
        "completions.json is out of date. Run: .venv/Scripts/python tools/make_api_reference.py"
    assert b"\r" not in FILE.read_bytes()


def test_the_names_are_the_public_names_in_order():
    assert [e["name"] for e in data()["names"]] == list(funground._PUBLIC_NAMES)
    assert data()["version"] == funground.__version__


def test_every_entry_has_a_summary_and_a_link_that_exists():
    api = (ROOT / "docs" / "reference" / "API.md").read_text(encoding="utf-8")
    anchors = set(re.findall(r'<a id="([^"]+)"></a>', api))
    for e in data()["names"]:
        assert e["kind"] in ("function", "class", "value", "namespace"), e["name"]
        assert e["summary"].strip(), e["name"]
        assert e["signature"] and e["detail"], e["name"]
        path, _, anchor = e["url"].partition("#")
        assert path == "reference/API.md" and anchor in anchors, e


def test_kinds_and_signatures():
    found = entries()
    assert found["circle"]["signature"] == "circle(x, y, diameter)"
    assert found["circle"]["detail"] == "(x: float, y: float, diameter: float) -> None"
    assert found["Vector"]["kind"] == "class"
    assert found["width"]["kind"] == "value" and found["width"]["detail"] == "int"
    assert "'" not in found["fill"]["detail"] and '"' not in found["fill"]["detail"]


def test_the_star_flag_matches_the_star_import():
    for e in data()["names"]:
        assert e["star"] == (e["name"] not in funground.STAR_LEAVES_OUT), e["name"]
    assert entries()["filter"]["star"] is False


def test_option_words_come_with_meanings():
    options = entries()["blend_mode"]["options"]["mode"]
    assert {"word": "normal"}.items() <= options[0].items()
    assert all(o["word"] and o["meaning"] for o in options)
    assert "options" not in entries()["circle"]


def test_colours_and_the_parameters_that_take_one():
    colors = {c["name"]: c["hex"] for c in data()["colors"]}
    assert colors["tomato"] == "#ff6347"
    assert list(colors) == sorted(colors)
    pairs = {(p["function"], p["parameter"]) for p in data()["color_params"]}
    assert {("fill", "color"), ("stroke", "color"), ("background", "color")} <= pairs
    assert ("circle", "x") not in pairs


def test_colors_lists_every_named_colour_with_its_hex():
    entry = entries()["COLORS"]
    assert entry["kind"] == "namespace" and entry["star"] is True
    members = entry["members"]
    assert len(members) == len(funground.COLORS) == 665
    tomato = next(m for m in members if m["name"] == "TOMATO")
    assert tomato == {"name": "TOMATO", "value": "tomato", "hex": "#ff6347"}


def test_constants_lists_each_group_with_its_words_and_the_functions_that_take_them():
    entry = entries()["CONSTANTS"]
    assert entry["kind"] == "namespace"
    groups = {g["name"]: g for g in entry["members"]}
    assert list(groups) == [name for name, _ in funground.CONSTANTS._members.items()]
    align = groups["ALIGN"]
    assert align["used_by"] == ["text_align"]
    left = next(m for m in align["members"] if m["name"] == "LEFT")
    assert left["value"] == "left" and left["meaning"].startswith("x is where the text starts")
    assert "meaning" not in next(m for m in groups["MODE"]["members"] if m["name"] == "CENTER")
    assert groups["KEY"]["used_by"] == ["key_down", "f.key"]
    for group in groups.values():
        assert group["members"] and all(m["value"] for m in group["members"])


def test_other_entries_have_no_members():
    assert "members" not in entries()["circle"]
