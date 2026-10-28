"""One pose task with timestamps, to line up with proxy.py's log.
python -I telemetry_run.py MODEL.task IMAGE.jpg [--idle N] [--empty-fields] [--frames N]
Prints wall-clock time (same clock as proxy.py) for: create, each 25 frames, close, end of idle."""
import sys, time, os, socket
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import nostubs  # noqa
import mediapipe as mp
from mediapipe.tasks.python import BaseOptions, vision
model, image = sys.argv[1], sys.argv[2]
idle = float(sys.argv[sys.argv.index("--idle") + 1]) if "--idle" in sys.argv else 10
frames = int(sys.argv[sys.argv.index("--frames") + 1]) if "--frames" in sys.argv else 100
MODE = sys.argv[sys.argv.index("--variant") + 1] if "--variant" in sys.argv else "default"
if MODE != "default":
    # HACK for measuring only: change what BaseOptions.to_ctypes hands to the native library.
    from mediapipe.tasks.python.core import base_options as _bo
    _orig = _bo.BaseOptions.to_ctypes
    def _patched(self):
        o = _orig(self)
        if MODE in ("nocerts", "all"): o.ca_bundle_path = None
        if MODE in ("unknownhost", "all"): o.host_environment = 0; o.host_system = 0; o.host_version = None
        return o
    _bo.BaseOptions.to_ctypes = _patched
NOCLOSE = "--noclose" in sys.argv
def t(m): print(f"{time.time():.3f} {m}", flush=True)
from tcp_watch import TcpWatch
w = TcpWatch(); w.start()
t("start")
img = mp.Image.create_from_file(image)
t("creating task")
d = vision.PoseLandmarker.create_from_options(vision.PoseLandmarkerOptions(
    base_options=BaseOptions(model_asset_path=model), running_mode=vision.RunningMode.IMAGE))
t("task created")
for i in range(frames):
    n = len(d.detect(img).pose_landmarks[0])
    if i % 25 == 0: t(f"frame {i} landmarks {n}")
t(f"{frames} frames done, idling {idle}s")
time.sleep(idle)
t("closing"); (None if NOCLOSE else d.close()); t("closed (skipped)" if NOCLOSE else "closed")
time.sleep(idle)
t("end"); w.stop()
for (ip, port), (ts, st) in sorted(w.seen.items(), key=lambda kv: kv[1][0]):
    try: name = socket.gethostbyaddr(ip)[0]
    except OSError: name = "?"
    print(f"{ts:.3f} TCP {ip}:{port} {st} {name}")
print("remote connections seen:", len(w.seen))
