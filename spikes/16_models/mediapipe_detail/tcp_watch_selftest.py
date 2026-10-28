"""Check that tcp_watch.py really sees a connection: open one to example.com and hold it for a moment."""
import socket, sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tcp_watch import TcpWatch
w = TcpWatch(); w.start()
s = socket.create_connection(("example.com", 443), timeout=10); time.sleep(0.3); s.close(); time.sleep(0.3); w.stop()
print("seen:", list(w.seen))
