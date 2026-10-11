"""S-175: which names in the existing examples would clash with `from funground import *`?

Module-level clash: the sketch assigns or defines a star name at the top level (it hides funground's, or is hidden by it
depending on order). Local clash: a function assigns a star name or takes it as a parameter (harmless unless it then
calls funground's function of that name inside the same function).
"""
import ast
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import funground  # noqa: E402

STAR = set(funground.__all__)
module_hits, local_hits = Counter(), Counter()
files = sorted((ROOT / "examples").rglob("*.py"))
files_with_module_hit = set()


def targets(node):
    for n in ast.walk(node):
        if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store):
            yield n.id


for path in files:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError:
        continue
    for stmt in tree.body:
        names = set()
        if isinstance(stmt, (ast.FunctionDef, ast.ClassDef)):
            names.add(stmt.name)
        elif isinstance(stmt, (ast.Assign, ast.AnnAssign, ast.AugAssign, ast.For)):
            names.update(targets(stmt.targets[0] if isinstance(stmt, ast.Assign) else stmt.target))
        for name in names & STAR:
            module_hits[name] += 1
            files_with_module_hit.add(path)
    for func in (n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.Lambda))):
        args = func.args
        params = {a.arg for a in args.posonlyargs + args.args + args.kwonlyargs}
        stored = {t for stmt in (func.body if isinstance(func, ast.FunctionDef) else [func.body]) for t in targets(stmt)}
        for name in (params | stored) & STAR:
            local_hits[name] += 1

print(f"{len(files)} example files")
print(f"module-level clashes ({len(files_with_module_hit)} files):", dict(module_hits.most_common()))
print("local clashes:", dict(local_hits.most_common()))
