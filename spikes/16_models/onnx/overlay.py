"""Draw points from an ort_*.json (or a web json) on its frame, to check by eye.  python -I overlay.py FRAME.png POINTS.json OUT.png"""
import json, sys
from PIL import Image, ImageDraw
im = Image.open(sys.argv[1]).convert("RGB"); d = ImageDraw.Draw(im)
for i, p in enumerate(json.load(open(sys.argv[2]))["points"] or []):
    d.ellipse([p[0] - 4, p[1] - 4, p[0] + 4, p[1] + 4], outline=(255, 0, 0), width=2)
    d.text((p[0] + 5, p[1] - 5), str(i), fill=(255, 255, 0))
im.save(sys.argv[3])
