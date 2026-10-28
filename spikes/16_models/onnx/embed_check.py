"""S-231 step 5: (a) cosine similarity of the same picture's vector on desktop and in the browser, (b) a small sanity check that
the vectors group similar pictures: cats vs cats flipped and darker vs unrelated pictures (desktop, both models).
  python -I embed_check.py DESKTOP_DIR(ort_embed*.json) WEB_JSON MODELS_DIR FRAMES_DIR"""
import json, os, sys
import numpy as np
from PIL import Image, ImageEnhance, ImageOps
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import onnxruntime as ort
import ort_glue as g
desk, web_json, models, frames = sys.argv[1:5]
web = {j["result"]["task"]: j["result"]["last"]["vector"] for j in json.load(open(web_json))["jobs"] if j.get("ok")}
out = {"desktop_vs_web_cosine": {}}
for t in ("embed", "embed_dino"):
    a, b = np.array(json.load(open(os.path.join(desk, f"ort_{t}.json")))["vector"]), np.array(web[t])
    out["desktop_vs_web_cosine"][t] = float(a @ b / np.linalg.norm(a) / np.linalg.norm(b))
load = lambda n: Image.open(os.path.join(frames, n)).convert("RGB")
pics = {"cats": load("cats.png"), "cats_flipped": ImageOps.mirror(load("cats.png")), "cats_darker": ImageEnhance.Brightness(load("cats.png")).enhance(0.6),
        "city": load("city-streets.png"), "yoga": load("pose.png"), "portrait": load("portrait.png")}
for t, f in (("embed", "mnv4.onnx"), ("embed_dino", "dino_q8.onnx")):
    s = ort.InferenceSession(os.path.join(models, f))
    v = {k: g.embed(s, np.asarray(im)) for k, im in pics.items()}
    out[t + "_cosine_to_cats"] = {k: round(float(v["cats"] @ x), 3) for k, x in v.items() if k != "cats"}
print(json.dumps(out, indent=1))
