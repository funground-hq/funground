"""Find ASCII and UTF-16LE strings matching a regex in a binary.  python -I wide_strings.py FILE REGEX"""
import re, sys
data = open(sys.argv[1], "rb").read(); pat = sys.argv[2]
seen = set()
for kind, rx in (("ascii", re.compile(rb"[\x20-\x7e]{4,300}")), ("utf16", re.compile(rb"(?:[\x20-\x7e]\x00){4,300}"))):
    for m in rx.finditer(data):
        s = m.group().decode("ascii" if kind == "ascii" else "utf-16-le")
        if re.search(pat, s, re.I) and (kind, s) not in seen:
            seen.add((kind, s)); print(f"{kind:5} {m.start():>10}  {s[:200]}")
