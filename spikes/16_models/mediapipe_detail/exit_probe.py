"""Does the upload happen when the task is NOT closed? python -I exit_probe.py MODEL IMAGE (del | exit)
del  = drop the last reference and collect garbage, then watch 5 s.
exit = leave it to the interpreter's exit; an atexit hook (registered first, so it runs last) watches 3 s more."""
import sys, os, time, gc, atexit
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import nostubs  # noqa
import mediapipe as mp
from mediapipe.tasks.python import BaseOptions, vision
from tcp_watch import TcpWatch
w = TcpWatch(); w.start()
def report(tag):
    time.sleep(3 if tag == "exit" else 5); w.stop()
    print(tag, "connections:", [(ip, port) for (ip, port) in w.seen] or "none", flush=True)
if sys.argv[3] == "exit": atexit.register(report, "exit")
d = vision.PoseLandmarker.create_from_options(vision.PoseLandmarkerOptions(base_options=BaseOptions(model_asset_path=sys.argv[1])))
d.detect(mp.Image.create_from_file(sys.argv[2]))
if sys.argv[3] == "del":
    del d; gc.collect(); report("del")
