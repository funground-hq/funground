"""S-175 harness: counts, and frame comparison between an original example and its global-style rewrite.

Run from the worktree root:  PYTHONPATH=. SDL_VIDEODRIVER=dummy FUNGROUND_HEADLESS=1 <venv python> spikes/12_sketch_style/compare.py
Writes nothing but prints a table. Variants derived from the rewrite (the rewrite is written with colors.X and
option constants):  strings = the same sketch with quoted words; flat = colours as flat capitals (TOMATO).
"""
from __future__ import annotations

import ast
import inspect
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

import funground  # noqa: E402
from funground import api, constants  # noqa: E402
from funground.sketch import Sketch  # noqa: E402
from test_events import ScriptedPlatform  # noqa: E402
from funground.platform.base import InputEvent  # noqa: E402

PAIRS = [
    ("01_first_sketch", ROOT / "examples/session1/01_first_sketch.py"),
    ("07_bounce", ROOT / "examples/session1/07_bounce.py"),
    ("02_paint", ROOT / "examples/gallery/interaction/02_paint.py"),
    ("02_align", ROOT / "examples/gallery/text/02_align.py"),
    ("12_justified_columns", ROOT / "examples/gallery/text/12_justified_columns.py"),
    ("03_clock", ROOT / "examples/gallery/animation/03_clock.py"),
]
GLOBAL = Path(__file__).parent / "global"
OPTIONS = {n for n in constants.OPTION_WORDS}


def code_only(source: str) -> str:
    """The source without its module docstring."""
    tree = ast.parse(source)
    if tree.body and isinstance(tree.body[0], ast.Expr) and isinstance(getattr(tree.body[0], "value", None), ast.Constant) \
            and isinstance(tree.body[0].value.value, str):
        lines = source.splitlines(keepends=True)
        return "".join(lines[tree.body[0].end_lineno:]).lstrip("\n")
    return source


def as_strings(source: str) -> str:
    """Same sketch with quoted words instead of constants (colors.TOMATO -> "tomato")."""
    source = re.sub(r"colors\.([A-Z]+)", lambda m: '"' + m.group(1).lower() + '"', source)
    return re.sub(r"\b(" + "|".join(sorted(OPTIONS)) + r")\b(?!\s*=)", lambda m: '"' + m.group(1).lower() + '"', source)


def as_flat(source: str) -> str:
    return source.replace("colors.", "")


def counts(source: str) -> tuple[int, int, int]:
    return len(source), len(source.splitlines()), len(re.findall(r"\bf\.", source))


# Scripted input for the paint example: both versions get the same events.
PAINT_SCRIPT = {
    1: [InputEvent("mouse_moved", 100, 100), InputEvent("mouse_pressed", 100, 100, button="left"),
        InputEvent("mouse_dragged", 150, 140), InputEvent("mouse_released", 150, 140, button="left")],
    2: [InputEvent("key_pressed", 0, 0, key="r", key_code=114), InputEvent("mouse_dragged", 200, 160),
        InputEvent("mouse_pressed", 300, 200, button="right"), InputEvent("mouse_wheel", delta=-3.0),
        InputEvent("key_pressed", 0, 0, key="g", key_code=103), InputEvent("mouse_dragged", 320, 250)],
}


def run_frame(source: str, name: str, original: bool, frames: int):
    namespace: dict = {"__name__": "__sketch__", "__file__": name}
    sketch = api.use_sketch(Sketch(platform=ScriptedPlatform(PAINT_SCRIPT if name == "02_paint" else {})))
    sketch.random_seed(0)
    saved = funground.run

    def harness_run(*, fps=1000, max_frames=frames):
        api.active_sketch().run_namespace(inspect.currentframe().f_back.f_globals, fps=fps, max_frames=max_frames)

    funground.run = harness_run
    try:
        exec(compile(source, name, "exec"), namespace)
        if not original:                          # the rewrite never calls run(): start it as the exit hook would
            sketch.run_namespace(namespace, fps=1000, max_frames=frames)
    finally:
        funground.run = saved
    return api.active_sketch().last_frame


def main() -> None:
    print(f"{'example':22} {'version':10} {'chars':>6} {'lines':>6} {'f.':>4}  frame")
    for name, original in PAIRS:
        before = code_only(original.read_text(encoding="utf-8"))
        path = GLOBAL / f"{name}.py"
        after = path.read_text(encoding="utf-8")
        frames = 6 if name == "02_paint" else 31
        same = "time dependent"
        if name != "03_clock":
            a = run_frame(original.read_text(encoding="utf-8"), name, True, frames)
            b = run_frame(after, name, False, frames)
            same = "identical" if a == b else "DIFFERENT"
        rows = [("before", before), ("strings", as_strings(after)), ("colors.X", after), ("flat", as_flat(after))]
        for label, text in rows:
            c, l, fs = counts(text)
            print(f"{name:22} {label:10} {c:6} {l:6} {fs:4}  {same if label == 'colors.X' else ''}")


if __name__ == "__main__":
    main()
