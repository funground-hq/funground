"""The camera library: the computer's camera, photos and short clips.

Bring it in with one line, then every call says ``camera.``::

    import funground as f
    from funground import camera

    cam = camera.open()

Name the camera object ``cam``, not ``camera``: ``camera = camera.open()`` would hide the library.

New in 0.2. During 0.2's development these were ``f.camera``, ``f.cameras`` and ``f.load_clip``; they never shipped
on ``f``. The library imports the core, and the core never imports it (ADR-007, S-247). The code is in the underscore module beside this file:
``_device`` (the Camera and Clip classes, and the device that delivers frames). The core serves the camera's frame
before each ``draw()`` through its ``frame_inputs`` registry, where this file registers it when it is imported.
"""
from __future__ import annotations

import sys
import types
from typing import TYPE_CHECKING

from .. import frame_inputs, moved_message
from ..api import _sketch_folder, canvas_sketch
from . import _device

if TYPE_CHECKING:
    from ._device import Camera, Clip

__all__ = ["open", "names", "load_clip"]


class _CameraLibrary(types.ModuleType):
    """The type of this module (D-123). Once ``from funground import camera`` has run, ``f.camera`` is this module, so
    old code that calls ``f.camera()`` would get Python's bare "module is not callable". Calling the module gives the
    one sentence that says what to write instead."""

    def __call__(self, *args, **kwargs):
        raise TypeError(moved_message("camera"))


# D-123: giving a module its own class is Python's documented way to give a module behaviour (types.ModuleType and
# assigning to a module's __class__; see "Customizing module attribute access" in the Python data model).
sys.modules[__name__].__class__ = _CameraLibrary

# The core serves a started camera's frame before each draw() and stops it when the sketch ends (contract I4).
frame_inputs.register(_device.take_frames, _device.stop_all)


def open(name: str | None = None) -> Camera:
    """Make a camera object for the computer's default camera.

    Nothing opens, and no light comes on, until you call cam.start(). Then use it like a picture: f.image(cam, 0, 0) draws its latest frame. cam.picture() gives a still copy whose pixels you can read with get(), cam.save("me.png") writes a photo, and cam.record(3) keeps three seconds as a clip you can save as a GIF. Frames stay on your computer. In the browser, press Play and allow the camera when it asks. On a Mac, the desktop camera does not work yet: run the sketch on the website. With FUNGROUND_HEADLESS=1 the camera opens nothing and is never ready.

    Arguments:
        name: part of the name of the camera to use. The default None uses the first camera. See names(). In the browser the browser chooses, so leave it out.

    Returns:
        A Camera: start(width, height, mirror), stop(), is_ready(), width, height, picture(), save(path) and record(seconds).

    Raises:
        ValueError: name is not text.
        RuntimeError: there is no camera, no camera has that name, or this is a Mac desktop.

    Example:
        cam = camera.open()
        cam.start()
        f.image(cam, 0, 0)

    See also: names, load_clip, image, load_image
    """
    return _device.make(name, canvas_sketch)


def names() -> list[str]:
    """Return the names of the computer's cameras.

    The list is empty in the browser, where the browser chooses the camera, and on a Mac desktop.

    Returns:
        A list of names. Give part of one to open().

    Example:
        print(camera.names())

    See also: open
    """
    return _device.cameras()


def load_clip(path: str) -> Clip:
    """Read an animated GIF or WebP file and return it as a clip.

    It is the same kind of clip that cam.record() gives, so a take saved from the photo booth can come back in another
    sketch: len(clip) counts its frames, clip.frame(i) is one of them as a picture, and clip.fps is how many frames a
    second it plays. A relative path is found next to the sketch file first, then in the current folder. A still
    picture gives a clip of one frame. The frame rate comes from the file's frame times; when they differ, the middle
    one is used.

    Arguments:
        path: the file name, such as "take.gif".

    Returns:
        A Clip that is complete: clip.done is True.

    Raises:
        FileNotFoundError: there is no such file.
        ValueError: the file is not a picture funground can read, or it is an SVG file.

    Example:
        take = camera.load_clip("take.gif")
        f.image(take.frame(f.frame_count % len(take)), 0, 0)

    See also: open, load_image
    """
    from ..typography import _resolve_path

    resolved = _resolve_path(path, _sketch_folder(), "camera.load_clip()", "clip")
    return _device.load_clip(resolved, canvas_sketch)
