"""S-225 spike: measure the built chapter. Writes out/measurements.md and prints it.

    .venv/Scripts/python.exe spikes/15_book/make/measure.py     (after build.py)
"""
import json
import math
import os
import re
import sys
import warnings

warnings.simplefilter("ignore")
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
sys.path.insert(0, HERE)
LINE, TOP = 15, 36
RSWOP = r"C:\Windows\System32\spool\drivers\color\RSWOP.icm"     # read only: the profile spikes/11_cmyk measured with
TOKENS = {  # tokens.json, day values
    "paper (oldlace)": "#fdf5e6", "paper-code": "#fffaf0", "dot": "#e6d8bd", "ink (midnightblue)": "#191970",
    "ink-muted": "#5a4f7a", "tomato": "#ff6347", "gold": "#ffd700", "hotpink": "#ff69b4", "turquoise": "#40e0d0",
    "teal": "#008080", "orchid (code keyword)": "#9932cc", "link / code-string (firebrick)": "#b22222",
    "code-number": "#00706b", "code-comment": "#6b6380",
}
out = []


def say(line=""):
    out.append(line)
    print(line)


def table(head, rows):
    say("| " + " | ".join(head) + " |")
    say("|" + "---|" * len(head))
    for r in rows:
        say("| " + " | ".join(str(c) for c in r) + " |")
    say()


def lines_of(path):
    with open(path, encoding="utf-8") as fh:
        return sum(1 for _ in fh)


def grid_check(rep):
    bad, checked, exempt, nudges = [], 0, [], {}
    for p in rep["placed"]:
        if p["kind"].startswith("full-bleed"):
            exempt.append(p["kind"])
            continue
        ys = [("top", p["y"] - p["nudge"])]
        if p["bottom"] is not None:
            ys.append(("bottom", p["bottom"] - p["nudge"]))
        for which, y in ys:
            checked += 1
            if abs(((y - TOP) / LINE) - round((y - TOP) / LINE)) > 1e-9:
                bad.append((p["page"], p["kind"], which, y))
        if p["nudge"]:
            nudges.setdefault(p["kind"], set()).add(p["nudge"])
    return checked, bad, exempt, nudges


def delta_e_2000(l1, l2):
    L1, a1, b1 = l1
    L2, a2, b2 = l2
    C1, C2 = math.hypot(a1, b1), math.hypot(a2, b2)
    Cm = (C1 + C2) / 2
    G = 0.5 * (1 - math.sqrt(Cm ** 7 / (Cm ** 7 + 25 ** 7)))
    a1p, a2p = a1 * (1 + G), a2 * (1 + G)
    C1p, C2p = math.hypot(a1p, b1), math.hypot(a2p, b2)
    h1 = math.degrees(math.atan2(b1, a1p)) % 360
    h2 = math.degrees(math.atan2(b2, a2p)) % 360
    dL, dC = L2 - L1, C2p - C1p
    dh = h2 - h1
    if C1p * C2p == 0:
        dh = 0
    elif dh > 180:
        dh -= 360
    elif dh < -180:
        dh += 360
    dH = 2 * math.sqrt(C1p * C2p) * math.sin(math.radians(dh / 2))
    Lm, Cpm = (L1 + L2) / 2, (C1p + C2p) / 2
    if C1p * C2p == 0:
        hm = h1 + h2
    elif abs(h1 - h2) <= 180:
        hm = (h1 + h2) / 2
    else:
        hm = (h1 + h2 + 360) / 2 if h1 + h2 < 360 else (h1 + h2 - 360) / 2
    T = (1 - 0.17 * math.cos(math.radians(hm - 30)) + 0.24 * math.cos(math.radians(2 * hm))
         + 0.32 * math.cos(math.radians(3 * hm + 6)) - 0.20 * math.cos(math.radians(4 * hm - 63)))
    dtheta = 30 * math.exp(-(((hm - 275) / 25) ** 2))
    Rc = 2 * math.sqrt(Cpm ** 7 / (Cpm ** 7 + 25 ** 7))
    Sl = 1 + 0.015 * (Lm - 50) ** 2 / math.sqrt(20 + (Lm - 50) ** 2)
    Sc, Sh = 1 + 0.045 * Cpm, 1 + 0.015 * Cpm * T
    Rt = -math.sin(math.radians(2 * dtheta)) * Rc
    return math.sqrt((dL / Sl) ** 2 + (dC / Sc) ** 2 + (dH / Sh) ** 2 + Rt * (dC / Sc) * (dH / Sh))


def font_names(res, found, seen):
    """Walk page resources and Form XObjects for /BaseFont names."""
    res = res.get_object()
    for fobj in (res.get("/Font") or {}).values():
        found.add(str(fobj.get_object().get("/BaseFont")))
    for xobj in (res.get("/XObject") or {}).values():
        xo = xobj.get_object()
        if id(xo) not in seen and xo.get("/Subtype") == "/Form":
            seen.add(id(xo))
            font_names(xo.get("/Resources", {}), found, seen)


def cmyk_delta_e():
    """sRGB -> CMYK (the 11_cmyk ICC route: RSWOP, relative colorimetric, black point compensation) -> back to Lab,
    against the colour's own Lab. Pillow's 8-bit Lab has steps of about 0.4 L and 1 a/b, so read small values loosely."""
    from PIL import Image, ImageCms
    flags = ImageCms.Flags.BLACKPOINTCOMPENSATION
    intent = ImageCms.Intent.RELATIVE_COLORIMETRIC
    srgb, cmyk, lab = ImageCms.createProfile("sRGB"), ImageCms.getOpenProfile(RSWOP), ImageCms.createProfile("LAB")
    to_cmyk = ImageCms.buildTransform(srgb, cmyk, "RGB", "CMYK", renderingIntent=intent, flags=flags)
    back = ImageCms.buildTransform(cmyk, lab, "CMYK", "LAB", renderingIntent=intent, flags=flags)
    orig = ImageCms.buildTransform(srgb, lab, "RGB", "LAB", renderingIntent=intent, flags=flags)
    rows = []
    for name, hexv in TOKENS.items():
        rgb = tuple(int(hexv[i:i + 2], 16) for i in (1, 3, 5))
        px = Image.new("RGB", (1, 1), rgb)
        c = ImageCms.applyTransform(px, to_cmyk)
        L = lambda im: (lambda v: (v[0] * 100 / 255, v[1] - 128, v[2] - 128))(im.getpixel((0, 0)))
        l0, l1 = L(ImageCms.applyTransform(px, orig)), L(ImageCms.applyTransform(c, back))
        de76 = math.dist(l0, l1)
        rows.append((name, hexv, "/".join(str(round(v / 2.55)) for v in c.getpixel((0, 0))), round(de76, 1),
                     round(delta_e_2000(l0, l1), 1)))
    return rows


def main():
    from pypdf import PdfReader
    timing = json.load(open(os.path.join(OUT, "timing.json")))
    say("## 1. Build time and file size")
    say()
    rows = []
    for trim in ("Square", "B5"):
        rep = json.load(open(os.path.join(OUT, f"report_{trim}.json")))
        sizes = [os.path.getsize(os.path.join(OUT, f"chapter_{trim}_{k}.pdf")) for k in ("print", "screen")]
        rows.append((trim, f"{timing[trim]} s", f"{rep['drawn_seconds']} s", f"{sizes[0] / 1024:.0f} KB",
                     f"{sizes[1] / 1024:.0f} KB", rep["pages"]))
    table(["Trim", "Build, whole process", "Of which draw (fonts, pictures, layout)", "Print PDF", "Screen PDF", "Pages"], rows)
    for trim in ("Square", "B5"):
        rep = json.load(open(os.path.join(OUT, f"report_{trim}.json")))
        say(f"{trim} inside the process (seconds): " + ", ".join(f"{k} {v}" for k, v in rep["save_seconds"].items()))
    say()
    say(f"The four sketches run first, one process each: {timing['sketches']} s in all (not in the trim times).")
    say()

    say("## 2. Grid check")
    say()
    rows = []
    for trim in ("Square", "B5"):
        rep = json.load(open(os.path.join(OUT, f"report_{trim}.json")))
        checked, bad, exempt, nudges = grid_check(rep)
        rows.append((trim, len(rep["placed"]), checked, len(bad), "PASS" if not bad else "FAIL: " + str(bad[:3])))
        say(f"{trim}: text area {rep['lines']} lines; canvas side {rep['panel']} pt; "
            f"optical nudges inside a slot: " + ", ".join(f"{k} +{sorted(v)}" for k, v in sorted(nudges.items())) +
            f"; exempt: {sorted(set(exempt))}")
    say()
    table(["Trim", "Items placed", "Vertical positions checked (slot top and bottom, less nudge)", "Off the 15 pt line", "Result"], rows)

    say("## 3. Longest code line against the measure")
    say()
    rows = []
    for trim in ("Square", "B5"):
        rep = json.load(open(os.path.join(OUT, f"report_{trim}.json")))
        worst = max(rep["code"], key=lambda c: c["chars"])
        measure = worst["measure"]
        rows.append((trim, f"{worst['chars']} ({worst['text'].strip()})", measure, "fits" if worst["chars"] <= measure else "TOO LONG"))
    table(["Trim", "Longest line, characters", "Measure, characters (4 columns less the number gutter, at 9.5 pt)", "Result"], rows)

    say("## 4. PDF page boxes (read with pypdf)")
    say()
    rows = []
    for trim in ("Square", "B5"):
        for kind in ("print", "screen"):
            r = PdfReader(os.path.join(OUT, f"chapter_{trim}_{kind}.pdf"))
            boxes = set()
            fonts = set()
            for page in r.pages:
                boxes.add(tuple(f"{n}={[round(float(v), 1) for v in page.get('/' + n, [])]}"
                                for n in ("MediaBox", "TrimBox", "BleedBox")))
                font_names(page.get("/Resources", {}), fonts, set())
            rows.append((f"{trim} {kind}", len(r.pages), "; ".join(sorted(" ".join(b) for b in boxes)),
                         ", ".join(sorted(re.sub(r"^/[A-Z]{6}\+", "", x) for x in fonts))))
    table(["PDF", "Pages", "Boxes on every page (one line per distinct set)", "Fonts in page resources (embedded subsets)"], rows)

    say("## 5. Script length")
    say()
    rows = [(n, lines_of(os.path.join(HERE, n))) for n in ("build.py", "nocoords.py", "run_sketch.py", "measure.py")]
    sk = sum(lines_of(os.path.join(HERE, "sketches", s)) for s in os.listdir(os.path.join(HERE, "sketches")) if s.endswith(".py"))
    rows.append(("sketches/*.py (4 files)", sk))
    table(["File", "Lines"], rows)

    say("## 6. CMYK change of each palette token")
    say()
    say("Route: `spikes/11_cmyk` option d (littleCMS through Pillow, Windows' RSWOP.icm as the press profile, relative "
        "colorimetric with black point compensation). The 11_cmyk scripts print CMYK values only, so the delta-E step "
        "(CMYK back to Lab, against the colour's own Lab, CIE76 and CIEDE2000) is added here. The book PDFs themselves are "
        "still RGB: this measures what the conversion would do to each token.")
    say()
    try:
        table(["Token (day)", "Hex", "CMYK % (C/M/Y/K)", "dE76", "dE2000"], cmyk_delta_e())
    except Exception as exc:                                   # noqa: BLE001
        say(f"SKIPPED: {type(exc).__name__}: {exc}")
    with open(os.path.join(OUT, "measurements.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(out) + "\n")


main()
