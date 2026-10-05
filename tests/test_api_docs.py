"""The API reference and the docstrings behind it (D-066, S-125).

Docstring format (parsed by tools/make_api_reference.py):

    Summary sentence ending with a full stop.
    Prose.
    Arguments:   x, y: text
    Returns:     text
    Raises:      ValueError: text
    Example:     code
    See also: a, b
"""
import ast
import importlib.util
import inspect
import re
import subprocess
import sys
from pathlib import Path

import pytest

import funground as f
from funground import api

ROOT = Path(__file__).resolve().parent.parent
TOOL = ROOT / "tools" / "make_api_reference.py"

_spec = importlib.util.spec_from_file_location("make_api_reference", TOOL)
tool = importlib.util.module_from_spec(_spec)
sys.modules["make_api_reference"] = tool
_spec.loader.exec_module(tool)

LIVE = set(api.LIVE_NAMES)
FUNCTIONS = [n for n in f.__all__ if n not in LIVE and callable(getattr(f, n)) and not inspect.isclass(getattr(f, n))]
CLASS_ENTRIES = tool.class_names()


def _example_blocks(doc):
    body = tool.parse_doc(doc)["Example"]
    return body


@pytest.mark.parametrize("name", FUNCTIONS)
def test_summary_line_ends_with_a_full_stop(name):
    doc = getattr(f, name).__doc__
    assert doc, f"f.{name} has no docstring"
    first = inspect.cleandoc(doc).splitlines()[0]
    assert first.endswith("."), f"f.{name}: the first line must end with a full stop, not {first!r}"


@pytest.mark.parametrize("name", FUNCTIONS)
def test_every_parameter_is_under_arguments(name):
    obj = getattr(f, name)
    params = [p.name for p in inspect.signature(obj).parameters.values()]
    documented = tool.documented_params(obj.__doc__)
    missing = [p for p in params if p not in documented]
    assert not missing, f"f.{name}: parameters not under 'Arguments:': {missing}"


@pytest.mark.parametrize("name", FUNCTIONS)
def test_examples_parse(name):
    example = _example_blocks(getattr(f, name).__doc__)
    if example:
        ast.parse(example)


def test_live_docs_keys_equal_live_names():
    assert hasattr(api, "LIVE_DOCS"), "funground.api.LIVE_DOCS does not exist yet"
    assert set(api.LIVE_DOCS) == LIVE


@pytest.mark.parametrize("name", sorted(LIVE))
def test_live_docs_have_a_summary_and_parsing_examples(name):
    doc = getattr(api, "LIVE_DOCS", {}).get(name)
    assert doc, f"LIVE_DOCS has no entry for {name}"
    assert inspect.cleandoc(doc).splitlines()[0].endswith(".")
    example = _example_blocks(doc)
    if example:
        ast.parse(example)


def test_class_list_exists():
    assert tool.CLASS_LIST.exists(), "docs/reference/api_classes.txt does not exist yet"
    assert CLASS_ENTRIES


def _class_members():
    for entry in CLASS_ENTRIES:
        cls = tool.resolve_class(entry)
        for mname, member in tool.public_members(cls):
            yield pytest.param(cls, mname, member, id=f"{cls.__name__}.{mname}")


@pytest.mark.parametrize("entry", CLASS_ENTRIES)
def test_class_has_a_docstring_with_a_summary(entry):
    cls = tool.resolve_class(entry)
    assert cls.__doc__, f"{entry} has no docstring"
    assert inspect.cleandoc(cls.__doc__).splitlines()[0].endswith(".")


@pytest.mark.parametrize("cls, mname, member", list(_class_members()))
def test_public_class_members_have_docstrings(cls, mname, member):
    func = member.fget if isinstance(member, property) else member
    doc = func.__doc__
    assert doc, f"{cls.__name__}.{mname} has no docstring"
    assert inspect.cleandoc(doc).splitlines()[0].endswith("."), f"{cls.__name__}.{mname}: summary needs a full stop"
    if not isinstance(member, property):
        params = [p for p in inspect.signature(func).parameters if p not in ("self", "cls")]
        documented = tool.documented_params(doc)
        missing = [p for p in params if p not in documented]
        assert not missing, f"{cls.__name__}.{mname}: parameters not under 'Arguments:': {missing}"
    example = _example_blocks(doc)
    if example:
        ast.parse(example)


def test_every_public_name_is_in_a_group():
    tool.check_groups()           # raises SystemExit naming any name that is missing, duplicated or unknown


def test_the_generated_page_is_current():
    result = subprocess.run([sys.executable, str(TOOL), "--check"], capture_output=True, text=True,
                            cwd=ROOT, env={**__import__("os").environ, "FUNGROUND_HEADLESS": "1"})
    assert result.returncode == 0, result.stdout + result.stderr


def test_the_page_has_an_anchor_for_every_name():
    text = (ROOT / "docs" / "reference" / "API.md").read_text(encoding="utf-8")
    anchors = set(re.findall(r'<a id="([^"]+)"></a>', text))
    for name in f.__all__:
        if name in LIVE:
            assert f"live-{name}" in anchors
        elif inspect.isclass(getattr(f, name)):
            assert f"cls-{name}" in anchors
        else:
            assert f"fn-{name}" in anchors


def test_links_in_the_documentation_front_door_and_api_page_resolve():
    for page in (ROOT / "docs" / "README.md", ROOT / "docs" / "reference" / "API.md"):
        text = page.read_text(encoding="utf-8")
        for target in re.findall(r"\]\(([^)\s]+)\)", text):
            if target.startswith(("http:", "https:", "mailto:")):
                continue
            if target.startswith("#"):
                continue                      # in-page anchors: test_in_page_anchor_links_resolve_in_the_api_page
            path = target.split("#")[0]
            assert (page.parent / path).exists(), f"{page.name}: broken link {target}"


def test_in_page_anchor_links_resolve_in_the_api_page():
    text = (ROOT / "docs" / "reference" / "API.md").read_text(encoding="utf-8")
    ids = set(re.findall(r'<a id="([^"]+)"></a>', text))
    for target in re.findall(r"\]\(#([^)\s]+)\)", text):
        assert target in ids, f"API.md: link to missing anchor #{target}"
