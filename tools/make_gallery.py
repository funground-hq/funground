"""Build the Examples Gallery from the code it shows (S-068).

    python tools/make_gallery.py              # every example: images + index
    python tools/make_gallery.py --index      # rewrite docs/gallery/README.md and SHOWCASE.md only
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
                               list_examples, title_and_description)
GALLERY = ROOT / "examples" / "gallery"
OUT = ROOT / "docs" / "gallery"
IMAGES = OUT / "images"
INDEX = OUT / "README.md"
SHOWCASE = OUT / "SHOWCASE.md"
FRAMES = 30

# The curated showcase: (example id, one line on what it shows). Order is the page order.
SHOWCASE_PICKS = [
    ("colour-03_gradients", "A sunset sky made from a gradient, with a gradient-filled shape on top."),
    ("compositing-01_blend_opacity_shadow", "Blend modes, opacity and soft shadows."),
    ("shapes-04_rounded", "Rectangles with rounded corners, each corner its own size."),
    ("curves-01_curves", "Smooth curves drawn through points you choose."),
    ("paths-05_booleans", "Shapes joined, cut and overlapped with union, intersection, difference and xor."),
    ("text-05_text_path", "Letters turned into shapes, then cut, outlined and filled with a gradient."),
    ("text-07_formatted", "Bold, italic, coloured and big words together in one piece of text."),
    ("randomness-03_noise", "Smooth noise drawn as a picture, a line and a hill."),
    ("motion-01_movers", "Little movers pushed about by vectors: this one is animated."),
    ("images-04_filters", "One picture changed by resize, blur, threshold, posterize, masks and more."),
    ("saving-04_poster_file", "A poster saved as PDF and SVG, with layers, real text, Hindi and an emoji."),
    ("documents-01_booklet", "Three pages saved to one PDF file."),
]


def examples() -> list[Path]:
    return list_examples(GALLERY)


def build_index() -> str:
    parts = [
        "# funground Examples Gallery",
        "",
        "Every picture below is made by running the example beside it — `python tools/make_gallery.py`",
        "regenerates them. Each example is a complete sketch: copy it into a file and run it.",
        "",
        "Browse these examples interactively: `python -m funground.gallery`",
        "",
        "Short on time? See the [showcase](SHOWCASE.md): a dozen of the best pictures on one page.",
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


def build_showcase() -> str:
    by_id = {example_id(p): p for p in examples()}
    parts = [
        "# funground Showcase",
        "",
        "A dozen pictures that show what funground can do. Each one is made by the example linked under it.",
        "See the [full gallery](README.md) for every example.",
        "",
    ]
    for ident, line in SHOWCASE_PICKS:
        path = by_id[ident]
        title, _ = title_and_description(path)
        source = path.relative_to(ROOT).as_posix()
        parts += [
            f"## {title}",
            "",
            f"![{title}](images/{ident}.png)",
            "",
            line,
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
    SHOWCASE.write_text(build_showcase(), encoding="utf-8", newline="\n")
    print(f"index -> {INDEX.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
