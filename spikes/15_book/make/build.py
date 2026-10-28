"""S-225 spike: build the test chapter ("One shape", 12 pages) with funground as the layout engine.

    .venv/Scripts/python.exe spikes/15_book/make/build.py [--theme day|night]

With no arguments this runs every sketch (one process each, see run_sketch.py), then builds each trim in its own
process for each theme (`build.py --trim Square --theme day`, and so on) and times them. `--theme` builds one theme only.
Day is the oldlace book. Night is a screen-only version on the site's dark tokens; it has no print PDF.
Output goes to spikes/15_book/make/out/:
    sketch/<name>.png, .svg                the sketches' own pictures
    chapter_<trim>_print.pdf               day only: bleed 3 mm and crop marks
    chapter_<trim>_screen.pdf              day: no bleed, no marks
    chapter_<trim>_screen_night.pdf        night
    spread_<trim>_<n>.png                  both pages of a spread side by side (day)
    spread_<trim>_night_<n>.png            the same for night
    spread_<trim>_night_2b.png             night, spread 2 only, with the sketch drawn on midnightblue (a comparison)
    report_<trim>.json, report_<trim>_night.json     what the grid check and measure.py read

The grid is the dict TRIMS plus LINE and GUT, below. Every vertical position goes through Grid.Y(line).
"""
import glob
import json
import math
import os
import re
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
PY = sys.executable
SKETCHES = ["1_0_opener", "1_1_circle", "1_2_square", "1_3_random"]
VARIANT = "1_1_circle_night"      # the comparison sketch for night spread 2: same code, midnightblue background

# ---------------------------------------------------------------- the grid: a handful of numbers, in one place
LINE = 15            # pt: body 11 on 15, and every vertical distance in the book
GUT = 12             # pt: column gutter
COLS = 6
TRIMS = {            # name -> funground page name and margins (pt)
    "Square": dict(page="Square", inner=48, outer=36, top=36, bottom=54),
    "B5": dict(page="B5", inner=48, outer=36, top=36, bottom=48),
}
BLEED_MM = 3
CHAPTER = "One shape"

# ---------------------------------------------------------------- the themes: every colour the layout uses is in this table
# Day is the print and screen book. Night is a screen-only version on the site's dark tokens (tokens.json, "dark").
THEMES = {
    "day": dict(
        paper="oldlace", paper_hex="#fdf5e6", code_ground="#fffaf0",     # paper, and the ground inside the Predict frame
        ink="#191970", muted="#5a4f7a", on_gold="#191970", frame="#191970",   # frame: the line round a picture
        keyword="#9932cc", string="#b22222", number="#00706b", comment="#6b6380",
        highlight="#fee98a",         # the gold marker behind the changed code lines: gold mixed 40 per cent with oldlace
        tint=0.20,                   # share of the accent in a picture page's ground (the rest is the paper)
        tint_base="#fdf5e6", predict_share=0.10, line_gold="#d9a300",
        highlight_bar=False,
        offset=None,                 # the block behind a picture frame: None means the accent
    ),
    "night": dict(
        paper="#191970", paper_hex="#191970", code_ground="#10104a",
        ink="#fdf5e6", muted="#c4c0e6", on_gold="#191970", frame="#191970",   # navy: the sketch canvas inside is oldlace
        keyword="#ee82ee", string="#ffa07a", number="#40e0d0", comment="#a9a4d6",
        highlight="#3e375f", highlight_bar=True,   # gold mixed 16 per cent with the navy (pale code needs 4.5), and a full gold bar beside it
        tint=0.20, tint_base="#191970", predict_share=0.10, line_gold="#ffd700",
        offset="#05052e",            # the site's sticker shadow on night
    ),
}
THEME = "day"


def set_theme(name):
    """Point the colour names below at one theme's table. Everything else reads them when it draws."""
    global THEME, INK, MUTED, PAPER, PAPER_HEX, WHITEISH, KEYWORD, STRING, NUMBER, COMMENT, HIGHLIGHT, TINT, ON_GOLD
    t = THEMES[name]
    THEME = name
    INK, MUTED, PAPER, PAPER_HEX, WHITEISH = t["ink"], t["muted"], t["paper"], t["paper_hex"], t["code_ground"]
    KEYWORD, STRING, NUMBER, COMMENT = t["keyword"], t["string"], t["number"], t["comment"]
    HIGHLIGHT, TINT, ON_GOLD = t["highlight"], t["tint"], t["on_gold"]
    STATE["ground"] = PAPER_HEX


GOLD, HOTPINK, TURQUOISE = "gold", "hotpink", "turquoise"
ACCENT_HEX = {"tomato": "#ff6347", "gold": "#ffd700", "turquoise": "#40e0d0", "hotpink": "#ff69b4"}
SPREAD_ACCENT = ["tomato", "turquoise", "hotpink", "gold", "tomato", "turquoise"]    # one accent for each spread
KEYWORDS = {"import", "from", "as", "def", "for", "in", "if", "else", "elif", "while", "return", "True", "False", "None"}


def run_all(themes):
    """Orchestrator: sketches, then each trim and theme in its own process (night also builds its comparison spread)."""
    os.makedirs(os.path.join(OUT, "sketch"), exist_ok=True)
    path = os.path.join(OUT, "timing.json")
    timing = json.load(open(path)) if os.path.exists(path) else {}      # keep the other theme numbers
    t0 = time.time()
    for name in SKETCHES + ([VARIANT] if "night" in themes else []):
        subprocess.run([PY, os.path.join(HERE, "run_sketch.py"), os.path.join(HERE, "sketches", name + ".py"),
                        os.path.join(OUT, "sketch")], check=True)
    timing["sketches"] = round(time.time() - t0, 2)
    for theme in themes:
        for trim in TRIMS:
            t0 = time.time()
            subprocess.run([PY, os.path.abspath(__file__), "--trim", trim, "--theme", theme], check=True)
            key = trim if theme == "day" else f"{trim}_night"
            timing[key] = round(time.time() - t0, 2)
            print(f"{key}: {timing[key]} s")
            if theme == "night":
                t0 = time.time()
                subprocess.run([PY, os.path.abspath(__file__), "--trim", trim, "--theme", "night", "--variant"], check=True)
                timing[key + "_2b"] = round(time.time() - t0, 2)
                print(f"{key}_2b: {timing[key + '_2b']} s")
    with open(path, "w") as fh:
        json.dump(timing, fh, indent=1)


# ---------------------------------------------------------------- everything below runs inside one trim's process
if "--trim" in sys.argv:
    os.environ["FUNGROUND_HEADLESS"] = "1"
    sys.path.insert(0, HERE)
    import funground as f


class Grid:
    def __init__(self, name):
        t = TRIMS[name]
        self.name = name
        self.W, self.H = f.page_size(t["page"])
        self.inner, self.outer, self.top, self.bottom = t["inner"], t["outer"], t["top"], t["bottom"]
        self.text_w = self.W - self.inner - self.outer
        self.colw = (self.text_w - (COLS - 1) * GUT) / COLS
        self.lines = int((self.H - self.top - self.bottom) // LINE)
        self.bleed = f.mm(BLEED_MM)

    def x0(self, recto):
        return self.inner if recto else self.outer

    def colx(self, recto, c):
        return self.x0(recto) + c * (self.colw + GUT)

    def span(self, n):
        return n * self.colw + (n - 1) * GUT

    def Y(self, line):
        assert isinstance(line, int), f"a line must be a whole number, got {line!r}"
        return self.top + LINE * line

    def snap(self, width):
        """The largest whole number of lines that fits in width: a picture's square side."""
        return int(width // LINE) * LINE

    def panel(self):
        """The canvas: square, 4 columns wide on Square, 6 on B5, snapped to whole lines (Chapters 1 and 2)."""
        return self.snap(self.span(4 if self.name == "Square" else 6))


PLACED = []      # every vertical position the build uses: (page, kind, y_slot_top, y_slot_bottom, nudge)
NOTES = []       # things the grid cannot hold, with the reason
OVERFLOW = []    # text that did not fit its box
CODE_LINES = []  # (sketch, line text, characters)
TEXTS = []       # (kind, text colour, ground colour): measure.py reads their contrast
STATE = {"page": 0, "wob": 0, "ground": "#fdf5e6", "accent": "tomato"}
set_theme("day")


# ---------------------------------------------------------------- colour maths (the page's accent, tints and shades)
def rgb(hexv):
    return tuple(int(hexv[i:i + 2], 16) for i in (1, 3, 5))


def hexof(c):
    return "#%02x%02x%02x" % tuple(int(round(v)) for v in c)


def mix(a, b, share):
    """share of a, the rest b (both hex)."""
    return hexof([x * share + y * (1 - share) for x, y in zip(rgb(a), rgb(b))])


def luminance(hexv):
    def lin(v):
        v /= 255
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = (lin(v) for v in rgb(hexv))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b):
    la, lb = sorted((luminance(a), luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def accent():
    return ACCENT_HEX[STATE["accent"]]


def line_accent():
    """For thin lines on the paper: gold is too faint on oldlace, so it gets a deeper gold there."""
    return THEMES[THEME]["line_gold"] if STATE["accent"] == "gold" else accent()


def tint(share=None, base=None):
    """The accent mixed into the paper (day) or into the navy (night)."""
    return mix(accent(), base or THEMES[THEME]["tint_base"], TINT if share is None else share)


def shade(on=None):
    """The accent mixed toward the ink until it reads as text (4.5 to 1) on the paper (or on `on`)."""
    on = on or PAPER_HEX
    a = accent()
    for step in range(0, 101, 5):
        c = mix(INK, a, step / 100)
        if contrast(c, on) >= 4.5:
            return c
    return INK


def note_text(kind, color):
    TEXTS.append((kind, color, STATE["ground"]))


def reg(kind, y, bottom=None, nudge=0.0):
    PLACED.append(dict(page=STATE["page"], kind=kind, y=y, bottom=bottom, nudge=nudge))


# ---------------------------------------------------------------- fonts
def load_fonts():
    google = f.CONSTANTS.PROVIDERS.GOOGLE_FONTS
    return dict(
        display=f.load_font("Bricolage Grotesque", provider=google, weight=700),
        body=f.load_font("Atkinson Hyperlegible Next", provider=google, weight=400),
        bold=f.load_font("Atkinson Hyperlegible Next", provider=google, weight=700),
        mono=f.load_font("JetBrains Mono", provider=google, weight=400),
    )


# ---------------------------------------------------------------- small drawing helpers
def text_at(g, message, x, line, font, size, color=None, nudge=0.0, kind="text"):
    """One line of text, its slot starting on `line`. nudge is the small optical offset inside the slot."""
    color = color or INK
    f.push()
    f.text_font(FONTS[font], size)
    f.fill(color)
    f.text_align("left", "top")
    y = g.Y(line)
    f.text(message, x, y + nudge)
    f.pop()
    note_text(kind, color)
    reg(kind, y + nudge, y + LINE + nudge, nudge)       # what was drawn; the check takes the nudge off again


def wrap_count(message, width, font, size):
    """How many lines text_box will make (own count: text_box does not say)."""
    f.push()
    f.text_font(FONTS[font], size)
    n = 0
    for para in str(message).split("\n"):
        line = ""
        n += 1
        for word in para.split(" "):
            trial = (line + " " + word).strip()
            if line and f.text_width(trial) > width:
                n += 1
                line = word
            else:
                line = trial
    f.pop()
    return n


def prose(g, message, line, x, width, font="body", size=11, lead=LINE, color=None, lines=None, kind="prose"):
    """Wrapped, ranged left, no hyphenation. Returns the number of grid lines it takes."""
    color = color or INK
    n = lines or wrap_count(message, width, font, size)
    f.push()
    f.text_font(FONTS[font], size)
    f.text_leading(lead)
    f.text_align("left", "top")
    y = g.Y(line)
    rest = f.text_box(message, x, y, width, n * lead, color)
    f.pop()
    note_text(kind, color)
    if str(rest).strip():
        OVERFLOW.append(dict(page=STATE["page"], kind=kind, text=str(rest)[:40]))
    used = -(-n * lead // LINE)
    reg(kind, y, y + used * LINE)
    if lead % LINE:
        NOTES.append(dict(kind=kind, why=f"leading {lead} is not a multiple of {LINE}: only the first line sits on the grid"))
    return used


def wobble(points, color, width=1.6, amp=1.1, step=6.0, closed=False, fill=None):
    """A hand-drawn line through points (or, with fill=, a filled shape; color None means no outline).
    The wobble is f.noise() with a fixed seed, so every build is the same."""
    pts = list(points)
    segs = list(zip(pts, pts[1:] + ([pts[0]] if closed else [])))
    path = f.path()
    first = True
    for (x1, y1), (x2, y2) in segs:
        d = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
        n = max(2, int(d / step))
        nx, ny = -(y2 - y1) / d, (x2 - x1) / d
        for i in range(n):
            t = i / n
            STATE["wob"] += 1
            w = (f.noise(STATE["wob"] * 0.31, 7.5) - 0.5) * 2 * amp
            px, py = x1 + (x2 - x1) * t + nx * w, y1 + (y2 - y1) * t + ny * w
            if first:
                path.move_to(px, py)
                first = False
            else:
                path.line_to(px, py)
    last = pts[0] if closed else pts[-1]
    path.line_to(*last)
    if closed:
        path.close()
    f.push()
    if fill:
        f.fill(fill)
    else:
        f.no_fill()
    if color:
        f.stroke(color)
        f.stroke_width(width)
        f.stroke_cap("round")
        f.stroke_join("round")
    else:
        f.no_stroke()
    f.draw_path(path)
    f.pop()


def blob_circle(cx, cy, r, fill, amp=2.0, color=None, width=2.0):
    """A hand-drawn filled circle."""
    n = 56
    pts = [(cx + r * math.cos(2 * math.pi * i / n), cy + r * math.sin(2 * math.pi * i / n)) for i in range(n)]
    wobble(pts, color, width, amp=amp, step=r * 0.12 + 2, closed=True, fill=fill)


def blob_square(x, y, side, fill, amp=2.0, color=None, width=2.0, tilt=0.0):
    """A hand-drawn filled square, turned a little by tilt (degrees) about its middle."""
    mx, my, a = x + side / 2, y + side / 2, math.radians(tilt)
    pts = [(mx + (px - mx) * math.cos(a) - (py - my) * math.sin(a), my + (px - mx) * math.sin(a) + (py - my) * math.cos(a))
           for px, py in ((x, y), (x + side, y), (x + side, y + side), (x, y + side))]
    wobble(pts, color, width, amp=amp, step=8, closed=True, fill=fill)


def wobble_rect(x, y, w, h, color, width=1.8):
    wobble([(x, y), (x + w, y), (x + w, y + h), (x, y + h)], color, width, closed=True)


def put_picture(name, x, y, w, h):
    """Place a sketch's PNG so it covers the box (cropped, never stretched)."""
    pic = PICS[name]
    pw, ph = pic.width, pic.height
    if w / h >= pw / ph:
        sw, sh = pw, pw * h / w
    else:
        sw, sh = ph * w / h, ph
    f.image(pic, x, y, w, h, (pw - sw) / 2, (ph - sh) / 2, sw, sh)


# ---------------------------------------------------------------- code colouring
TOKEN = re.compile(r"(?P<comment>#.*)|(?P<string>\"[^\"]*\"|'[^']*')|(?P<number>\b\d+(?:\.\d+)?\b)|(?P<word>[A-Za-z_]\w*)")


def colour_line(src):
    fs = f.FormattedString()
    pos = 0

    def run(text, color):
        fs.append(text, font=FONTS["mono"], size=9.5, color=color)

    for m in TOKEN.finditer(src):
        if m.start() > pos:
            run(src[pos:m.start()], INK)
        kind, text = m.lastgroup, m.group()
        color = {"comment": COMMENT, "string": STRING, "number": NUMBER}.get(kind, INK)
        if kind == "word" and text in KEYWORDS:
            color = KEYWORD
        run(text, color)
        pos = m.end()
    if pos < len(src):
        run(src[pos:], INK)
    return fs


NUMW = 20     # width of the line-number gutter in a code block


def code_block(g, name, source, line0, highlight=(), notes=()):
    """The whole sketch with numbered lines on the verso: code in the inner 4 columns, notes in the outer 2."""
    rows = source.strip("\n").split("\n")
    for kind, color in (("code keyword", KEYWORD), ("code string", STRING), ("code number value", NUMBER),
                        ("code comment", COMMENT), ("code name", INK)):
        note_text(kind, color)
    cx = g.colx(False, 2)
    cw = g.span(4)
    f.push()
    f.text_font(FONTS["mono"], 9.5)
    char_w = f.text_width("0")
    f.pop()
    measure = int((cw - NUMW) // char_w)
    for i, src in enumerate(rows):
        CODE_LINES.append(dict(sketch=name, text=src, chars=len(src), measure=measure))
        n = line0 + i
        if i in highlight:
            STATE["ground"] = HIGHLIGHT
            for kind, color in (("code keyword", KEYWORD), ("code string", STRING), ("code number value", NUMBER),
                                ("code name", INK), ("code number", shade(HIGHLIGHT))):
                note_text(kind + " (highlighted)", color)
            STATE["ground"] = PAPER_HEX
            f.push()
            f.no_stroke()
            f.fill(HIGHLIGHT)
            f.rect(cx - 4, g.Y(n), cw + 4, LINE)
            if THEMES[THEME]["highlight_bar"]:
                f.fill(GOLD)
                f.rect(cx - 4, g.Y(n), 3, LINE)
            f.pop()
            reg("highlight", g.Y(n), g.Y(n) + LINE)
        STATE["ground"] = HIGHLIGHT if i in highlight else PAPER_HEX
        text_at(g, str(i + 1).rjust(2), cx, n, "mono", 8, shade(STATE["ground"]), nudge=3.5, kind="code number")
        STATE["ground"] = PAPER_HEX
        if src.strip():
            f.push()
            f.text_align("left", "top")
            f.text(colour_line(src), cx + NUMW, g.Y(n) + 2.5)
            f.pop()
            reg("code", g.Y(n) + 2.5, g.Y(n) + LINE + 2.5, 2.5)
    # side notes: first line on the code line it explains, pushed down by whole lines when two would touch
    nx, nw = g.colx(False, 0), g.span(2) - 16
    next_free = 0
    for idx, message in notes:
        want = line0 + idx
        top_line = max(want, next_free)
        used = prose(g, message, top_line, nx, nw, size=8.5, lead=11, color=MUTED, kind="side note")
        next_free = top_line + used
        ty = g.Y(top_line) + 6.5
        cy = g.Y(want) + 8
        wobble([(nx + nw + 3, ty), (cx - 3, cy)], shade(), width=1, amp=0.7, step=5)
    return line0 + len(rows)


def folio(g, recto):
    n = STATE["page"] + 1          # the chapter is imagined to start on a verso (page 2)
    label = f"{n}    {CHAPTER}" if not recto else f"{CHAPTER}    {n}"
    f.push()
    f.text_font(FONTS["body"], 8)
    w = f.text_width(label)
    f.pop()
    x = g.x0(False) if not recto else g.W - g.outer - w
    text_at(g, label, x, g.lines + 1, "body", 8, MUTED, nudge=2, kind="folio")
    spots(g, recto, x, w)


def marker(x, y, width, thick=8):
    """A gold marker stroke, like the site's underline: wobbly, a little longer than the words."""
    wobble([(x - 3, y), (x + width + 4, y - 1.5)], "#ffd700", width=thick, amp=1.4, step=9)


def heading(g, message, recto, line=0):
    x = g.x0(recto) if recto else g.colx(False, 2)
    f.push()
    f.text_font(FONTS["display"], 22)
    w = f.text_width(message)
    f.pop()
    y = g.Y(line)
    marker(x, y + 25, w)                      # under the words, drawn first
    f.push()
    f.text_font(FONTS["display"], 22)
    f.fill(INK)
    f.text_align("left", "top")
    f.text(message, x, y)
    f.pop()
    note_text("heading", INK)
    reg("heading 22/30", y, y + 2 * LINE)


def label(g, message, x, line):
    text_at(g, message, x, line, "mono", 8, MUTED, nudge=3, kind="label")


# ---------------------------------------------------------------- colour around the page
def ground(g):
    """A picture page: the spread's accent, lightened, over the whole page and into the bleed."""
    b = g.bleed
    STATE["ground"] = tint()
    f.push()
    f.no_stroke()
    f.fill(STATE["ground"])
    f.rect(-b, -b, g.W + 2 * b, g.H + 2 * b)
    f.pop()


def heading_shape(g, recto, kind):
    """A big hand-drawn shape in the accent, half off the page, beside the heading: never behind its text."""
    col = accent()
    if not recto:                                   # top outer corner of a verso; its right edge stops short of the heading
        right = g.colx(False, 2) - 24
        cx = right * 0.25
        r = right - cx
        if kind == "circle":
            blob_circle(cx, -10, r, col, amp=2.5)
        else:
            side = right + 40
            blob_square(-40, 120 - side, side, col, amp=2.2, tilt=7)
    else:                                           # top outer corner of a recto; stays above the compare strip
        if kind == "circle":
            blob_circle(g.W + 20, -30, 140, col, amp=2.5)
        else:
            blob_square(g.W - 120, -40, 150, col, amp=2.2, tilt=7)


SPOTS = {0: ["c"], 1: ["c"], 2: ["s", "c"], 3: ["s", "S", "L"], 4: ["c", "d", "D"], 5: ["c"]}   # by spread: the lesson in small


def spots(g, recto, fx, fw):
    """A few small hand-wobbled shapes beside the folio, echoing the spread's lesson. Never touching text."""
    y = g.Y(g.lines + 1) + 6.5
    r = 7.5
    items = []
    for code in SPOTS[(STATE["page"] - 1) // 2]:
        size = {"c": 15, "s": 14, "S": 10, "L": 18, "d": 8, "D": 11}[code]
        items.append((code, size))
    x = fx + fw + 20 if not recto else fx - 20
    for code, size in items:
        if recto:
            x -= size
        if code in "sSL":
            blob_square(x, y - size / 2, size, accent(), amp=0.6, tilt=5)
        else:
            blob_circle(x + size / 2, y + (3 if code == "D" else -2 if code == "d" else 0), size / 2, accent(), amp=0.6)
        x = x + size + 9 if not recto else x - 9


# ---------------------------------------------------------------- components
def big_panel(g, recto, name, caption):
    """A sketch panel large, inside the margins with its whole frame (a picture run into the bleed read as cut off)."""
    side = min(g.snap(g.text_w), LINE * (g.lines - 2))
    x = g.x0(recto) + (g.text_w - side) / 2
    y = g.Y(0)
    blob_square(x + 9, y + 9, side, THEMES[THEME]["offset"] or accent(), amp=1.4)   # offset behind the frame: colour around the picture
    put_picture(name, x, y, side, side)
    reg("big panel", y, y + side)
    wobble_rect(x, y, side, side, THEMES[THEME]["frame"], 1.6)
    label(g, caption, x, side // LINE + 1)


def predict_frame(g, recto, x, line):
    side = g.panel()
    y = g.Y(line)
    wobble([(x, y), (x + side, y), (x + side, y + side), (x, y + side)], accent(), 2.4, closed=True,
           fill=mix(accent(), WHITEISH, THEMES[THEME]["predict_share"]), step=6)
    reg("predict frame", g.Y(line), g.Y(line) + side)
    return line + side // LINE


def small_panel(g, name, x, line, side):
    put_picture(name, x, g.Y(line), side, side)
    reg("small panel", g.Y(line), g.Y(line) + side)
    wobble_rect(x, g.Y(line), side, side, THEMES[THEME]["frame"], 1.4)
    return line + side // LINE


def compare_strip(g, recto, line, study, param, values, fmt):
    """3 panels of 2 columns, made with f.variations: the same size, one value changed, each labelled."""
    side = g.snap(g.span(2))
    with f.mark():                            # variations also draws its own sheet: record it and throw it away
        results = f.variations(study, **{param: values})
    k = side / 600
    for i, (vals, mark) in enumerate(results):
        x = g.colx(recto, i * 2)
        y = g.Y(line)
        f.push()
        f.clip(f.path().rect(x, y, side, side))
        f.translate(x, y)
        f.scale(k)
        mark.place(0, 0)
        f.pop()
        wobble_rect(x, y, side, side, line_accent(), 2.0)
        reg("compare panel", y, y + side)
        label(g, fmt(vals[param]), x, line + side // LINE)
    return line + side // LINE + 1


def try_this(g, recto, line, title, task):
    x, w = g.x0(recto) + 6, g.span(4) - 12
    STATE["ground"] = ACCENT_HEX["gold"]
    f.push()
    f.no_stroke()
    f.fill(GOLD)
    f.rect(x - 14, g.Y(line), w + 28, 4 * LINE)
    f.pop()
    reg("try this block", g.Y(line), g.Y(line) + 4 * LINE)
    text_at(g, title, x, line, "bold", 11, ON_GOLD, nudge=1.5, kind="try this title")
    prose(g, task, line + 1, x, w, lines=3, color=ON_GOLD, kind="try this text")
    STATE["ground"] = PAPER_HEX


# ---------------------------------------------------------------- the chapter
def sketch_source(name):
    with open(os.path.join(HERE, "sketches", name + ".py"), encoding="utf-8") as fh:
        return fh.read().rstrip()


CIRCLE = "1_1_circle"            # the sketch on spread 2; the night comparison swaps in VARIANT
CODE_CIRCLE = sketch_source(CIRCLE)
CODE_SQUARE = sketch_source("1_2_square")
CODE_RANDOM = sketch_source("1_3_random")


def study_square(size):
    f.no_stroke()
    f.fill(TURQUOISE)
    f.square(300 - size / 2, 300 - size / 2, size)
    f.fill("tomato")
    f.circle(300, 300, 200)


def study_seed(seed):
    f.random_seed(seed)
    f.no_stroke()
    for color in ("tomato", "gold", "turquoise"):
        f.fill(color)
        f.circle(f.random(600), f.random(600), 80)


def page_opener_left(g):
    b = g.bleed
    put_picture("1_0_opener", -b, -b, g.W + 2 * b, g.H + 2 * b)
    reg("full-bleed picture (top at the bleed edge)", g.H, g.H)       # bottom is the bleed edge: no line to check


def page_opener_right(g):
    x, w = g.x0(True), g.span(4)
    blob_circle(g.W + 20, -20, 175 if g.name == "Square" else 150, ACCENT_HEX["tomato"], amp=3.0)   # echoes the cover
    blob_circle(g.x0(True) + 12, g.Y(g.lines - 4), 11, ACCENT_HEX["gold"], amp=0.8)
    blob_circle(g.x0(True) + 40, g.Y(g.lines - 3) + 4, 7, ACCENT_HEX["turquoise"], amp=0.6)
    label(g, "Chapter 1", x, 2)
    f.push()
    f.text_font(FONTS["display"], 48)
    tw = f.text_width(CHAPTER)
    f.pop()
    marker(x - 2, g.Y(3) + 52, tw, thick=13)
    f.push()
    f.text_font(FONTS["display"], 48)
    f.fill(INK)
    f.text_align("left", "top")
    f.text(CHAPTER, x - 2, g.Y(3))
    f.pop()
    note_text("chapter title", INK)
    reg("chapter title 48/60", g.Y(3), g.Y(3) + 4 * LINE)
    prose(g, "Draw a shape. Then change one thing about it, and see what happens.", 8, x, w, lines=3)
    label(g, "In this chapter", x, 13)
    items = [("1.1", "One circle", "4"), ("1.2", "Add a square: predict, then reveal", "6"),
             ("1.3", "Somewhere random", "10"), ("1.4", "Your page", "12")]
    for i, (num, title, page) in enumerate(items):
        line = 14 + i
        text_at(g, num, x, line, "mono", 8, shade(), nudge=3, kind="contents")
        text_at(g, title, x + 28, line, "body", 11, INK, nudge=1.5, kind="contents")
        f.push()
        f.text_font(FONTS["mono"], 8)
        pw = f.text_width("p." + page)
        f.pop()
        text_at(g, "p." + page, x + w - pw, line, "mono", 8, MUTED, nudge=3, kind="contents")


def page_show_verso(g):
    heading_shape(g, False, "circle")
    heading(g, "One circle", False)
    prose(g, "This is a whole sketch. Run it, and a circle appears in the middle of the canvas.", 3,
          g.colx(False, 2), g.span(4), lines=3)
    code_block(g, CIRCLE, CODE_CIRCLE, 7, notes=[
        (2, "The canvas: 600 wide, 600 high."),
        (3, "A colour is a word, in quotes."),
        (4, "No outline: the shape is filled only."),
        (6, "300 across, 300 down: the middle. 200 wide."),
        (7, "Opens the window."),
    ])


def page_show_recto(g):
    ground(g)
    big_panel(g, True, CIRCLE, "1.1 circle.py")


def page_predict_verso(g):
    heading_shape(g, False, "square")
    heading(g, "Add a square", False)
    prose(g, "Two new lines are in gold. Read them. What will the picture look like?", 3,
          g.colx(False, 2), g.span(4), lines=3)
    end = code_block(g, "1_2_square", CODE_SQUARE, 7, highlight=(5, 6))
    side = g.snap(g.span(2))
    x = g.colx(False, 2)
    line = end + 2
    small_panel(g, "1_1_circle", x, line, side)
    label(g, "what you know: 1.1 circle.py", x, line + side // LINE)


def page_predict_recto(g):
    ground(g)
    x = g.x0(True)
    end = predict_frame(g, True, x, 0)
    f.push()
    f.text_font(FONTS["bold"], 11)
    f.fill(INK)
    f.text_align("left", "top")
    f.text("What will change? Draw it.", x, g.Y(end + 1))
    f.pop()
    note_text("predict caption", INK)
    reg("predict caption", g.Y(end + 1), g.Y(end + 2))


def page_reveal_verso(g):
    ground(g)
    big_panel(g, False, "1_2_square", "1.2 square.py")


def page_reveal_recto(g):
    x = g.x0(True)
    heading_shape(g, True, "square")
    heading(g, "Change the size", True)
    prose(g, "The square is 300 wide. Here are three sizes, side by side. Only the size changes.", 3, x, g.span(4), lines=3)
    end = compare_strip(g, True, 7, study_square, "size", [220, 300, 400], lambda v: f"size {v}")
    try_this(g, True, end + 2, "Try this", "Change 300 to 500 in the square. Where does it start now?")


def page_random_verso(g):
    heading_shape(g, False, "circle")
    heading(g, "Somewhere random", False)
    prose(g, "f.random() picks a number, so the circle lands somewhere new. Each call picks its own place.", 3,
          g.colx(False, 2), g.span(4), lines=3)
    end = code_block(g, "1_3_random", CODE_RANDOM, 7, notes=[
        (4, "No outline: fills only."),
        (6, "Any place across, any place down. 80 wide."),
        (8, "Same call. A new place."),
    ])
    label(g, "Compare: three seeds", g.colx(False, 0), end + 1)
    compare_strip(g, False, end + 2, study_seed, "seed", [1, 2, 3], lambda v: f"seed={v}")


def page_random_recto(g):
    ground(g)
    big_panel(g, True, "1_3_random", "1.3 random.py")


def page_your_verso(g):
    heading_shape(g, False, "circle")
    heading(g, "Your page", False)
    prose(g, "Draw any shape. Change its colour, its size, and where it goes. Which change surprised you most?", 3,
          g.colx(False, 2), g.span(4), lines=4)
    side = g.panel()
    x = g.W - g.inner - side
    wobble([(x, g.Y(8)), (x + side, g.Y(8)), (x + side, g.Y(8) + side), (x, g.Y(8) + side)], accent(), 2.4,
           closed=True, fill=tint(0.22), step=6)
    reg("your canvas frame", g.Y(8), g.Y(8) + side)
    end = 8 + side // LINE
    text_at(g, "Your canvas. Draw here, then try it in Play.", x, end + 1, "bold", 11, INK, nudge=1.5, kind="caption")


def page_colophon(g):
    x, w = g.x0(True), g.span(4)
    heading_shape(g, True, "circle")
    heading(g, "Colophon", True)
    fs = f.FormattedString()
    fs.append("Set in ", font=FONTS["body"], size=11)
    fs.append("Bricolage Grotesque", font=FONTS["display"], size=11)
    fs.append(", ", font=FONTS["body"], size=11)
    fs.append("Atkinson Hyperlegible Next", font=FONTS["body"], size=11)
    fs.append(" and ", font=FONTS["body"], size=11)
    fs.append("JetBrains Mono", font=FONTS["mono"], size=10)
    fs.append(". All three are under the SIL Open Font License 1.1, which allows printing and embedding in a PDF.",
              font=FONTS["body"], size=11)
    plain = ("Set in Bricolage Grotesque, Atkinson Hyperlegible Next and JetBrains Mono. All three are under the SIL "
             "Open Font License 1.1, which allows printing and embedding in a PDF.")
    n = wrap_count(plain, w, "body", 11)
    f.push()
    f.text_leading(LINE)
    f.text_align("left", "top")
    f.fill(INK)
    rest = f.text_box(fs, x, g.Y(3), w, (n + 1) * LINE)
    f.pop()
    note_text("colophon fonts", INK)
    if str(rest).strip():
        OVERFLOW.append(dict(page=STATE["page"], kind="colophon fonts", text=str(rest)[:40]))
    reg("prose", g.Y(3), g.Y(3) + (n + 1) * LINE)
    line = 3 + n + 2
    line += prose(g, "The pictures are drawn by the sketches printed in this book. A program ran each one and "
                     "placed its picture beside its code.", line, x, w) + 1
    line += prose(g, "Made with funground. This chapter was laid out by a funground script: the grid, the type, "
                     "the colours and the hand-drawn lines.", line, x, w) + 1
    prose(g, "Paper is oldlace. Ink is midnightblue. The code in this book is CC0.", line, x, w)


PAGES = [  # (function, kind of page; True = recto)
    (page_opener_left, False, "opener"), (page_opener_right, True, "opener"),
    (page_show_verso, False, "show"), (page_show_recto, True, "show"),
    (page_predict_verso, False, "predict"), (page_predict_recto, True, "predict"),
    (page_reveal_verso, False, "reveal"), (page_reveal_recto, True, "reveal"),
    (page_random_verso, False, "show"), (page_random_recto, True, "show"),
    (page_your_verso, False, "your page"), (page_colophon, True, "colophon"),
]


def build_trim(name, theme="day", variant=False):
    """One trim in one theme. variant: only spread 2, with the comparison sketch (night, picture and code), as a PNG."""
    global FONTS, PICS, CIRCLE, CODE_CIRCLE
    t0 = time.time()
    set_theme(theme)
    suffix = "" if theme == "day" else "_night"
    pages = PAGES
    first = 0
    if variant:
        CIRCLE, CODE_CIRCLE = VARIANT, sketch_source(VARIANT)
        first, pages = 2, PAGES[2:4]
    f.size(*f.page_size(TRIMS[name]["page"]))
    g = Grid(name)
    f.noise_seed(11)
    FONTS = load_fonts()
    PICS = {n: f.load_image(os.path.join(OUT, "sketch", n + ".png")) for n in SKETCHES + ([VARIANT] if variant else [])}
    for k, (page, recto, _kind) in enumerate(pages):
        i = first + k
        STATE["page"] = i + 1
        STATE["accent"] = SPREAD_ACCENT[i // 2]
        STATE["ground"] = PAPER_HEX
        if k:
            f.new_page()
        f.background(PAPER)
        page(g)
        if i:
            folio(g, recto)
    drawn = time.time() - t0
    base = os.path.join(OUT, f"chapter_{name}")
    pngdir = os.path.join(OUT, "pages" + suffix + ("_2b" if variant else ""))
    os.makedirs(pngdir, exist_ok=True)
    t1 = t2 = t3 = time.time()
    if not variant:
        if theme == "day":
            f.save(base + "_print.pdf", bleed=g.bleed, marks=True)
            t2 = time.time()
            f.save(base + "_screen.pdf")
        else:
            t2 = time.time()
            f.save(base + "_screen_night.pdf")
        t3 = time.time()
    f.save(os.path.join(pngdir, f"{name}.png"), dpi=800 * 72 / g.W)      # each page 800 px wide: a spread is 1600
    t4 = time.time()
    if variant:
        spreads(name, pngdir, len(pages), f"spread_{name}_night_2b.png")
        return
    spreads(name, pngdir, len(pages), None, f"spread_{name}{suffix}_")
    saves = dict(print_pdf=round(t2 - t1, 2) if theme == "day" else 0, screen_pdf=round(t3 - t2, 2),
                 page_pngs=round(t4 - t3, 2), spreads=round(time.time() - t4, 2))
    report = dict(trim=name, theme=theme, W=g.W, H=g.H, colw=g.colw, lines=g.lines, panel=g.panel(), bleed=g.bleed,
                  drawn_seconds=round(drawn, 2), save_seconds=saves, placed=PLACED, notes=NOTES, overflow=OVERFLOW, code=CODE_LINES,
                  wobble_points=STATE["wob"], pages=len(PAGES), texts=sorted(set(TEXTS)))
    with open(os.path.join(OUT, f"report_{name}{suffix}.json"), "w") as fh:
        json.dump(report, fh, indent=1)


def spreads(name, pngdir, count, single, prefix=None):
    """Put the page PNGs side by side. `single` names the one spread to write (the comparison); else prefix + number."""
    from PIL import Image
    files = sorted(glob.glob(os.path.join(pngdir, f"{name}_*.png")),
                   key=lambda p: int(re.search(r"_(\d+)\.png$", p).group(1)))
    assert len(files) == count, (len(files), files)
    for k in range(0, len(files), 2):
        a, b = Image.open(files[k]).convert("RGB"), Image.open(files[k + 1]).convert("RGB")
        sheet = Image.new("RGB", (a.width + b.width, max(a.height, b.height)), "white")
        sheet.paste(a, (0, 0))
        sheet.paste(b, (a.width, 0))
        sheet.save(os.path.join(OUT, single or f"{prefix}{k // 2 + 1}.png"))


if __name__ == "__main__":
    theme = sys.argv[sys.argv.index("--theme") + 1] if "--theme" in sys.argv else None
    assert theme in (None, "day", "night"), theme
    if "--trim" in sys.argv:
        build_trim(sys.argv[sys.argv.index("--trim") + 1], theme or "day", "--variant" in sys.argv)
    else:
        run_all([theme] if theme else ["day", "night"])
