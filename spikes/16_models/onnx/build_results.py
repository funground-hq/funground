"""Collects the per-run JSON files into results.json (points and request lists trimmed).
  python -I build_results.py SCRATCH_ORT_OUT_DIR TELEMETRY_RUNS.jsonl     (run in this folder)"""
import glob, json, os, sys
out_dir, tel = sys.argv[1], sys.argv[2]
here = os.path.dirname(os.path.abspath(__file__))
J = lambda n: json.load(open(os.path.join(here, n)))
desktop = {}
for f in sorted(glob.glob(os.path.join(out_dir, "ort_*.json"))):
    d = json.load(open(f))
    for k in ("points", "vector", "items", "face"): d.pop(k, None)
    desktop[os.path.basename(f)[4:-5]] = d
def web(files):
    rows = []
    for n in files:
        j = J(n)
        for job in j["jobs"]:
            if not job.get("ok"): rows.append({"task": job["task"], "ok": False, "error": job.get("error", "")[:300]}); continue
            r = {k: v for k, v in job["result"].items() if k not in ("last", "resources")}
            r["hosts"] = job["hosts"]
            r["wire_bytes_by_host"] = {}
            for q in job["requests"]:
                h = "ours" if q["url"].startswith("/") else q["url"].split("/")[2] if "://" in q["url"] else "blob"
                r["wire_bytes_by_host"][h] = r["wire_bytes_by_host"].get(h, 0) + (q.get("bytes") or 0)
            r["file"] = n
            rows.append(r)
    return rows
tjs = []
for n in ("tjs_remote.json", "tjs_cdn.json", "tjs_local.json"):
    for job in J(n)["jobs"]:
        r = {"spec": job["spec"], "ok": job["ok"], "hosts": job["hosts"]}
        if job["ok"]: r.update({k: v for k, v in job["result"].items() if k != "resources"})
        else: r["error"] = job["error"][:300]
        r["non_200"] = [(q["url"][:110], q.get("status")) for q in job["requests"] if q.get("status") not in (200, None)]
        r["requests"] = [(q["url"][:130], q.get("status"), q.get("bytes")) for q in job["requests"]]
        tjs.append(r)
res = {"date": "2026-10-28", "chrome": J("web_wasm_t1.json")["chrome"], "ort_web": "1.31.1", "onnxruntime_python": "1.31.1",
       "telemetry_runs": [json.loads(l) for l in open(tel)], "desktop_ort": desktop,
       "web_wasm_1thread": web(["web_wasm_t1.json", "web_wasm_t1_objects.json", "web_wasm_t1_movenet.json", "web_wasm_t1_embed.json", "web_wasm_t1_recheck.json"]),
       "web_wasm_4threads_isolated": web(["web_wasm_t4_iso.json"]), "web_webgpu": web(["web_gpu.json"]),
       "agreement_desktop_vs_web": J("compare_wasm.json"), "embeddings": J("embed_check.json"), "transformers_js": tjs,
       "glue_lines": json.loads(os.popen(f'"{sys.executable}" -I "{os.path.join(here, "count_lines.py")}"').read())}
json.dump(res, open(os.path.join(here, "results.json"), "w"), indent=1)
print("ok", len(json.dumps(res)), "bytes")
