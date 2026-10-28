"""S-231: do desktop onnxruntime and onnxruntime-web agree on the same .onnx file and the same 640 x 480 frame?
  python -I compare.py DESKTOP_DIR(ort_*.json) WEB_JSON [WEB_JSON ...]    prints a JSON list: task, largest and mean point difference in px.
The desktop run is Pillow's bilinear warp, the web run is Chrome's canvas drawImage: the two differ only in how pixels are resampled."""
import json, sys, os
import numpy as np
desk_dir, webs = sys.argv[1], sys.argv[2:]
web = {}
for w in webs:
    for j in json.load(open(w))["jobs"]:
        if j.get("ok") and j["result"]["task"] not in web:
            web[j["result"]["task"]] = j["result"]
rows = []
for task, r in sorted(web.items()):
    d = json.load(open(os.path.join(desk_dir, f"ort_{task}.json")))
    row = {"task": task}
    if d.get("points") and isinstance(r["last"], list) and isinstance(r["last"][0], list):
        a, b = np.array(d["points"])[:, :2], np.array(r["last"])[:, :2]
        e = np.linalg.norm(a - b, axis=1)
        row.update(points=len(e), max_px=round(float(e.max()), 2), mean_px=round(float(e.mean()), 2), worst_point=int(e.argmax()))
    elif task == "yunet" and d.get("face"):
        a = np.array(d["face"][5]); b = np.array(r["last"]["points"])
        e = np.linalg.norm(a - b, axis=1); row.update(points=5, max_px=round(float(e.max()), 2), mean_px=round(float(e.mean()), 2))
    elif task in ("classify",):
        row.update(desktop=d["items"][:3], web=r["last"][:3], same_top5=[x[0] for x in d["items"]] == [x[0] for x in r["last"]],
                   max_prob_diff=round(max(abs(x[1] - y[1]) for x, y in zip(d["items"], r["last"])), 4))
    elif task == "embed":
        # desktop JSON keeps no vector for embed; compared in compare_embed.py
        continue
    elif task == "objects":
        a, b = {(x[0], round(x[1], 1)) for x in d["items"]}, {(x[0], round(x[1], 1)) for x in r["last"]}
        row.update(desktop_n=d["found"], web_n=r["found"], labels_desktop=sorted(x[0] for x in d["items"])[:8], labels_web=sorted(x[0] for x in r["last"])[:8])
    else:
        row.update(desktop_found=d["found"], web_found=r["found"], note="pixel counts (desktop at 640x480, web at model size)")
    rows.append(row)
print(json.dumps(rows, indent=1))
