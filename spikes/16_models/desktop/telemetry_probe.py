"""Watch this process's TCP connections (netstat) while a pose task runs. Prints remote addresses seen."""
import os, subprocess, sys, threading, time
import mediapipe as mp
from mediapipe.tasks.python import BaseOptions, vision
pid = str(os.getpid()); seen = {}; stop = False
def poll():
    while not stop:
        out = subprocess.run(["netstat", "-ano", "-p", "tcp"], capture_output=True, text=True).stdout
        for l in out.splitlines():
            p = l.split()
            if len(p) >= 5 and p[-1] == pid and p[3] != "LISTENING":
                seen.setdefault(p[2], (p[3], round(time.time() - t0, 1)))
        time.sleep(0.15)
t0 = time.time(); th = threading.Thread(target=poll, daemon=True); th.start()
model, image = sys.argv[1], sys.argv[2]
d = vision.PoseLandmarker.create_from_options(vision.PoseLandmarkerOptions(
    base_options=BaseOptions(model_asset_path=model), running_mode=vision.RunningMode.IMAGE))
img = mp.Image.create_from_file(image)
for _ in range(30): d.detect(img)
print("ran 30 frames; waiting 20 s", flush=True)
time.sleep(20); d.close(); time.sleep(8); stop = True; th.join()
print("connections seen:", seen or "none")
