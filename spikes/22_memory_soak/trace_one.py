"""Name the lines that grow: tracemalloc snapshot after warm-up and after N more frames. Usage: trace_one.py SKETCH [warmup] [frames]"""
import os, sys, inspect, tracemalloc
os.environ.setdefault("FUNGROUND_HEADLESS", "1")
import random; random.seed(0)
import funground
from funground import api
path = os.path.abspath(sys.argv[1]); warm = int(sys.argv[2]) if len(sys.argv) > 2 else 100
more = int(sys.argv[3]) if len(sys.argv) > 3 else 300
snaps, n = [], [0]
class Stop(Exception): pass
def harness_run(**_):
    g = inspect.currentframe().f_back.f_globals; draw = g["draw"]
    def wrapped(*a, **k):
        r = draw(*a, **k); n[0] += 1
        if n[0] == warm: snaps.append(tracemalloc.take_snapshot())
        if n[0] == warm + more: snaps.append(tracemalloc.take_snapshot()); raise Stop
        return r
    g["draw"] = wrapped
    api.active_sketch().run_namespace(g, fps=1000, max_frames=10**9)
funground.run, funground.show = harness_run, (lambda *a, **k: None)
tracemalloc.start(1)
os.chdir(os.path.dirname(path))
try:
    exec(compile(open(path).read(), path, "exec"), {"__name__": "__sketch__", "__file__": path})
except Stop:
    pass
print(f"## {os.path.relpath(path)}: frames {warm}..{warm+more}")
for s in snaps[1].compare_to(snaps[0], "lineno")[:5]:
    print("-", s)
