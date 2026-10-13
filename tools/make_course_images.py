"""Render course examples and build reproducible learner downloads.

Run: python tools/make_course_images.py [--lessons 3 4]
The optional filter renders a batch; both download bundles always include current sources.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parent.parent
EXAMPLES = ROOT / "examples" / "course"
COURSE = ROOT / "docs" / "course"

# Bound live sketches in the renderer without changing learner files or opening a window.
RUNNER = """
import inspect, sys, runpy
import funground as f
from funground import api
def bounded_run(*, fps=None, max_frames=None):
    caller = inspect.currentframe().f_back
    api.active_sketch().run_namespace(caller.f_globals, fps=1000, max_frames=max_frames or 3)
f.run = bounded_run
runpy.run_path(sys.argv[1], run_name="__main__")
"""


def bundle(name, sketches, label):
    downloads = COURSE / "downloads"
    downloads.mkdir(parents=True, exist_ok=True)
    archive = downloads / name
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as output:
        for path in sorted([*sketches, ROOT / "examples/LICENSE"], key=lambda p: p.name):
            entry = zipfile.ZipInfo(path.name, date_time=(1980, 1, 1, 0, 0, 0))
            entry.compress_type = zipfile.ZIP_DEFLATED
            entry.external_attr = 0o644 << 16
            output.writestr(entry, path.read_bytes())
        entry = zipfile.ZipInfo("README.txt", date_time=(1980, 1, 1, 0, 0, 0))
        entry.compress_type = zipfile.ZIP_DEFLATED
        entry.external_attr = 0o644 << 16
        output.writestr(entry, (
            f"Creative practice with funground: {label}\n\n"
            "Use the Python environment where funground is installed.\n"
            "Begin with each lesson's NN_starter.py. The other files are comparison studies.\n"
            "Scripts save a PNG in your current folder and show the image.\n"
            "Lesson 9's live sketches respond continuously; close the window to finish.\n"
            "The optional 09_loop.py GIF exporter needs funground[extras] or ffmpeg.\n"
            "Files ending in _exercise.py are assignment starters.\n\n"
            "Source: https://github.com/funground-hq/funground\n"
            "Course pages: docs/course/README.md in that repository.\n"
            "All sketches are CC0; LICENSE gives the terms.\n"
        ))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lessons", type=int, nargs="+", choices=range(1, 12))
    args = parser.parse_args()
    sketches = sorted(EXAMPLES.glob("[0-9][0-9]_*.py"))
    demonstrations = [p for p in sketches if not p.stem.endswith("_exercise")
                      and (not args.lessons or int(p.name[:2]) in args.lessons)]
    images = COURSE / "images"
    images.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ)
    env["FUNGROUND_HEADLESS"] = "1"
    env["PYTHONPATH"] = str(ROOT) + os.pathsep + env.get("PYTHONPATH", "")
    with tempfile.TemporaryDirectory(prefix="funground-course-") as folder:
        for path in demonstrations:
            subprocess.run([sys.executable, "-c", RUNNER, str(path)],
                           cwd=folder, env=env, check=True, timeout=30)
            result = Path(folder) / (path.stem + ".png")
            if not result.is_file():
                raise RuntimeError(f"{path.name} did not save {result.name}")
            shutil.copyfile(result, images / result.name)
            gif = Path(folder) / (path.stem + ".gif")
            if gif.is_file():
                shutil.copyfile(gif, images / gif.name)
    bundle("first_two_lessons.zip", [p for p in sketches if int(p.name[:2]) <= 2], "first two lessons")
    bundle("course_sketches.zip", sketches, "all eleven lessons")
    print(f"Rendered {len(demonstrations)} examples; bundled {len(sketches)} sketches.")


if __name__ == "__main__":
    main()
