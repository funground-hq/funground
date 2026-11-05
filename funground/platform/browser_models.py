"""The models for a host that runs them in the page (stories S-232 and S-234, ML_Package_Note.md, Web_Runner_Note.md).

On a computer `funground_ml` runs the ONNX files itself. In a web page the runner runs them in a worker of its own,
so inference never blocks the sketch's step. The two halves meet here, in the way the camera's do (browser_camera.py).

**Pictures** (the "pose", "hand" and "person" tasks):

* `request(task, key, rgba, width, height)` sends one picture to the page. At most one is in flight for each task and
  source; a picture that comes while one is being worked on is dropped, never queued.
* `push(task, key, points, score, width, height)` is what the page calls with a result of points (the "pose" and "hand"
  tasks), and `push_mask(task, key, mask, mask_width, mask_height, width, height)` with a result that is a mask (the "person"
  task). The host delivers either between two steps, so the sketch never sees a result appear half way through a frame.
* `latest(task, key)` is what funground_ml reads: the newest result for that task and source, a `PointsResult` or a
  `MaskResult`, or None before the first.

**Sound** (the "words" task, S-234):

* `request_sound(task, key, samples, rate)` sends one phrase to the page: `samples` is mono float32 bytes (4 bytes for each
  sample, little-endian, values -1 to 1, as `array("f").tobytes()` gives) and `rate` is how many samples there are in a second
  (the microphone's, for example 44100; the page resamples). At most one phrase is in flight for each task and source; a
  phrase that comes while one is being worked on is dropped here, and funground_ml keeps the newest one waiting and sends it
  when the answer is in, so the sketch hears the newest phrase last.
* `push_words(task, key, text, score)` is what the page calls with the answer: the words heard (a string, "" for none) and the
  score, 0 to 1 (the mean probability of the words the model chose). The same rules as for pictures: delivered between two
  steps, and ignored if nothing is in flight for that source.
* `latest(task, key)` gives the `WordsResult`, or None before the first.

What the page does with a phrase (funground_ml expects exactly this; the desktop does the same in `funground_ml/_whisper.py`):
resample to 16 kHz by linear interpolation (`count = floor(n * 16000 / rate)`; for output j, `p = j * rate / 16000`,
`i = floor(p)`, `t = p - i`, `y[j] = x[i] * (1 - t) + x[min(i + 1, n - 1)] * t`); take the log-mel of 30 s padded with
silence; run Whisper tiny.en (8-bit encoder, then the merged decoder with its past key values) choosing the likeliest piece
each time, at most 224 pieces, skipping the suppressed numbers; turn the pieces into text with the byte-level table of
`vocab.json`; push the text and the mean probability of the chosen pieces. The Python side drops an answer whose score is
under 0.4 or whose text is empty, so the page need not.

`key` says which source a request came from (funground_ml uses `id()` of the camera, picture, microphone or sound). `task` is
"pose", "hand", "person" or "words". A result can be one frame behind, which is what `ml.pose(cam)` gives in a page
(contract ML3), and a phrase's answer arrives a second or two after the speaker pauses.

`on_models(command, fields)` is told what the sketch wants:

    request   {"task", "key", "width", "height", "pixels"}   find the body or hand in these RGBA bytes
    request   {"task", "key", "rate", "samples"}             hear the words in this phrase (samples: float32 bytes)
    close     {}                                              the run ended: forget every source

A "request" with a "samples" field is a phrase and one with "pixels" is a picture; the "task" says the same.

If the page cannot run a model (no connection for the first download, a file that fails its check) it calls
`unavailable(task, reason)`, which prints the reason once and stops asking for that task. Without `on_models`
nothing asks the page, so there is never a result.
"""
from __future__ import annotations

from collections.abc import Callable
from typing import NamedTuple

ModelsCallback = Callable[[str, dict], None]


class PointsResult(NamedTuple):
    """One answer of points from the page (the "pose" and "hand" tasks), for the pixels it was sent."""
    points: tuple | None        # ((x, y), ...) in pixels of the picture that was sent, or None when nobody was found
    score: float
    width: int                  # the size of the picture that was sent
    height: int


class MaskResult(NamedTuple):
    """One answer that is a mask from the page (the "person" task), for the pixels it was sent."""
    mask: bytes                 # mask_width * mask_height bytes, row by row from the top left: 0 is not the person, 255 is
    mask_width: int             # the mask's own size, not the picture's: it covers the whole picture, stretched
    mask_height: int
    width: int                  # the size of the picture that was sent
    height: int


class WordsResult(NamedTuple):
    """One answer of words from the page (the "words" task)."""
    text: str                   # the words heard, "" for none
    score: float                # 0 to 1: the mean probability of the pieces of words the model chose


ModelResult = PointsResult | MaskResult | WordsResult


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

    def request_sound(self, task: str, key: int, samples, rate: int) -> bool:
        """Send one phrase: *samples* are mono float32 bytes (`array("f").tobytes()`), *rate* is samples a second. Returns
        False when it was dropped, because `busy` is true."""
        if self.busy(task, key):
            return False
        data = bytes(samples)
        if rate <= 0 or len(data) == 0 or len(data) % 4:
            raise ValueError(f"a phrase for the models must be float32 bytes (4 for each sample) and a rate above 0; got "
                             f"{len(data)} bytes at {rate}")
        self._in_flight.add((task, key))
        self._asked = True
        self._on_models("request", {"task": task, "key": key, "rate": int(rate), "samples": data})
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
        self._latest[(task, key)] = PointsResult(found, float(score), int(width), int(height))
        self.generation += 1

    def push_mask(self, task: str, key: int, mask, mask_width: int, mask_height: int, width: int, height: int) -> None:
        """A result that is a mask from the page: `mask` is `mask_width * mask_height` bytes, one for each pixel of the
        mask, row by row from the top left (0 is not the person, 255 is the person). `width` and `height` are the size of
        the picture that was sent. A result for a source the run has forgotten is ignored."""
        if (task, key) not in self._in_flight:
            return
        self._in_flight.discard((task, key))
        data = bytes(mask)
        if mask_width <= 0 or mask_height <= 0 or len(data) != mask_width * mask_height:
            raise ValueError(f"a mask from the models must be mask_width * mask_height bytes; got {len(data)} bytes "
                             f"for {mask_width} x {mask_height}")
        self._latest[(task, key)] = MaskResult(data, int(mask_width), int(mask_height), int(width), int(height))
        self.generation += 1

    def push_words(self, task: str, key: int, text: str, score: float) -> None:
        """A result that is words from the page: the text heard ("" for none) and the score, 0 to 1. A result for a source the
        run has forgotten is ignored."""
        if (task, key) not in self._in_flight:
            return
        self._in_flight.discard((task, key))
        self._latest[(task, key)] = WordsResult(str(text), float(score))
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
