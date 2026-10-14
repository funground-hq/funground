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


def test_colors_and_constants_are_declared_statically_as_final_words():
    """An editor reads the class bodies, so each name is ``NAME: Final = "word"`` (S-174), not made at run time."""
    def class_bodies(path, names):
        tree = ast.parse((PACKAGE / path).read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name in names:
                yield node

    seen = 0
    for path, names in (("_color_names_class.py", {"COLORS"}), ("_constants.py", {"CONSTANTS"})):
        for cls in class_bodies(path, names):
            for group in [cls, *[n for n in cls.body if isinstance(n, ast.ClassDef)]]:
                for stmt in group.body:
                    if isinstance(stmt, ast.AnnAssign):
                        assert ast.unparse(stmt.annotation) == "Final", ast.unparse(stmt)
                        assert isinstance(stmt.value, ast.Constant) and isinstance(stmt.value.value, str)
                        seen += 1
                    else:
                        assert isinstance(stmt, (ast.Expr, ast.ClassDef)), ast.unparse(stmt)   # a docstring, or a group
    assert seen == len(f.COLORS) + sum(len(group) for group in f.CONSTANTS)


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
        "circle(1, 2, 3)\n"
        "reveal_type(f.COLORS.TOMATO)\n"
        "f.fill(f.COLORS.TOMATO)\n"
        "f.text_align(f.CONSTANTS.ALIGN.CENTER)\n"
        "text_align(CONSTANTS.ALIGN.LEFT, CONSTANTS.ALIGN.BASELINE)\n"
        "f.blend_mode('multiply')\n"
        "f.text_align('centre')\n"
        "f.rect_mode(f.CONSTANTS.ALIGN.TOP)\n"
        "f.fill(f.COLORS.TOMATOE)\n", encoding="utf-8")
    run = subprocess.run([shutil.which("pyright"), "--outputjson", str(sketch)], capture_output=True, text=True,
                         cwd=str(PACKAGE.parent), timeout=300)
    report = json.loads(run.stdout)
    diagnostics = report["generalDiagnostics"]
    errors = [d for d in diagnostics if d["severity"] == "error"]
    # the last three lines are meant to be wrong: a misspelt word, a word of another group, a misspelt colour
    wrong = [d for d in errors if d["range"]["start"]["line"] >= 12]
    assert len(wrong) == 3 and {d["range"]["start"]["line"] for d in wrong} == {12, 13, 14}, wrong
    errors = [d for d in errors if d not in wrong]
    assert not errors, errors
    assert not [d for d in diagnostics if "reportPrivateImportUsage" in d.get("rule", "")]
    infos = " ".join(d["message"] for d in diagnostics if d["severity"] == "information")
    assert 'Type of "f.width" is "int"' in infos and 'Type of "f.width" is "object"' not in infos
    assert 'Type of "f.COLORS.TOMATO" is "str"' not in infos
    assert "Literal['tomato']" in infos or 'Literal["tomato"]' in infos
