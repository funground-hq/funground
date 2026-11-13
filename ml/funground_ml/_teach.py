"""Teaching and guessing: the taught set, the thread that makes vectors, and the guess (S-235, contract ML8; D-145, D-146, D-147).

``ml.teach(name, picture)`` keeps a copy of the picture as one example of ``name``. A **picture model** (MobileNetV4-small, the default, or DINOv2-small) turns each example into a
vector, beside the sketch (one daemon thread for each taught set), so ``ml.teach`` never waits. ``ml.guess(source)`` turns the source
into a vector the same way and names the taught name whose nearest example it is closest to.

* The **TaughtSet** is one for each sketch (a weak dictionary keyed on the sketch, so a new run starts empty). It keeps the names
  in the order they were first taught, each with its examples. An example has a vector, or is still waiting for one.
* The **_Worker** is the thread. Its queue of teaching jobs is first in, first out: every taught picture becomes a vector. A camera
  that is being guessed has one slot of its own that holds only the newest frame. Teaching jobs go before guessing jobs.
* The **_Similarities** are one answer's cosine similarities, name by name. The Guess for each ``k`` is cut from them.

numpy is imported inside the functions that need it (desktop only); importing this module loads neither numpy nor onnxruntime.
"""
from __future__ import annotations

import threading
import weakref
from collections import deque
from dataclasses import dataclass
from typing import Any, Callable

from funground import host_services
from funground.api import canvas_sketch
from funground.picture import FrameSource, Picture

from . import _pictures, _source, _tasks
from ._results import Guess

MODEL_NAMES = ("dinov2", "mobilenet")
DEFAULT_MODEL = "mobilenet"        # D-147
FEW_EXAMPLES = 5                    # a name with fewer examples than this gets the hint
MARGIN = 0.1                        # a lead of this much in similarity over the runner-up scores 0.95
LOWEST, HIGHEST = 0.05, 0.95
ONE_NAME_HINT = "Teach at least two things, so I can compare."


@dataclass(frozen=True)
class PictureModel:
    """One way to turn a picture into a vector: the model files to fetch (a task of ``_models.TASKS``), and ``load(paths)``,
    which makes the function from a Pillow RGB image to a unit-length float32 numpy vector. ``load`` runs in the worker thread."""
    task: str
    load: Callable[[dict[str, str]], Callable[[Any], Any]]


PICTURE_MODELS: dict[str, PictureModel] = {
    "dinov2": PictureModel("picture_dinov2", lambda paths: _pictures.load(paths, _pictures.dinov2_vector)),
    "mobilenet": PictureModel("picture_mobilenet", lambda paths: _pictures.load(paths, _pictures.mobilenet_vector)),
}


# ---- the worker thread
class _Slot:
    """Where a vector is put when the worker has made it. ``failed`` is set when the worker could not."""
    __slots__ = ("vector", "failed")

    def __init__(self) -> None:
        self.vector: Any = None
        self.failed = False

    @property
    def pending(self) -> bool:
        return self.vector is None and not self.failed


class _Example(_Slot):
    """One taught picture. It remembers which picture and version it came from, but does not keep the picture alive."""
    __slots__ = ("picture", "version")

    def __init__(self, picture: Picture, version: int) -> None:
        super().__init__()
        self.picture = weakref.ref(picture)
        self.version = version


class _Worker:
    """One daemon thread that makes vectors. It starts with the first job.

    *load* is ``() -> (image -> vector)``; it runs in the thread, so it can take its time to make the session. An error in the
    thread is kept and raised by the next ``check()``, in the sketch's thread; the job it was working on is lost (its slot is
    marked failed) and the thread goes on with the next one.
    """

    def __init__(self, load: Callable[[], Callable[[Any], Any]]) -> None:
        self._load = load
        self._condition = threading.Condition()
        self._jobs: deque[tuple[_source.Frame, _Slot]] = deque()      # teaching, and the pictures that wait: in order
        self._looks: dict[int, _source.Frame] = {}                    # camera key -> its newest frame, not yet taken
        self._vectors: dict[int, Any] = {}                            # camera key -> the newest vector that came back
        self._working = False                                         # a job from _jobs is being worked on
        self._error: BaseException | None = None
        self._closed = False
        self._thread: threading.Thread | None = None
        self.results = 0                                              # how many vectors have been made, ever

    def _start(self) -> None:
        if self._thread is None:
            self._thread = threading.Thread(target=self._run, name="funground teach", daemon=True)
            self._thread.start()

    def add(self, frame: _source.Frame, slot: _Slot) -> None:
        """Queue a picture: its vector goes into *slot*."""
        with self._condition:
            self._jobs.append((frame, slot))
            self._start()
            self._condition.notify_all()

    def look(self, key: int, frame: _source.Frame) -> None:
        """Queue a camera's frame for guessing. Only the newest frame waits: this one replaces an older one still waiting."""
        with self._condition:
            self._looks[key] = frame
            self._start()
            self._condition.notify_all()

    def newest(self, key: int) -> Any:
        """The newest vector made for the camera *key*, or None."""
        with self._condition:
            return self._vectors.get(key)

    def check(self) -> None:
        """Raise the error the thread stopped a job on, if there is one."""
        with self._condition:
            error, self._error = self._error, None
        if error is not None:
            raise error

    def wait_for(self, slot: _Slot) -> Any:
        """The vector in *slot*, waiting for it (after every job queued before it). Raises the thread's error."""
        with self._condition:
            self._condition.wait_for(lambda: not slot.pending or self._error is not None)
        self.check()
        return slot.vector

    def drain(self) -> None:
        """Wait until every picture queued so far has its vector. Raises the thread's error."""
        with self._condition:
            self._condition.wait_for(lambda: (not self._jobs and not self._working) or self._error is not None)
        self.check()

    def close(self) -> None:
        with self._condition:
            self._closed = True
            self._condition.notify_all()

    def _run(self) -> None:
        compute = None
        while True:
            with self._condition:
                while not self._jobs and not self._looks and not self._closed:
                    self._condition.wait()
                if self._closed:
                    return
                if self._jobs:
                    (frame, slot), key = self._jobs.popleft(), None
                    self._working = True
                else:
                    key = next(iter(self._looks))
                    frame, slot = self._looks.pop(key), None
            try:
                if compute is None:
                    compute = self._load()
                vector = compute(frame.image())
            except BaseException as error:           # kept for the sketch: a thread must not lose it
                with self._condition:
                    self._error = error
                    if slot is not None:
                        slot.failed = True
                    self._working = False
                    self._condition.notify_all()
                continue
            with self._condition:
                if slot is not None:
                    slot.vector = vector
                else:
                    self._vectors[key] = vector
                self.results += 1
                self._working = False
                self._condition.notify_all()


# ---- the answer
class _Similarities:
    """Each taught name's similarity to one source, the highest first (equal ones in the order taught)."""

    def __init__(self, ordered: list[tuple[str, float]]) -> None:
        self.ordered = ordered
        self._guesses: dict[int, Guess] = {}

    def _score(self, name: str, similarity: float) -> float:
        others = [s for n, s in self.ordered if n != name]
        if not others:
            return 0.5
        score = 0.5 + 0.5 * (similarity - max(others)) / MARGIN
        return min(HIGHEST, max(LOWEST, score))

    def guess(self, k: int) -> Guess:
        """The Guess listing the best *k* names; the same object for the same *k*."""
        found = self._guesses.get(k)
        if found is None:
            listed = [Guess(name, self._score(name, s)) for name, s in self.ordered[:k]]
            found = self._guesses[k] = Guess(listed[0].name, listed[0].score, tuple(listed[1:]))
        return found


class TaughtSet:
    """Everything taught in one sketch, and the thread that makes the vectors."""

    def __init__(self) -> None:
        self.names: dict[str, list[_Example]] = {}
        self.model: str | None = None
        self.worker: _Worker | None = None
        self.version = 0                                    # grows with every example added
        self._last_from: "weakref.WeakKeyDictionary[Any, _Example]" = weakref.WeakKeyDictionary()   # camera -> last taught
        self._hinted: set[str] = set()
        self._stamp_frame: int | None = None
        self._stamp_results = 0

    def use(self, name: str, paths: dict[str, str]) -> None:
        """Fix the picture model to *name*, and make the worker (its thread starts with the first job)."""
        entry = PICTURE_MODELS[name]
        self.model = name
        self.worker = _Worker(lambda: entry.load(paths))
        weakref.finalize(self, self.worker.close)

    def count(self, name: str) -> int:
        return sum(1 for example in self.names.get(name, ()) if not example.failed)

    def teach(self, name: str, item: object, who: str) -> None:
        """Add a copy of *item*'s picture to *name*, unless a rule says it adds nothing (contract ML8)."""
        is_picture = isinstance(item, Picture)
        if not is_picture:
            last = self._last_from.get(item)
            if last is not None and last.pending:           # D-146: a camera teaches one picture at a time
                return
        opened = _source.open_source(item, who)
        if opened is None:                                  # a camera with no frame yet
            return
        frame, owner = opened
        if any(e.picture() is frame.picture and e.version == frame.version for e in self.names.get(name, ())):
            return
        example = _Example(frame.picture, frame.version)
        self.names.setdefault(name, []).append(example)
        self.version += 1
        if not is_picture:
            self._last_from[owner] = example
        self.worker.add(frame, example)

    def stamp(self) -> int:
        """What the cached answers are keyed on, besides the picture: grows when anything is taught or a vector comes in.

        The vectors that come in are counted once for each frame, so every call in one frame gets the same answer; teaching
        counts at once, so a guess after teaching is fresh.
        """
        frame = _tasks._frame()
        if frame != self._stamp_frame:
            self._stamp_frame, self._stamp_results = frame, self.worker.results
        return self.version + self._stamp_results

    def similarities(self, vector: Any) -> _Similarities | None:
        """The similarity of *vector* to each name's nearest ready example, or None when no example is ready."""
        import numpy as np

        vector = np.asarray(vector, dtype=np.float32)
        ready = {name: [e.vector for e in examples if e.vector is not None] for name, examples in self.names.items()}
        ready = {name: vectors for name, vectors in ready.items() if vectors}
        if not ready:
            return None
        found = [(name, float(np.max(np.stack(vectors) @ vector))) for name, vectors in ready.items()]
        found.sort(key=lambda pair: -pair[1])               # a stable sort: equal similarities stay in the order taught
        self._hint(ready)
        return _Similarities(found)

    def _hint(self, ready: dict[str, list]) -> None:
        if len(ready) == 1 and "one" not in self._hinted:
            self._hinted.add("one")
            print(ONE_NAME_HINT)
        if "few" not in self._hinted and any(len(v) < FEW_EXAMPLES for v in ready.values()):
            self._hinted.add("few")
            name = min(ready, key=lambda n: len(ready[n]))          # the fewest; the first taught on a tie
            count = len(ready[name])
            print(f'"{name}" has {count} example{"" if count == 1 else "s"}. {FEW_EXAMPLES} or more of each makes better guesses.')


_sets: "weakref.WeakKeyDictionary[Any, TaughtSet]" = weakref.WeakKeyDictionary()


def _taught() -> TaughtSet:
    """The taught set of this sketch."""
    sketch = canvas_sketch()
    found = _sets.get(sketch)
    if found is None:
        found = _sets[sketch] = TaughtSet()
    return found


# ---- ml.teach
def _is_source(item: object) -> bool:
    return isinstance(item, (Picture, FrameSource))


def _describe(item: object) -> str:
    return f"a {type(item).__name__}"


def _check_name(name: object, who: str) -> None:
    if not isinstance(name, str):
        raise TypeError(f"{who} needs a name that is text, such as \"cat\", not {_describe(name)}.")
    if not name:
        raise ValueError(f"{who} needs a name that is not empty.")


def _check_items(items: object, name: str, who: str, listed: bool = False) -> list:
    """The pictures to teach under *name*: one source, or a list of them. Raises TypeError for anything else."""
    if isinstance(items, (list, tuple)):
        for position, item in enumerate(items):
            if not _is_source(item):
                raise TypeError(f"{who} needs a camera or a picture, but item {position} of the list for \"{name}\" is "
                                f"{_describe(item)}. (The first item is item 0.)")
        return list(items)
    if listed:
        raise TypeError(f"{who} needs a list of cameras or pictures for \"{name}\", not {_describe(items)}.")
    if not _is_source(items):
        raise TypeError(f"{who} needs a camera from camera.open() or a picture, or a list of them, not {_describe(items)}.")
    return [items]


def _plan(name: object, source: object, who: str) -> tuple[list[tuple[str, list]], bool]:
    """The (name, items) pairs to teach, in order, and whether the dict form was used. Raises TypeError or ValueError."""
    if isinstance(name, dict):
        if source is not None:
            raise TypeError(f"{who} takes either a dict of names and lists, or a name and something to teach, not both.")
        plan = []
        for key, value in name.items():
            _check_name(key, who)
            plan.append((key, _check_items(value, key, who, listed=True)))
        return plan, True
    _check_name(name, who)
    if source is None:
        raise TypeError(f"{who} needs a camera or a picture to learn from after the name \"{name}\".")
    return [(name, _check_items(source, name, who))], False


def _check_model(model: object, who: str) -> str | None:
    if model is None or (isinstance(model, str) and model in MODEL_NAMES):
        return model
    raise ValueError(f"{who}: model must be \"dinov2\" or \"mobilenet\", not {model!r}.")


def _use_model(taught: TaughtSet, chosen: str | None, base_dir: str | None, who: str) -> None:
    """Fix the picture model at the first teach (downloading its file, here in the sketch's thread); check it later on."""
    if taught.model is not None:
        if chosen is not None and chosen != taught.model:
            raise ValueError(f"{who}: this sketch already teaches with the \"{taught.model}\" picture model, so it cannot "
                             f"also use \"{chosen}\".")
        return
    name = chosen or DEFAULT_MODEL
    entry = PICTURE_MODELS[name]
    if host_services.models is not None:
        raise NotImplementedError(f"{who}: teaching is not built for Play yet (S-235).")
    from . import _fetch

    taught.use(name, _fetch.ensure(entry.task, base_dir, who))


def teach(name: object, source: object, model: object, base_dir: str | None):
    """Teach *source* under *name* (or a list, or a dict of names and lists); the number of examples, or a dict of them."""
    who = "ml.teach()"
    plan, is_dict = _plan(name, source, who)
    chosen = _check_model(model, who)
    taught = _taught()
    _use_model(taught, chosen, base_dir, who)
    taught.worker.check()
    counts = {}
    for taught_name, items in plan:
        for item in items:
            taught.teach(taught_name, item, who)
        counts[taught_name] = taught.count(taught_name)
    return counts if is_dict else counts[plan[0][0]]


# ---- ml.guess
def guess(source: object, k: object) -> Guess | None:
    """The name nearest to *source* among the taught ones, or None."""
    who = "ml.guess()"
    if isinstance(k, bool) or not isinstance(k, int):
        raise TypeError(f"{who} needs k to be a whole number, such as 1 or 3, not {_describe(k)}.")
    if k < 1:
        raise ValueError(f"{who} needs k to be 1 or more, not {k}.")
    taught = _sets.get(canvas_sketch())
    if taught is None or taught.worker is None:             # nothing taught: no model yet, so nothing to download
        _source.open_source(source, who)                    # (a source that is neither a camera nor a picture is still an error)
        return None
    worker = taught.worker
    worker.check()
    is_picture = isinstance(source, Picture)
    if is_picture:
        worker.drain()                                      # on a computer a picture waits for every example already queued
        vector = _source.answer(source, "guess vector", who, lambda frame, state: _wait_for(worker, frame))

    def make(frame: _source.Frame, state: _source._State) -> _Similarities | None:
        if not is_picture:
            sent = (id(frame.picture), frame.version)
            if state.requested != sent:                     # a new picture: its frame takes the place of one still waiting
                worker.look(state.key, frame)
                state.requested = sent
            found = worker.newest(state.key)
        else:
            found = vector
        return None if found is None else taught.similarities(found)

    similarities = _source.answer(source, "guess", who, make, stamp=taught.stamp)
    return None if similarities is None else similarities.guess(k)


def _wait_for(worker: _Worker, frame: _source.Frame) -> Any:
    slot = _Slot()
    worker.add(frame, slot)
    return worker.wait_for(slot)
