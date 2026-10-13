"""The pages for AI assistants (S-129): llms.txt and llms-full.txt tell the truth about funground.

The rules are written by hand in docs/reference/llms_rules.md; tools/make_api_reference.py builds both pages
from them and from API.md (test_api_docs checks that the built pages are current). Here: the rules' code runs,
the names they use exist, the names they say do not exist really do not, and the links lead somewhere.
"""
from __future__ import annotations

import re

import pytest

import funground
from conftest import ROOT, run_sketch

RULES = ROOT / "docs" / "reference" / "llms_rules.md"
INDEX = ROOT / "llms.txt"
FULL = ROOT / "llms-full.txt"
REPO_URL = "https://github.com/funground-hq/funground/blob/main/"
BLOCK = re.compile(r"```python\n(.*?)```", re.S)

# Names from p5 and DrawBot that the rules say funground does not have, under these spellings.
NOT_IN_FUNGROUND = ["createCanvas", "angleMode", "oval", "BezierPath", "strokeWeight", "lineHeight", "map", "dist"]


def rules() -> str:
    return RULES.read_text(encoding="utf-8")


@pytest.mark.parametrize("code", [pytest.param(m.group(1), id=f"block{i}")
                                  for i, m in enumerate(BLOCK.finditer(rules()), 1)])
def test_the_rules_examples_run_as_printed(code, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)                       # the script example saves a PDF
    sketch = tmp_path / "example.py"
    sketch.write_text(code, encoding="utf-8")
    (w, h), data = run_sketch(sketch, frames=3)
    assert len(data) == w * h * 3


def test_the_rules_show_a_sketch_a_script_and_the_shorter_style():
    blocks = [m.group(1) for m in BLOCK.finditer(rules())]
    assert any("def draw" in b and "f.run()" in b for b in blocks)
    assert any("def draw" not in b and "f.show()" in b for b in blocks)
    assert any(b.startswith("from funground import *") for b in blocks)


def test_every_f_name_in_the_rules_exists():
    names = set(re.findall(r"\bf\.([a-z_][a-z0-9_]*)", rules()))
    missing = sorted(n for n in names if not hasattr(funground, n))
    assert not missing, f"llms_rules.md names what funground does not have: {missing}"


def test_the_names_said_not_to_exist_do_not():
    for name in NOT_IN_FUNGROUND:
        assert f"`{name}`" in rules(), f"the rules no longer mention {name}: update NOT_IN_FUNGROUND"
        assert name not in funground._PUBLIC_NAMES, name


def test_the_star_import_note_matches_the_package():
    for left_out, instead in funground.STAR_NAMES_FOR.items():
        assert f"`{instead}` (not `{left_out}`)" in rules()
        assert left_out not in funground.__all__ and instead in funground.__all__


def test_llms_txt_has_the_llmstxt_shape():
    lines = INDEX.read_text(encoding="utf-8").splitlines()
    assert lines[0] == "# funground"
    assert lines[2].startswith("> ")
    assert "## Docs" in lines and "## Optional" in lines


def test_every_link_in_llms_txt_is_a_file_of_the_repository():
    targets = re.findall(r"\]\((https://[^)]+)\)", INDEX.read_text(encoding="utf-8"))
    assert targets
    for url in targets:
        assert url.startswith(REPO_URL), url
        path = url[len(REPO_URL):].split("#")[0]
        assert (ROOT / path).is_file(), path


def test_llms_full_holds_the_rules_and_every_public_name():
    full = FULL.read_text(encoding="utf-8")
    assert "## Rules for writing funground code" in full and "## The API reference" in full
    assert '<a id="' not in full                      # the anchors of API.md are left out
    assert not re.search(r"\]\((?!https?://)[^)]+\)", full), "a relative link would not work outside the repository"
    missing = [n for n in funground._PUBLIC_NAMES if f"f.{n}" not in full and f"`{n}`" not in full]
    assert not missing, missing


def test_the_package_carries_the_same_pages():
    for name in ("llms.txt", "llms-full.txt"):
        assert (ROOT / "funground" / name).read_bytes() == (ROOT / name).read_bytes()


def test_agents_md_links_resolve():
    text = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    links = re.findall(r"\]\(([^)#\s]+)(?:#[^)]*)?\)", text)
    assert links
    for link in links:
        if not link.startswith("http"):
            assert (ROOT / link).exists(), link
