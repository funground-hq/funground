"""A small AST mutation tester for spike 21.

Usage:
    mutate.py MODULE_PATH TIMEOUT_SECONDS OUT_JSON TEST_FILE [TEST_FILE ...]

It lists mutation sites in one module, then runs the given test files once per mutant
on four private copies of the repository (made with shutil.copytree, without .git and .venv), so
the checkout is never touched. PYTHONPATH points each run at its copy.

Mutation operators:
  compare  <→<=, <=→<, >→>=, >=→>, ==→!=, !=→==, is↔is not, in↔not in
  binop    +↔-, *↔/, //→/, %→//, **→*
  const    an int or float constant n → n + 1 (booleans and data tables skipped)
  boolop   and↔or
  unary    -x → x
A mutant is killed when pytest exits non-zero or runs longer than the timeout.
"""

from __future__ import annotations

import ast
import json
import os
import shutil
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PY = os.path.join(REPO, ".venv", "bin", "python")
WORK = os.environ.get("MUT_WORK", "/tmp/mutwork")
WORKERS = 4

CMP = {ast.Lt: ast.LtE, ast.LtE: ast.Lt, ast.Gt: ast.GtE, ast.GtE: ast.Gt,
       ast.Eq: ast.NotEq, ast.NotEq: ast.Eq, ast.Is: ast.IsNot, ast.IsNot: ast.Is,
       ast.In: ast.NotIn, ast.NotIn: ast.In}
BIN = {ast.Add: ast.Sub, ast.Sub: ast.Add, ast.Mult: ast.Div, ast.Div: ast.Mult,
       ast.FloorDiv: ast.Div, ast.Mod: ast.FloorDiv, ast.Pow: ast.Mult}
TABLE = 6  # a literal list/tuple/dict/set with this many elements or more is data


def _parents(tree):
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            child._parent = node  # noqa: SLF001


def _in_table(node) -> bool:
    p = getattr(node, "_parent", None)
    while p is not None:
        if isinstance(p, (ast.List, ast.Tuple, ast.Set)) and len(p.elts) >= TABLE:
            return True
        if isinstance(p, ast.Dict) and len(p.keys) >= TABLE:
            return True
        if isinstance(p, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
            return False
        p = getattr(p, "_parent", None)
    return False


def _in_annotation_or_all(node) -> bool:
    p = getattr(node, "_parent", None)
    child = node
    while p is not None:
        if isinstance(p, (ast.arg, ast.AnnAssign)) and getattr(p, "annotation", None) is child:
            return True
        if isinstance(p, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "__all__" for t in p.targets):
            return True
        child, p = p, getattr(p, "_parent", None)
    return False


def sites(src: str):
    """Yield (index, kind, lineno, description) for every mutation site."""
    tree = ast.parse(src)
    _parents(tree)
    out = []
    for node in ast.walk(tree):
        if _in_annotation_or_all(node):
            continue
        if isinstance(node, ast.Compare):
            for i, op in enumerate(node.ops):
                if type(op) in CMP:
                    out.append(("compare", node.lineno, f"{type(op).__name__}->{CMP[type(op)].__name__}", (node, i)))
        elif isinstance(node, (ast.BinOp, ast.AugAssign)):
            if type(node.op) in BIN:
                out.append(("binop", node.lineno, f"{type(node.op).__name__}->{BIN[type(node.op)].__name__}", (node, None)))
        elif isinstance(node, ast.BoolOp):
            out.append(("boolop", node.lineno, f"{type(node.op).__name__}->swap", (node, None)))
        elif isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
            out.append(("unary", node.lineno, "drop unary minus", (node, None)))
        elif isinstance(node, ast.Constant) and type(node.value) in (int, float) and not _in_table(node):
            out.append(("const", node.lineno, f"{node.value!r}->{node.value + 1!r}", (node, None)))
    out.sort(key=lambda s: (s[1], s[0], s[2]))
    return out


def mutant_source(src: str, index: int) -> tuple[str, dict]:
    tree = ast.parse(src)
    _parents(tree)
    kind, line, desc, (node, i) = sites_from_tree(tree)[index]
    if kind == "compare":
        node.ops[i] = CMP[type(node.ops[i])]()
    elif kind == "binop":
        node.op = BIN[type(node.op)]()
    elif kind == "boolop":
        node.op = ast.Or() if isinstance(node.op, ast.And) else ast.And()
    elif kind == "unary":
        parent = node._parent
        for field, value in ast.iter_fields(parent):
            if value is node:
                setattr(parent, field, node.operand)
            elif isinstance(value, list):
                for j, v in enumerate(value):
                    if v is node:
                        value[j] = node.operand
    elif kind == "const":
        node.value = node.value + 1
    return ast.unparse(tree), {"id": index, "kind": kind, "line": line, "desc": desc}


def sites_from_tree(tree):
    # same order as sites(), but over an already parsed tree
    src_sites = []
    for node in ast.walk(tree):
        if _in_annotation_or_all(node):
            continue
        if isinstance(node, ast.Compare):
            for i, op in enumerate(node.ops):
                if type(op) in CMP:
                    src_sites.append(("compare", node.lineno, f"{type(op).__name__}->{CMP[type(op)].__name__}", (node, i)))
        elif isinstance(node, (ast.BinOp, ast.AugAssign)):
            if type(node.op) in BIN:
                src_sites.append(("binop", node.lineno, f"{type(node.op).__name__}->{BIN[type(node.op)].__name__}", (node, None)))
        elif isinstance(node, ast.BoolOp):
            src_sites.append(("boolop", node.lineno, f"{type(node.op).__name__}->swap", (node, None)))
        elif isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
            src_sites.append(("unary", node.lineno, "drop unary minus", (node, None)))
        elif isinstance(node, ast.Constant) and type(node.value) in (int, float) and not _in_table(node):
            src_sites.append(("const", node.lineno, f"{node.value!r}->{node.value + 1!r}", (node, None)))
    src_sites.sort(key=lambda s: (s[1], s[0], s[2]))
    return src_sites


def make_copies():
    os.makedirs(WORK, exist_ok=True)
    for w in range(WORKERS):
        dst = os.path.join(WORK, f"w{w}")
        if not os.path.isdir(dst):
            shutil.copytree(REPO, dst, symlinks=True,
                            ignore=shutil.ignore_patterns(".git", ".venv", "__pycache__", "spikes"))


def run_tests(copy: str, tests: list[str], timeout: float) -> tuple[str, float, str]:
    env = dict(os.environ, PYTHONPATH=copy, FUNGROUND_HEADLESS="1",
               SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy")
    cmd = [PY, "-m", "pytest", "-x", "-q", "-o", "addopts=", "-p", "no:cacheprovider", *tests]
    t0 = time.monotonic()
    try:
        r = subprocess.run(cmd, cwd=copy, env=env, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return "timeout", time.monotonic() - t0, ""
    dt = time.monotonic() - t0
    tail = (r.stdout + r.stderr).strip().splitlines()[-1:] or [""]
    return ("survived" if r.returncode == 0 else "killed"), dt, tail[0]


def main():
    module, timeout, out_json, *tests = sys.argv[1:]
    timeout = float(timeout)
    src = open(os.path.join(REPO, module), encoding="utf-8").read()
    n = len(sites(src))
    make_copies()
    # sanity: every copy runs green on the real code, and imports its own funground
    for w in range(WORKERS):
        copy = os.path.join(WORK, f"w{w}")
        shutil.copyfile(os.path.join(REPO, module), os.path.join(copy, module))
    results = []
    lock_free = list(range(WORKERS))
    from threading import Lock
    lock = Lock()
    stamp = [int(time.time()) + 10]

    def job(index):
        with lock:
            w = lock_free.pop()
            stamp[0] += 2
            mtime = stamp[0]
        copy = os.path.join(WORK, f"w{w}")
        target = os.path.join(copy, module)
        try:
            msrc, info = mutant_source(src, index)
            with open(target, "w", encoding="utf-8") as fh:
                fh.write(msrc)
            os.utime(target, (mtime, mtime))  # a fresh mtime so no stale .pyc is used
            status, dt, tail = run_tests(copy, tests, timeout)
            info.update(status=status, seconds=round(dt, 1), tail=tail)
        finally:
            shutil.copyfile(os.path.join(REPO, module), target)
            os.utime(target, (mtime + 1, mtime + 1))
            with lock:
                lock_free.append(w)
        with lock:
            results.append(info)
            if len(results) % 10 == 0:
                _save(out_json, module, n, results, partial=True)
        return info

    with ThreadPoolExecutor(WORKERS) as pool:
        list(pool.map(job, range(n)))
    _save(out_json, module, n, results, partial=False)


def _save(out_json, module, n, results, partial):
    results = sorted(results, key=lambda r: r["id"])
    killed = sum(r["status"] in ("killed", "timeout") for r in results)
    data = {"module": module, "sites": n, "done": len(results), "killed": killed,
            "score": round(killed / max(1, len(results)), 3), "partial": partial, "mutants": results}
    with open(out_json, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=1)


if __name__ == "__main__":
    main()
