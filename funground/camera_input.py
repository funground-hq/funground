"""Camera input (S-172; contracts I4 and I5; D-089; Camera_Note.md).

With ``imaging.py`` and ``sound.py`` this is one of the few funground modules that uses pygame. It is the only one
that uses ``pygame.camera``, and all access to it is in ``_camera_module()``, ``_device_names()`` and
``_DesktopDevice``. pygame is imported when a camera is asked for, never when funground is imported.

A *device* is whatever delivers frames. The desktop's device wraps ``pygame.camera``; the web runner's device is the
page (``platform/browser_camera.HostCamera``, wired with ``use_host_camera``); tests use a fake. All three answer:

    start(width, height)              open it; RuntimeError if it cannot be opened
    read(width, height, mirror)       a new frame as ``width * height * 4`` bytes of BGRA (Cairo's layout), scaled to
                                      the asked size and mirrored if asked, or None when no new frame has arrived
    stop()                            let it go

A Camera never waits for a device. Before each ``draw()`` the sketch calls ``take_frames()``, which reads each started
camera once; the camera keeps that frame until the next draw, so every use in one frame sees the same picture. A
camera owns one Picture whose pixels are replaced by each new frame, so the IR names one picture with a new version
(contract P3).
"""
from __future__ import annotations

import os
import sys

from .sound import _is_headless

DEFAULT_SIZE = (640, 480)
MAX_SECONDS = 10

_MAC = ("f.camera(): the desktop camera works on Windows and Linux. On a Mac, run the sketch on the website (press "
        "Play) to use the camera")


def _no_device_message(extra: str = "") -> str:
    return ("f.camera(): " + (extra or "no camera was found on this computer")
            + ". Check that one is plugged in and that no other program is using it. On Windows, allow camera "
              "access in Settings, Privacy & security, Camera.")


# ---- a host's camera (the web runner)
_host_camera = None          # the host's camera while a web Session runs (platform/browser_camera.py), else None


def use_host_camera(host) -> None:
    """Use a host's camera (the web runner, Web_Runner_Note.md) instead of pygame's, or with None back to pygame.

    The host opens the device and pushes frames to ``host.push(...)``; a Camera reads them through the host's
    ``read``. See platform/browser_camera.HostCamera."""
    global _host_camera
    _host_camera = host


# ---- the one place that touches pygame.camera
def _camera_module():
    try:
        import pygame.camera as module
    except ImportError:
        raise RuntimeError("f.camera(): this copy of pygame has no camera support. Update it with: "
                           "pip install --upgrade pygame-ce") from None
    module.init()
    return module


def _device_names() -> list[str]:
    """The names of the computer's cameras."""
    module = _camera_module()
    try:
        return list(module.list_cameras())
    except Exception as exc:
        raise RuntimeError(_no_device_message(f"the computer's camera system did not answer ({exc})")) from exc


class _DesktopDevice:
    """A camera of the computer, through pygame.camera. Frames are scaled and mirrored with pygame's own transforms."""

    def __init__(self, name: str) -> None:
        self._name = name
        self._camera = None

    def start(self, width: int, height: int) -> None:
        module = _camera_module()
        try:
            camera = module.Camera(self._name, (width, height))
            camera.start()
        except Exception as exc:
            raise RuntimeError(_no_device_message(f"the camera {self._name!r} could not be opened ({exc})")) from exc
        self._camera = camera

    def read(self, width: int, height: int, mirror: bool) -> bytes | None:
        camera = self._camera
        if camera is None or not camera.query_image():          # query_image() never waits
            return None
        import pygame

        surface = camera.get_image()
        if surface.get_size() != (width, height):
            surface = pygame.transform.smoothscale(surface, (width, height))
        if mirror:
            surface = pygame.transform.flip(surface, True, False)
        return pygame.image.tobytes(surface, "BGRA")             # a camera frame has no see-through parts

    def stop(self) -> None:
        camera, self._camera = self._camera, None
        if camera is not None:
            try:
                camera.stop()
            except Exception:
                pass


# ---- the cameras that are started, and the frame taken before each draw()
_started: list["Camera"] = []


def take_frames(sketch) -> None:
    """Take the latest frame of every started camera, once. The sketch calls this before each draw()."""
    for camera in list(_started):
        camera._take(sketch)


def stop_all() -> None:
    """Stop every started camera (the sketch has ended)."""
    for camera in list(_started):
        camera.stop()


def cameras() -> list[str]:
    """The names of the computer's cameras. Empty when headless, in the browser (it picks the camera) and on a Mac."""
    if _host_camera is not None or _is_headless() or sys.platform == "darwin":
        return []
    return _device_names()


def make(name: str | None = None, canvas=None) -> "Camera":
    """A camera for the default device, or the first whose name contains *name* (I4).

    *canvas* is a function that returns the sketch the camera's pictures belong to."""
    if name is not None and (not isinstance(name, str) or not name):
        raise ValueError(f"f.camera(): name must be text such as 'USB', not {name!r}")
    if _host_camera is not None:
        if name is not None:
            raise RuntimeError("f.camera(name): choosing a camera by name only works in the desktop version. "
                               "In the browser, use f.camera() and choose the camera in the browser's own settings.")
        return Camera(None, canvas)
    if _is_headless():
        return Camera(None, canvas, silent=True)
    if sys.platform == "darwin":
        raise RuntimeError(_MAC)
    names = _device_names()
    if not names:
        raise RuntimeError(_no_device_message())
    if name is None:
        return Camera(names[0], canvas)
    for candidate in names:
        if name.lower() in candidate.lower():
            return Camera(candidate, canvas)
    raise RuntimeError(_no_device_message(f"no camera has {name!r} in its name (they are: "
                                          + ", ".join(repr(n) for n in names) + ")"))


def _whole(value, what: str, who: str) -> int:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value != int(value) or value <= 0:
        raise ValueError(f"{who}: {what} must be a whole number above 0, not {value!r}")
    return int(value)


class Camera:
    """A camera that your sketch can look through.

    You get one from f.camera(). Nothing opens until you call start(). Then the computer (or the browser) asks
    permission the first time, and frames begin to arrive.

    Use it like a picture: f.image(cam, 0, 0) draws its latest frame. cam.picture() gives you a still copy, to read
    pixels with get() or to change. cam.save("me.png") writes a photo. cam.record(3) keeps the next three seconds as
    a clip you can save as a GIF.

    The frame is taken once before each draw(), so everything you do in one frame sees the same picture. Before the
    first frame arrives, f.image(cam) draws nothing and cam.picture() is black, so use is_ready() to know when to
    start. Every frame is scaled to the size you asked for and, by default, flipped left to right like a mirror.
    Frames stay on your computer: funground never sends them anywhere. With FUNGROUND_HEADLESS=1 a camera opens
    nothing and is never ready.

    Example:
        cam = f.camera()
        cam.start()
        f.image(cam, 0, 0)

    See also: camera, cameras, Clip, image
    """

    def __init__(self, device_name: str | None, canvas=None, silent: bool = False) -> None:
        self._device_name = device_name
        self._canvas = canvas
        self._silent = silent
        self._device = None
        self._started = False
        self._width, self._height = DEFAULT_SIZE
        self._mirror = True
        self._frame: bytes | None = None             # the latest frame, BGRA, width * height * 4 bytes
        self._picture = None                         # the one Picture that frames are written into
        self._recordings: list[Clip] = []

    @property
    def width(self) -> int:
        """The width of every frame, in pixels: the size asked in start(), or 640 before that.

        Example:
            print(cam.width, cam.height)

        See also: height, start
        """
        return self._width

    @property
    def height(self) -> int:
        """The height of every frame, in pixels: the size asked in start(), or 480 before that.

        Example:
            print(cam.width, cam.height)

        See also: width, start
        """
        return self._height

    # ---- opening and closing
    def start(self, width: int = 640, height: int = 480, mirror: bool = True) -> None:
        """Open the camera.

        The computer or the browser may ask your permission first. Frames are scaled to width and height, so your
        layout never depends on the camera. Call it again with other numbers to change the size. The camera closes
        when you call stop() and when the sketch ends.

        Arguments:
            width, height: the size of every frame in pixels, whole numbers above 0.
            mirror: True (the default) flips each frame left to right, like a mirror. False shows what the camera sees.

        Raises:
            ValueError: if width or height is not a whole number above 0.
            RuntimeError: if the camera is busy, or the computer will not let funground use it.

        Example:
            cam = f.camera()
            cam.start(320, 240)

        See also: stop, is_ready, picture
        """
        width, height = _whole(width, "width", "cam.start()"), _whole(height, "height", "cam.start()")
        if not isinstance(mirror, bool):
            raise ValueError(f"cam.start(): mirror must be True or False, not {mirror!r}")
        if self._started and (width, height, mirror) == (self._width, self._height, self._mirror):
            return
        self.stop()
        self._width, self._height, self._mirror = width, height, mirror
        if not self._silent:
            if self._device is None:
                self._device = _host_camera if _host_camera is not None else _DesktopDevice(self._device_name)
            self._device.start(width, height)
        self._started = True
        _started.append(self)

    def stop(self) -> None:
        """Let go of the camera, so its light goes off.

        A recording that is still going ends early, and what it kept stays. After stop(), is_ready() is False and
        f.image(cam) draws nothing, until you call start() again. funground calls it when a sketch ends.

        Example:
            cam.stop()

        See also: start, record
        """
        if not self._started:
            return
        self._started = False
        if self in _started:
            _started.remove(self)
        for clip in self._recordings:
            clip._end()
        self._recordings.clear()
        self._frame = None
        if self._device is not None:
            self._device.stop()

    def is_ready(self) -> bool:
        """Whether a frame has arrived.

        Returns:
            True once the camera is started and its first frame has come, otherwise False. It stays False if you
            refuse permission, and always with FUNGROUND_HEADLESS=1.

        Example:
            if not cam.is_ready():
                f.text("Waiting for the camera", 20, 40)

        See also: start, picture
        """
        return self._frame is not None

    # ---- the frame
    def _take(self, sketch) -> None:
        """Read the device once (the sketch calls this before each draw) and keep what recordings need."""
        if self._device is not None:
            frame = self._device.read(self._width, self._height, self._mirror)
            if frame is not None:
                self._frame = frame
                self._show(sketch, frame)
        if self._frame is not None:
            for clip in list(self._recordings):
                clip._keep(self._frame)
                if clip.done:
                    self._recordings.remove(clip)

    def _show(self, sketch, frame: bytes) -> None:
        """Put the frame into the camera's own picture: the same picture, with a new version."""
        picture = self._picture
        if picture is None or (picture.width, picture.height) != (self._width, self._height):
            self._picture = self._new_picture(sketch, frame)
        else:
            picture._write_pixels(frame)

    def _new_picture(self, sketch, bgra: bytes):
        from .picture import Picture

        picture = Picture.from_pixels(self._width, self._height, bgra, sketch._next_graphics_name())
        picture._sketch._name_root = sketch._name_root or sketch
        return picture

    def _current_picture(self):
        """The picture f.image() draws, or None before the first frame."""
        return self._picture if self._frame is not None else None

    def picture(self):
        """Make a still picture from the latest frame.

        It is a new, ordinary picture that is yours to keep: later frames do not change it. Read its pixels with
        get(x, y), change them, filter it, or draw on it. Before the first frame it is black, at the size you asked.

        Returns:
            a new Picture, as wide and high as the camera's frames.

        Example:
            shot = cam.picture()
            colour = shot.get(100, 100)

        See also: save, is_ready, image
        """
        frame = self._frame if self._frame is not None else b"\x00\x00\x00\xff" * (self._width * self._height)
        return self._new_picture(self._canvas(), frame)

    def save(self, path: str) -> None:
        """Save the latest frame as a photo.

        The file type comes from the name: .png, or .jpg (a .jpg needs Pillow: pip install funground[extras]). It
        writes a new file. Before the first frame the photo is black.

        Arguments:
            path: the file name, such as "me.png".

        Raises:
            ValueError: if the name does not end in .png, .jpg or .jpeg.
            RuntimeError: for a .jpg, if Pillow is not installed.

        Example:
            cam.save("me.png")

        See also: picture, record
        """
        ending = os.path.splitext(path)[1].lower() if isinstance(path, str) else ""
        if ending == ".png":
            self.picture().save(path)
        elif ending in (".jpg", ".jpeg"):
            from .export import motion

            image = motion._pillow()
            if image is None:
                raise RuntimeError("cam.save(): a .jpg photo needs Pillow. Install it with:  pip install funground[extras]"
                                   "  or save a .png instead.")
            frame = self._frame if self._frame is not None else b"\x00\x00\x00\xff" * (self._width * self._height)
            image.frombytes("RGB", (self._width, self._height),
                            motion.bgra_to_rgb(frame, self._width, self._height)).save(path)
        else:
            raise ValueError(f"cam.save(): a photo must end in .png, .jpg or .jpeg, not {path!r}")

    # ---- clips
    def record(self, seconds: float) -> "Clip":
        """Start keeping the frames of the next few seconds.

        It returns a clip at once, and the clip fills as the sketch draws. One frame is kept for each frame the
        sketch draws while the camera is ready, so a full clip holds seconds times the frame rate. The clip is held
        in memory, so it is limited to 10 seconds. Nothing is written until you call clip.save().

        Arguments:
            seconds: how long to record, more than 0 and at most 10.

        Returns:
            a Clip that is empty now and full after the time has passed. Check clip.done.

        Raises:
            ValueError: if seconds is not more than 0 and at most 10. The message says how much memory a longer clip needs.
            RuntimeError: if the camera is not started.

        Example:
            clip = cam.record(3)
            # later, when clip.done is True:
            clip.save("me.gif")

        See also: Clip, stop, save
        """
        sketch = self._canvas()
        who = "cam.record()"
        if not self._started:
            raise RuntimeError(f"{who}: the camera is not started. Call cam.start() first.")
        if isinstance(seconds, bool) or not isinstance(seconds, (int, float)) or not seconds > 0:
            raise ValueError(f"{who}: seconds must be more than 0 and at most {MAX_SECONDS}, not {seconds!r}")
        if seconds > MAX_SECONDS:
            megabytes = self._width * self._height * 4 * sketch.fps * seconds / 1_000_000
            raise ValueError(f"{who}: a clip can be at most {MAX_SECONDS} seconds, because every frame stays in memory. "
                             f"{seconds:g} seconds at {self._width} x {self._height} and {sketch.fps} frames a second "
                             f"would need about {megabytes:,.0f} MB.")
        clip = Clip(self._width, self._height, sketch.fps, max(1, round(seconds * sketch.fps)), self._canvas)
        self._recordings.append(clip)
        return clip


class Clip:
    """A few seconds of camera frames, kept in memory.

    You get one from cam.record(). It fills while the sketch draws. When clip.done is True it is full. len(clip)
    is how many frames it holds, clip.frame(i) is one of them as a picture, and clip.save("me.gif") writes it as
    an animated GIF (or an MP4 on a computer with the video extra). Nothing is written to a file until you save.

    Example:
        clip = cam.record(2)
        if clip.done:
            clip.save("me.gif")

    See also: Camera, record
    """

    def __init__(self, width: int, height: int, fps: int, total: int, canvas) -> None:
        self._width = width
        self._height = height
        self._fps = fps
        self._total = total
        self._canvas = canvas
        self._frames: list[bytes] = []
        self._ended = False                          # cam.stop() ended the recording before it was full

    @property
    def fps(self) -> int:
        """How many frames a second the clip plays: the sketch's frame rate when it was recorded.

        Example:
            print(clip.fps)

        See also: done
        """
        return self._fps

    @property
    def done(self) -> bool:
        """Whether the recording is over, so nothing more will be added.

        It is True when the clip is full, or when cam.stop() ended the recording early. Check len(clip) to see how
        many frames it holds.

        Example:
            if clip.done:
                clip.save("me.gif")

        See also: save
        """
        return self._ended or len(self._frames) >= self._total

    def __len__(self) -> int:
        return len(self._frames)

    def _end(self) -> None:
        self._ended = True

    def _keep(self, frame: bytes) -> None:
        if not self.done:
            self._frames.append(frame)

    def frame(self, i: int):
        """Make a picture from one frame of the clip.

        Arguments:
            i: the frame number. 0 is the first. A negative number counts from the end, so -1 is the last.

        Returns:
            a new Picture.

        Raises:
            IndexError: if there is no frame i.

        Example:
            first = clip.frame(0)
            last = clip.frame(-1)

        See also: save, done
        """
        if isinstance(i, bool) or not isinstance(i, int):
            raise TypeError(f"clip.frame() needs a whole number, not {i!r}")
        if not -len(self._frames) <= i < len(self._frames):
            raise IndexError(f"clip.frame({i}): this clip has {len(self._frames)} frames")
        from .picture import Picture

        sketch = self._canvas()
        picture = Picture.from_pixels(self._width, self._height, self._frames[i], sketch._next_graphics_name())
        picture._sketch._name_root = sketch._name_root or sketch
        return picture

    def save(self, path: str) -> None:
        """Write the frames kept so far to a file.

        The file type comes from the name. A .gif is an endless animation and works everywhere. An .mp4 is a movie:
        it works on a computer with the video extra (pip install funground[video]), not in the browser. It writes a
        new file.

        Arguments:
            path: the file name, such as "me.gif".

        Raises:
            ValueError: if the name does not end in a type that works, or the clip has no frames yet.
            RuntimeError: if the computer has nothing to write that type with.

        Example:
            clip.save("me.gif")

        See also: frame, done
        """
        from .export import motion

        works = ".gif" if _host_camera is not None else ".gif or .mp4"
        ending = os.path.splitext(path)[1].lower() if isinstance(path, str) else ""
        if ending not in (".gif", ".mp4") or (ending == ".mp4" and _host_camera is not None):
            raise ValueError(f"clip.save(): the file name must end in {works}, not {path!r}")
        if not self._frames:
            raise ValueError("clip.save(): the clip has no frames yet. Wait until len(clip) is more than 0, "
                             "and check that the camera is ready.")
        motion.require_encoder(ending[1:])
        size = (self._width, self._height)
        frames = [motion.bgra_to_rgb(frame, *size) for frame in self._frames]
        durations = [1.0 / self._fps] * len(frames)
        (motion.write_gif if ending == ".gif" else motion.write_mp4)(path, frames, size, durations)
