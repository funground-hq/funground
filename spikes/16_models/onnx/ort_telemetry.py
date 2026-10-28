"""Parent: starts the child, watches the CHILD's TCP connections from outside until the child has exited (so interpreter
exit is covered), and prints each connection against the child's phase markers.
  python -I ort_telemetry.py ORTVENV_PYTHON MODEL.onnx [env]     env = 'default' or 'disabled' (ORT_DISABLE_TELEMETRY=1)"""
import os, subprocess, sys, time, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tcp_watch import TcpWatch
py, model, mode = sys.argv[1], sys.argv[2], sys.argv[3]
env = {k: v for k, v in os.environ.items() if k != "ORT_DISABLE_TELEMETRY"}
if mode == "disabled": env["ORT_DISABLE_TELEMETRY"] = "1"
child = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ort_telemetry_child.py")
p = subprocess.Popen([py, "-I", child, model], stdout=subprocess.PIPE, text=True, env=env)
w = TcpWatch(pid=int(p.stdout.readline().split()[1])); w.start()
marks = {}; mods = []
for line in p.stdout:
    if line.startswith("MARK"): _, name, t = line.split(); marks[name] = float(t)
    elif line.startswith("MODS"): mods = line.split()[1:]
rc = p.wait(); t_end = time.time(); time.sleep(1.0); w.stop()
print(json.dumps({"mode": mode, "returncode": rc, "marks_rel_s": {k: round(v - marks["start"], 2) for k, v in marks.items()},
                  "net_modules_loaded": mods, "exit_to_end_s": round(t_end - marks["exiting"], 2),
                  "connections": [{"remote": f"{ip}:{port}", "first_seen_rel_s": round(t - marks["start"], 2), "state": st} for (ip, port), (t, st) in w.seen.items()]}))
