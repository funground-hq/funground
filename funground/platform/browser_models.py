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

**Sound** (the "words" task, S-234, and the "sound" task, S-250):

* `request_sound(task, key, samples, rate)` sends one phrase to the page: `samples` is mono float32 bytes (4 bytes for each
  sample, little-endian, values -1 to 1, as `array("f").tobytes()` gives) and `rate` is how many samples there are in a second
  (the microphone's, for example 44100; the page resamples). At most one phrase is in flight for each task and source; a
  phrase that comes while one is being worked on is dropped here, and funground_ml keeps the newest one waiting and sends it
  when the answer is in, so the sketch hears the newest phrase last.
* `push_words(task, key, text, score)` is what the page calls with the answer: the words heard (a string, "" for none) and the
  score, 0 to 1 (the mean probability of the words the model chose). The same rules as for pictures: delivered between two
  steps, and ignored if nothing is in flight for that source.
* `latest(task, key)` gives the `WordsResult`, or None before the first.
* `push_sound_scores(task, key, scores)` is what the page calls for the "sound" task: `scores` is the 521 scores of the sound
  model as float32 bytes (4 bytes for each score, little-endian; a Float32Array's `to_bytes()` in Pyodide gives them), and
  `latest` then gives a `SoundResult`. Float32 bytes keep the numbers exactly as the model made them. The Python side chooses the
  names; the page sends none.

What the page does with a phrase (funground_ml expects exactly this; the desktop does the same in `funground_ml/_whisper.py`):
resample to 16 kHz by linear interpolation (`count = floor(n * 16000 / rate)`; for output j, `p = j * rate / 16000`,
`i = floor(p)`, `t = p - i`, `y[j] = x[i] * (1 - t) + x[min(i + 1, n - 1)] * t`); take the log-mel of 30 s padded with
silence; run Whisper tiny.en (8-bit encoder, then the merged decoder with its past key values) choosing the likeliest piece
each time, at most 224 pieces, skipping the suppressed numbers; turn the pieces into text with the byte-level table of
`vocab.json`; push the text and the mean probability of the chosen pieces. The Python side drops an answer whose score is
under 0.4 or whose text is empty, so the page need not.

What the page does with a window of the "sound" task (`request_sound("sound", key, samples, rate)`; funground_ml expects exactly
this; the desktop does the same in `funground_ml/_yamnet.py`): resample to 16 kHz with the same formula as above; run YAMNet
(`yamnet.onnx`, the input `waveform`: float32, 16 kHz, no other preparation) which gives a table of one row of 521 scores for
each 0.96 s of sound; take the mean of the rows, column by column (a microphone's window of 0.96 s is one row; a whole Sound is
several); push the 521 mean scores as float32 bytes with `push_sound_scores`. The quiet-window rule and the choosing of names
are done in Python before and after, never on the page. A window of a microphone comes about twice a second.

**Vectors** (the "picture_mobilenet" and "picture_dinov2" tasks, S-235, ML8):

* `request_vector(task, job, rgba, width, height)` sends one picture to be turned into a vector, as the same "request" message
  that pictures use (the page tells it apart by the task). `job` is a whole number that is unique within the run (funground_ml
  numbers its jobs 1, 2, 3, ...). Nothing is dropped for being busy: many jobs can be in flight and the page works on them in
  order. It returns False only when nothing listens (no `on_models`) or the task has failed.
* `push_vector(task, job, vector)` is what the page calls with the answer: the vector as float32 bytes (4 bytes each, little-endian),
  already made length 1 by the page, or a sequence of numbers. It is kept for that job, and ignored if that job is not in flight
  (the run was forgotten).
* `take_vector(task, job)` is what funground_ml reads: the vector as a tuple of floats, forgotten as it is given, or None if it
  has not come. `failed(task)` is True after `unavailable(task, reason)`.

What the page does with a picture of a vector task (funground_ml expects exactly this; the desktop does the same in
`funground_ml/_pictures.py`): the RGBA picture (see-through pixels are already opaque black, which `Frame.rgba()` makes them);
scale the shorter side to 256 with Pillow's bicubic resampling (the page reproduces Pillow's); cut the middle 224 x 224; divide by
255; subtract the ImageNet mean (0.485, 0.456, 0.406) and divide by the spread (0.229, 0.224, 0.225) for red, green and blue; lay it
out as NCHW; run the task's model. MobileNetV4: output 0, row 0 (1280 numbers). DINOv2: output 0 at [0, 0] (384 numbers). Make the
vector length 1 and push it as float32 bytes.

`key` says which source a request came from (funground_ml uses `id()` of the camera, picture, microphone or sound). `task` is
"pose", "hand", "person", "words", "sound", "picture_mobilenet" or "picture_dinov2". A result can be one frame behind, which is what `ml.pose(cam)` gives in a page
(contract ML3), and a phrase's answer arrives a second or two after the speaker pauses.

`on_models(command, fields)` is told what the sketch wants:

    request   {"task", "key", "width", "height", "pixels"}   find the body or hand in these RGBA bytes
    request   {"task", "key", "rate", "samples"}             hear the words ("words") or name the sound ("sound") in these
                                                              samples (float32 bytes)
    request   {"task", "key", "width", "height", "pixels"}   make the vector of these RGBA bytes ("picture_mobilenet",
                                                              "picture_dinov2"); "key" is the job number
    close     {}                                              the run ended: forget every source

A "request" with a "samples" field is a phrase or a window of sound and one with "pixels" is a picture; the "task" says the same
(a picture of a vector task is not dropped when busy, and its "key" is a job number, not a source).

If the page cannot run a model (no connection for the first download, a file that fails its check) it calls
`unavailable(task, reason)`, which prints the reason once and stops asking for that task. Without `on_models`
nothing asks the page, so there is never a result.
"""
from __future__ import annotations

import struct
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


class SoundResult(NamedTuple):
    """One answer of sound scores from the page (the "sound" task)."""
    scores: tuple               # the model's 521 scores (floats, 0 to 1), the mean over the windows heard


ModelResult = PointsResult | MaskResult | WordsResult | SoundResult


class HostModels:
    """The host's models: funground_ml sends pictures with `request` and reads answers with `latest`."""

    def __init__(self, on_models: ModelsCallback | None = None) -> None:
        self._on_models = on_models
        self._in_flight: set[tuple[str, int]] = set()
        self._latest: dict[tuple[str, int], ModelResult] = {}
        self._failed: set[str] = set()                    # tasks the page cannot run in this run
        self._jobs: set[tuple[str, int]] = set()          # (task, job) of vectors asked for and not yet come
        self._vectors: dict[tuple[str, int], tuple] = {}  # vectors that have come and not yet been taken
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

    def request_vector(self, task: str, job: int, rgba, width: int, height: int) -> bool:
        """Send one picture to be made into a vector (RGBA bytes, as `request`). Never dropped for being busy: many jobs can be
        in flight. Returns False only when nothing listens or the task has failed."""
        if self._on_models is None or task in self._failed:
            return False
        data = bytes(rgba)
        if width <= 0 or height <= 0 or len(data) != width * height * 4:
            raise ValueError(f"a picture for the models must be width * height * 4 bytes of RGBA; got {len(data)} bytes "
                             f"for {width} x {height}")
        self._jobs.add((task, job))
        self._asked = True
        self._on_models("request", {"task": task, "key": job, "width": width, "height": height, "pixels": data})
        return True

    def take_vector(self, task: str, job: int) -> tuple | None:
        """The vector for this job as a tuple of floats, forgotten as it is given; None if it has not come."""
        return self._vectors.pop((task, job), None)

    def failed(self, task: str) -> bool:
        """True when the page has said it cannot run this task (`unavailable`)."""
        return task in self._failed

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

    def push_sound_scores(self, task: str, key: int, scores) -> None:
        """A result that is sound scores from the page: `scores` is the model's scores as float32 bytes (4 bytes each, little
        endian), or a sequence of numbers. A result for a source the run has forgotten is ignored."""
        if (task, key) not in self._in_flight:
            return
        self._in_flight.discard((task, key))
        if isinstance(scores, (bytes, bytearray, memoryview)):
            data = bytes(scores)
            if len(data) == 0 or len(data) % 4:
                raise ValueError(f"sound scores must be float32 bytes (4 for each score); got {len(data)} bytes")
            numbers = struct.unpack(f"<{len(data) // 4}f", data)
        else:
            numbers = tuple(float(v) for v in scores)
        self._latest[(task, key)] = SoundResult(numbers)
        self.generation += 1

    def push_vector(self, task: str, job: int, vector) -> None:
        """A result that is a vector from the page: float32 bytes (4 bytes each, little-endian), or a sequence of numbers. It is
        kept for `take_vector`. A result for a job that is not in flight (a forgotten run) is ignored."""
        if (task, job) not in self._jobs:
            return
        self._jobs.discard((task, job))
        if isinstance(vector, (bytes, bytearray, memoryview)):
            data = bytes(vector)
            if len(data) == 0 or len(data) % 4:
                raise ValueError(f"a vector must be float32 bytes (4 for each number); got {len(data)} bytes")
            numbers = struct.unpack(f"<{len(data) // 4}f", data)
        else:
            numbers = tuple(float(v) for v in vector)
        self._vectors[(task, job)] = numbers
        self.generation += 1

    def unavailable(self, task: str, reason: str) -> None:
        """The page could not run this task. Prints one line the first time, and the task is not asked for again."""
        if task in self._failed:
            return
        self._failed.add(task)
        self._in_flight = {item for item in self._in_flight if item[0] != task}
        self._jobs = {item for item in self._jobs if item[0] != task}
        self.generation += 1
        print(str(reason).rstrip())

    def close(self) -> None:
        """The run ended: forget every source and tell the page to do the same."""
        self._in_flight.clear()
        self._latest.clear()
        self._jobs.clear()
        self._vectors.clear()
        self._failed.clear()
        if self._asked and self._on_models is not None:
            self._asked = False
            self._on_models("close", {})
