"""Counts the glue's lines of code (blank lines, comment-only lines and docstrings left out), per piece.  python -I count_lines.py"""
import re, json, os
here = os.path.dirname(os.path.abspath(__file__))
def py_count(path):
    out, cur, doc = {}, "header", False
    for line in open(path, encoding="utf8"):
        s = line.strip()
        if s.startswith("## "): cur = s[3:]; continue
        if doc:
            if s.endswith('"""') or s.endswith("'''"): doc = False
            continue
        if s.startswith('"""') or s.startswith("'''"):
            if not (len(s) > 3 and (s.endswith('"""') or s.endswith("'''"))): doc = True
            continue
        if not s or s.startswith("#"): continue
        out[cur] = out.get(cur, 0) + 1
    return out
def js_count(path):
    out, cur = {}, "header"
    for line in open(path, encoding="utf8"):
        s = line.strip()
        m = re.match(r"(?:export )?(?:async )?(?:function|class) (\w+)|const (\w+) =", line)
        if m and not line.startswith(" "): cur = m.group(1) or m.group(2)
        if not s or s.startswith("//"): continue
        out[cur] = out.get(cur, 0) + 1
    return out
py, js = py_count(os.path.join(here, "ort_glue.py")), js_count(os.path.join(here, "glue_web.js"))
print(json.dumps({"python": {**py, "TOTAL": sum(py.values())}, "javascript": {**js, "TOTAL": sum(js.values())}}, indent=1))
