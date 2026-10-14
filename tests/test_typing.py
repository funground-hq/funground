"""Type information for editors (S-130): py.typed, a literal __all__, typed live values, annotated functions."""
import ast
import inspect
import json
import shutil
import subprocess
from pathlib import Path

import pytest

import funground as f
from funground import api

PACKAGE = Path(f.__file__).parent
INIT_TREE = ast.parse((PACKAGE / "__init__.py").read_text(encoding="utf-8"))

def type_checking_blocks():
    for node in INIT_TREE.body:
        if isinstance(node, ast.If) and isinstance(node.test, ast.Name) and node.test.id == "TYPE_CHECKING":
            yield node


def test_py_typed_marker_exists():
    assert (PACKAGE / "py.typed").is_file()


def test_py_typed_ships_in_the_wheel():
    assert '"py.typed"' in (PACKAGE.parent / "pyproject.toml").read_text(encoding="utf-8")


def test_all_is_a_literal_list_of_strings():
    values = [n.value for n in INIT_TREE.body if isinstance(n, ast.Assign)
              and any(isinstance(t, ast.Name) and t.id == "__all__" for t in n.targets)]
    assert len(values) == 1 and isinstance(values[0], ast.List)
    assert all(isinstance(e, ast.Constant) and isinstance(e.value, str) for e in values[0].elts)
    assert [e.value for e in values[0].elts] == f.__all__


def test_public_names_are_all_plus_the_left_out_four():
    assert f._PUBLIC_NAMES == [*f.__all__, *f.STAR_LEAVES_OUT]
    assert len(set(f._PUBLIC_NAMES)) == len(f._PUBLIC_NAMES)


def test_every_live_value_is_declared_for_type_checkers():
    declared = {stmt.target.id for block in type_checking_blocks() for stmt in block.body
                if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name)}
    assert declared == set(api.LIVE_NAMES)


def test_left_out_names_are_imported_in_the_alias_form():
    aliased = {a.name for node in INIT_TREE.body if isinstance(node, ast.ImportFrom) and node.module == "api"
               for a in node.names if a.asname == a.name}
    assert set(f.STAR_LEAVES_OUT) <= aliased


def public_functions():
    for name in f._PUBLIC_NAMES:
        if name in api.LIVE_NAMES:
            continue
        obj = getattr(f, name)
        if callable(obj) and not inspect.isclass(obj):
            yield name, obj


def missing_annotations(obj):
    sig = inspect.signature(obj)
    return [p.name for p in sig.parameters.values() if p.annotation is p.empty] + (
        ["return"] if sig.return_annotation is sig.empty else [])


def test_every_public_function_is_annotated():
    lacking = {name: missing_annotations(obj) for name, obj in public_functions() if missing_annotations(obj)}
    assert not lacking, lacking


@pytest.mark.skipif(shutil.which("pyright") is None, reason="pyright is not installed")
def test_pyright_reads_the_package(tmp_path):
    sketch = tmp_path / "sketch.py"
    sketch.write_text(
        "import funground as f\n"
        "from funground import *\n"
        "f.circle(f.width / 2, f.mouse_y, 10)\n"
        "f.filter('invert')\n"
        "reveal_type(f.width)\n"
        "reveal_type(f.mouse_x)\n"
        "circle(1, 2, 3)\n", encoding="utf-8")
    run = subprocess.run([shutil.which("pyright"), "--outputjson", str(sketch)], capture_output=True, text=True,
                         cwd=str(PACKAGE.parent), timeout=300)
    report = json.loads(run.stdout)
    diagnostics = report["generalDiagnostics"]
    errors = [d for d in diagnostics if d["severity"] == "error"]
    assert not errors, errors
    assert not [d for d in diagnostics if "reportPrivateImportUsage" in d.get("rule", "")]
    infos = " ".join(d["message"] for d in diagnostics if d["severity"] == "information")
    assert 'Type of "f.width" is "int"' in infos and 'Type of "f.width" is "object"' not in infos
