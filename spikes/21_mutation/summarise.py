"""Print the score table and every survivor from the results_*.json files (spike 21)."""
import glob
import json
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))
print("| Module | Mutants run | Killed (incl. timeouts) | Timeouts | Survived | Score | Complete |")
print("|---|---|---|---|---|---|---|")
for f in sorted(glob.glob("results_*.json")):
    d = json.load(open(f))
    t = sum(r["status"] == "timeout" for r in d["mutants"])
    print(f"| {d['module']} ({f}) | {d['done']} of {d['sites']} | {d['killed']} | {t} | {d['done'] - d['killed']} | "
          f"{d['score']:.1%} | {'no (partial)' if d['partial'] else 'yes'} |")
print()
for f in sorted(glob.glob("results_*.json")):
    d = json.load(open(f))
    s = [r for r in d["mutants"] if r["status"] == "survived"]
    print(f"## {f}: {len(s)} survivors\n")
    for r in s:
        print(f"- #{r['id']} line {r['line']}: {r['kind']} {r['desc']}")
    print()
