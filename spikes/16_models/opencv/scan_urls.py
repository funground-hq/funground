"""List URLs and telemetry-like words in the binaries and Python files of a package folder. Usage: scan_urls.py DIR"""
import os, re, sys
URL = re.compile(rb"https?://[A-Za-z0-9._~:/?#\[\]@!$&'()*+,;=%-]{4,200}")
WORDS = re.compile(rb"googleapis|clearcut|telemetry|analytics|sentry|usage[_ ]?log|crash[_ ]?report|phone[_ ]?home", re.I)
urls, words, n = {}, {}, 0
for root, _, files in os.walk(sys.argv[1]):
    for f in files:
        p = os.path.join(root, f)
        if f.endswith((".pyc", ".onnx", ".jpg", ".png")) or os.path.getsize(p) > 200e6:
            continue
        data = open(p, "rb").read(); n += 1
        for m in URL.findall(data):
            urls.setdefault(m.decode(), set()).add(f)
        for m in WORDS.findall(data):
            words.setdefault(m.decode().lower(), set()).add(f)
print("files scanned:", n)
print("words:", {k: sorted(v) for k, v in words.items()})
for u in sorted(urls):
    print(u, sorted(urls[u])[:3])
