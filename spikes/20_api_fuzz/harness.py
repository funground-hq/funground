"""Spike 20: fuzz funground's public API the way confused beginners would.

Run from the repository root with the venv's Python:

    SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy FUNGROUND_HEADLESS=1 \
        .venv/bin/python spikes/20_api_fuzz/harness.py calls  OUT_DIR
    ... harness.py programs OUT_DIR N SEED

Each case is a tiny program (a list of source lines). The parent imports funground once and
forks one child per case (4 at a time). The child sets an address-space limit of 2 GB, runs
the program, and reports through a pipe. The parent kills a child after 10 s. Every finding is
appended to OUT_DIR/findings.jsonl as soon as it is known.
"""
from __future__ import annotations

import ast
import json
import math
import os
import resource
import select
import signal
import sys
import tempfile
import time
import traceback

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("FUNGROUND_HEADLESS", "1")

import funground as f  # noqa: E402
from funground import camera, sangeet, sound  # noqa: E402

PKG = os.path.dirname(f.__file__)
TIME_LIMIT = 10.0
MEM_LIMIT = 2 * 1024 ** 3
WORKERS = 4

# Names that wait forever for a window, a device or a person, or end the process on purpose.
SKIP = {
    "f.run": "runs a window loop; exercised only inside examples with max_frames",
    "f.show": "opens a window and waits for it to close",
    "f.full_screen": "needs a real display",
    "f.exit": "ends the sketch on purpose (SystemExit)",
    "f.stop": "ends the sketch on purpose (SystemExit)",
    "camera.open": "needs a camera device",
    "sound.microphone": "needs a microphone device",
}

# Beginner mistakes and edges, as source text so that every repro is printable.
BAD = [
    "0", "-1", "1", "1e308", "-1e308", "1e-308", "10**12", "2**63", "0.5",
    "float('nan')", "float('inf')", "-float('inf')", "None", "True", "False",
    "'10'", "'abc'", "''", "'tomatoe'", "'🎨😀'", "'שלום עולם'", "'नमस्ते'", "'\\ud800'",
    "'x' * 100000", "[1, 2]", "[[1, 2], [3]]", "(1, 2)", "()", "[]", "{}", "1j", "object()",
    "(255, 0)", "(1, 2, 3, 4, 5)", "'#12'", "-0.0",
]


def doc_example(obj) -> str | None:
    doc = obj.__doc__ or ""
    i = doc.find("Example:")
    if i < 0:
        return None
    lines = []
    for line in doc[i + len("Example:"):].splitlines()[1:]:
        if line.strip().startswith("See also") or (line.strip() == "" and lines and not lines[-1].strip() == ""
                                                    and False):
            break
        if line.strip().startswith(("Since ", "See also")):
            break
        lines.append(line)
    import textwrap
    src = textwrap.dedent("\n".join(lines)).strip("\n")
    return src or None


def targets():
    out = []
    for n in sorted(f._PUBLIC_NAMES):
        o = getattr(f, n)
        if callable(o) and not isinstance(o, type):
            out.append((f"f.{n}", o))
    for libname, lib in (("sound", sound), ("sangeet", sangeet), ("camera", camera)):
        for n in lib.__all__:
            out.append((f"{libname}.{n}", getattr(lib, n)))
    return out


class Mutator(ast.NodeTransformer):
    def __init__(self, dotted, which, how, pos):
        self.pos = pos
        self.mod, self.attr = dotted.split(".")
        self.which, self.how, self.done = which, how, False

    def visit_Call(self, node):
        self.generic_visit(node)
        fn = node.func
        if (not self.done and (node.lineno, node.col_offset) == self.pos and isinstance(fn, ast.Attribute) and fn.attr == self.attr
                and isinstance(fn.value, ast.Name) and fn.value.id == self.mod):
            self.done = True
            kind, idx, val = self.which, self.how[0], self.how[1]
            new = ast.parse(val, mode="eval").body if val is not None else None
            if kind == "arg":
                node.args[idx] = new
            elif kind == "kw":
                node.keywords[idx].value = new
            elif kind == "drop":
                node.args = node.args[:-1]
            elif kind == "extra":
                node.args = node.args + [ast.Constant(7)]
        return node


def call_sites(tree, dotted):
    mod, attr = dotted.split(".")
    for node in ast.walk(tree):
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == attr
                and isinstance(node.func.value, ast.Name) and node.func.value.id == mod):
            return node
    return None


def prepare(src: str) -> str:
    src = src.replace("f.run()", "f.run(max_frames=3)").replace("f.show()", "pass")
    if "f.size(" not in src and "def setup" not in src:
        src = "f.size(200, 150)\n" + src
    return src


def call_cases():
    cases, skipped = [], dict(SKIP)
    for dotted, obj in targets():
        if dotted in SKIP:
            continue
        ex = doc_example(obj)
        if not ex:
            skipped[dotted] = "no Example in its docstring (not fuzzed)"
            continue
        try:
            tree = ast.parse(ex)
        except SyntaxError:
            skipped[dotted] = "Example does not parse"
            continue
        site = call_sites(tree, dotted)
        base = prepare(ex)
        cases.append({"name": dotted, "kind": "valid", "src": base})
        if site is None:
            continue
        muts = [("drop", (0, None)), ("extra", (0, None))] if site.args else [("extra", (0, None))]
        for i in range(len(site.args)):
            muts += [("arg", (i, v)) for v in BAD]
        for i in range(len(site.keywords)):
            if site.keywords[i].arg is not None:
                muts += [("kw", (i, v)) for v in BAD]
        for which, how in muts:
            t = Mutator(dotted, which, how, (site.lineno, site.col_offset)).visit(ast.parse(ex))
            cases.append({"name": dotted, "kind": f"{which}{how[0]}={how[1]}", "src": prepare(ast.unparse(t))})
    return cases, skipped


# ---------------------------------------------------------------- the child

LEARNER_TYPES = {"RuntimeError", "KeyboardInterrupt", "ValueError", "TypeError", "FungroundError", "FileNotFoundError", "SystemExit",
                 "IsADirectoryError", "PermissionError", "NotADirectoryError"}


def check_files(folder):
    """Save PNG, PDF, SVG and GIF and read each back with a real parser. Returns a list of problems."""
    problems = []
    from PIL import Image
    import pypdf
    import xml.etree.ElementTree as ET
    for ext in ("png", "pdf", "svg"):
        p = os.path.join(folder, f"out.{ext}")
        try:
            f.save(p)
        except Exception as e:  # a save that refuses is judged like any other call
            problems.append(("save-error", ext, f"{type(e).__module__}.{type(e).__name__}: {e}"[:300],
                             _frames(e.__traceback__)))
            continue
        try:
            if ext == "png":
                with Image.open(p) as im:
                    im.load()
            elif ext == "pdf":
                r = pypdf.PdfReader(p, strict=True)
                for page in r.pages:
                    page.extract_text()
                raw = open(p, "rb").read()
                if b" nan " in raw.lower() or b" inf " in raw.lower():
                    problems.append(("nan-in-file", ext, "nan or inf in the PDF content", []))
            else:
                text = open(p, encoding="utf-8").read()
                ET.fromstring(text)
                low = text.lower()
                for tok in ("nan", "inf"):
                    import re
                    if re.search(r'[\s"(,=-]' + tok + r'[\s",)]', low):
                        problems.append(("nan-in-file", ext, f"{tok} in the SVG", []))
        except Exception as e:
            problems.append(("unreadable", ext, f"{type(e).__name__}: {e}"[:300], []))
    gif = os.path.join(folder, "out.gif")
    if os.path.exists(gif):
        try:
            with Image.open(gif) as im:
                for i in range(getattr(im, "n_frames", 1)):
                    im.seek(i)
                    im.load()
        except Exception as e:
            problems.append(("unreadable", "gif", f"{type(e).__name__}: {e}"[:300], []))
    return problems


def _frames(tb):
    out = []
    for fr in traceback.extract_tb(tb):
        out.append([fr.filename.replace(PKG, "funground"), fr.lineno, fr.name])
    return out


def child(case, wfd, with_files):
    resource.setrlimit(resource.RLIMIT_AS, (MEM_LIMIT, MEM_LIMIT))
    folder = tempfile.mkdtemp(prefix="fz")
    os.chdir(folder)
    res = {"status": "ok"}
    ns = {"f": f, "sound": sound, "sangeet": sangeet, "camera": camera, "__name__": "__fuzz__"}
    import warnings
    warnings.simplefilter("ignore")
    try:
        code = compile(case["src"], "<sketch>", "exec")
        exec(code, ns)
        if with_files:
            res["files"] = check_files(folder)
    except BaseException as e:  # noqa: BLE001 - we are classifying everything
        res = {"status": "raised", "type": f"{type(e).__module__}.{type(e).__name__}",
               "msg": str(e)[:400], "frames": _frames(e.__traceback__)}
    data = json.dumps(res).encode()
    os.write(wfd, data)
    os._exit(0)


# ---------------------------------------------------------------- the parent

def classify(case, res, rc, elapsed):
    if res is None:
        if rc == "timeout":
            return 2, "hang over 10 s"
        if isinstance(rc, int) and os.WIFSIGNALED(rc):
            sig = os.WTERMSIG(rc)
            return 1, f"killed by signal {signal.Signals(sig).name}"
        return 1, f"died without a report (status {rc})"
    if res["status"] == "raised":
        t = res["type"].split(".")[-1]
        if t == "MemoryError":
            return 2, "MemoryError (over the 2 GB limit)"
        frames = res["frames"]
        last = frames[-1][0] if frames else ""
        inside = last.startswith("funground")
        if t not in LEARNER_TYPES:
            return 4, f"raw {res['type']}"
        if not inside and last != "<sketch>":
            return 4, f"{t} raised from outside funground ({os.path.basename(last)})"
        return None, None
    for kind, ext, msg, fr in res.get("files", []):
        if kind in ("unreadable", "nan-in-file"):
            return 3, f"{kind} {ext}: {msg}"
        if kind in ("save-error", "gif"):
            t = msg.split(":")[0].split(".")[-1]
            if t not in LEARNER_TYPES:
                return 4, f"raw {msg.split(':')[0]} while saving {ext}"
    return None, None


def run_all(cases, out_dir, with_files_for=lambda c: False):
    os.makedirs(out_dir, exist_ok=True)
    fpath = os.path.join(out_dir, "findings.jsonl")
    spath = os.path.join(out_dir, "summary.jsonl")
    running = {}
    queue = list(enumerate(cases))
    counts = {"ok": 0, "learner-error": 0, "finding": 0}
    t0 = time.time()
    while queue or running:
        while queue and len(running) < WORKERS:
            idx, case = queue.pop(0)
            r, w = os.pipe()
            pid = os.fork()
            if pid == 0:
                os.close(r)
                child(case, w, with_files_for(case))
            os.close(w)
            running[pid] = (idx, case, r, time.time(), bytearray())
        rfds = [v[2] for v in running.values()]
        ready, _, _ = select.select(rfds, [], [], 0.05)
        for pid, (idx, case, r, start, buf) in list(running.items()):
            if r in ready:
                chunk = os.read(r, 65536)
                if chunk:
                    buf.extend(chunk)
                    continue
            done, status = os.waitpid(pid, os.WNOHANG)
            elapsed = time.time() - start
            rc = None
            if done == 0:
                if elapsed < TIME_LIMIT:
                    continue
                os.kill(pid, signal.SIGKILL)
                os.waitpid(pid, 0)
                rc = "timeout"
            else:
                rc = status
                while True:
                    chunk = os.read(r, 65536)
                    if not chunk:
                        break
                    buf.extend(chunk)
            os.close(r)
            del running[pid]
            res = None
            if rc != "timeout" and buf:
                try:
                    res = json.loads(buf.decode())
                except ValueError:
                    res = None
            cls, why = classify(case, res, rc, elapsed)
            rec = {"idx": idx, **case, "class": cls, "why": why, "secs": round(elapsed, 2), "res": res}
            if cls is not None:
                counts["finding"] += 1
                with open(fpath, "a") as fh:
                    fh.write(json.dumps(rec) + "\n")
            elif res and res["status"] == "raised":
                counts["learner-error"] += 1
            else:
                counts["ok"] += 1
            with open(spath, "a") as fh:
                fh.write(json.dumps({"idx": idx, "name": case["name"], "kind": case["kind"], "class": cls,
                                     "status": res and res["status"], "type": res and res.get("type"),
                                     "msg": res and res.get("msg", "")[:160], "secs": round(elapsed, 2)}) + "\n")
    print(json.dumps(counts), f"{time.time() - t0:.0f}s", flush=True)


def main():
    mode, out = sys.argv[1], sys.argv[2]
    if mode == "calls":
        cases, skipped = call_cases()
        os.makedirs(out, exist_ok=True)
        with open(os.path.join(out, "skipped.json"), "w") as fh:
            json.dump(skipped, fh, indent=1)
        print(len(cases), "cases;", len(skipped), "names skipped", flush=True)
        run_all(cases, out, with_files_for=lambda c: c["kind"] == "valid")
    elif mode == "programs":
        from programs import make_programs
        n, seed = int(sys.argv[3]), int(sys.argv[4])
        run_all(make_programs(n, seed), out, with_files_for=lambda c: True)


if __name__ == "__main__":
    main()
