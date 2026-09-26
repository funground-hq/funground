"""Regenerate the Quick Reference screenshots from the code they document (S-030).

    python tools/make_reference_images.py            # every sketch
    python tools/make_reference_images.py 05_text    # just one

Each ``examples/reference/*.py`` sketch is run headless (``FUNGROUND_HEADLESS=1``,
no window, no SDL) for ``FRAMES`` loop iterations; when the run ends the harness
saves the last frame shown to ``docs/reference/images/<stem>.png`` - so a sketch
that calls ``f.no_loop()`` still gets its picture.
The sketches are ordinary learner sketches - they call ``f.run()`` themselves -
so a picture in the reference can never drift from the code beside it.
"""
from __future__ import annotations

import inspect
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import funground  # noqa: E402
from funground import api  # noqa: E402
from funground.export import save_pixels  # noqa: E402
from funground.platform.headless import HeadlessPlatform  # noqa: E402
from funground.sketch import Sketch  # noqa: E402

SKETCHES = ROOT / "examples" / "reference"
IMAGES = ROOT / "docs" / "reference" / "images"
FRAMES = 30  # the same length as the Session-1 golden runs; deterministic sketches only


class _SavingPlatform(HeadlessPlatform):
    """Headless, and on close() writes the last presented frame to a PNG."""

    def __init__(self, out: Path) -> None:
        super().__init__()
        self._out = out

    def close(self) -> None:
        if self._last is not None:
            save_pixels(self._last, str(self._out))
        super().close()


def render(sketch: Path, out: Path, frames: int = FRAMES) -> Path:
    """Run *sketch* headless for *frames* iterations and save the last frame shown to *out*."""
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        out.unlink()                    # a failed run must not leave the old picture looking fresh
    api.use_sketch(Sketch(platform=_SavingPlatform(out)))
    source = sketch.read_text(encoding="utf-8")
    namespace: dict[str, object] = {"__name__": "__sketch__", "__file__": str(sketch)}

    def harness_run(*, fps=None, max_frames=frames):
        sketch_globals = inspect.currentframe().f_back.f_globals
        api.active_sketch().run_namespace(sketch_globals, fps=1000, max_frames=max_frames)

    original = funground.run
    funground.run = harness_run
    try:
        exec(compile(source, str(sketch), "exec"), namespace)
    finally:
        funground.run = original
    if not out.exists():
        raise RuntimeError(f"{sketch.name} never showed a frame; nothing saved")
    return out


def main(argv: list[str]) -> int:
    os.environ["FUNGROUND_HEADLESS"] = "1"
    wanted = set(argv)
    sketches = sorted(SKETCHES.glob("*.py"))
    if wanted:
        sketches = [s for s in sketches if s.stem in wanted or s.name in wanted]
        missing = wanted - {s.stem for s in sketches} - {s.name for s in sketches}
        if missing:
            print(f"no such reference sketch: {', '.join(sorted(missing))}", file=sys.stderr)
            return 2
    for sketch in sketches:
        out = render(sketch, IMAGES / f"{sketch.stem}.png")
        print(f"{sketch.relative_to(ROOT)} -> {out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
