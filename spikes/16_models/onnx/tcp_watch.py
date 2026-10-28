"""(S-231 ORT copy of mediapipe_detail/tcp_watch.py; only change: optional pid, to watch a child process.)
Windows only, no admin. Poll this process's own TCP connections through the IP Helper API
(GetExtendedTcpTable, every ~2 ms) and record every remote address it sees. Standard library only.
  w = TcpWatch(); w.start(); ...; w.stop(); w.seen  -> {(ip, port): (first_seen_time, state)}"""
import ctypes, os, socket, struct, threading, time
from ctypes import wintypes
_iph = ctypes.WinDLL("iphlpapi")
_STATES = {1: "CLOSED", 2: "LISTEN", 3: "SYN_SENT", 4: "SYN_RCVD", 5: "ESTABLISHED", 6: "FIN_WAIT1",
           7: "FIN_WAIT2", 8: "CLOSE_WAIT", 9: "CLOSING", 10: "LAST_ACK", 11: "TIME_WAIT", 12: "DELETE_TCB"}

def _table(family):
    size = wintypes.DWORD(0)
    _iph.GetExtendedTcpTable(None, ctypes.byref(size), False, family, 5, 0)
    buf = ctypes.create_string_buffer(size.value + 4096)
    size = wintypes.DWORD(len(buf))
    if _iph.GetExtendedTcpTable(buf, ctypes.byref(size), False, family, 5, 0) != 0:
        return []
    n = struct.unpack_from("<I", buf, 0)[0]
    rows = []
    for i in range(n):
        if family == socket.AF_INET:
            st, la, lp, ra, rp, pid = struct.unpack_from("<6I", buf, 4 + i * 24)
            rows.append((pid, st, socket.inet_ntop(socket.AF_INET, struct.pack("<I", ra)), socket.ntohs(rp & 0xFFFF)))
        else:
            o = 4 + i * 56
            ra = bytes(buf[o + 24:o + 40]); rp = struct.unpack_from("<I", buf, o + 44)[0]
            st, pid = struct.unpack_from("<2I", buf, o + 48)
            rows.append((pid, st, socket.inet_ntop(socket.AF_INET6, ra), socket.ntohs(rp & 0xFFFF)))
    return rows

class TcpWatch:
    def __init__(self, pid=None): self.seen = {}; self._stop = False; self._t = None; self.pid = pid   # pid=None: this process
    def start(self):
        self.t0 = time.time(); self._t = threading.Thread(target=self._run, daemon=True); self._t.start()
    def _run(self):
        pid = self.pid or os.getpid()
        while not self._stop:
            for fam in (socket.AF_INET, socket.AF_INET6):
                for p, st, ip, port in _table(fam):
                    if p == pid and st not in (2,) and ip not in ("0.0.0.0", "::", "127.0.0.1", "::1"):
                        self.seen.setdefault((ip, port), (time.time(), _STATES.get(st, st)))
            time.sleep(0.002)
    def stop(self):
        self._stop = True
        if self._t: self._t.join(2)
