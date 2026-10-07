"""Play: exploring with variations and keeping versions (story S-132 part 3, a prototype for D-071).

``f.variations(fn, gap=[...])`` draws a labelled contact sheet: one cell for each value (or each pair of
values), each cell ``fn``'s drawing recorded as a Mark and placed scaled into the cell. ``f.keep(note)``
saves the current picture, a copy of the sketch and a JSON record into a ``studio/`` folder.

The module is called ``exploring`` and not ``play`` on purpose: ``f.play`` is a public name, and a
submodule called ``play`` would replace it as an attribute of the package the first time it was imported.

How variations works:

- **Layout.** One parameter: the number of columns that gives the largest cells for the canvas's shape, so a
  wide canvas gets a row and a square one a near-square grid. Two parameters: rows for the first, columns
  for the second. Cells cover ``f.ground.content``, with a small gutter and a label strip under each picture.
- **Fit.** Each cell shows the whole ground (the canvas, 0 to width and 0 to height) scaled down by one
  factor for every cell, not each drawing fitted by its own bounds. So a drawing that is wider for gap=60
  than for gap=10 looks wider in its cell, and the cells can be compared.
- **Isolation.** A mark's block starts from the style at the call and no transform, and puts everything back
  when it ends, so one cell's ``fill()`` cannot reach the next one.
- **Seed.** Every cell starts the random generator from the run's seed (``random_seed(n)``, or the one
  funground chose at the start), so cells differ only in the parameter. The generator is put back afterwards.
- **background() in a cell** paints the cell's whole ground instead of raising (a mark has no edges).
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

GUTTER = 10          # space between cells, in canvas units
LABEL_SIZE = 11      # the label's text size
LABEL_STRIP = 16     # the height kept under each picture for its label
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


def _best_columns(n: int, area, W: float, H: float) -> int:
    """The number of columns that makes n ground-shaped cells largest in *area* (ties: more columns)."""
    best, best_k = 1, -1.0
    for cols in range(1, n + 1):
        rows = math.ceil(n / cols)
        cw = (area.width - GUTTER * (cols - 1)) / cols
        ch = (area.height - GUTTER * (rows - 1)) / rows - LABEL_STRIP
        if cw <= 0 or ch <= 0:
            continue
        k = min(cw / W, ch / H)
        if k >= best_k - 1e-9:
            best, best_k = cols, k
    return best


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


def variations(fn, values: dict) -> list:
    """f.variations(): see api.variations for the learner's description."""
    from . import api
    from .paths import PathBuilder
    from .surface import make_grid

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
        cols = _best_columns(len(combos), area, W, H)
        rows = math.ceil(len(combos) / cols)
    else:
        first, second = names
        combos = [{first: a, second: b} for a in lists[first] for b in lists[second]]
        rows, cols = len(lists[first]), len(lists[second])
    try:
        cells = make_grid(cols, rows, GUTTER, area)
    except ValueError:
        raise ValueError(f"f.variations(): {len(combos)} versions do not fit in the canvas "
                         f"({area.width:g} x {area.height:g}). Try fewer values, or a bigger canvas.") from None
    seed = canvas._seed
    state = canvas._rng.getstate()
    results = []
    used_random = False
    try:
        for cell, combo in zip(cells, combos):
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
    out = []
    for combo, m, cell in results:
        k = min(cell.w / W, (cell.h - LABEL_STRIP) / H)
        bw, bh = W * k, H * k
        bx = cell.x + (cell.w - bw) / 2
        by = cell.y + (cell.h - bh - LABEL_STRIP) / 2
        box = PathBuilder().rect(bx, by, bw, bh)
        with sketch.saved_state():
            sketch.clip(box)
            m.place(bx, by, scale=k)
        with sketch.saved_state():
            sketch._states.current = GraphicsState(fill=None, stroke=sketch._paint(FRAME_COLOR), stroke_width=1,
                                                   text_size=LABEL_SIZE)
            sketch.draw_path(box)
            sketch.clip(PathBuilder().rect(cell.x, by + bh, cell.w, LABEL_STRIP))
            sketch._states.update(fill=sketch._paint(LABEL_COLOR), stroke=None)
            sketch.text(label_of(combo), bx, by + bh + 3)
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
]


def keep(note: str, pdf: bool, settings: dict, caller) -> str:
    """f.keep(): see api.keep for the learner's description."""
    from . import __version__, api
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
    base = os.path.join(folder, f"{next_number(folder):03d}")

    written = []
    if canvas._script:
        canvas._flush_pixel_patch()
        canvas._script_flush()
        save_pixels(canvas._view_pixels(), base + ".png")
        if pdf:
            save_frame(canvas._with_layers(canvas.frame, files=True), base + ".pdf", canvas.width, canvas.height,
                       canvas._script_scale, "live")
        ops = canvas.frame.ops
    else:
        canvas.save(base + ".png")                # written when this frame is complete
        if pdf:
            canvas.save(base + ".pdf")
        ops = canvas.frame.ops or (getattr(canvas, "last_ops", None) or ())
    written.append(".png")
    if pdf:
        written.append(".pdf")
    if source:
        shutil.copyfile(source, base + ".py")
        written.append(".py")

    noise = canvas._noise
    record = {
        "note": note,
        "settings": _jsonable(settings),
        "controls": _controls(canvas),
        "seed": canvas._seed,
        "seed_chosen_by": canvas._seed_chosen_by,
        "noise_seed": noise.seed_value,
        "noise_seed_chosen_by": noise.seed_chosen_by,
        "size": [canvas.width, canvas.height],
        "margin": list(canvas._margin),
        "page": canvas.page_count() if canvas._script else None,
        "frame_count": canvas.frame_count if canvas.running else None,
        "date": datetime.now().astimezone().isoformat(timespec="seconds"),
        "sketch": os.path.basename(source) if source else None,
        "funground": __version__,
        "python": _platform.python_version(),
        "platform": _platform.platform(),
        "fonts_used": _fonts_used(ops),
        "files_read": _files_read(home),
        "not_captured": NOT_CAPTURED,
    }
    with open(base + ".json", "w", encoding="utf-8") as fh:
        json.dump(record, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    written.append(".json")
    try:
        shown = os.path.relpath(base)
    except ValueError:                            # another drive on Windows
        shown = base
    if shown.startswith(".."):
        shown = base
    print(f"f.keep(): kept {shown} ({' '.join(written)})", file=sys.stdout)
    return base
