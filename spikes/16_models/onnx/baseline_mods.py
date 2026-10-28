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
