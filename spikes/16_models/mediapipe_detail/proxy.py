"""Tiny logging HTTP proxy for the S-231 telemetry question. Standard library only.

Logs ONLY: time, method, host:port, bytes sent each way. It never logs paths, headers or bodies.
  python -I proxy.py [--port 8899] [--mode tunnel|refuse] [--log FILE] [--seconds 120]
tunnel = forward CONNECT traffic to the real host (the app behaves as normal).
refuse = answer 403 (the app sees a blocked network).
Plain-http requests (no CONNECT) are logged by host and refused in both modes.
"""
import argparse, socket, sys, threading, time

ap = argparse.ArgumentParser()
ap.add_argument("--port", type=int, default=8899)
ap.add_argument("--mode", choices=("tunnel", "refuse"), default="tunnel")
ap.add_argument("--log", default=None)
ap.add_argument("--seconds", type=float, default=120)
a = ap.parse_args()
T0 = time.time()
lock = threading.Lock()
out = open(a.log, "a", encoding="utf-8") if a.log else sys.stdout

def log(msg):
    with lock:
        print(f"{time.time():.3f} +{time.time() - T0:6.2f}s {msg}", file=out, flush=True)

def pipe(src, dst, counter, i):
    try:
        while True:
            d = src.recv(65536)
            if not d:
                break
            counter[i] += len(d)
            dst.sendall(d)
    except OSError:
        pass
    finally:
        try: dst.shutdown(socket.SHUT_WR)
        except OSError: pass

def handle(c):
    try:
        c.settimeout(10)
        buf = b""
        while b"\r\n\r\n" not in buf and len(buf) < 65536:
            d = c.recv(4096)
            if not d: return
            buf += d
        first = buf.split(b"\r\n", 1)[0].decode("latin1").split()
        if len(first) < 2: return
        method, target = first[0], first[1]
        if method == "CONNECT":
            host, _, port = target.rpartition(":")
            if a.mode == "refuse":
                log(f"CONNECT {host}:{port} REFUSED")
                c.sendall(b"HTTP/1.1 403 Forbidden\r\nContent-Length: 0\r\n\r\n"); return
            try:
                u = socket.create_connection((host, int(port)), timeout=10)
            except OSError as e:
                log(f"CONNECT {host}:{port} FAILED {type(e).__name__}")
                c.sendall(b"HTTP/1.1 502 Bad Gateway\r\nContent-Length: 0\r\n\r\n"); return
            c.sendall(b"HTTP/1.1 200 Connection established\r\n\r\n")
            c.settimeout(None); u.settimeout(None)
            n = [0, 0]
            t = threading.Thread(target=pipe, args=(u, c, n, 1), daemon=True); t.start()
            pipe(c, u, n, 0); t.join(5)
            log(f"CONNECT {host}:{port} closed, bytes up {n[0]} down {n[1]}")
            u.close()
        else:
            host = target.split("//", 1)[-1].split("/", 1)[0]
            log(f"{method} http://{host} REFUSED (plain http)")
            c.sendall(b"HTTP/1.1 403 Forbidden\r\nContent-Length: 0\r\n\r\n")
    except OSError:
        pass
    finally:
        c.close()

s = socket.socket(); s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(("127.0.0.1", a.port)); s.listen(20); s.settimeout(1)
log(f"proxy up on 127.0.0.1:{a.port} mode={a.mode}")
while time.time() - T0 < a.seconds:
    try: c, _ = s.accept()
    except socket.timeout: continue
    threading.Thread(target=handle, args=(c,), daemon=True).start()
log("proxy stopped")
