"""Freeze the public API of a release into funground/released_names.json (S-229, D-116).

    .venv/Scripts/python tools/make_released_names.py --ref v0.1.0 --version 0.1.0

It reads the source at a git ref with ``git show`` and ``ast``; the old code is never imported. For the version it
records every name in ``_PUBLIC_NAMES`` and, for each public class listed in funground/completions.json, the public
methods and properties the class has at that ref (a class that did not exist then is left out). Releases already in the
file are kept. tools/since.py reads the file to say which names arrive in a later release.

Run it once after each release is tagged (docs/developer/Releasing.md), then regenerate the API reference.
"""
from __future__ import annotations

import argparse
import ast
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "funground" / "released_names.json"
COMPLETIONS = ROOT / "funground" / "completions.json"


def git(*args: str) -> str:
    result = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, encoding="utf-8")
    if result.returncode:
        raise SystemExit(f"git {' '.join(args)}: {result.stderr.strip()}")
    return result.stdout


def string_list(node: ast.AST) -> list[str] | None:
    if isinstance(node, (ast.List, ast.Tuple)) and all(isinstance(e, ast.Constant) and isinstance(e.value, str) for e in node.elts):
        return [e.value for e in node.elts]
    return None


def public_names_at(ref: str) -> list[str]:
    """_PUBLIC_NAMES as the source at *ref* builds it: a literal list, or a literal __all__ plus the four star-out names."""
    tree = ast.parse(git("show", f"{ref}:funground/__init__.py"))
    literal: dict[str, list[str]] = {}
    star: list[str] = []
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            name = node.targets[0].id
            found = string_list(node.value)
            if found is not None:
                literal[name] = found
            elif name == "STAR_NAMES_FOR" and isinstance(node.value, ast.Dict):
                star = [k.value for k in node.value.keys if isinstance(k, ast.Constant)]
    if "_PUBLIC_NAMES" in literal:
        return sorted(set(literal["_PUBLIC_NAMES"]))
    if "__all__" in literal:
        return sorted(set(literal["__all__"]) | set(star))
    raise SystemExit(f"cannot read the public names from funground/__init__.py at {ref}")


def class_definitions_at(ref: str) -> dict[str, list[ast.ClassDef]]:
    """Every class defined anywhere in the package at *ref*, by name."""
    found: dict[str, list[ast.ClassDef]] = {}
    for path in git("ls-tree", "-r", "--name-only", ref, "funground").splitlines():
        if path.endswith(".py"):
            for node in ast.walk(ast.parse(git("show", f"{ref}:{path}"))):
                if isinstance(node, ast.ClassDef):
                    found.setdefault(node.name, []).append(node)
    return found


def members_of(node: ast.ClassDef, classes: dict[str, list[ast.ClassDef]], seen: frozenset = frozenset()) -> set[str]:
    """Public methods and properties of a class, own and inherited from classes in the package."""
    out: set[str] = set()
    for item in node.body:
        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and not item.name.startswith("_"):
            out.add(item.name)
    for base in node.bases:
        if isinstance(base, ast.Name) and base.id in classes and base.id not in seen and len(classes[base.id]) == 1:
            out |= members_of(classes[base.id][0], classes, seen | {node.name})
    return out


def class_members_at(ref: str, class_names: list[str]) -> dict[str, list[str]]:
    classes = class_definitions_at(ref)
    out: dict[str, list[str]] = {}
    for name in class_names:
        found = classes.get(name, [])
        if len(found) > 1:
            raise SystemExit(f"class {name} is defined more than once at {ref}; the tool cannot choose")
        if found:
            out[name] = sorted(members_of(found[0], classes))
    return out


def current_class_names() -> list[str]:
    return sorted(json.loads(COMPLETIONS.read_text(encoding="utf-8"))["classes"])


def build_release(ref: str) -> dict:
    return {"names": public_names_at(ref), "classes": class_members_at(ref, current_class_names())}


def released_text(version: str, ref: str, existing: dict | None = None) -> str:
    data = dict(existing or {})
    data[version] = build_release(ref)
    data = dict(sorted(data.items(), key=lambda kv: [int(p) for p in kv[0].split(".")]))
    return json.dumps(data, indent=1, ensure_ascii=False) + "\n"


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--ref", required=True, help="the git commit or tag of the release")
    ap.add_argument("--version", required=True, help="the release version, such as 0.1.0")
    args = ap.parse_args(argv)
    existing = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {}
    OUT.write_bytes(released_text(args.version, args.ref, existing).encode("utf-8"))
    print(f"wrote {OUT.relative_to(ROOT).as_posix()} for {args.version} from {args.ref}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
