"""The Examples Gallery browser, written in funground itself (S-083, S-103).

    python -m funground.gallery           open the browser
    python -m funground.gallery --list    print every example, one per line (no window)

The examples travel inside funground, so this works after a plain install. In a source
checkout it shows the same examples from the repository's own folders.

Views
    Grid     every example as a small picture with its title; pick an area on the left.
    Detail   the picture large, the title, the description and the source code.

Mouse
    Click an area, a picture or a button. The wheel scrolls the grid or the code.

Keys
    Left / Right    previous / next example (in the current area)
    Enter           run the example in its own window
    C               copy the example (and its data files) into the current folder
    O               open the folder where the example saved its files (after you ask, never before)
    Backspace       back to the grid
    / or f          filter the grid by part of a title (Enter keeps it, Backspace clears it)
    Up / Down       scroll
    Escape          quit (funground always ends a sketch on Escape)

Run starts the example as its own program, in a temporary folder, so any file it saves
stays out of the installed package. Those windows keep running if you close the browser.
Each run gets its own folder. When an example saves a file, the browser says where, and
prints the folder to the terminal too. Copy never overwrites: a name that is taken gets _2, _3.

This module is loaded only by ``python -m funground.gallery`` (and the tools that share its
example list); ``import funground`` never imports it.
"""
from __future__ import annotations

import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

import funground as f

# ---- where the examples are
# The one list of areas: display order and titles. An area missing here is listed last, by name.
AREAS = {
    "basics": "Basics",
    "shapes": "Shapes",
    "colour": "Colour",
    "compositing": "Blending, opacity and shadows",
    "lines": "Fill, stroke and lines",
    "curves": "Curves",
    "text": "Text",
    "animation": "Animation and time",
    "motion": "Motion",
    "transforms": "Transforms",
    "paths": "Paths and clipping",
    "randomness": "Randomness and noise",
    "maths": "Useful maths",
    "interaction": "Interaction",
    "saving": "Saving your work",
    "documents": "Documents and pages",
    "images": "Pictures and images",
    "sound": "Sound",
}
TIME_DEPENDENT_MARK = "# gallery: time-dependent"


@dataclass(frozen=True)
class Locations:
    """Where the examples and their pictures are: ``examples`` holds ``<area>/NN_name.py``."""
    examples: Path
    images: Path
    installed: bool = False


def locate(package_dir: Path | None = None) -> Locations:
    """Find the examples and pictures.

    An installed funground has them beside this file (``examples`` and
    ``gallery_images``: the build maps them in, see pyproject.toml). A source checkout does not,
    so we fall back to the repository's own ``examples/gallery`` and ``docs/gallery/images``.
    """
    here = Path(package_dir) if package_dir is not None else Path(__file__).resolve().parent
    packaged = here / "examples"
    if packaged.is_dir():
        return Locations(packaged, here / "gallery_images", installed=True)
    repo = here.parent
    return Locations(repo / "examples" / "gallery", repo / "docs" / "gallery" / "images")


LOCATIONS = locate()
FONT_NAME = "DejaVuSansMono.ttf"


def area_rank(area: str) -> int:
    return list(AREAS).index(area) if area in AREAS else len(AREAS)


def list_examples(examples_dir: Path) -> list[Path]:
    return sorted(examples_dir.glob("*/*.py"), key=lambda p: (area_rank(p.parent.name), p.parent.name, p.name))


def example_id(path: Path) -> str:
    """Stable id used for images, goldens and snapshots: '<area>-<stem>'."""
    return f"{path.parent.name}-{path.stem}"


def is_time_dependent(path: Path) -> bool:
    return TIME_DEPENDENT_MARK in path.read_text(encoding="utf-8")


def title_and_description(path: Path) -> tuple[str, str]:
    """First docstring line is the title; the rest (joined) is the description."""
    source = path.read_text(encoding="utf-8")
    doc = source.split('"""')[1] if source.lstrip().startswith('"""') else ""
    lines = [line.strip() for line in doc.strip().splitlines()]
    title = lines[0] if lines else path.stem
    description = " ".join(line for line in lines[1:] if line)
    return title, description


def data_files(path: Path) -> list[Path]:
    """Files beside an example that its code names (``"data/photo.jpg"``, ``"fonts/x.ttf"``)."""
    found = []
    for name in re.findall(r"""["']([^"'\n]+)["']""", path.read_text(encoding="utf-8")):
        candidate = path.parent / name
        try:
            if candidate.is_file() and candidate != path and candidate not in found:
                found.append(candidate)
        except OSError:
            continue
    return found


def free_name(folder: Path, name: str) -> Path:
    """``folder/name``, or ``name_2``, ``name_3`` ... when that is taken. Never an existing file."""
    target = folder / name
    stem, suffix, n = target.stem, target.suffix, 2
    while target.exists():
        target = folder / f"{stem}_{n}{suffix}"
        n += 1
    return target


def open_in_file_browser(folder: Path) -> None:
    """Show ``folder`` in the system file browser. Called only when the learner asks."""
    if sys.platform == "win32":
        os.startfile(str(folder))                       # noqa: S606
    elif sys.platform == "darwin":
        subprocess.Popen(["open", str(folder)])
    else:
        subprocess.Popen(["xdg-open", str(folder)])


def saved_files(folder: Path) -> list[str]:
    """The names of the files under ``folder`` (folders inside it are shown as sub/name), sorted."""
    if not folder.is_dir():
        return []
    return sorted(p.relative_to(folder).as_posix() for p in folder.rglob("*") if p.is_file())


def saved_message(names: list[str], folder: Path, shown: int = 3) -> str:
    more = f" + {len(names) - shown} more" if len(names) > shown else ""
    return f"Saved: {', '.join(names[:shown])}{more}  →  {folder}"


def copy_example(path: Path, folder: Path) -> tuple[Path, list[Path], list[Path]]:
    """Copy an example and the data files it names into ``folder``.

    The example never overwrites: a taken name becomes ``name_2.py``. Data files keep their
    place (``data/photo.jpg``) because the code names them that way; one that already exists is
    left alone. Returns (the new example, data files written, data files already there).
    """
    folder.mkdir(parents=True, exist_ok=True)
    target = free_name(folder, path.name)
    shutil.copyfile(path, target)
    written, kept = [], []
    for source in data_files(path):
        place = folder / source.relative_to(path.parent)
        if place.exists():
            kept.append(place)
            continue
        place.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, place)
        written.append(place)
    return target, written, kept


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

MISSING = "no picture yet (the gallery pictures are built by tools/make_gallery.py)"
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
    "folder": (730, 24, 106, 36),
    "copy": (848, 24, 106, 36),
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
    run_dirs: dict = field(default_factory=dict)       # example path -> the folder of its latest run
    seen_files: dict = field(default_factory=dict)     # example path -> file names already reported
    finished: set = field(default_factory=set)         # example paths whose last run has had its final look
    copy_dir: Path | None = None                       # where Copy writes; None = the current folder

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
        run_dir = free_name(self.scratch, entry.path.stem)      # a fresh folder for every run
        try:
            run_dir.mkdir(parents=True)
            self.running[entry.path] = subprocess.Popen([sys.executable, str(entry.path)], cwd=str(run_dir))
        except OSError as problem:
            self.status = (f"Could not start it: {problem}", frame + 240)
            return
        self.run_dirs[entry.path] = run_dir
        self.seen_files[entry.path] = []
        self.finished.discard(entry.path)
        self.status = (f"Started: {entry.title}", frame + 150)

    def watch(self, frame: int) -> None:
        """Look for new files in the run folders. Called every frame; cheap, no extra thread."""
        for path, folder in self.run_dirs.items():
            if path in self.finished:
                continue
            names = saved_files(folder)
            if names and names != self.seen_files.get(path):
                self.status = (saved_message(names, folder), frame + 600)
                print(f"Saved in {folder}: {', '.join(names)}", flush=True)
            self.seen_files[path] = names
            proc = self.running.get(path)
            if proc is None or proc.poll() is not None:
                self.finished.add(path)

    def folder_of(self, entry: Entry | None) -> Path | None:
        """The folder of this example's latest run, if it saved anything there."""
        if entry is None:
            return None
        folder = self.run_dirs.get(entry.path)
        return folder if folder is not None and saved_files(folder) else None

    def open_folder(self, frame: int) -> None:
        """Open the saved-files folder of the current example, only when asked."""
        folder = self.folder_of(self.entry)
        if folder is None:
            self.status = ("Nothing saved yet. Run the example first.", frame + 150)
            return
        try:
            open_in_file_browser(folder)
        except OSError as problem:
            self.status = (f"Could not open the folder: {problem}", frame + 300)
            return
        self.status = (f"Opened {folder}", frame + 150)

    def copy_entry(self, frame: int) -> None:
        """Copy the example, and the data files it names, into the current folder. Never overwrites."""
        entry = self.entry
        if entry is None:
            return
        folder = self.copy_dir if self.copy_dir is not None else Path.cwd()
        try:
            target, written, kept = copy_example(entry.path, folder)
        except OSError as problem:
            self.status = (f"Could not copy it: {problem}", frame + 300)
            return
        more = f" + {len(written)} data file{'s' if len(written) != 1 else ''}" if written else ""
        self.status = (f"Copied to {target.parent}: {target.name}{more}", frame + 300)

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
                 "folder": lambda: self.open_folder(frame), "copy": lambda: self.copy_entry(frame), "run": lambda: self.run_entry(frame)}[name]()
                return

    def button_enabled(self, name: str) -> bool:
        if name == "previous":
            return self.position() > 0
        if name == "next":
            return self.position() < len(self.visible()) - 1
        if name == "folder":
            return self.folder_of(self.entry) is not None
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
        elif name == "c" and self.view == "detail":
            self.copy_entry(frame)
        elif name == "o" and self.view == "detail":
            self.open_folder(frame)
        elif name in ("up", "down"):
            self.wheel(-1 if name == "up" else 1)

    # ---- drawing
    def draw(self) -> None:
        self.watch(f.frame_count)
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
            tip = "Left / Right: previous, next     Enter: run     C: copy     O: open saved-files folder     Backspace: back     Esc: quit"
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
        label(f"{entry.area}/{entry.path.name}", tx, GY + PIC_H - 18, 13, MUTED)
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


def load_entries(where: Locations | None = None) -> list[Entry]:
    entries = []
    where = where or LOCATIONS
    for path in list_examples(where.examples):
        title, description = title_and_description(path)
        ident = example_id(path)
        picture = where.images / f"{ident}.png"
        try:
            image = f.load_image(str(picture)) if picture.exists() else None
        except Exception:            # an unreadable file is shown like a missing one
            image = None
        entries.append(Entry(path, path.parent.name, ident, title, description,
                             is_time_dependent(path), path.read_text(encoding="utf-8"),
                             image, make_thumbnail(image)))
    return entries


def list_areas(entries: list[Entry]) -> list[tuple[str | None, str, int]]:
    keys = sorted({e.area for e in entries}, key=lambda a: (area_rank(a), a))
    areas: list[tuple[str | None, str, int]] = [(None, "All", len(entries))]
    for key in keys:
        areas.append((key, AREAS.get(key, key.title()), sum(e.area == key for e in entries)))
    return areas


# ---- the sketch
app: Browser | None = None


def setup():
    global app
    f.size(W, H, title="funground gallery", fps=60)
    entries = load_entries()
    app = Browser(entries, list_areas(entries))
    font = LOCATIONS.examples / "text" / "fonts" / FONT_NAME
    if font.exists():
        app.mono = f.load_font(str(font))


def draw():
    app.draw()


def mouse_pressed():
    if f.mouse_button == "left":
        app.click(f.mouse_x, f.mouse_y, f.frame_count)


def mouse_wheel(delta):
    app.wheel(delta)


def key_pressed():
    app.key(f.key, f.frame_count)


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if "--list" in args:
        for path in list_examples(LOCATIONS.examples):
            print(f"{example_id(path)}  {title_and_description(path)[0]}")
        return 0
    if args:
        print("usage: python -m funground.gallery [--list]")
        return 2
    f.run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
