"""The list of suggestions for editors (S-195, D-102): funground/completions.json.

tools/make_api_reference.py writes it with the API reference. These tests check that it is current, covers
every public name, links to real places in the reference, and says which words and colours go where.
"""
from __future__ import annotations

import importlib.util
import ast
import json
import re
import sys

import pytest

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


def test_the_names_are_the_public_names_most_used_first():
    names = [e["name"] for e in data()["names"]]
    assert sorted(names) == sorted(funground._PUBLIC_NAMES)
    assert names == [e["name"] for e in sorted(data()["names"], key=lambda e: (-e["rank"], e["name"]))]
    assert names[:3] == ["size", "fill", "background"]
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


def test_functions_name_the_class_they_give_back():
    found = entries()
    assert found["path"]["returns"] == "PathBuilder"
    assert found["grid"]["returns"] == "Grid"
    assert {e["name"]: e for e in data()["libraries"]["camera"]}["open"]["returns"] == "Camera"
    assert {e["name"]: e for e in data()["libraries"]["sound"]}["tone"]["returns"] == "Sound"
    assert "returns" not in found["circle"] and "returns" not in found["Vector"]


def test_every_documented_class_lists_its_members():
    classes = data()["classes"]
    assert set(classes) == {name for name, _ in tool.all_classes()}
    api = (ROOT / "docs" / "reference" / "API.md").read_text(encoding="utf-8")
    anchors = set(re.findall(r'<a id="([^"]+)"></a>', api))
    for name, cls in classes.items():
        assert cls["summary"].strip() and cls["url"] == f"reference/API.md#cls-{name}", name
        for member in cls["members"]:
            assert member["kind"] in ("method", "property") and member["signature"], (name, member)
            assert member["url"].partition("#")[2] in anchors, member
            if "returns" in member:
                assert member["returns"] in classes, member


def test_members_are_signed_without_self_and_chain_by_what_they_return():
    members = {m["name"]: m for m in data()["classes"]["PathBuilder"]["members"]}
    assert members["rect"]["signature"] == "rect(x, y, w, h, *radii)"
    assert members["rect"]["returns"] == "PathBuilder" and members["union"]["returns"] == "PathBuilder"
    camera = {m["name"]: m for m in data()["classes"]["Camera"]["members"]}
    assert camera["width"]["kind"] == "property" and camera["record"]["returns"] == "Clip"
    assert camera["picture"]["returns"] == "Picture"          # from the Returns text: the method has no annotation
    assert "self" not in camera["start"]["detail"]


def test_the_models_functions_name_the_result_they_give_back():
    ml = {e["name"]: e for e in data()["libraries"]["ml"]}
    assert {n: ml[n]["returns"] for n in ("pose", "hand", "words", "sound", "guess")} == \
        {"pose": "Body", "hand": "Hand", "words": "Words", "sound": "Heard", "guess": "Guess"}
    assert set(data()["classes"]) >= {"Body", "Hand", "Words", "Guess", "Heard"}
    assert not {"Body", "Hand", "Words", "Guess", "Heard"} & set(entries())      # results are not public names


def test_the_models_results_list_their_points_and_scores():
    classes = data()["classes"]
    body = {m["name"]: m for m in classes["Body"]["members"]}
    assert body["left_wrist"]["returns"] == "Vector" and body["score"]["detail"] == "float" and "points" in body
    assert len(body) == 35 and len(classes["Hand"]["members"]) == 23
    assert {m["name"] for m in classes["Words"]["members"]} == {"text", "score", "is_new"}
    assert {m["name"] for m in classes["Guess"]["members"]} == {"name", "score", "next"}
    assert {m["name"] for m in classes["Heard"]["members"]} == {"name", "score", "next", "is_new"}


def test_gradient_raga_and_tala_list_their_documented_attributes():
    classes = data()["classes"]
    assert [m["name"] for m in classes["Gradient"]["members"]] == ["kind", "points", "stops"]
    raga = {m["name"]: m for m in classes["Raga"]["members"]}
    assert {"name", "thaat", "swaras", "aroha", "vadi", "samvadi", "time"} <= set(raga)
    assert raga["swaras"]["detail"] == "tuple[str, ...]" and raga["thaat"]["kind"] == "property"
    tala = {m["name"] for m in classes["Tala"]["members"]}
    assert {"name", "beats", "vibhag", "tali", "khali", "sam", "bols"} <= tala


# ---- the words for blocks and editors (S-300): Blocks: sections, section, rank, element types


def library(name: str) -> dict:
    return {e["name"]: e for e in data()["libraries"][name]}


def test_blocks_sections_become_plain_also_and_kinds():
    opacity = entries()["opacity"]
    assert "transparent" in opacity["also"] and opacity["plain"] == "Make what you draw next see-through."
    assert opacity["kinds"] == {"amount": {"kind": "range", "low": 0, "high": 255, "step": 1}}
    assert entries()["rotate"]["kinds"] == {"degrees": {"kind": "angle"}}
    assert {"start": {"kind": "angle"}, "stop": {"kind": "angle"}}.items() <= entries()["arc"]["kinds"].items()
    assert entries()["save"]["kinds"] == {"path": {"kind": "file"}}
    assert entries()["stroke_width"]["kinds"] == {"pixels": {"kind": "pixels"}}
    assert "plain" not in entries()["fill"]
    assert library("sound")["tone"]["kinds"]["volume"] == {"kind": "range", "low": 0, "high": 1, "step": 0.05}
    assert "webcam" in library("camera")["open"]["also"]
    assert "speech" in library("ml")["words"]["also"]


def test_a_colour_parameter_gets_the_colour_kind_without_being_written():
    pairs = {(p["function"], p["parameter"]) for p in data()["color_params"]}
    for function, parameter in pairs:
        assert entries()[function]["kinds"][parameter] == {"kind": "colour"}, (function, parameter)
    kinds = entries()["lerp_color"]["kinds"]
    assert kinds["c1"] == kinds["c2"] == {"kind": "colour"} and kinds["amount"]["kind"] == "range"
    assert "kinds" not in entries()["no_fill"]


def test_every_also_list_is_a_few_lower_case_words():
    rows = list(entries().items()) + [(f"{lib}.{e['name']}", e) for lib, es in data()["libraries"].items() for e in es]
    found = 0
    for name, entry in rows:
        if "also" in entry:
            found += 1
            assert 2 <= len(entry["also"]) <= 6, name
            assert all(w and w == w.lower() == w.strip() for w in entry["also"]), name
    assert found >= 90
    for lib in ("ml", "sound", "camera", "sangeet"):
        assert all("also" in e for e in data()["libraries"][lib]), lib
    top = [e for e in data()["names"] if e["kind"] != "namespace"][:60]
    assert all("also" in e for e in top), [e["name"] for e in top if "also" not in e]


def test_an_unknown_key_in_a_blocks_section_raises_with_its_name():
    with pytest.raises(ValueError, match="'alsoo'"):
        tool.parse_blocks("plain: Hi.\nalsoo: a, b", "f.demo")
    with pytest.raises(ValueError, match="'speed'"):
        tool.parse_blocks("kinds: speed=angle", "f.demo", ["x"])
    with pytest.raises(ValueError, match="speed=fast"):
        tool.parse_blocks("kinds: speed=fast", "f.demo", ["speed"])
    assert tool.parse_blocks("also: a, b\nkinds: x=range(0, 1, 0.5), y=pixels", "f.demo", ["x", "y"]) == \
        {"also": ["a", "b"], "kinds": {"x": {"kind": "range", "low": 0, "high": 1, "step": 0.5}, "y": {"kind": "pixels"}}}


def test_every_entry_has_a_section_and_a_rank():
    found = entries()
    assert found["circle"]["section"] == "Shapes" and found["fill"]["section"] == "Fill and stroke"
    assert found["width"]["section"] == "Live values" and found["Vector"]["section"] == "Classes"
    assert library("sound")["tone"]["section"] == "sound" and library("ml")["pose"]["section"] == "ml"
    every = list(found.values()) + [e for lib in data()["libraries"].values() for e in lib]
    for cls_name, cls in data()["classes"].items():
        for member in cls["members"]:
            assert member["section"] == cls_name, member
            every.append(member)
    assert all(isinstance(e["section"], str) and e["section"] and isinstance(e["rank"], int) and e["rank"] >= 0 for e in every)
    assert found["size"]["rank"] > found["circle"]["rank"] > 0


def test_ranks_count_the_example_files_that_use_the_name():
    used = {name: 0 for name in funground._PUBLIC_NAMES}
    for path in (ROOT / "examples").rglob("*.py"):
        seen = {n.attr for n in ast.walk(ast.parse(path.read_text(encoding="utf-8")))
                if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name) and n.value.id == "f"}
        for name in seen & set(used):
            used[name] += 1
    assert {n: e["rank"] for n, e in entries().items()} == used
    assert library("sound")["melody"]["rank"] > 0


def test_names_and_each_library_are_in_order_of_rank_then_name():
    for rows in [data()["names"], *data()["libraries"].values()]:
        assert [(-e["rank"], e["name"]) for e in rows] == sorted((-e["rank"], e["name"]) for e in rows)
    assert data()["libraries"]["camera"][0]["name"] == "open"


def test_a_list_of_a_class_names_its_element():
    classes = data()["classes"]
    guess_next = {m["name"]: m for m in classes["Guess"]["members"]}["next"]
    assert guess_next["element"] == "Guess" and "returns" not in guess_next
    assert {m["name"]: m for m in classes["Heard"]["members"]}["next"]["element"] == "Heard"
    assert entries()["svg_paths"]["element"] == "PathBuilder"
    assert {m["name"]: m for m in classes["FormattedString"]["members"]}["runs"]["element"] == "Run"
    for entry in [*entries().values(), *(m for c in classes.values() for m in c["members"])]:
        if "element" in entry:
            assert entry["element"] in classes, entry


# ---- the shared cases for "what does this variable hold" (S-300): funground/type_cases.json

CASES = ROOT / "funground" / "type_cases.json"


def cases() -> list[dict]:
    return json.loads(CASES.read_text(encoding="utf-8"))["cases"]


def test_the_type_cases_are_well_formed():
    table = json.loads(CASES.read_text(encoding="utf-8"))
    assert set(table) == {"about", "cases"} and table["about"].strip()
    classes = data()["classes"]
    assert 20 <= len(table["cases"]) <= 40
    for case in table["cases"]:
        assert set(case) == {"program", "line", "object", "class", "needs"}, case
        ast.parse(case["program"])                                         # a complete, valid program
        lines = case["program"].splitlines()
        assert 1 <= case["line"] <= len(lines), case
        assert case["object"] + "." in lines[case["line"] - 1], case
        ast.parse(case["object"], mode="eval")
        assert case["class"] is None or case["class"] in classes, case
        assert set(case["needs"]) <= {"element", "hint"} and len(set(case["needs"])) == len(case["needs"]), case
        assert case["object"] not in ("f", "sound", "camera", "ml", "sangeet"), "a library is a module, not a class"
    assert {c["class"] is None for c in table["cases"]} == {True, False}
    assert {n for c in table["cases"] for n in c["needs"]} == {"element", "hint"}


def test_the_type_cases_ship_in_the_package():
    import tomllib

    patterns = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["tool"]["setuptools"]["package-data"]["funground"]
    assert "type_cases.json" in patterns and "completions.json" in patterns
    assert CASES.parent == FILE.parent


def class_of(case: dict, steps: set[str]):
    """The rule the cases describe, in its smallest form: Python's own parser and the catalogue, and nothing else."""
    tree = ast.parse(case["program"])
    names = {e["name"]: e for e in data()["names"]}
    libraries = data()["libraries"]
    imported = {a.name for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.module == "funground" for a in n.names}
    classes = data()["classes"]

    def entry_of(node, line):
        """The catalogue entry a call or an attribute gives, or None."""
        if isinstance(node, ast.Call):
            node = node.func
        if not isinstance(node, ast.Attribute):
            return None
        if isinstance(node.value, ast.Name) and node.value.id == "f":
            return names.get(node.attr)
        if isinstance(node.value, ast.Name) and node.value.id in imported and node.value.id in libraries:
            return library(node.value.id).get(node.attr)
        owner = class_at(node.value, line)
        return {m["name"]: m for m in classes[owner]["members"]}.get(node.attr) if owner else None

    def class_at(node, line):
        if isinstance(node, ast.Name):
            return variable(node.id, line)
        entry = entry_of(node, line)
        return entry.get("returns") if entry else None

    def variable(name, line):
        """The last thing above *line* that gave *name* a value: (line, how, node)."""
        found = []
        for node in ast.walk(tree):
            if getattr(node, "lineno", line) >= line:
                continue
            if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == name for t in node.targets):
                found.append((node.lineno, "value", node.value))
            elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.target.id == name:
                found.append((node.lineno, "hint", node.annotation))
            elif isinstance(node, ast.For) and isinstance(node.target, ast.Name) and node.target.id == name:
                found.append((node.lineno, "element", node.iter))
            elif isinstance(node, ast.FunctionDef):
                found += [(node.lineno, "hint", arg.annotation) for arg in node.args.args if arg.arg == name]
        if not found:
            return None
        where, how, node = max(found, key=lambda b: b[0])
        if how == "value":
            return class_at(node, where)
        if how == "element":
            entry = entry_of(node, where)
            return entry.get("element") if entry and "element" in steps else None
        if "hint" in steps and isinstance(node, ast.Constant) and node.value in classes:
            return node.value                                              # the quoted class name
        return None

    return class_at(ast.parse(case["object"], mode="eval").body, case["line"])


def test_the_basic_rule_and_its_two_steps_give_every_case_its_class():
    """A small version of the rule, run on the table, so a case cannot ask for something the catalogue cannot answer."""
    for case in cases():
        assert class_of(case, set(case["needs"])) == case["class"], case
        if case["needs"]:                                                  # without its steps the case is not answered
            assert class_of(case, set()) is None, case
