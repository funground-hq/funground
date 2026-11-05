"""Re-run chosen mutants against the current tests, on a separate copy (spike 21).

Usage: verify.py MODULE_PATH TESTS ... -- ID [ID ...]
The copy is refreshed from the checkout's funground/ and tests/ each time, so new tests are used.
"""
import os
import shutil
import sys
import time

import mutate

args = sys.argv[1:]
cut = args.index("--")
module, tests, ids = args[0], args[1:cut], [int(i) for i in args[cut + 1:]]
copy = os.path.join(mutate.WORK, "verify")
if os.path.isdir(copy):
    shutil.rmtree(copy)
shutil.copytree(mutate.REPO, copy, symlinks=True,
                ignore=shutil.ignore_patterns(".git", ".venv", "__pycache__", "spikes"))
src = open(os.path.join(mutate.REPO, module), encoding="utf-8").read()
status, dt, tail = mutate.run_tests(copy, tests, 120)
print("real code:", status, tail)
t = int(time.time()) + 100
for i in ids:
    msrc, info = mutate.mutant_source(src, i)
    target = os.path.join(copy, module)
    open(target, "w", encoding="utf-8").write(msrc)
    t += 2
    os.utime(target, (t, t))
    status, dt, tail = mutate.run_tests(copy, tests, 120)
    print(i, info["line"], info["kind"], info["desc"], "->", status)
shutil.copyfile(os.path.join(mutate.REPO, module), os.path.join(copy, module))
