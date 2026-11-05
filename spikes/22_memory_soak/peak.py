"""Peak memory of one big print or export job, in its own process. Usage: peak.py CASE OUTDIR OUT.jsonl
Cases: a0_png, a0_pdf, pdf60, gif300, mp4300. Run under `prlimit --as=12884901888` and `timeout 180`."""
import json, os, resource, sys, time
os.environ.setdefault("FUNGROUND_HEADLESS", "1")
import random; random.seed(0)
import funground as f
from funground import api

case, outdir, out = sys.argv[1], sys.argv[2], sys.argv[3]
os.makedirs(outdir, exist_ok=True)
PHOTO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "examples", "gallery", "images", "data", "photo.jpg")
t0, err, extra = time.monotonic(), None, {}

def art(w, h, n=400):
    f.background(250)
    for i in range(n):
        f.fill(random.randint(0, 255), random.randint(0, 255), 160)
        f.circle(random.uniform(0, w), random.uniform(0, h), random.uniform(5, w / 20))
    f.text_size(h / 30); f.fill(0); f.text("funground memory spike", w / 20, h / 10)

try:
    if case in ("a0_png", "a0_pdf"):
        f.size(2384, 3370); art(f.width, f.height)   # A0, 841 x 1189 mm, in points: "A0" is not a named page
        if case == "a0_png":
            f.save(os.path.join(outdir, "a0.png"), dpi=300)
        else:
            f.save(os.path.join(outdir, "a0.pdf"))
    elif case == "pdf60":
        f.size("A4"); photo = f.load_image(PHOTO)
        for p in range(60):
            if p: f.new_page()
            art(f.width, f.height, 50); f.image(photo, 40, 40, f.width - 80, (f.width - 80) * 0.75)
        f.save(os.path.join(outdir, "sixty.pdf"))
    elif case in ("gif300", "mp4300"):
        f.size(1920, 1080)
        state = {"started": False}
        def draw():
            if not state["started"]:
                state["started"] = True
                (f.save_gif if case == "gif300" else f.save_movie)(os.path.join(outdir, case + (".gif" if case == "gif300" else ".mp4")), 10)
            art(1920, 1080, 60)
        # 30 fps x 10 s = 300 frames; run a few more so the recording finishes
        api.active_sketch().run_namespace({"draw": draw}, fps=30, max_frames=310)
    for name in os.listdir(outdir):
        if name.startswith(("a0", "sixty", case)):
            extra[name] = os.path.getsize(os.path.join(outdir, name))
except BaseException as e:
    err = f"{type(e).__name__}: {e}"[:400]
rec = {"case": case, "peak_mb": round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024, 1),
       "secs": round(time.monotonic() - t0, 1), "error": err, "files": extra}
with open(out, "a") as fh:
    fh.write(json.dumps(rec) + "\n")
print(rec)
