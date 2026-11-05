"""Print a Markdown table from soak JSONL files, rising sketches first. Usage: table.py FILE.jsonl..."""
import json, sys, os
rows = [json.loads(l) for p in sys.argv[1:] for l in open(p) if l.strip()]
rows.sort(key=lambda r: -(r.get("mb_per_1000_2nd_half") or -1e9))
print("| sketch | frames | secs after warm-up | MB at warm-up | MB at end | MB per 1,000 frames | 2nd half MB/1,000 | error |")
print("|---|---:|---:|---:|---:|---:|---:|---|")
for r in rows:
    name = os.path.relpath(r["sketch"], os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
    print(f"| {name} | {r['frames']} | {r.get('secs')} | {r.get('mb_warm','')} | {r.get('mb_end','')} | "
          f"{r.get('mb_per_1000','')} | {r.get('mb_per_1000_2nd_half','')} | {(r.get('error') or '')[:80]} |")
