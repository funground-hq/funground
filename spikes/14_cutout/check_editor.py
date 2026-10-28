"""Run outline_editor.py headless for a few frames and simulate one drag. Used to test the demo; not part of the spike's results.

Run:  FUNGROUND_HEADLESS=1 .venv/Scripts/python spikes/14_cutout/check_editor.py
"""
import os
import runpy
import sys
from pathlib import Path

os.environ["FUNGROUND_HEADLESS"] = "1"
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
os.chdir(HERE)

import funground as f                                              # noqa: E402
from funground import api                                          # noqa: E402
from funground.platform.base import InputEvent                     # noqa: E402
from funground.platform.headless import HeadlessPlatform           # noqa: E402
from funground.sketch import Sketch                                # noqa: E402

sketch = api.use_sketch(Sketch(platform=HeadlessPlatform()))
log = {}


def run_here(**_ignored):
    """Stands in for f.run(): one frame, then a drag from the nearest point to a new place, then two frames."""
    ns = sys._getframe(1).f_globals
    sketch.start(ns, max_frames=5)
    platform = sketch._platform
    log["before"] = list(ns["points"])
    sketch.step()                                                  # frame 1
    target = ns["points"][0]
    platform.post(InputEvent("mouse_pressed", int(target[0]), int(target[1]), button="left"))
    sketch.step()
    platform.post(InputEvent("mouse_dragged", 20, 30, button="left"))
    sketch.step()
    platform.post(InputEvent("mouse_released", 20, 30, button="left"))
    sketch.step()
    sketch.step()
    log["after"] = list(ns["points"])
    sketch.finish()
    log["frame"] = sketch.last_frame


f.run = run_here
runpy.run_path(str(HERE / "outline_editor.py"), run_name="__main__")
before, after = log["before"], log["after"]
moved = [i for i, (a, b) in enumerate(zip(before, after)) if a != b]
print("points:", len(before), "| moved:", moved, "| point 0 now", after[0])
(w, h), rgb = log["frame"]
print("last frame:", w, "x", h, "bytes", len(rgb))
import pygame                                                      # noqa: E402
(HERE / "out").mkdir(exist_ok=True)
pygame.image.save(pygame.image.frombytes(bytes(rgb), (w, h), "RGB"), str(HERE / "out" / "editor_after_drag.png"))
assert moved == [0] and after[0] == (20, 30)
print("OK")
