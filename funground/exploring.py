"""Play: exploring with variations and keeping versions (story S-132 parts 3 and 4, contracts E1 and E2,
decisions D-071 and D-073).

``f.variations(fn, gap=[...])`` draws a labelled contact sheet: one cell for each value (or each pair of
values), each cell ``fn``'s drawing recorded as a Mark and placed scaled into the cell. ``f.keep(note)``
saves the current picture, a copy of the sketch and a JSON record into a ``studio/`` folder.

The module is called ``exploring`` and not ``play`` on purpose: a submodule is set as an attribute of the
package when it is imported, so it must never share a name with a public function (tests/test_play.py).

How variations works:

- **Layout** (built on ``Area`` and ``Grid``). One parameter: one row while the row is readable, that is,
  while every picture in it is at least ``MIN_ROW_PICTURE`` units wide and its label fits on one line under
  it. Otherwise the number of columns that makes the cells largest for the canvas's shape (near-square on a
  square canvas). ``columns=`` overrides both. Two parameters: rows for the first, columns for the second,
  and ``columns=`` is an error. Cells cover ``f.ground.content``, with a small gutter and a label strip
  under each picture.
- **Fit.** Each cell shows the whole ground (the canvas, 0 to width and 0 to height) scaled down by one
  factor for every cell, not each drawing fitted by its own bounds. So a drawing that is wider for gap=60
  than for gap=10 looks wider in its cell, and the cells can be compared. Each picture is clipped to its box.
- **Isolation.** A mark's block starts from the style at the call and no transform, and puts everything back
  when it ends, so one cell's ``fill()`` cannot reach the next one.
- **Seed.** Every cell starts the random generator from the run's seed (``random_seed(n)``, or the one
  funground chose at the start), so cells differ only in the parameter. The generator is put back afterwards.
- **background() in a cell** paints the cell's whole ground instead of raising (a mark has no edges).
- **Labels and frames belong to the sheet.** They are drawn on the canvas, never into the returned marks.

How keep works in an animated sketch: the call reserves the next number and waits for the end of the frame
being drawn (``Sketch._frame_end``). Then it writes the picture, the PDF, the source copy and the record
together, so all of them describe that frame.
"""
from __future__ import annotations

import json
import math
import os
import platform as _platform
import re
import shutil
import sys
from datetime import datetime

from . import marks
from .state import GraphicsState

GUTTER = 10            # space between cells, in canvas units
LABEL_SIZE = 11        # the label's text size
LABEL_STRIP = 16       # the height kept under each picture for its label
LABEL_GAP = 3          # from the picture's bottom edge to the label
MIN_ROW_PICTURE = 100  # one parameter: a row is used while every picture is at least this wide (and labels fit)
FRAME_COLOR = "#9a9a9a"
LABEL_COLOR = "#555555"

# The recorders of variation cells now open: background() inside one paints the cell's ground.
_cells: list = []


# ---------------------------------------------------------------- variations
def _values_of(name: str, values) -> list:
    if isinstance(values, (str, bytes)) or not hasattr(values, "__iter__"):
        raise TypeError(f"f.variations(): {name} needs a list of values to try, such as {name}=[10, 20, 40], "
                        f"not {values!r}")
    out = list(values)
    if not out:
        raise ValueError(f"f.variations(): {name} has no values to try. Give at least one, such as {name}=[10, 20].")
    return out


def _shown(value) -> str:
    if isinstance(value, float):
        return f"{value:g}"
    if isinstance(value, (int, str)):
        return str(value)
    return repr(value)


def label_of(values: dict) -> str:
    """The label of a cell: 'gap = 35', or 'gap = 35, size = 2'."""
    return ", ".join(f"{k} = {_shown(v)}" for k, v in values.items())


def label_width(text: str) -> float:
    """How wide a label is drawn: the default font at LABEL_SIZE."""
    from .typography import effective_font, text_settings, text_width

    state = GraphicsState(text_size=LABEL_SIZE)
    return text_width(text, LABEL_SIZE, effective_font(state), **text_settings(state))


def picture_scale(cell, W: float, H: float) -> float:
    """The scale that fits a W x H ground, with the label strip under it, into *cell* (0 or less: no room)."""
    return min(cell.width / W, (cell.height - LABEL_STRIP) / H)


def _sheet(area, cols: int, rows: int):
    """The sheet's grid, or None when the cells do not fit."""
    try:
        return area.grid(cols, rows, gutter=GUTTER)
    except ValueError:
        return None


def row_is_readable(labels: list[str], area, W: float, H: float) -> bool:
    """One parameter: whether one row of len(labels) cells is readable. Every picture must be at least
    MIN_ROW_PICTURE units wide, and every label must fit on one line under its picture."""
    grid = _sheet(area, len(labels), 1)
    if grid is None:
        return False
    k = picture_scale(grid[0], W, H)
    if k <= 0:
        return False
    width = W * k
    return width >= MIN_ROW_PICTURE and all(label_width(t) <= width for t in labels)


def _best_columns(n: int, area, W: float, H: float) -> int:
    """The number of columns that makes n ground-shaped cells largest in *area* (ties: more columns)."""
    best, best_k = 1, -1.0
    for cols in range(1, n + 1):
        grid = _sheet(area, cols, math.ceil(n / cols))
        if grid is None:
            continue
        k = picture_scale(grid[0], W, H)
        if k > 0 and k >= best_k - 1e-9:
            best, best_k = cols, k
    return best


def layout(combos: list[dict], names: list[str], lists: dict, columns, area, W: float, H: float) -> tuple[int, int]:
    """(cols, rows) of the sheet: see the module docstring."""
    if len(names) == 2:
        if columns is not None:
            raise ValueError("f.variations(): with two parameters the sheet has one row for each value of the "
                             f"first ({names[0]}) and one column for each value of the second ({names[1]}), so "
                             "columns= cannot be used. Leave it out, or swap the two parameters.")
        return len(lists[names[1]]), len(lists[names[0]])
    n = len(combos)
    if columns is not None:
        if isinstance(columns, bool) or not isinstance(columns, int):
            raise TypeError(f"f.variations(): columns needs a whole number, such as columns=3, not {columns!r}")
        if columns < 1:
            raise ValueError(f"f.variations(): columns needs to be 1 or more, but got {columns}")
        return columns, math.ceil(n / columns)
    if row_is_readable([label_of(c) for c in combos], area, W, H):
        return n, 1
    cols = _best_columns(n, area, W, H)
    return cols, math.ceil(n / cols)


def in_cell() -> bool:
    """Whether the innermost open mark block is a variations cell (so background() paints the cell)."""
    return bool(marks._open) and bool(_cells) and marks._open[-1] is _cells[-1]


def cell_background(color, more) -> None:
    """background() inside a variations cell: paint the whole ground, ignoring the style and transform."""
    from .api import active_sketch, canvas_sketch
    from .paths import PathBuilder

    s = active_sketch()
    g = canvas_sketch().ground
    paint = s._paint(color, *more)
    with s.saved_state():
        s.reset_matrix()
        s._states.update(fill=paint, stroke=None, opacity=255, blend_mode="normal", shadow=None, erasing=None)
        s.draw_path(PathBuilder().rect(0, 0, g.width, g.height))


def variations(fn, values: dict, columns=None) -> list:
    """f.variations(): see api.variations for the learner's description."""
    from . import api
    from .paths import PathBuilder
    from .surface import Area

    if not callable(fn):
        raise TypeError(f"f.variations() needs a function to call first, such as f.variations(study, gap=[10, 20]), "
                        f"not {fn!r}")
    if not values:
        raise ValueError("f.variations() needs a parameter to vary, such as f.variations(study, gap=[10, 20, 40])")
    if len(values) > 2:
        names = ", ".join(values)
        raise ValueError(f"f.variations() varies one or two parameters at a time, but got {len(values)}: {names}. "
                         "Fix the others: give them one value inside your function, or a default value, "
                         "and vary them in a later sheet.")
    lists = {name: _values_of(name, v) for name, v in values.items()}
    canvas = api.canvas_sketch()
    ground = canvas.ground
    W, H = ground.width, ground.height
    area = ground.content
    names = list(lists)
    if len(names) == 1:
        combos = [{names[0]: v} for v in lists[names[0]]]
    else:
        first, second = names
        combos = [{first: a, second: b} for a in lists[first] for b in lists[second]]
    cols, rows = layout(combos, names, lists, columns, area, W, H)
    sheet = _sheet(area, cols, rows)
    k = picture_scale(sheet[0], W, H) if sheet is not None else 0
    if k <= 0:
        raise ValueError(f"f.variations(): {len(combos)} versions do not fit in the canvas "
                         f"({area.width:g} x {area.height:g}). Try fewer values, or a bigger canvas.")
    seed = canvas._seed
    state = canvas._rng.getstate()
    results = []
    used_random = False
    try:
        for cell, combo in zip(sheet, combos):
            canvas._rng.seed(seed)
            fresh = canvas._rng.getstate()
            m = marks.Mark()
            with m:
                _cells.append(m._recorder)
                try:
                    fn(**combo)
                finally:
                    _cells.pop()
            used_random = used_random or canvas._rng.getstate() != fresh
            results.append((combo, m, cell))
    finally:
        canvas._rng.setstate(state)

    sketch = api.active_sketch()
    bw, bh = W * k, H * k                          # one scale for every cell
    out = []
    for combo, m, cell in results:
        picture = Area(cell.cx - bw / 2, cell.top + (cell.height - bh - LABEL_STRIP) / 2, bw, bh)
        box = PathBuilder().rect(picture.left, picture.top, picture.width, picture.height)
        with sketch.saved_state():
            sketch.clip(box)
            m.place(picture.left, picture.top, scale=k)
        with sketch.saved_state():
            sketch._states.current = GraphicsState(fill=None, stroke=sketch._paint(FRAME_COLOR), stroke_width=1,
                                                   text_size=LABEL_SIZE)
            sketch.draw_path(box)
            sketch.clip(PathBuilder().rect(cell.left, picture.bottom, cell.width, LABEL_STRIP))
            sketch._states.update(fill=sketch._paint(LABEL_COLOR), stroke=None)
            sketch.text(label_of(combo), picture.left, picture.bottom + LABEL_GAP)
        out.append((combo, m))
    if used_random:
        _tell_seed(canvas)
    return out


def _tell_seed(canvas) -> None:
    """Print the seed once per run, when funground chose it and the cells used it, so the sheet can be made
    again."""
    told = getattr(canvas, "_seed_told", None)
    if canvas._seed_chosen_by == "funground" and told != canvas._seed:
        canvas._seed_told = canvas._seed
        print(f"f.variations(): every cell used the random seed {canvas._seed}. "
              f"Add f.random_seed({canvas._seed}) at the top to get the same sheet again.")


# ---------------------------------------------------------------- keep
_NUMBERED = re.compile(r"^(\d+)\.(png|pdf|py|json)$", re.IGNORECASE)
_PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))


def sketch_file(frame) -> str | None:
    """The file of the sketch that called keep: the first caller outside funground with a __file__."""
    while frame is not None:
        code_file = os.path.abspath(frame.f_code.co_filename)
        if not code_file.startswith(_PACKAGE_DIR + os.sep):
            found = frame.f_globals.get("__file__")
            if found and os.path.isfile(found):
                return os.path.abspath(found)
            return None
        frame = frame.f_back
    return None


def next_number(folder: str) -> int:
    """One more than the highest NNN.png/.pdf/.py/.json already in *folder* (1 in an empty or new folder)."""
    highest = 0
    if os.path.isdir(folder):
        for name in os.listdir(folder):
            m = _NUMBERED.match(name)
            if m:
                highest = max(highest, int(m.group(1)))
    return highest + 1


def _jsonable(value):
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    return repr(value)


def _controls(canvas) -> list[dict]:
    from .controls import Button, Checkbox, Slider

    out = []
    for c in canvas._panel.controls:
        if isinstance(c, Slider):
            out.append({"kind": "slider", "label": c.label, "value": c.value()})
        elif isinstance(c, Checkbox):
            out.append({"kind": "checkbox", "label": c.label, "value": c.checked()})
        elif isinstance(c, Button):
            out.append({"kind": "button", "label": c.label, "value": None})
    return out


def _fonts_used(ops) -> list[dict]:
    from . import ir, typography

    seen, out = set(), []
    for op in ops:
        if type(op) is not ir.Text:
            continue
        try:
            resource = typography.effective_font(op.style)
        except RuntimeError:
            continue
        key = (resource.path, resource.face)
        if key in seen:
            continue
        seen.add(key)
        bundled = os.path.abspath(resource.path).startswith(os.path.abspath(typography.FONT_DIR) + os.sep)
        out.append({"family": resource.family, "style": resource.style_name,
                    "file": os.path.basename(resource.path) if bundled else os.path.abspath(resource.path),
                    "face": resource.face, "bundled with funground": bundled})
    return out


def _shown_path(path: str, home: str) -> str:
    """*path* relative to the sketch's folder when it is inside it (with / between parts), otherwise as it is."""
    inside = os.path.abspath(path)
    if inside.startswith(os.path.abspath(home) + os.sep):
        return os.path.relpath(inside, home).replace(os.sep, "/")
    return inside


def _files_read(home: str) -> list[dict]:
    from .typography import files_read

    out = []
    for path, what in files_read.items():
        try:
            size = os.path.getsize(path)
        except OSError:
            size = None
        out.append({"kind": what, "path": _shown_path(path, home), "bytes": size})
    return out


NOT_CAPTURED = [
    "Fonts installed on this computer (system_font) may differ or be missing on another computer.",
    "Files the sketch read (images, SVGs, sounds, fonts) may change or move; only their names and sizes are kept.",
    "Anything the sketch got from outside funground: Python's own random module, the clock, the mouse, "
    "the microphone, the internet, other files it opened itself.",
    "Other Python packages the sketch imported, and their versions.",
    "The seeds make funground's random() and noise() repeatable; they do not make everything else repeatable.",
]


class _PendingKeep:
    """f.keep() in an animated sketch: the files of one kept version, written at the end of the frame being
    drawn (Sketch._frame_end), so the picture, the copy and the record all describe that frame."""

    def __init__(self, canvas, folder: str, number: int, note: str, pdf: bool, settings: dict,
                 source: str | None, home: str) -> None:
        self.canvas, self.folder, self.number = canvas, folder, number
        self.note, self.pdf, self.settings = note, pdf, settings
        self.source, self.home = source, home

    @property
    def base(self) -> str:
        return os.path.join(self.folder, f"{self.number:03d}")

    def __call__(self, drawn: bool) -> None:
        from . import ir
        from .export import save_frame, save_pixels

        canvas = self.canvas
        if drawn:                                  # the frame just drawn: its ops are still in canvas.frame
            ops, frame_count = canvas.frame.ops, canvas.frame_count
        else:                                      # no frame drawn this time (no_loop()): the one on screen
            ops, frame_count = (getattr(canvas, "last_ops", None) or ()), max(0, canvas.frame_count - 1)
        os.makedirs(self.folder, exist_ok=True)
        written = []
        save_pixels(canvas._view_pixels(), self.base + ".png")
        written.append(".png")
        if self.pdf:
            save_frame(canvas._with_layers(ir.Frame(list(ops)), files=True), self.base + ".pdf", canvas.width,
                       canvas.height, canvas._platform.backing_scale, "live")
            written.append(".pdf")
        _finish(canvas, self.base, written, self.note, self.settings, self.source, self.home, ops,
                page=None, frame_count=frame_count)


def _record(canvas, note, settings, source, home, ops, page, frame_count) -> dict:
    from . import __version__

    noise = canvas._noise
    return {
        "note": note,
        "settings": _jsonable(settings),
        "controls": _controls(canvas),
        "seed": canvas._seed,
        "seed_chosen_by": canvas._seed_chosen_by,
        "noise_seed": noise.seed_value,
        "noise_seed_chosen_by": noise.seed_chosen_by,
        "size": [canvas.width, canvas.height],
        "margin": list(canvas._margin),
        "page": page,
        "frame_count": frame_count,
        "date": datetime.now().astimezone().isoformat(timespec="seconds"),
        "sketch": os.path.basename(source) if source else None,
        "funground": __version__,
        "python": _platform.python_version(),
        "platform": _platform.platform(),
        "fonts_used": _fonts_used(ops),
        "files_read": _files_read(home),
        "not_captured": NOT_CAPTURED,
    }


def _finish(canvas, base, written, note, settings, source, home, ops, page, frame_count) -> None:
    """Write the source copy and the record next to the picture, and say where they went."""
    if source:
        shutil.copyfile(source, base + ".py")
        written.append(".py")
    with open(base + ".json", "w", encoding="utf-8") as fh:
        json.dump(_record(canvas, note, settings, source, home, ops, page, frame_count), fh, indent=2,
                  ensure_ascii=False)
        fh.write("\n")
    written.append(".json")
    try:
        shown = os.path.relpath(base)
    except ValueError:                            # another drive on Windows
        shown = base
    if shown.startswith(".."):
        shown = base
    print(f"f.keep(): kept {shown} ({' '.join(written)})", file=sys.stdout)


def keep(note: str, pdf: bool, settings: dict, caller) -> str:
    """f.keep(): see api.keep for the learner's description."""
    from . import api
    from .export import save_frame, save_pixels

    marks.refuse_in_mark("f.keep()")
    if not isinstance(note, str):
        raise TypeError(f"f.keep(): the note is text, such as f.keep(\"gap 35 reads as a rhythm\"), not {note!r}")
    canvas = api.canvas_sketch()
    canvas._require_window()
    source = sketch_file(caller)
    home = os.path.dirname(source) if source else os.getcwd()
    folder = os.path.join(home, "studio")
    os.makedirs(folder, exist_ok=True)
    number = next_number(folder)
    waiting = [w.number for w in canvas._frame_end if isinstance(w, _PendingKeep) and w.folder == folder]
    if waiting:                                   # numbers already promised to keeps in this frame
        number = max(number, max(waiting) + 1)
    base = os.path.join(folder, f"{number:03d}")

    if not canvas._script:                        # an animated sketch: everything at the end of the frame (E2)
        canvas._frame_end.append(_PendingKeep(canvas, folder, number, note, pdf, settings, source, home))
        return base

    canvas._flush_pixel_patch()
    canvas._script_flush()
    save_pixels(canvas._view_pixels(), base + ".png")
    written = [".png"]
    if pdf:
        save_frame(canvas._with_layers(canvas.frame, files=True), base + ".pdf", canvas.width, canvas.height,
                   canvas._script_scale, "live")
        written.append(".pdf")
    _finish(canvas, base, written, note, settings, source, home, canvas.frame.ops, page=canvas.page_count(),
            frame_count=None)
    return base
