"""What a model reads from: a camera or a picture, and what is remembered for each one (D-125).

A camera gives the same Picture object for every frame and writes the new frame into it, so a picture's identity alone
cannot say whether a frame is new. The picture's version can: it changes when its pixels change (contract I4: the frame is
taken once before each ``draw()``, so every call in one frame sees one version). The answer is kept per source and task,
keyed on the picture and its version, so asking twice in a frame gives the same result and does no work.
"""
from __future__ import annotations

import weakref
from typing import Any, Callable

from PIL import Image

from funground.picture import FrameSource, Picture

from ._glue import Tracker


class Frame:
    """The picture to read now, as Pillow sees it."""

    def __init__(self, picture: Picture, mirrored: bool) -> None:
        # Reading the pixels draws anything the picture has waiting, then gives a frozen copy and its version.
        self._snapshot = picture._snapshot()
        self.picture = picture
        self.version: int = self._snapshot.version
        self.mirrored = mirrored

    def image(self) -> Image.Image:
        """The pixels as a Pillow RGB image. See-through pixels count as black (the pixels are premultiplied)."""
        snap = self._snapshot
        bgra = Image.frombuffer("RGBA", (snap.phys_width, snap.phys_height), snap.pixels, "raw", "BGRA", 0, 1)
        return bgra.convert("RGB")

    def to_logical(self, x: float, y: float) -> tuple[float, float]:
        """Pixel coordinates of the image as coordinates of the source as drawn (they differ on a high-density picture)."""
        snap = self._snapshot
        return x * snap.logical_width / snap.phys_width, y * snap.logical_height / snap.phys_height


class _State:
    """What is kept for one source and one task."""

    def __init__(self) -> None:
        self.picture: weakref.ref | None = None
        self.version = -1
        self.result: Any = None
        self.tracker = Tracker()

    def get(self, frame: Frame) -> tuple[bool, Any]:
        """(True, the result) when this is the picture and version the result was made for."""
        if self.picture is not None and self.picture() is frame.picture and self.version == frame.version:
            return True, self.result
        return False, None

    def put(self, frame: Frame, result: Any) -> None:
        self.picture, self.version, self.result = weakref.ref(frame.picture), frame.version, result


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


def answer(source: object, task: str, who: str, make: Callable[[Frame, Tracker], Any]) -> Any:
    """The result of *task* for *source*: the one kept for this frame, or ``make(frame, tracker)``, kept.

    Returns None when a camera has no frame yet. *make* may return None (nobody there); that is kept too.
    """
    opened = open_source(source, who)
    if opened is None:
        return None
    frame, owner = opened
    state = _states.setdefault(owner, {}).setdefault(task, _State())
    known, result = state.get(frame)
    if known:
        return result
    result = make(frame, state.tracker)
    state.put(frame, result)
    return result
