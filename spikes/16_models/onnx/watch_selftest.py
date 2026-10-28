"""Self-test of the child-process watch: a child opens one TCP connection to 1.1.1.1:443; the parent must see it."""
import subprocess, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tcp_watch import TcpWatch
code = "import socket,time,os; print('PID', os.getpid(), flush=True); s=socket.create_connection(('pypi.org',443),timeout=10); print('child connected', s.getpeername(), flush=True); time.sleep(1.5)"
p = subprocess.Popen([sys.executable, "-I", "-c", code], stdout=subprocess.PIPE, text=True)   # the venv python.exe is a launcher: the real interpreter has another pid, so the child reports it
w = TcpWatch(pid=int(p.stdout.readline().split()[1])); w.start(); p.wait(); w.stop()
print("seen:", list(w.seen))
