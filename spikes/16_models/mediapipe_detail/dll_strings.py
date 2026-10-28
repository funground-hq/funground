"""List printable strings of the MediaPipe DLL that match logging-related words, with a little context.
python -I dll_strings.py PATH_TO_libmediapipe.dll [regex]"""
import re, sys
data = open(sys.argv[1], "rb").read()
pat = sys.argv[2] if len(sys.argv) > 2 else r"clearcut|play\.googleapis|usage|telemetry|opt.?out|logging_client|log_source|LogSource|analytics|HOSTENV|upload"
rx = re.compile(pat.encode(), re.I)
seen = set()
for m in re.finditer(rb"[\x20-\x7e]{6,300}", data):
    s = m.group().decode()
    if rx.search(m.group()) and s not in seen:
        seen.add(s); print(f"{m.start():>10}  {s[:240]}")
