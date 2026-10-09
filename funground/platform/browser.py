"""BrowserPlatform: the Platform for a host that owns the window (story S-152, Web_Runner_Note.md).

A web page (or a test) owns the canvas, the clock and the input. This platform opens no window and
never waits. What the host does:

  * gives the canvas size (`display_size`) and the backing scale when it builds the platform;
  * pushes input with `push_event(InputEvent(...))`; the next step delivers the events in order;
  * sets the time of each step with `set_time(seconds)`; `tick()` returns the seconds since the step before;
  * receives each finished frame through the `on_frame` callback;
  * receives sounds through `on_sound`, and the microphone's requests through `on_microphone`, and pushes what
    the microphone heard with `push_microphone(samples)` (platform/browser_audio.py has the commands).

The event vocabulary is the one of `InputEvent` (platform.base): kinds in `EVENT_KINDS`, buttons in
`MOUSE_BUTTONS`, coordinates in logical pixels, keys as a character ("a", " ") or a name from `KEY_NAMES`
("left", "enter", "space", "escape"). Escape does not stop the sketch: the page has a Stop button.

Everything that is the same as the headless platform (the event queue, the polled mouse and key state,
`capture`) is inherited from it.
"""
from __future__ import annotations

from collections.abc import Callable

from .base import EVENT_KINDS, MOUSE_BUTTONS, InputEvent, Pixels
from .browser_audio import HostMicrophone, HostMixer, MicrophoneCallback, SoundCallback
from .headless import HeadlessPlatform

# on_frame(data, width, height, stride): data is the frame's bytes (BGRA, premultiplied, row-major),
# width and height are physical pixels, stride is the bytes per row. `data` is a view of the renderer's
# surface: valid only during the call, so a host that keeps the frame must copy it.
FrameCallback = Callable[[memoryview, int, int, int], None]


class BrowserPlatform(HeadlessPlatform):
    # Read by Sketch (run_namespace, show): a host steps the loop, so f.run() returns after setup()
    # and f.show() returns after presenting. See funground.web.
    host_driven = True

    def __init__(self, width: int, height: int, scale: float = 1.0, on_frame: FrameCallback | None = None,
                 on_sound: SoundCallback | None = None, on_microphone: MicrophoneCallback | None = None) -> None:
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
        self.mixer = HostMixer(on_sound)         # what sound.py plays through, instead of pygame's mixer
        self.microphone = HostMicrophone(on_microphone)

    @property
    def backing_scale(self) -> float:
        return self._scale

    # ---- input, pushed by the host
    def push_event(self, event: InputEvent) -> None:
        if event.kind not in EVENT_KINDS:
            raise ValueError(f"unknown event kind {event.kind!r}; the kinds are {', '.join(EVENT_KINDS)}")
        if event.button is not None and event.button not in MOUSE_BUTTONS:
            raise ValueError(f"unknown mouse button {event.button!r}; the buttons are {', '.join(MOUSE_BUTTONS)}")
        self.post(event)

    def push_microphone(self, samples) -> None:
        """Mono samples (-1 to 1, 44 100 Hz) that the host's microphone heard; they are used while a sketch listens."""
        self.microphone.feed(samples)

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

    def tick(self, fps: int) -> float:
        elapsed = 1.0 / fps if self._previous is None else self._now - self._previous
        self._previous = self._now
        return elapsed

    def close(self) -> None:
        self.mixer.stop_all()                    # a run that ends leaves nothing playing or listening
        self.microphone.close()
        super().close()

    # ---- output, to the host
    def present(self, pixels: Pixels) -> None:
        super().present(pixels)                  # keeps the frame for capture()
        if self._on_frame is not None:
            data = memoryview(pixels.data)
            self._on_frame(data, pixels.width, pixels.height, len(data) // pixels.height)
