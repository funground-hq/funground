"""Soak one sketch in this process: warm-up frames, then run until a time limit, sampling RSS.
Usage: soak_one.py SKETCH OUT.jsonl [seconds] [warmup] [every]. Approach copied from tests/conftest.py run_sketch."""
import json, os, sys, time, inspect
os.environ.setdefault("FUNGROUND_HEADLESS", "1")
os.environ.setdefault("SDL_VIDEODRIVER", "dummy"); os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
import random; random.seed(0)
import funground
from funground import api

def rss_mb():
    with open("/proc/self/statm") as fh:
        return int(fh.read().split()[1]) * os.sysconf("SC_PAGE_SIZE") / 1e6

class Stop(Exception):
    pass

def main(path, out, seconds=20.0, warmup=100, every=200):
    samples, state = [], {"n": 0, "t0": None}
    def harness_run(*, fps=1000, max_frames=None, **_):
        g = inspect.currentframe().f_back.f_globals
        draw = g.get("draw")
        def wrapped(*a, **k):
            r = draw(*a, **k)
            state["n"] += 1; n = state["n"]
            if n == warmup:
                state["t0"] = time.monotonic(); samples.append((n, rss_mb()))
            elif n > warmup and (n - warmup) % every == 0:
                samples.append((n, rss_mb()))
                if time.monotonic() - state["t0"] > seconds:
                    raise Stop
            return r
        g["draw"] = wrapped
        api.active_sketch().run_namespace(g, fps=1000, max_frames=10**9)
    funground.run, funground.show = harness_run, (lambda *a, **k: None)
    err = None
    os.chdir(os.path.dirname(os.path.abspath(path)))
    try:
        exec(compile(open(path, encoding="utf-8").read(), path, "exec"),
             {"__name__": "__sketch__", "__file__": os.path.abspath(path)})
    except Stop:
        pass
    except BaseException as e:   # record, do not hide
        err = f"{type(e).__name__}: {e}"[:300]
    rec = {"sketch": path, "frames": state["n"], "samples": samples, "error": err,
           "secs": None if state["t0"] is None else round(time.monotonic() - state["t0"], 1)}
    if len(samples) >= 2:
        (n0, m0), (n1, m1) = samples[0], samples[-1]
        rec.update(mb_warm=round(m0, 1), mb_end=round(m1, 1),
                   mb_per_1000=round((m1 - m0) / max(n1 - n0, 1) * 1000, 2))
        half = samples[len(samples) // 2]
        rec["mb_per_1000_2nd_half"] = round((m1 - half[1]) / max(n1 - half[0], 1) * 1000, 2)
    with open(out, "a") as fh:
        fh.write(json.dumps(rec) + "\n")

if __name__ == "__main__":
    a = sys.argv
    main(os.path.abspath(a[1]), os.path.abspath(a[2]), float(a[3]) if len(a) > 3 else 20.0,
         int(a[4]) if len(a) > 4 else 100, int(a[5]) if len(a) > 5 else 200)
