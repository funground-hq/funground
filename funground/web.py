"""The host API: how a web page (or a test) runs a learner's file (story S-152, Web_Runner_Note.md).

This is not learner API; learners never import it, and funground/__init__ does not export it.

    session = Session(640, 480, scale=2.0, on_frame=draw_on_canvas)
    session.start(source, "sketch.py")      # runs the file; for an animated sketch, setup() has run
    while session.step(now_seconds):        # once per display frame; False when the sketch ended
        pass
    session.stop()                          # always; ends the run and runs the sketch's finish()

How "a host is active" works. A Session builds the sketch with a BrowserPlatform, and that platform says
`host_driven = True`. The sketch reads this one flag where the desktop would run a loop of its own:
`f.run()` calls `Sketch.start()` and returns, and `f.show()` presents the drawing and returns. The
Session then calls `Sketch.step()` itself. Nothing else differs, and with no Session the flag is
absent, so the desktop paths run exactly as before (contract W1).

Running again in the same Python (D-083). A host may run the next file in the same interpreter, with a
new Session each time. A new Session starts afresh: the sketch and its namespace, random and noise,
sound, the microphone, fonts loaded from files, and modules imported from the sketch's own folder (an
edited helper is read again). It shares what cannot be reset cheaply, or need not be:
the deterministic caches (colours, tables, shaped text, bundled fonts); the standard library's own
state, such as the `random` module when a sketch uses it directly; third-party modules once imported;
anything a sketch changes in a module it imported (for example replacing a funground function); and
files written to disk.
"""
from __future__ import annotations

import hashlib
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

from . import api, exploring, global_style, host_services, typography, web_fonts
from .platform.base import InputEvent
from .platform.browser import BrowserPlatform, FrameCallback
from .platform.browser_audio import MicrophoneCallback, SoundCallback
from .platform.browser_camera import CameraCallback
from .sketch import Sketch


def _checked_fetcher(fetch_font: Callable[[str], Any], fonts: dict[str, dict[str, Any]]) -> Callable[[str], bytes]:
    """Wrap the host's `fetch_font` for typography: bytes out, and checked against the manifest's size and SHA-256."""
    def fetch(name: str) -> bytes:
        try:
            result = fetch_font(name)
        except Exception as error:                 # the network, or the host: one plain line, not a JavaScript trace
            raise OSError(f"The font {name} could not be downloaded ({error}). Check the connection and run again.") from None
        data = result.to_bytes() if hasattr(result, "to_bytes") else bytes(result)    # a JsProxy, or bytes
        expected = fonts.get(name)
        if expected is not None and len(data) != expected["size"]:
            raise OSError(f"The font {name} does not match the runtime's manifest: {len(data)} bytes, expected {expected['size']}.")
        if expected is not None and hashlib.sha256(data).hexdigest() != expected["sha256"]:
            raise OSError(f"The font {name} does not match the runtime's manifest: its SHA-256 differs.")
        return data
    return fetch


def _checked_url_fetcher(fetch_url: Callable[[str], Any]) -> Callable[[str], bytes]:
    """Wrap the host's `fetch_url` for web_fonts (S-230): bytes out, and any failure one plain ConnectionError."""
    def fetch(address: str) -> bytes:
        try:
            result = fetch_url(address)
            return result.to_bytes() if hasattr(result, "to_bytes") else bytes(result)      # a JsProxy, or bytes
        except Exception:
            raise ConnectionError(
                f"f.load_font(): the browser could not download '{address}'. The site may not allow it, "
                "or there is no connection. Download the file and use Add file.") from None
    return fetch


class Session:
    """One learner's file, run by a host that owns the canvas, the clock and the input.

    `width` and `height` are the host's canvas in logical pixels (what f.full_screen() fills);
    `scale` is the backing scale (physical pixels per logical pixel); `on_frame(data, width, height,
    stride)` receives each finished frame as BGRA bytes (see platform.browser).

    Sound and the microphone go through the host too (S-137): `on_sound(command, voice, fields, samples)`
    plays what the sketch makes, `on_microphone(command)` is asked to start and stop the input, and
    `push_microphone(samples)` delivers what it heard (platform.browser_audio has the commands). Without
    these callbacks sounds play silently and keep time, and the microphone hears nothing.

    The camera goes through the host as well (S-172): `on_camera(command, fields)` is told "start" (with the
    width and height the sketch asked for), "stop" and "close", and `push_camera(pixels, width, height)` delivers a
    frame as RGBA bytes, row by row, `width * height * 4` of them, at the size asked (a frame of another size is
    scaled). The sketch mirrors it when it asked for that. `camera_unavailable(reason)` tells the Session that the
    page could not open the camera: it prints one line, "The camera is not available: ...", for each start, and
    the camera stays not ready. Without `on_camera` the camera never becomes ready.

    The bundled fonts are not in the browser's package (S-211, D-114): `fetch_font(file name)` is called the first
    time funground opens one, and returns its bytes (bytes, or a JavaScript Uint8Array or ArrayBuffer). `fonts`
    maps each file name to {"size": bytes, "sha256": hex} from the host's manifest; a font that differs raises
    an OSError naming it. Without `fetch_font` the fonts are the files of the package, as on a computer.

    A font at a web address (S-230) is downloaded by the host too: `fetch_url(address)` returns the bytes (bytes, or a
    JavaScript Uint8Array or ArrayBuffer). When it fails, the sketch gets a ConnectionError that says to use Add file.
    Without `fetch_url` funground downloads with urllib, as on a computer."""

    def __init__(self, width: int, height: int, scale: float = 1.0, on_frame: FrameCallback | None = None,
                 on_sound: SoundCallback | None = None, on_microphone: MicrophoneCallback | None = None,
                 on_camera: CameraCallback | None = None, fetch_font: Callable[[str], Any] | None = None,
                 fonts: dict[str, dict[str, Any]] | None = None,
                 fetch_url: Callable[[str], Any] | None = None) -> None:
        web_fonts.set_url_fetcher(_checked_url_fetcher(fetch_url) if fetch_url is not None else None)
        if fetch_font is not None:
            typography.set_font_fetcher(_checked_fetcher(fetch_font, fonts or {}))
        self._platform = BrowserPlatform(width, height, scale, on_frame, on_sound, on_microphone, on_camera)
        host_services.mixer = self._platform.mixer
        host_services.microphone = self._platform.microphone
        host_services.camera = self._platform.camera
        self._sketch = api.use_sketch(Sketch(platform=self._platform))
        self._stopped = False
        self._font_mark = typography.file_font_mark()
        self._folder: Path | None = None            # the sketch's folder, known once start() is called
        self._file: Path | None = None              # the sketch's file name in that folder (it need not exist on disk)
        self._source: str | None = None             # the sketch's code, kept so keep() can save a copy
        self._modules_before: set[str] = set()

    @property
    def canvas_size(self) -> tuple[int, int]:
        """The sketch's canvas in logical pixels, as the file set it with f.size()."""
        return (self._sketch.width, self._sketch.height)

    @property
    def running(self) -> bool:
        """True from the end of start() until the sketch ends or stop() is called."""
        return self._sketch.running

    def start(self, source: str, filename: str = "sketch.py") -> None:
        """Run the learner's file as `python sketch.py` does. An error in it ends the Session and is raised to the host.

        A file that ends with f.run() is left with setup() done and no frame drawn: call step(). A
        script (ends with f.show()) has presented its drawing(s) and is finished."""
        namespace = {"__name__": "__main__", "__file__": filename}
        self._font_mark = typography.file_font_mark()
        self._file = Path(filename).resolve()
        self._folder = self._file.parent
        self._source = source
        self._modules_before = set(sys.modules)
        try:
            exec(compile(source, filename, "exec"), namespace)
            if callable(namespace.get("draw")) and not (self._sketch.started or self._sketch._script):
                self._sketch.run_namespace(namespace)     # a file that defines draw() and never called run() (D-088)
            elif self._sketch.unseen_drawing:
                self._sketch.show()                       # a script that never called f.show() (S-180)
        except BaseException as error:
            global_style.explain_clash(error, namespace)  # a global-style script's error at the top level
            self.stop()
            raise

    def keep(self, note: str = "") -> str:
        """Keep this run's picture, as f.keep(note) does in the sketch: studio/NNN.png, .py and .json in the
        sketch's folder (the code is the code this Session was started with). Returns the path without its ending.

        The host calls this between frames, so the last frame drawn is complete: the files are written now, before
        keep() returns, whether the sketch still draws (the frame on screen is kept, as when f.keep() runs after
        f.no_loop()) or has stopped drawing (a script that has finished). Before the first frame of an animated
        sketch there is nothing drawn yet, so the keep waits for that frame, which the next step() draws. Raises
        RuntimeError when the run has been stopped or has ended, because its picture is gone."""
        if self._stopped or self._file is None:
            raise RuntimeError("The sketch is not running, so there is no picture to keep. Run it, then keep.")
        base = exploring.keep_sketch(note, False, {}, str(self._file), self._source)
        sketch = self._sketch
        if not sketch._script and sketch.frame_count > 0:
            sketch._run_frame_end(False)            # the frame on screen is complete: write now, not at the next frame's end
        return base

    def push_event(self, kind: str, x: int = 0, y: int = 0, button: str | None = None, key: str | None = None,
                   key_code: int | None = None, delta: float = 0.0) -> None:
        """Queue one input event for the next step. The vocabulary is InputEvent's (platform.base):
        a kind from EVENT_KINDS, logical x and y, a button from MOUSE_BUTTONS, a key as a character or
        a KEY_NAMES entry. Unknown kinds and buttons raise ValueError."""
        self._platform.push_event(InputEvent(kind, x, y, button, key, key_code, delta))

    def step(self, now: float) -> bool:
        """Run one frame. `now` is the host's clock in seconds (requestAnimationFrame time / 1000).

        Returns True while the sketch goes on. When it ends (f.stop(), max_frames) or raises, the run is
        finished first, so the host only has to stop displaying; an exception is raised to the host."""
        if not self._sketch.running:
            return False
        self._platform.set_time(now)
        if not self._platform.frame_due(self._sketch.fps):
            return True                     # too early for the sketch's frame rate: events wait for the next frame
        try:
            going = self._sketch.step()
        except BaseException:
            self.stop()
            raise
        if not going:
            self.stop()
        return going

    def push_microphone(self, samples) -> None:
        """Mono samples from -1 to 1 at 44 100 Hz that the host's microphone heard. Used while the sketch listens."""
        self._platform.push_microphone(samples)

    def push_camera(self, pixels, width: int, height: int) -> None:
        """One frame from the host's camera: RGBA bytes, row by row from the top left, `width * height * 4` of them,
        at the size "start" asked for (another size is scaled). Used while the sketch has the camera started."""
        self._platform.push_camera(pixels, width, height)

    def camera_unavailable(self, reason: str) -> None:
        """The page could not open the camera (refused, none, busy). Prints one line to the sketch's output for each
        start; the camera stays not ready."""
        self._platform.camera.unavailable(reason)

    def stop(self) -> None:
        """End the run: the sketch's finish() runs, once; sounds stop and the microphone and camera are let go. Safe to call again."""
        if self._stopped:
            return
        self._stopped = True
        try:
            self._sketch.finish()
        finally:
            host_services.mixer = None
            host_services.microphone = None
            host_services.camera = None
            web_fonts.set_url_fetcher(None)
            api.use_sketch(None)
            typography.forget_file_fonts(self._font_mark)
            self._forget_sketch_modules()

    def _forget_sketch_modules(self) -> None:
        """Drop the modules the run imported from the sketch's folder, so the next run reads them again.
        funground's own modules stay, even when the sketch sits beside the package."""
        if self._folder is None:
            return
        for name in set(sys.modules) - self._modules_before:
            path = getattr(sys.modules[name], "__file__", None)
            if path and name.partition(".")[0] != "funground" and Path(path).resolve().is_relative_to(self._folder):
                del sys.modules[name]
