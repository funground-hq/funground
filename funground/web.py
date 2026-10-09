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
"""
from __future__ import annotations

from . import api, microphone_input, sound
from .platform.base import InputEvent
from .platform.browser import BrowserPlatform, FrameCallback
from .platform.browser_audio import MicrophoneCallback, SoundCallback
from .sketch import Sketch


class Session:
    """One learner's file, run by a host that owns the canvas, the clock and the input.

    `width` and `height` are the host's canvas in logical pixels (what f.full_screen() fills);
    `scale` is the backing scale (physical pixels per logical pixel); `on_frame(data, width, height,
    stride)` receives each finished frame as BGRA bytes (see platform.browser).

    Sound and the microphone go through the host too (S-137): `on_sound(command, voice, fields, samples)`
    plays what the sketch makes, `on_microphone(command)` is asked to start and stop the input, and
    `push_microphone(samples)` delivers what it heard (platform.browser_audio has the commands). Without
    these callbacks sounds play silently and keep time, and the microphone hears nothing."""

    def __init__(self, width: int, height: int, scale: float = 1.0, on_frame: FrameCallback | None = None,
                 on_sound: SoundCallback | None = None, on_microphone: MicrophoneCallback | None = None) -> None:
        self._platform = BrowserPlatform(width, height, scale, on_frame, on_sound, on_microphone)
        sound.use_host_mixer(self._platform.mixer)
        microphone_input.use_host_input(self._platform.microphone)
        self._sketch = api.use_sketch(Sketch(platform=self._platform))
        self._stopped = False

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
        try:
            exec(compile(source, filename, "exec"), namespace)
        except BaseException:
            self.stop()
            raise

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

    def stop(self) -> None:
        """End the run: the sketch's finish() runs, once; sounds stop and the microphone is let go. Safe to call again."""
        if self._stopped:
            return
        self._stopped = True
        try:
            self._sketch.finish()
        finally:
            sound.use_host_mixer(None)
            microphone_input.use_host_input(None)
            api.use_sketch(None)
