"""Child of ort_telemetry.py. Runs ONE small ONNX model through onnxruntime and prints a timestamped marker per phase:
import, session creation, 100 runs, close (del), then lets the interpreter exit.   python -I child.py MODEL.onnx"""
import sys, time, os
def mark(p): print(f"MARK {p} {time.time():.3f}", flush=True)
print("PID", os.getpid(), flush=True)   # the venv python.exe is a launcher; the parent needs the real interpreter pid
mark("start")
import numpy as np
import onnxruntime as ort
mark("imported")
s = ort.InferenceSession(sys.argv[1], providers=["CPUExecutionProvider"])
mark("session")
i = s.get_inputs()[0]
shape = [d if isinstance(d, int) else 1 for d in i.shape]
x = np.random.rand(*shape).astype(np.float32 if "float)" in i.type else np.int32)
for _ in range(100): s.run(None, {i.name: x})
mark("100runs")
del s
mark("closed")
time.sleep(float(os.environ.get("PROBE_SLEEP", "2")))   # a long sleep lets a delayed uploader show itself
mark("exiting")   # after this the interpreter shuts down; the parent keeps watching until the process is gone
# Which network DLLs ended up loaded in this process? (EnumProcessModules)
import ctypes
from ctypes import wintypes
k = ctypes.WinDLL("kernel32"); ps = ctypes.WinDLL("psapi")
k.GetCurrentProcess.restype = wintypes.HANDLE
ps.EnumProcessModules.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.HMODULE), wintypes.DWORD, ctypes.POINTER(wintypes.DWORD)]
ps.GetModuleBaseNameW.argtypes = [wintypes.HANDLE, wintypes.HMODULE, wintypes.LPWSTR, wintypes.DWORD]
h = k.GetCurrentProcess(); arr = (wintypes.HMODULE * 1024)(); need = wintypes.DWORD()
ps.EnumProcessModules(h, arr, ctypes.sizeof(arr), ctypes.byref(need))
names = []
for m in arr[: need.value // ctypes.sizeof(wintypes.HMODULE)]:
    b = ctypes.create_unicode_buffer(260); ps.GetModuleBaseNameW(h, m, b, 260); names.append(b.value.lower())
print("MODS", " ".join(sorted(n for n in names if any(x in n for x in ("winhttp", "wininet", "ws2_32", "mswsock", "dnsapi", "onnx", "crypt32", "schannel", "webio", "wsock")))), flush=True)
