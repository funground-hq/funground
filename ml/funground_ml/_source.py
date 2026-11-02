"""What a model reads from: a camera or a picture, and what is remembered for each one (D-125).

A camera gives the same Picture object for every frame and writes the new frame into it, so a picture's identity alone
cannot say whether a frame is new. The picture's version can: it changes when its pixels change (contract I4: the frame is
taken once before each ``draw()``, so every call in one frame sees one version). The answer is kept per source and task,
keyed on the picture and its version, so asking twice in a frame gives the same result and does no work.
"""
from __future__ import annotations

import weakref
from typing import Any, Callable

from funground.picture import FrameSource, Picture

# numpy and Pillow (through _glue and PIL) are imported inside the functions that need them, on the desktop path only: in a
# web page the models run in the page, and importing this module must pull in neither (Web_Runner_Note.md).


class Frame:
    """The picture to read now, as Pillow sees it."""

    def __init__(self, picture: Picture, mirrored: bool) -> None:
        # Reading the pixels draws anything the picture has waiting, then gives a frozen copy and its version.
        self._snapshot = picture._snapshot()
        self.picture = picture
        self.version: int = self._snapshot.version
        self.mirrored = mirrored

    def image(self):
        """The pixels as a Pillow RGB image. See-through pixels count as black (the pixels are premultiplied)."""
        from PIL import Image

        snap = self._snapshot
        bgra = Image.frombuffer("RGBA", (snap.phys_width, snap.phys_height), snap.pixels, "raw", "BGRA", 0, 1)
        return bgra.convert("RGB")

    def rgba(self) -> tuple[bytes, int, int]:
        """The pixels as opaque RGBA bytes for the page's models, and their width and height. As in image(), see-through
        pixels count as black."""
        snap = self._snapshot
        bgra = snap.pixels
        out = bytearray(len(bgra))
        out[0::4], out[1::4], out[2::4] = bgra[2::4], bgra[1::4], bgra[0::4]
        out[3::4] = b"\xff" * (len(bgra) // 4)
        return bytes(out), snap.phys_width, snap.phys_height

    def to_logical(self, x: float, y: float, size: tuple[int, int] | None = None) -> tuple[float, float]:
        """Pixel coordinates of the image as coordinates of the source as drawn (they differ on a high-density picture).
        *size* is the width and height of the picture the coordinates are in, when that is not this frame's own."""
        snap = self._snapshot
        width, height = size or (snap.phys_width, snap.phys_height)
        return x * snap.logical_width / width, y * snap.logical_height / height


class _State:
    """What is kept for one source and one task."""

    def __init__(self, key: int) -> None:
        self.key = key                          # id() of the source: how the page's models tell sources apart
        self.picture: weakref.ref | None = None
        self.version = -1
        self.stamp = 0
        self.result: Any = None
        self.requested: tuple | None = None      # (picture, version) last sent to the page's models
        self._tracker: Any = None

    @property
    def tracker(self):
        """The box that is reused from picture to picture (desktop only; made, and numpy imported, on first use)."""
        if self._tracker is None:
            from ._glue import Tracker

            self._tracker = Tracker()
        return self._tracker

    def get(self, frame: Frame, stamp: int) -> tuple[bool, Any]:
        """(True, the result) when this is the picture and version (and stamp) the result was made for."""
        if (self.picture is not None and self.picture() is frame.picture and self.version == frame.version
                and self.stamp == stamp):
            return True, self.result
        return False, None

    def put(self, frame: Frame, stamp: int, result: Any) -> None:
        self.picture, self.version, self.stamp, self.result = weakref.ref(frame.picture), frame.version, stamp, result


_states: "weakref.WeakKeyDictionary[Any, dict[str, _State]]" = weakref.WeakKeyDictionary()


def open_source(source: object, who: str) -> tuple[Frame, object] | None:
    """The Frame to read and the object the memory is kept on, or None when a camera has no frame yet.

    Raises:
        TypeError: if *source* is neither a Picture nor a camera.
    """
    if isinstance(source, Picture):
        return Frame(source, False), source
    if isinstance(source, FrameSource):
        picture = source._current_picture()
        if picture is None:
            return None
        # A camera started with mirror=True (the default) gives mirrored pictures.
        return Frame(picture, getattr(source, "_mirror", False) is True), source
    raise TypeError(f"{who} needs a camera from camera.open() or a picture from f.load_image(), "
                    f"not {type(source).__name__}.")


def answer(source: object, task: str, who: str, make: Callable[[Frame, _State], Any],
           stamp: Callable[[], int] = lambda: 0) -> Any:
    """The result of *task* for *source*: the one kept for this frame, or ``make(frame, state)``, kept.

    ``state.tracker`` is the reused box (desktop). In a web page the answer also depends on what the page's models have
    sent, and that only changes between two frames, so *stamp()* (their count of results) is part of what is kept: a
    still picture is answered again when a result arrives for it, and the same frame still gets one answer.

    Returns None when a camera has no frame yet. *make* may return None (nobody there); that is kept too.
    """
    opened = open_source(source, who)
    if opened is None:
        return None
    frame, owner = opened
    states = _states.setdefault(owner, {})
    if task not in states:
        states[task] = _State(id(owner))
    state, now = states[task], stamp()
    known, result = state.get(frame, now)
    if known:
        return result
    result = make(frame, state)
    state.put(frame, now, result)
    return result
