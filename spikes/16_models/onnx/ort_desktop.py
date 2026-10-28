"""S-231 step 2: time ONNX models on the desktop with onnxruntime (CPU), 640 x 480 frames, 100 timed frames, one task per process.
  python -I ort_desktop.py TASK MODELS_DIR FRAMES_DIR OUT_DIR
TASK: pose pose_tracked hand hand_tracked selfie humanseg yunet movenet movenet_int8 classify classify_int8 objects objects_int8
      embed
'tracked' = the detector ran once and its box is reused (the cost of a tracked frame, like the cv2.dnn 'landmark model only' rows).
Writes OUT_DIR/ort_TASK.json: timings and the points found (so the web run can be compared). Models/frames stay in the scratchpad."""
import json, os, statistics, sys, time
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
task, models, frames, out_dir = sys.argv[1:5]
t_import = time.perf_counter()
import onnxruntime as ort
import ort_glue as g
if os.environ.get("ORT_THREADS"):   # like-for-like with the browser's one wasm thread: ORT_THREADS=1
    _Session, _n = ort.InferenceSession, int(os.environ["ORT_THREADS"])
    def _limited(path, *a, **k):
        o = ort.SessionOptions(); o.intra_op_num_threads = _n; o.inter_op_num_threads = 1
        return _Session(path, sess_options=o, providers=["CPUExecutionProvider"])
    ort.InferenceSession = _limited
M = lambda n: os.path.join(models, n)
img = lambda n: np.asarray(Image.open(os.path.join(frames, n)).convert("RGB"))
labels = lambda n: json.load(open(M(n)))["id2label"]
t0 = time.perf_counter()
base = task.replace("_tracked", "")
if base in ("pose", "hand"):
    cls, d, l, pic = (g.Pose, "zoo_persondet.onnx", "zoo_pose.onnx", "pose.png") if base == "pose" else (g.Hand, "zoo_palm.onnx", "zoo_hand.onnx", "thumb_up.png")
    m, frame = cls(M(d), M(l), ort), img(pic)
    def step():
        if not task.endswith("_tracked") or (m.region if base == "pose" else m.box) is None:
            m.find(frame)
        return m.points(frame)
elif base == "selfie":   m, frame = ort.InferenceSession(M("selfie.onnx")), img("pose.png"); step = lambda: g.selfie(m, frame)
elif base == "humanseg": m, frame = ort.InferenceSession(M("zoo_humanseg.onnx")), img("pose.png"); step = lambda: g.humanseg(m, frame)
elif base == "yunet":    m, frame = ort.InferenceSession(M("zoo_yunet.onnx")), img("portrait.png"); step = lambda: g.yunet(m, frame)
elif base.startswith("movenet"): m, frame = ort.InferenceSession(M(base + ".onnx")), img("pose.png"); step = lambda: g.movenet(m, frame)
elif base.startswith("classify"): 
    m, frame, lab = ort.InferenceSession(M("mnv4%s.onnx" % base[8:])), img("cats.png"), labels("mnv4_config.json"); step = lambda: g.classify(m, frame, lab)
elif base.startswith("objects"):
    m, frame, lab = ort.InferenceSession(M("dfine%s.onnx" % base[7:])), img("city-streets.png"), labels("dfine_config.json"); step = lambda: g.objects(m, frame, lab)
elif base in ("embed", "embed_dino"): m, frame = ort.InferenceSession(M("mnv4.onnx" if base == "embed" else "dino_q8.onnx")), img("cats.png"); step = lambda: g.embed(m, frame)
first = step()
t_first = time.perf_counter() - t0
ms = []
for _ in range(100):
    s = time.perf_counter(); r = step(); ms.append((time.perf_counter() - s) * 1000)
ms.sort()
def found(r):
    if r is None: return {"found": 0}
    if isinstance(r, np.ndarray) and r.dtype == bool: return {"found": int(r.sum()), "unit": "person pixels"}
    if isinstance(r, np.ndarray) and r.ndim == 2 and r.shape == (480, 640): return {"found": int((r > 0.5).sum()), "unit": "person pixels (mask > 0.5)"}
    if isinstance(r, np.ndarray): return {"found": len(r), "unit": "points"}
    if isinstance(r, tuple): return {"found": 1, "unit": "face"}
    return {"found": len(r), "unit": "items"}
res = {"task": task, "onnxruntime": ort.__version__, "import_s": round(t0 - t_import, 3), "first_result_s": round(t_first, 3),
       "median_ms": round(statistics.median(ms), 2), "p90_ms": round(ms[89], 2), "per_second": round(1000 / statistics.mean(ms), 1),
       **found(r), "threads": int(os.environ.get("ORT_THREADS") or os.cpu_count())}
dump = {"vector": r.tolist() if base.startswith("embed") else None, "points": np.asarray(r).tolist() if isinstance(r, np.ndarray) and r.ndim == 2 and r.shape[0] < 100 else None}
if isinstance(r, list): dump["items"] = r[:10]
if isinstance(r, tuple): dump["face"] = [np.asarray(x).tolist() if not isinstance(x, float) else x for x in r]
os.makedirs(out_dir, exist_ok=True)
json.dump({**res, **dump}, open(os.path.join(out_dir, f"ort_{task}" + ("_t%s" % os.environ["ORT_THREADS"] if os.environ.get("ORT_THREADS") else "") + ".json"), "w"))
print(json.dumps(res))
