"""Print the printable strings in a byte range of the DLL (used to read the embedded mediapipe_log_extension.proto field names).
python -I dll_proto_fields.py DLL START END"""
import re, sys
d = open(sys.argv[1], "rb").read()[int(sys.argv[2]):int(sys.argv[3])]
print(" ".join(m.group().decode() for m in re.finditer(rb"[\x20-\x7e]{4,}", d))[:4000])
