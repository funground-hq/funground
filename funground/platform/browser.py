"""BrowserPlatform: the Platform for a host that owns the window (story S-152, Web_Runner_Note.md).

A web page (or a test) owns the canvas, the clock and the input. This platform opens no window and
never waits. What the host does:

  * gives the canvas size (`display_size`) and the backing scale when it builds the platform;
  * pushes input with `push_event(InputEvent(...))`; the next step delivers the events in order;
  * sets the time of each step with `set_time(seconds)`; `tick()` returns the seconds since the step before;
  * receives each finished frame through the `on_frame` callback;
  * receives sounds through `on_sound`, and the microphone's requests through `on_microphone`, and pushes what
    the microphone heard with `push_microphone(samples)` (platform/browser_audio.py has the commands);
  * receives the camera's requests through `on_camera`, and is pushed its frames with `push_camera(pixels, width,
    height)` (platform/browser_camera.py has the commands).

The event vocabulary is the one of `InputEvent` (platform.base): kinds in `EVENT_KINDS`, buttons in
`MOUSE_BUTTONS`, coordinates in logical pixels, keys as a character ("a", " ") or a name from `KEY_NAMES`
("left", "enter", "space", "escape"). Escape does not stop the sketch: the page has a Stop button.

The sketch's controls panel (S-329, contract U1) is shown as on the desktop: each frame handed to `on_frame` is the
canvas with the panel below it, one frame taller by the panel (physical pixels, the same format). Mouse events
at or below the canvas's bottom edge go to the panel, by the rule the desktop uses (controls.PanelMouse); the
sketch does not see them. `capture()` stays the canvas alone.

Everything that is the same as the headless platform (the event queue, the polled mouse and key state,
`capture`) is inherited from it.
"""
from __future__ import annotations

from collections.abc import Callable

from ..controls import PanelMouse
from .base import EVENT_KINDS, MOUSE_BUTTONS, InputEvent, Pixels
from .browser_audio import HostMicrophone, HostMixer, MicrophoneCallback, SoundCallback
from .browser_camera import CameraCallback, HostCamera
from .browser_models import HostModels, ModelsCallback
from .headless import HeadlessPlatform

# on_frame(data, width, height, stride): data is the frame's bytes (BGRA, premultiplied, row-major),
# width and height are physical pixels, stride is the bytes per row. `data` is a view of the renderer's
# surface: valid only during the call, so a host that keeps the frame must copy it.
FrameCallback = Callable[[memoryview, int, int, int], None]


JITTER = 0.004    # seconds: a quarter of a 60 Hz refresh, the slack frame_due() allows for the host's clock

class BrowserPlatform(HeadlessPlatform):
    # Read by Sketch (run_namespace, show): a host steps the loop, so f.run() returns after setup()
    # and f.show() returns after presenting. See funground.web.
    host_driven = True

    def __init__(self, width: int, height: int, scale: float = 1.0, on_frame: FrameCallback | None = None,
                 on_sound: SoundCallback | None = None, on_microphone: MicrophoneCallback | None = None,
                 on_camera: CameraCallback | None = None, on_models: ModelsCallback | None = None) -> None:
        super().__init__()
        if width <= 0 or height <= 0:
            raise ValueError("the host's canvas size must be above 0")
        if scale <= 0:
            raise ValueError("the host's backing scale must be above 0")
        self.SCREEN_SIZE = (width, height)       # full_screen() fills the host's canvas
        self._scale = float(scale)
        self._on_frame = on_frame
        self._now = 0.0                          # the host's clock, in seconds
        self._previous: float | None = None      # the clock at the previous tick
        self.mixer = HostMixer(on_sound)         # what the sound library plays through, instead of pygame's mixer
        self.microphone = HostMicrophone(on_microphone)
        self.camera = HostCamera(on_camera)
        self.models = HostModels(on_models)
        self._panel = None                       # the sketch's ControlPanel, or None (S-329)
        self._panel_pixels: Pixels | None = None   # the last drawn panel, a copy (the sketch reuses its surface)
        self._panel_mouse = PanelMouse()
        self._canvas = (0, 0)                    # the canvas's logical size, as open_window was given it

    @property
    def backing_scale(self) -> float:
        return self._scale

    # ---- controls panel (S-329)
    def open_window(self, width: int, height: int, title: str) -> tuple[int, int]:
        self._canvas = (width, height)
        return super().open_window(width, height, title)

    def set_controls(self, panel) -> bool:
        self._panel = panel if panel else None
        self._panel_pixels = None
        self._panel_mouse.reset()
        return True

    def present_panel(self, pixels: Pixels) -> None:
        self._panel_pixels = Pixels(bytes(pixels.data), pixels.width, pixels.height, pixels.format)
        if self._last is not None:               # a control changed: show it now, even if the sketch draws nothing
            self._send(self._last)

    # ---- input, pushed by the host
    def push_event(self, event: InputEvent) -> None:
        if event.kind not in EVENT_KINDS:
            raise ValueError(f"unknown event kind {event.kind!r}; the kinds are {', '.join(EVENT_KINDS)}")
        if event.button is not None and event.button not in MOUSE_BUTTONS:
            raise ValueError(f"unknown mouse button {event.button!r}; the buttons are {', '.join(MOUSE_BUTTONS)}")
        if self._panel_mouse.route(self._panel, event, *self._canvas):
            return
        self.post(event)

    def push_microphone(self, samples) -> None:
        """Mono samples (-1 to 1, 44 100 Hz) that the host's microphone heard; they are used while a sketch listens."""
        self.microphone.feed(samples)

    def push_camera(self, pixels, width: int, height: int) -> None:
        """One RGBA frame from the host's camera (`width * height * 4` bytes); the sketch uses the latest."""
        self.camera.push(pixels, width, height)

    def push_models(self, task: str, key: int, points, score: float, width: int, height: int, scores=None) -> None:
        """One result from the host's models (browser_models.py); the sketch reads the latest."""
        self.models.push(task, key, points, score, width, height, scores)

    def push_models_mask(self, task: str, key: int, mask, mask_width: int, mask_height: int, width: int, height: int) -> None:
        """One result that is a mask from the host's models (browser_models.py); the sketch reads the latest."""
        self.models.push_mask(task, key, mask, mask_width, mask_height, width, height)

    def push_models_words(self, task: str, key: int, text: str, score: float) -> None:
        """One result that is words from the host's models (browser_models.py); the sketch reads the latest."""
        self.models.push_words(task, key, text, score)

    def push_models_sound(self, task: str, key: int, scores) -> None:
        """One result that is sound scores from the host's models (browser_models.py); the sketch reads the latest."""
        self.models.push_sound_scores(task, key, scores)

    def push_models_vector(self, task: str, key: int, vector) -> None:
        """One result that is a picture's vector from the host's models (browser_models.py); the sketch reads it once."""
        self.models.push_vector(task, key, vector)

    def poll(self) -> bool:
        super().poll()
        for event in self._events:               # a page reports the space bar as " "; key_down("space") must see it
            if event.key == " ":
                if event.kind == "key_pressed":
                    self._keys.add("space")
                elif event.kind == "key_released":
                    self._keys.discard("space")
        return True                              # only the host stops a sketch (and f.stop())

    # ---- time, from the host
    def set_time(self, seconds: float) -> None:
        self._now = seconds

    def start(self) -> None:
        self._previous = None

    def frame_due(self, fps: int) -> bool:
        """Whether the sketch's next frame is due at the host's time. The host calls on every display refresh
        (60 times a second or more); the desktop sleeps to the frame rate, so here a call that comes too early
        draws nothing and the sketch keeps its f.run(fps=...) speed. JITTER lets a frame that is due on this
        refresh, give or take the host's timing noise, run now rather than one refresh late (so 30 fps on a
        60 Hz display is every second refresh, not every third)."""
        return self._previous is None or self._now - self._previous >= 1.0 / fps - JITTER

    def tick(self, fps: int) -> float:
        elapsed = 1.0 / fps if self._previous is None else self._now - self._previous
        self._previous = self._now
        return elapsed

    def close(self) -> None:
        self.mixer.stop_all()                    # a run that ends leaves nothing playing or listening
        self.microphone.close()
        self.camera.close()
        self.models.close()
        super().close()

    # ---- output, to the host
    def present(self, pixels: Pixels) -> None:
        super().present(pixels)                  # keeps the canvas for capture(): the panel is not part of the picture
        self._send(pixels)

    def _send(self, pixels: Pixels) -> None:
        """Give the host the canvas, with the panel below it when one is shown."""
        if self._on_frame is None:
            return
        data = memoryview(pixels.data)
        height = pixels.height
        panel = self._panel_pixels
        if self._panel is not None and panel is not None and panel.width == pixels.width and panel.format == pixels.format:
            data = memoryview(bytes(data) + panel.data)      # rows have no padding, so the panel's rows follow the canvas's
            height += panel.height
        self._on_frame(data, pixels.width, height, len(data) // height)
