"""The models for a host that runs them in the page (story S-232, ML_Package_Note.md, Web_Runner_Note.md).

On a computer `funground_ml` runs the ONNX files itself. In a web page the runner runs them in a worker of its own,
so inference never blocks the sketch's step. The two halves meet here, in the way the camera's do (browser_camera.py):

* `request(task, key, rgba, width, height)` sends one picture to the page. At most one is in flight for each task and
  source; a picture that comes while one is being worked on is dropped, never queued.
* `push(task, key, points, score, width, height)` is what the page calls with a result. The host delivers it between
  two steps, so the sketch never sees a result appear half way through a frame.
* `latest(task, key)` is what funground_ml reads: the newest result for that task and source, or None before the first.

`key` says which source a picture came from (funground_ml uses `id()` of the camera or picture). `task` is "pose" or
"hand". A result can be one frame behind the picture, which is what `ml.pose(cam)` gives in a page (contract ML3).

`on_models(command, fields)` is told what the sketch wants:

    request   {"task", "key", "width", "height", "pixels"}   find the body or hand in these RGBA bytes
    close     {}                                              the run ended: forget every source

If the page cannot run a model (no connection for the first download, a file that fails its check) it calls
`unavailable(task, reason)`, which prints the reason once and stops asking for that task. Without `on_models`
nothing asks the page, so there is never a result.
"""
from __future__ import annotations

from collections.abc import Callable
from typing import NamedTuple

ModelsCallback = Callable[[str, dict], None]


class ModelResult(NamedTuple):
    """One answer from the page, for the pixels it was sent."""
    points: tuple | None        # ((x, y), ...) in pixels of the picture that was sent, or None when nobody was found
    score: float
    width: int                  # the size of the picture that was sent
    height: int


class HostModels:
    """The host's models: funground_ml sends pictures with `request` and reads answers with `latest`."""

    def __init__(self, on_models: ModelsCallback | None = None) -> None:
        self._on_models = on_models
        self._in_flight: set[tuple[str, int]] = set()
        self._latest: dict[tuple[str, int], ModelResult] = {}
        self._failed: set[str] = set()                    # tasks the page cannot run in this run
        self._asked = False                               # a "request" has been sent since the last "close"
        self.generation = 0                               # counts every result and failure: it says when an answer may differ

    # ---- what funground_ml calls
    def busy(self, task: str, key: int) -> bool:
        """True when a picture for this task and source should not be sent now: one is in flight, the page cannot run
        the task, or nothing is listening."""
        return self._on_models is None or task in self._failed or (task, key) in self._in_flight

    def request(self, task: str, key: int, rgba, width: int, height: int) -> bool:
        """Send one picture (RGBA bytes, row by row from the top left). Returns False when it was dropped, because
        `busy` is true."""
        if self.busy(task, key):
            return False
        data = bytes(rgba)
        if width <= 0 or height <= 0 or len(data) != width * height * 4:
            raise ValueError(f"a picture for the models must be width * height * 4 bytes of RGBA; got {len(data)} bytes "
                             f"for {width} x {height}")
        self._in_flight.add((task, key))
        self._asked = True
        self._on_models("request", {"task": task, "key": key, "width": width, "height": height, "pixels": data})
        return True

    def latest(self, task: str, key: int) -> ModelResult | None:
        """The newest result for this task and source, or None before the first one."""
        return self._latest.get((task, key))

    # ---- what the host calls
    def push(self, task: str, key: int, points, score: float, width: int, height: int) -> None:
        """A result from the page. `points` is a flat sequence x0, y0, x1, y1, ... in pixels of the picture that was
        sent, or None when nobody was found. A result for a source the run has forgotten is ignored."""
        if (task, key) not in self._in_flight:
            return
        self._in_flight.discard((task, key))
        if points is None:
            found = None
        else:
            flat = [float(v) for v in points]
            if len(flat) % 2:
                raise ValueError("the points of a model result must be x, y pairs: an even number of values")
            found = tuple(zip(flat[0::2], flat[1::2]))
        self._latest[(task, key)] = ModelResult(found, float(score), int(width), int(height))
        self.generation += 1

    def unavailable(self, task: str, reason: str) -> None:
        """The page could not run this task. Prints one line the first time, and the task is not asked for again."""
        if task in self._failed:
            return
        self._failed.add(task)
        self._in_flight = {item for item in self._in_flight if item[0] != task}
        self.generation += 1
        print(str(reason).rstrip())

    def close(self) -> None:
        """The run ended: forget every source and tell the page to do the same."""
        self._in_flight.clear()
        self._latest.clear()
        self._failed.clear()
        if self._asked and self._on_models is not None:
            self._asked = False
            self._on_models("close", {})
