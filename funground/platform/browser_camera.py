"""The camera for a host that owns the device (story S-172, Web_Runner_Note.md).

The page opens the camera (with the browser's permission) and pushes each frame to `HostCamera.push`; funground keeps
the latest. the camera library reads it as it reads a desktop camera, so nothing else differs. pygame is not imported.

`on_camera(command, fields)` is told what the sketch wants:

    start     {"width": w, "height": h}     open the camera and push frames at about this size
    stop      {}                            stop the frames (the sketch let the camera go)
    close     {}                           the run ended: release the camera for good

If the page cannot open the camera (refused, none, busy) it calls `unavailable(reason)`, which prints one line for
the learner. Without `on_camera` nothing asks the page for frames, so the camera never becomes ready.
"""
from __future__ import annotations

from array import array
from collections.abc import Callable

from ..export import motion

CameraCallback = Callable[[str, dict], None]


class HostCamera:
    """The host's camera: the page pushes RGBA frames to `push`, and a Camera reads them with `read`."""

    def __init__(self, on_camera: CameraCallback | None = None) -> None:
        self._on_camera = on_camera
        self._started = False
        self._opened = False                     # a "start" has been sent since the last "close"
        self._reported = False                   # this start's unavailable line has been printed
        self._latest: tuple[bytes, int, int] | None = None     # RGBA pixels, width, height; None once read

    # ---- what the camera library calls (the device interface)
    def start(self, width: int, height: int) -> None:
        self._started = True
        self._opened = True
        self._reported = False
        self._latest = None
        self._request("start", width=width, height=height)

    def stop(self) -> None:
        self._started = False
        self._latest = None
        self._request("stop")

    def read(self, width: int, height: int, mirror: bool) -> bytes | None:
        """The frame pushed since the last read, as BGRA scaled to width x height (mirrored if asked), or None."""
        latest, self._latest = self._latest, None
        if latest is None:
            return None
        rgba, from_width, from_height = latest
        bgra = _rgba_to_bgra(rgba)
        if (from_width, from_height) != (width, height):
            bgra = motion.resample_bgra(bgra, from_width, from_height, width, height)
        return _mirrored(bgra, width, height) if mirror else bgra

    # ---- what the host calls
    def push(self, pixels, width: int, height: int) -> None:
        """One frame from the page: RGBA bytes, row by row from the top left, `width * height * 4` of them.
        Frames the sketch has not used yet are replaced, never queued. Ignored when the sketch has not started the camera."""
        if self._on_camera is None or not self._started:
            return
        data = bytes(pixels)
        if width <= 0 or height <= 0 or len(data) != width * height * 4:
            raise ValueError(f"a camera frame must be width * height * 4 bytes of RGBA; got {len(data)} bytes "
                             f"for {width} x {height}")
        self._latest = (data, width, height)

    def unavailable(self, reason: str) -> None:
        """The page could not open the camera. Prints one line per start; the camera stays not ready."""
        if not self._started or self._reported:
            return
        self._reported = True
        print(f"The camera is not available: {str(reason).rstrip('. ')}.")

    def close(self) -> None:
        """Let go of the camera, if a sketch opened it."""
        self._started = False
        self._latest = None
        if self._opened:
            self._opened = False
            self._request("close")

    def _request(self, command: str, **fields) -> None:
        if self._on_camera is not None:
            self._on_camera(command, fields)


def _rgba_to_bgra(rgba: bytes) -> bytes:
    """Swap red and blue, and make every pixel opaque (a camera has no see-through parts)."""
    out = bytearray(len(rgba))
    out[0::4], out[1::4], out[2::4] = rgba[2::4], rgba[1::4], rgba[0::4]
    out[3::4] = b"\xff" * (len(rgba) // 4)
    return bytes(out)


def _mirrored(bgra: bytes, width: int, height: int) -> bytes:
    """Every row of 4-byte pixels turned round, left to right."""
    pixels = array("I")
    pixels.frombytes(bgra)
    out = array("I")
    for y in range(height):
        row = pixels[y * width:(y + 1) * width]
        row.reverse()
        out.extend(row)
    return out.tobytes()
