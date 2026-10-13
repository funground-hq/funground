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
sys.path.insert(0, str(ROOT))      # the example list and parsing live in the package: one source of truth
from funground.gallery import (AREAS, TIME_DEPENDENT_MARK, area_rank, example_id, is_time_dependent,  # noqa: E402,F401
                               explanation, list_examples, title_and_description)
GALLERY = ROOT / "examples" / "gallery"
OUT = ROOT / "docs" / "gallery"
IMAGES = OUT / "images"
INDEX = OUT / "README.md"
FRAMES = 30

def examples() -> list[Path]:
    return list_examples(GALLERY)


def explanation_block(path: Path) -> list[str]:
    """How it works and Make it yours, in one collapsed section (S-120): 83 open lists would bury the pictures."""
    parts = explanation(path)
    if not parts.how:
        return []
    lines = ["<details>", "<summary>How it works, and how to make it yours</summary>", "", "**How it works**", ""]
    lines += [f"- {point}" for point in parts.how]
    lines += ["", "**Make it yours**", ""]
    lines += [f"- {idea}" for idea in parts.make]
    return lines + ["", "</details>", ""]


def build_index() -> str:
    parts = [
        "# funground Examples Gallery",
        "",
        "Every picture below is made by running the example beside it — `python tools/make_gallery.py`",
        "regenerates them. Each example is a complete sketch: copy it into a file and run it.",
        "",
        "Browse these examples interactively: `python -m funground.gallery`",
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
        ]
        parts += explanation_block(path)
        parts += [
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
