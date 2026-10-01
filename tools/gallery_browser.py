"""A browser for the Examples Gallery, written in funground itself (S-083).

    python tools/gallery_browser.py

Pictures come from docs/gallery/images/ (build them with ``python tools/make_gallery.py``).

Views
    Grid     every example as a small picture with its title; pick an area on the left.
    Detail   the picture large, the title, the description and the source code.

Mouse
    Click an area, a picture or a button. The wheel scrolls the grid or the code.

Keys
    Left / Right    previous / next example (in the current area)
    Enter           run the example in its own window
    Backspace       back to the grid
    / or f          filter the grid by part of a title (Enter keeps it, Backspace clears it)
    Up / Down       scroll
    Escape          quit (funground always ends a sketch on Escape)

Run starts the example as its own program, in a temporary folder, so any file it saves
stays out of the repository. Those windows keep running if you close the browser.
"""
from __future__ import annotations

import importlib.util
import math
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

import funground as f

ROOT = Path(__file__).resolve().parent.parent
FONT_FILE = ROOT / "examples" / "gallery" / "text" / "fonts" / "DejaVuSansMono.ttf"


def _load_gallery_tool():
    spec = importlib.util.spec_from_file_location("make_gallery", ROOT / "tools" / "make_gallery.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gallery = _load_gallery_tool()
IMAGES_DIR = gallery.IMAGES

# ---- look
W, H = 1100, 720
BG = (248, 247, 243)
SIDE_TOP, SIDE_BOTTOM = (240, 238, 232), (226, 229, 237)
INK = (38, 42, 50)
MUTED = (112, 117, 128)
ACCENT = (44, 106, 196)
ACCENT_SOFT = (219, 230, 247)
CARD = (255, 255, 255)
LINE = (216, 216, 210)
GREY = (226, 226, 222)
PAPER = (253, 253, 251)
DISABLED = (190, 192, 196)

MISSING = "no picture yet — run tools/make_gallery.py"
STALE = "picture from the last gallery build"
STILL = "A still picture: press Run to see it move."

# ---- layout (all in window pixels; pure functions, so tests can aim clicks)
SIDE_W = 240
ROW_H = 31
AREA_TOP = 92
GX, GY = 264, 88                  # top-left of the grid viewport
GRID_BOTTOM = H - 34
COLS, CARD_W, CARD_H, GAP = 3, 252, 212, 16
THUMB_W, THUMB_H = 236, 148
PIC_W, PIC_H = 384, 240           # the large picture in the detail view
CODE_BOX = (264, 360, 812, 326)   # x, y, width, height of the code panel
CODE_PAD = 14
CODE_SIZE, CODE_LEADING = 14, 19
BUTTONS = {                       # detail-view buttons: x, y, width, height
    "back": (264, 24, 90, 36),
    "previous": (366, 24, 110, 36),
    "next": (488, 24, 90, 36),
    "run": (966, 24, 110, 36),
}
WHEEL_STEP = 48


def area_rect(i: int) -> tuple[int, int, int, int]:
    return (14, AREA_TOP + i * ROW_H, SIDE_W - 28, ROW_H - 3)


def card_rect(i: int, scroll: float = 0.0) -> tuple[float, float, int, int]:
    col, row = i % COLS, i // COLS
    return (GX + col * (CARD_W + GAP), GY + row * (CARD_H + GAP) - scroll, CARD_W, CARD_H)


def inside(x: float, y: float, rect) -> bool:
    rx, ry, rw, rh = rect
    return rx <= x < rx + rw and ry <= y < ry + rh


def grid_viewport() -> tuple[int, int, int, int]:
    return (GX - 8, GY - 12, W - GX, GRID_BOTTOM - GY + 12)


# ---- data
@dataclass
class Entry:
    path: Path
    area: str
    ident: str
    title: str
    description: str
    time_dependent: bool
    source: str
    image: object = None            # a picture from f.load_image, or None when it is missing
    thumb: object = None            # the small copy made once in setup


@dataclass
class Browser:
    entries: list[Entry]
    areas: list[tuple[str | None, str, int]]          # (key, title, count); key None = All
    mono: object = None
    view: str = "grid"
    area: str | None = None
    entry: Entry | None = None
    filter: str = ""
    typing: bool = False
    grid_scroll: float = 0.0
    code_scroll: float = 0.0
    status: tuple[str, int] = ("", 0)
    running: dict = field(default_factory=dict)
    scratch: Path | None = None

    # ---- queries
    def visible(self) -> list[Entry]:
        words = self.filter.strip().lower()
        return [e for e in self.entries
                if (self.area is None or e.area == self.area) and words in e.title.lower()]

    def position(self) -> int:
        shown = self.visible()
        return shown.index(self.entry) if self.entry in shown else 0

    def area_title(self) -> str:
        return next(title for key, title, _ in self.areas if key == self.area)

    def is_running(self, entry: Entry) -> bool:
        proc = self.running.get(entry.path)
        return proc is not None and proc.poll() is None

    def grid_height(self) -> float:
        rows = math.ceil(len(self.visible()) / COLS)
        return max(0, rows * (CARD_H + GAP) - GAP)

    def max_grid_scroll(self) -> float:
        return max(0.0, self.grid_height() - (GRID_BOTTOM - GY))

    def code_lines(self, entry: Entry) -> int:
        chars = max(1, int((CODE_BOX[2] - 2 * CODE_PAD) / self._char_width()))
        return sum(max(1, math.ceil(len(line) / chars)) for line in entry.source.splitlines())

    def max_code_scroll(self) -> float:
        need = self.code_lines(self.entry) * CODE_LEADING
        return max(0.0, need - (CODE_BOX[3] - 2 * CODE_PAD))

    def _char_width(self) -> float:
        return CODE_SIZE * 0.602              # DejaVu Sans Mono: every letter is 0.602 em wide

    # ---- actions
    def choose_area(self, key: str | None) -> None:
        self.area, self.view, self.entry = key, "grid", None
        self.grid_scroll = 0.0

    def open(self, entry: Entry) -> None:
        self.view, self.entry, self.code_scroll = "detail", entry, 0.0

    def back(self) -> None:
        self.view, self.entry = "grid", None
        self.grid_scroll = min(self.grid_scroll, self.max_grid_scroll())

    def step(self, direction: int) -> None:
        shown = self.visible()
        target = self.position() + direction
        if self.view == "detail" and 0 <= target < len(shown):
            self.open(shown[target])

    def run_entry(self, frame: int) -> None:
        """Start the example in its own process, in a scratch folder; never twice at once."""
        entry = self.entry
        if entry is None:
            return
        if self.is_running(entry):
            self.status = ("Already running — look for its window.", frame + 150)
            return
        if self.scratch is None:
            self.scratch = Path(tempfile.mkdtemp(prefix="funground-gallery-"))
        try:
            self.running[entry.path] = subprocess.Popen([sys.executable, str(entry.path)], cwd=str(self.scratch))
        except OSError as problem:
            self.status = (f"Could not start it: {problem}", frame + 240)
            return
        self.status = (f"Started: {entry.title}", frame + 150)

    # ---- input
    def click(self, x: float, y: float, frame: int = 0) -> None:
        for i, (key, _, _) in enumerate(self.areas):
            if inside(x, y, area_rect(i)):
                self.choose_area(key)
                return
        if self.view == "grid":
            if inside(x, y, grid_viewport()):
                for i, entry in enumerate(self.visible()):
                    if inside(x, y, card_rect(i, self.grid_scroll)):
                        self.open(entry)
                        return
            return
        for name, rect in BUTTONS.items():
            if inside(x, y, rect) and self.button_enabled(name):
                {"back": self.back, "previous": lambda: self.step(-1), "next": lambda: self.step(1),
                 "run": lambda: self.run_entry(frame)}[name]()
                return

    def button_enabled(self, name: str) -> bool:
        if name == "previous":
            return self.position() > 0
        if name == "next":
            return self.position() < len(self.visible()) - 1
        return True

    def wheel(self, delta: float) -> None:
        if self.view == "grid":
            self.grid_scroll = min(max(0.0, self.grid_scroll + delta * WHEEL_STEP), self.max_grid_scroll())
        else:
            self.code_scroll = min(max(0.0, self.code_scroll + delta * WHEEL_STEP), self.max_code_scroll())

    def key(self, name: str, frame: int = 0) -> None:
        if self.typing:
            if name == "enter":
                self.typing = False
            elif name == "backspace":
                if self.filter:
                    self.filter = self.filter[:-1]
                else:
                    self.typing = False
            elif len(name) == 1:
                self.filter += name
            elif name == "space":
                self.filter += " "
            self.grid_scroll = 0.0
            return
        if name == "backspace":
            if self.view == "detail":
                self.back()
            elif self.filter:
                self.filter, self.grid_scroll = "", 0.0
        elif self.view == "grid" and name in ("/", "f"):
            self.view, self.typing = "grid", True
        elif name == "left":
            self.step(-1)
        elif name == "right":
            self.step(1)
        elif name == "enter":
            self.run_entry(frame)
        elif name in ("up", "down"):
            self.wheel(-1 if name == "up" else 1)

    # ---- drawing
    def draw(self) -> None:
        f.background(BG)
        (self.draw_grid if self.view == "grid" else self.draw_detail)()
        self.draw_sidebar()
        self.draw_help()
        f.cursor("hand" if self.hovering() else "arrow")

    def hovering(self) -> bool:
        x, y = f.mouse_x, f.mouse_y
        if any(inside(x, y, area_rect(i)) for i in range(len(self.areas))):
            return True
        if self.view == "grid":
            return inside(x, y, grid_viewport()) and self.card_at(x, y) is not None
        return any(inside(x, y, r) and self.button_enabled(n) for n, r in BUTTONS.items())

    def card_at(self, x: float, y: float) -> int | None:
        for i in range(len(self.visible())):
            if inside(x, y, card_rect(i, self.grid_scroll)):
                return i
        return None

    def draw_sidebar(self) -> None:
        f.no_stroke()
        f.fill(f.linear_gradient(0, 0, 0, H, [SIDE_TOP, SIDE_BOTTOM]))
        f.rect(0, 0, SIDE_W, H)
        f.fill(LINE)
        f.rect(SIDE_W - 1, 0, 1, H)
        label("funground", 24, 20, 24, INK, "bold")
        label("Examples gallery", 24, 54, 14, MUTED)
        for i, (key, title, count) in enumerate(self.areas):
            x, y, w, h = area_rect(i)
            chosen = key == self.area
            hover = inside(f.mouse_x, f.mouse_y, (x, y, w, h))
            if chosen or hover:
                f.no_stroke()
                f.fill(ACCENT if chosen else (255, 255, 255))
                f.draw_path(rounded(x, y, w, h, 8))
            label(title, x + 12, y + 6, 15, (255, 255, 255) if chosen else INK)
            label(str(count), x + w - 12, y + 6, 14, (214, 226, 246) if chosen else MUTED, align="right")

    def draw_help(self) -> None:
        f.no_stroke()
        f.fill(BG)
        f.rect(SIDE_W, H - 30, W - SIDE_W, 30)
        if self.typing:
            tip = "Type part of a title     Enter: keep the filter     Backspace: delete     Esc: quit"
        elif self.view == "detail":
            tip = "Left / Right: previous, next     Enter: run     Backspace: back     Wheel: scroll the code     Esc: quit"
        else:
            tip = "Click a picture to open it     Wheel: scroll     / or f: filter     Backspace: clear filter     Esc: quit"
        label(tip, GX, H - 25, 13, MUTED)
        message, until = self.status
        if message and f.frame_count < until:
            label(message, W - 24, H - 25, 13, ACCENT, "bold", align="right")

    def draw_grid(self) -> None:
        shown = self.visible()
        label(self.area_title(), GX, 22, 24, INK, "bold")
        count = f"{len(shown)} example" + ("" if len(shown) == 1 else "s")
        label(count, GX + CARD_W * 3 + GAP * 2, 30, 14, MUTED, align="right")
        if self.typing or self.filter:
            caret = "|" if self.typing and (f.frame_count // 20) % 2 == 0 else ""
            label(f"Filter: {self.filter}{caret}", GX + 330, 30, 15, ACCENT)
        if not shown:
            label("No example matches that.", GX, GY + 20, 16, MUTED)
            return
        with f.saved_state():
            f.clip(rect_path(*grid_viewport()))
            for i, entry in enumerate(shown):
                x, y, w, h = card_rect(i, self.grid_scroll)
                if y + h < GY or y > GRID_BOTTOM:
                    continue
                hover = inside(f.mouse_x, f.mouse_y, grid_viewport()) and inside(f.mouse_x, f.mouse_y, (x, y, w, h))
                self.draw_card(entry, x, y, w, h, hover)

    def draw_card(self, entry: Entry, x: float, y: float, w: int, h: int, hover: bool) -> None:
        with f.saved_state():
            f.shadow(0, 4 if hover else 2, 12 if hover else 6, (30, 40, 70, 46 if hover else 24))
            f.no_stroke()
            f.fill(CARD)
            f.draw_path(rounded(x, y, w, h, 10))
        f.no_fill()
        f.stroke(ACCENT if hover else LINE)
        f.stroke_width(2 if hover else 1)
        f.draw_path(rounded(x, y, w, h, 10))
        f.image(entry.thumb, x + 8, y + 8)
        f.no_fill()
        f.stroke(LINE)
        f.stroke_width(1)
        f.rect(x + 8, y + 8, THUMB_W, THUMB_H)
        text_in_box(entry.title, x + 10, y + THUMB_H + 16, w - 20, 44, 14, INK, "bold" if hover else "normal")

    def draw_detail(self) -> None:
        entry = self.entry
        for name, rect in BUTTONS.items():
            self.draw_button(name, rect)
        shown = self.visible()
        label(f"{self.position() + 1} of {len(shown)}", 590, 33, 14, MUTED)

        px, py = GX, GY
        if entry.image is None:
            draw_placeholder(f, px, py, PIC_W, PIC_H, 15)
        else:
            f.no_stroke()
            f.fill(CARD)
            with f.saved_state():
                f.shadow(0, 3, 10, (30, 40, 70, 40))
                f.rect(px, py, PIC_W, PIC_H)
            f.image(entry.image, px, py, PIC_W, PIC_H)
        note = STILL if not entry.time_dependent else f"{STALE}. {STILL}"
        label(note, px, py + PIC_H + 8, 13, MUTED, "italic")

        tx = px + PIC_W + 28
        tw = W - 24 - tx
        text_in_box(entry.title, tx, GY - 2, tw, 64, 24, INK, "bold", leading=29)
        text_in_box(entry.description, tx, GY + 68, tw, 150, 15, INK)
        label(entry.path.relative_to(ROOT).as_posix(), tx, GY + PIC_H - 18, 13, MUTED)
        self.draw_code(entry)

    def draw_button(self, name: str, rect) -> None:
        x, y, w, h = rect
        enabled = self.button_enabled(name)
        hover = enabled and inside(f.mouse_x, f.mouse_y, rect)
        main = name == "run"
        if main and self.entry and self.is_running(self.entry):
            text = "Running"
        else:
            text = name.capitalize()
        with f.saved_state():
            if enabled:
                f.shadow(0, 2, 5, (30, 40, 70, 30))
            f.no_stroke()
            f.fill(ACCENT if main else CARD)
            if hover:
                f.fill(ACCENT_SOFT if not main else (30, 86, 170))
            f.draw_path(rounded(x, y, w, h, 8))
        f.no_fill()
        f.stroke(ACCENT if main else LINE)
        f.stroke_width(1)
        f.draw_path(rounded(x, y, w, h, 8))
        color = (255, 255, 255) if main else (INK if enabled else DISABLED)
        if hover and not main:
            color = ACCENT
        label(text, x + w / 2, y + 9, 15, color, "bold" if main else "normal", align="center")

    def draw_code(self, entry: Entry) -> None:
        x, y, w, h = CODE_BOX
        with f.saved_state():
            f.shadow(0, 3, 10, (30, 40, 70, 28))
            f.no_stroke()
            f.fill(PAPER)
            f.draw_path(rounded(x, y, w, h, 10))
        f.no_fill()
        f.stroke(LINE)
        f.stroke_width(1)
        f.draw_path(rounded(x, y, w, h, 10))
        with f.saved_state():
            f.clip(rect_path(x + 4, y + 6, w - 8, h - 12))
            f.no_stroke()
            if self.mono is not None:
                f.text_font(self.mono)
            f.text_size(CODE_SIZE)
            f.text_style("normal")
            f.text_leading(CODE_LEADING)
            f.text_align("left", "top")
            f.text_box(keep_spaces(entry.source), x + CODE_PAD, y + CODE_PAD - self.code_scroll,
                       w - 2 * CODE_PAD, None, INK)
            f.text_font(None)
            f.text_leading(None)
        top = self.max_code_scroll()
        if top > 0:                                   # a slim scroll bar
            track = h - 2 * CODE_PAD
            bar = max(24.0, track * track / (track + top))
            f.no_stroke()
            f.fill(GREY)
            f.draw_path(rounded(x + w - 9, y + CODE_PAD + (track - bar) * self.code_scroll / top, 5, bar, 2.5))


# ---- drawing helpers (work on the window `f` or on a picture)
def label(message: str, x: float, y: float, size: float, color, style: str = "normal", align: str = "left") -> None:
    f.no_stroke()
    f.text_size(size)
    f.text_style(style)
    f.text_align(align, "top")
    f.text(message, x, y, color)
    f.text_style("normal")


def text_in_box(message: str, x: float, y: float, w: float, h: float, size: float, color,
                style: str = "normal", leading: float | None = None) -> None:
    f.no_stroke()
    f.text_size(size)
    f.text_style(style)
    f.text_leading(leading)
    f.text_align("left", "top")
    f.text_box(message, x, y, w, h, color)
    f.text_style("normal")
    f.text_leading(None)


def keep_spaces(code: str) -> str:
    """text_box() wraps words and squeezes spaces; no-break spaces keep the indentation."""
    nbsp = chr(0xA0)
    lines = []
    for line in code.splitlines():
        body = line.lstrip(" ")
        indent = nbsp * (len(line) - len(body))
        lines.append(indent + re.sub(r" {2,}", lambda m: nbsp * (len(m.group()) - 1) + " ", body))
    return chr(10).join(lines)


def rect_path(x: float, y: float, w: float, h: float):
    return f.path().move_to(x, y).line_to(x + w, y).line_to(x + w, y + h).line_to(x, y + h).close()


def rounded(x: float, y: float, w: float, h: float, r: float):
    return (f.path().move_to(x + r, y).line_to(x + w - r, y).quad_to(x + w, y, x + w, y + r)
            .line_to(x + w, y + h - r).quad_to(x + w, y + h, x + w - r, y + h)
            .line_to(x + r, y + h).quad_to(x, y + h, x, y + h - r)
            .line_to(x, y + r).quad_to(x, y, x + r, y).close())


def draw_placeholder(g, x: float, y: float, w: float, h: float, size: float) -> None:
    """A grey box with a hint, for an example whose picture has not been built yet."""
    g.no_stroke()
    g.fill(GREY)
    g.rect(x, y, w, h)
    g.fill(MUTED)
    g.text_size(size)
    g.text_style("normal")
    g.text_align("center", "center")
    g.text_box(MISSING, x + 12, y, w - 24, h, MUTED)
    g.text_align("left", "top")


def make_thumbnail(image):
    """Scale a picture down once, into its own small picture (not every frame)."""
    thumb = f.create_graphics(THUMB_W, THUMB_H)
    if image is None:
        draw_placeholder(thumb, 0, 0, THUMB_W, THUMB_H, 14)
        return thumb
    thumb.background(GREY)
    scale = min(THUMB_W / image.width, THUMB_H / image.height)
    w, h = image.width * scale, image.height * scale
    thumb.image(image, (THUMB_W - w) / 2, (THUMB_H - h) / 2, w, h)
    return thumb


def load_entries() -> list[Entry]:
    entries = []
    for path in gallery.examples():
        title, description = gallery.title_and_description(path)
        ident = gallery.example_id(path)
        picture = IMAGES_DIR / f"{ident}.png"
        try:
            image = f.load_image(str(picture)) if picture.exists() else None
        except Exception:            # an unreadable file is shown like a missing one
            image = None
        entries.append(Entry(path, path.parent.name, ident, title, description,
                             gallery.is_time_dependent(path), path.read_text(encoding="utf-8"),
                             image, make_thumbnail(image)))
    return entries


def list_areas(entries: list[Entry]) -> list[tuple[str | None, str, int]]:
    keys = sorted({e.area for e in entries}, key=lambda a: (gallery.area_rank(a), a))
    areas: list[tuple[str | None, str, int]] = [(None, "All", len(entries))]
    for key in keys:
        areas.append((key, gallery.AREAS.get(key, key.title()), sum(e.area == key for e in entries)))
    return areas


# ---- the sketch
app: Browser | None = None


def setup():
    global app
    f.size(W, H, title="funground gallery", fps=60)
    entries = load_entries()
    app = Browser(entries, list_areas(entries))
    if FONT_FILE.exists():
        app.mono = f.load_font(str(FONT_FILE))


def draw():
    app.draw()


def mouse_pressed():
    if f.mouse_button == "left":
        app.click(f.mouse_x, f.mouse_y, f.frame_count)


def mouse_wheel(delta):
    app.wheel(delta)


def key_pressed():
    app.key(f.key, f.frame_count)


if __name__ == "__main__":
    f.run()
