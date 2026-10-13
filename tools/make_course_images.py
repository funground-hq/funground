"""Render the course comparisons and build a reproducible learner download.

Run from the repository root: python tools/make_course_images.py
All images are drawn by the linked Funground scripts; no existing gallery goldens change.
"""
from __future__ import annotations

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


def main():
    images = COURSE / "images"
    images.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ)
    env["FUNGROUND_HEADLESS"] = "1"
    env["PYTHONPATH"] = str(ROOT) + os.pathsep + env.get("PYTHONPATH", "")
    sketches = sorted(EXAMPLES.glob("[0-9][0-9]_*.py"))
    demonstrations = [path for path in sketches if not path.stem.endswith("_exercise")]
    with tempfile.TemporaryDirectory(prefix="funground-course-") as folder:
        for path in demonstrations:
            subprocess.run([sys.executable, str(path)], cwd=folder, env=env, check=True, timeout=30)
            result = Path(folder) / (path.stem + ".png")
            if not result.is_file():
                raise RuntimeError(f"{path.name} did not save {result.name}")
            shutil.copyfile(result, images / result.name)

    downloads = COURSE / "downloads"
    downloads.mkdir(parents=True, exist_ok=True)
    archive = downloads / "first_two_lessons.zip"
    files = [*sketches, ROOT / "examples" / "LICENSE"]
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
        for path in sorted(files, key=lambda p: p.name):
            entry = zipfile.ZipInfo(path.name, date_time=(1980, 1, 1, 0, 0, 0))
            entry.compress_type = zipfile.ZIP_DEFLATED
            entry.external_attr = 0o644 << 16
            bundle.writestr(entry, path.read_bytes())
        entry = zipfile.ZipInfo("README.txt", date_time=(1980, 1, 1, 0, 0, 0))
        entry.compress_type = zipfile.ZIP_DEFLATED
        entry.external_attr = 0o644 << 16
        bundle.writestr(entry, (
            "Creative Thinking Course: first two lessons\n\n"
            "Use the Python environment where Funground is installed.\n"
            "Start with: python 01_starter.py, then python 02_starter.py.\n"
            "Each script saves a PNG in your current folder and opens a window.\n"
            "Close the window to finish. Files ending in _exercise.py are your assignment starters.\n"
            "The other scripts show complete visual comparisons.\n\n"
            "Source repository: https://github.com/funground-hq/funground\n"
            "Course pages: docs/course/README.md in that repository.\n"
            "All sketches are CC0; the accompanying LICENSE gives the terms.\n"
        ))
    print(f"Rendered {len(demonstrations)} images; bundled {len(sketches)} sketches in {archive.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
