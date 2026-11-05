"""Spike 19: time per test file and the slowest tests, from a pytest --junitxml file. Usage: timings.py FILE.xml [N]"""
import sys, xml.etree.ElementTree as ET
from collections import defaultdict
cases = list(ET.parse(sys.argv[1]).getroot().iter("testcase"))
n = int(sys.argv[2]) if len(sys.argv) > 2 else 30
per_file, count = defaultdict(float), defaultdict(int)
for c in cases:
    f = c.get("classname", "")
    per_file[f] += float(c.get("time", 0)); count[f] += 1
total = sum(per_file.values())
print(f"{len(cases)} tests, {total:.0f} s in test bodies\n\n| File | Tests | Seconds | Share |\n|---|---:|---:|---:|")
for f, t in sorted(per_file.items(), key=lambda kv: -kv[1])[:25]:
    print(f"| {f} | {count[f]} | {t:.1f} | {100*t/total:.1f}% |")
print(f"\n| Slowest {n} tests | Seconds |\n|---|---:|")
for c in sorted(cases, key=lambda c: -float(c.get("time", 0)))[:n]:
    print(f"| {c.get('classname')}::{c.get('name')} | {float(c.get('time')):.2f} |")
