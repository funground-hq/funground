"""Spike 08, Part 2: compare headless-browser screenshots with the desktop goldens.

    python compare.py            (run from the repo venv: needs pycairo)

For every page/screenshots/<name>.png that has a tests/golden/<name>.png, reports the
fraction of pixels whose RGB differs by more than 8/255 in any channel and the mean
absolute difference, and writes page/screenshots/compare.json.  Two correct renderers
may differ in pixels (PROCESS: "they may not differ in ops"), so this is a plausibility
check, not a golden test.
"""
import json
import os

import cairo

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
SHOTS = os.path.join(HERE, "page", "screenshots")
GOLD = os.path.join(REPO, "tests", "golden")


def rgb(path):
    s = cairo.ImageSurface.create_from_png(path)
    s.flush()
    w, h, stride = s.get_width(), s.get_height(), s.get_stride()
    data = bytes(s.get_data())
    px = []
    for y in range(h):
        row = data[y * stride: y * stride + w * 4]
        px.extend((row[i + 2], row[i + 1], row[i]) for i in range(0, w * 4, 4))   # BGRA -> RGB
    return w, h, px


def compare(name):
    gw, gh, g = rgb(os.path.join(GOLD, name + ".png"))
    sw, sh, s = rgb(os.path.join(SHOTS, name + ".png"))
    if (gw, gh) != (sw, sh):
        return {"name": name, "size_ok": False, "golden": [gw, gh], "shot": [sw, sh]}
    diff = 0
    total = 0
    for a, b in zip(g, s):
        d = abs(a[0] - b[0]) + abs(a[1] - b[1]) + abs(a[2] - b[2])
        total += d
        if max(abs(a[0] - b[0]), abs(a[1] - b[1]), abs(a[2] - b[2])) > 8:
            diff += 1
    n = gw * gh
    return {
        "name": name, "size_ok": True, "size": [gw, gh],
        "pixels_differing_pct": round(100 * diff / n, 3),
        "mean_abs_diff": round(total / (3 * n), 3),
    }


if __name__ == "__main__":
    out = []
    for f in sorted(os.listdir(SHOTS)):
        name, ext = os.path.splitext(f)
        if ext == ".png" and os.path.exists(os.path.join(GOLD, f)):
            r = compare(name)
            out.append(r)
            print(json.dumps(r))
    with open(os.path.join(SHOTS, "compare.json"), "w", encoding="utf8") as fh:
        json.dump(out, fh, indent=2)
