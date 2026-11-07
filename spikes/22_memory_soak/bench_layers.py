"""S-258, Windows: bench_layers.py trail|busy|blink FRAMES [WIDTH HEIGHT]. Set PYTHONPATH to the tree to measure."""
import ctypes, gc, os, sys, time
os.environ["FUNGROUND_HEADLESS"] = "1"
import funground as f
from funground import api
from funground.sketch import Sketch
from funground.platform.headless import HeadlessPlatform
from ctypes import wintypes as wt
class PMC(ctypes.Structure):
    _fields_ = [("cb", wt.DWORD), ("PageFaultCount", wt.DWORD)] + [(n, ctypes.c_size_t) for n in
        ("Peak","WS","a","b","c","d","Private","PeakPrivate")]
k = ctypes.WinDLL("kernel32"); k.GetCurrentProcess.restype = wt.HANDLE
ps = ctypes.WinDLL("psapi"); ps.GetProcessMemoryInfo.argtypes = [wt.HANDLE, ctypes.POINTER(PMC), wt.DWORD]
def mb():
    p = PMC(); p.cb = ctypes.sizeof(p); assert ps.GetProcessMemoryInfo(k.GetCurrentProcess(), ctypes.byref(p), p.cb); return p.Private / 1e6
print(os.path.dirname(f.__file__)[-30:], end="  ")
sc = sys.argv[1]; N = int(sys.argv[2]); W, H = (int(sys.argv[3]), int(sys.argv[4])) if len(sys.argv) > 4 else (400, 300)
s = api.use_sketch(Sketch(platform=HeadlessPlatform())); f.size(W, H)
base = mb(); times = []
def frame(i):
    t0 = time.perf_counter()
    f.background(255)
    if sc == "trail":
        with f.layer(f"trail {i}"):
            f.no_stroke(); f.fill(200, 60, 40, 180); f.circle(i % W, 100 + i % 100, 10)
    elif sc == "busy":                       # 5 layers wiped and redrawn every frame
        for k_ in range(5):
            with f.layer(f"l{k_}"):
                f.clear(); f.fill(40, 80, 200, 150); f.circle((i * 3 + k_ * 40) % W, 150, 120)
    elif sc == "blink":                      # 20 layers, each redrawn once in 20 frames
        with f.layer(f"l{i % 20}"):
            f.clear(); f.fill(40, 80, 200, 150); f.circle(i % W, 150, 60)
    s._view_pixels(True)
    times.append(time.perf_counter() - t0)
for i in range(N):
    frame(i)
gc.collect()
tail = sorted(times[-30:]); first = sorted(times[:30])
print(f"{sc} {N}x{W}x{H}: private +{mb()-base:7.1f} MB, frame ms first30 median {first[15]*1000:6.2f}, last30 median {tail[15]*1000:6.2f}, worst {max(times)*1000:6.1f}, total {sum(times):5.1f} s")
