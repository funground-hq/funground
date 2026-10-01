"""Build the Examples Gallery from the code it shows (S-068).

    python tools/make_gallery.py              # every example: images + index
    python tools/make_gallery.py --index      # rewrite docs/gallery/README.md only
    python tools/make_gallery.py --force      # also re-render time-dependent examples

Every ``examples/gallery/<area>/NN_name.py`` is an ordinary learner sketch. It is run
headless for ``FRAMES`` frames and its last frame is saved to
``docs/gallery/images/<area>-<name>.png``; the index groups the pictures by area with
the title and description taken from each sketch's docstring. Nothing in the gallery
is drawn by hand, so a picture can never drift from the code beside it.
"""
from __future__ import annotations

import importlib.util
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GALLERY = ROOT / "examples" / "gallery"
OUT = ROOT / "docs" / "gallery"
IMAGES = OUT / "images"
INDEX = OUT / "README.md"
FRAMES = 30
TIME_DEPENDENT_MARK = "# gallery: time-dependent"

# Display order and titles for the areas; an area missing here is listed last, by name.
AREAS = {
    "basics": "Basics",
    "shapes": "Shapes",
    "colour": "Colour",
    "lines": "Fill, stroke and lines",
    "curves": "Curves",
    "text": "Text",
    "animation": "Animation and time",
    "transforms": "Transforms",
    "paths": "Paths and clipping",
    "randomness": "Randomness and noise",
    "maths": "Useful maths",
    "interaction": "Interaction",
    "saving": "Saving your work",
    "images": "Pictures and images",
}


def examples() -> list[Path]:
    return sorted(GALLERY.glob("*/*.py"), key=lambda p: (area_rank(p.parent.name), p.parent.name, p.name))


def area_rank(area: str) -> int:
    return list(AREAS).index(area) if area in AREAS else len(AREAS)


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


def build_index() -> str:
    parts = [
        "# funground Examples Gallery",
        "",
        "Every picture below is made by running the example beside it — `python tools/make_gallery.py`",
        "regenerates them. Each example is a complete sketch: copy it into a file and run it.",
        "",
        "Browse these examples interactively: `python tools/gallery_browser.py`",
        "",
    ]
    current = None
    for path in examples():
        area = path.parent.name
        if area != current:
            current = area
            parts += [f"## {AREAS.get(area, area.title())}", ""]
        title, description = title_and_description(path)
        source = path.relative_to(ROOT).as_posix()
        parts += [
            f"### {title}",
            "",
            f"![{title}](images/{example_id(path)}.png)",
            "",
            description + (" *(Uses real time, so the picture varies from run to run.)*" if is_time_dependent(path) else ""),
            "",
            f"Source: [`{source}`](../../{source})",
            "",
        ]
    return "\n".join(parts).rstrip() + "\n"


def _renderer():
    spec = importlib.util.spec_from_file_location("make_reference_images", ROOT / "tools" / "make_reference_images.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.render


def main(argv: list[str]) -> int:
    os.environ["FUNGROUND_HEADLESS"] = "1"
    OUT.mkdir(parents=True, exist_ok=True)
    if "--index" not in argv:
        render = _renderer()
        IMAGES.mkdir(parents=True, exist_ok=True)
        here = os.getcwd()
        with tempfile.TemporaryDirectory() as scratch:
            os.chdir(scratch)           # examples that f.save() write their own files here, not in the repo
            try:
                for path in examples():
                    target = IMAGES / f"{example_id(path)}.png"
                    if is_time_dependent(path) and target.exists() and "--force" not in argv:
                        # Its picture differs on every run; keep the committed one stable.
                        print(f"{path.relative_to(ROOT)} (time-dependent, kept)")
                        continue
                    out = render(path, target, FRAMES)
                    print(f"{path.relative_to(ROOT)} -> {out.relative_to(ROOT)}")
            finally:
                os.chdir(here)
    INDEX.write_text(build_index(), encoding="utf-8", newline="\n")
    print(f"index -> {INDEX.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
