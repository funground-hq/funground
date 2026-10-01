"""pygame-ce implementation of the Platform protocol.

The only module in the package allowed to import pygame (tests/test_boundaries.py).
pygame supplies the window, events, input, timing and the blit of a finished
frame; it draws nothing (D-008).
"""
from __future__ import annotations

import os
import sys

import pygame

from .base import KEY_NAMES, InputEvent, InputState, Pixels

_NAMED_KEYS = {
    "left": pygame.K_LEFT,
    "right": pygame.K_RIGHT,
    "up": pygame.K_UP,
    "down": pygame.K_DOWN,
    "space": pygame.K_SPACE,
    "enter": pygame.K_RETURN,
    "escape": pygame.K_ESCAPE,
}
assert set(_NAMED_KEYS) == set(KEY_NAMES)
_KEY_NAMES_BY_CODE = {code: name for name, code in _NAMED_KEYS.items()}


def key_code(key: str | int) -> int:
    """Map a funground key name / character / backend code to a pygame key code."""
    if isinstance(key, int):
        return key
    lowered = key.lower()
    if lowered in _NAMED_KEYS:
        return _NAMED_KEYS[lowered]
    if len(lowered) == 1:
        return pygame.key.key_code(lowered)
    raise ValueError(f"unknown key name: {key!r}")


def _uses_sdl_highdpi_window() -> bool:
    """True when the window should be opened through SDL's high-DPI route.

    macOS and Linux (Wayland) report *screen coordinates* for a window and only
    hand out a physical-resolution drawable when the window was created with
    SDL_WINDOW_ALLOW_HIGHDPI. pygame-ce's display.set_mode() never sets that
    flag; pygame.Window(allow_high_dpi=True) does (S-038). The override and the
    dummy driver keep the plain set_mode path so tests behave the same everywhere.
    """
    if os.environ.get("FUNGROUND_BACKING_SCALE"):
        return False
    driver = os.environ.get("SDL_VIDEODRIVER", "").lower()
    if driver == "dummy":
        return False
    if os.environ.get("FUNGROUND_HIGHDPI", "").lower() in ("1", "true", "yes"):
        return True                      # explicit opt-in, any platform
    if sys.platform == "darwin":
        return True
    if sys.platform.startswith("linux"):
        # X11 has no drawable/window scaling (the ratio is always 1.0), and the
        # Window route changes how the display surface is obtained, so only
        # Wayland sessions take it (S-067, narrowing S-038).
        return driver == "wayland" or (driver == "" and bool(os.environ.get("WAYLAND_DISPLAY")))
    return False


def _drawable_ratio(window) -> float:
    """Drawable pixels per screen-coordinate unit of a pygame.Window.

    SDL sizes the window surface with SDL_GetWindowSizeInPixels (SDL >= 2.26)
    and ``Window.size`` with SDL_GetWindowSize, so their ratio is the backing
    scale. Anything odd (zero width, no surface) degrades to 1.0.
    """
    try:
        ww, _wh = window.size
        sw, _sh = window.get_surface().get_size()
    except Exception:
        return 1.0
    if not ww or not sw:
        return 1.0
    return max(0.5, sw / ww)


def detect_backing_scale(window=None) -> float:
    """Physical pixels per logical pixel (contract C3, stories S-024 / S-038).

    FUNGROUND_BACKING_SCALE overrides (tests, unusual setups). The dummy video
    driver has no display, so it is always 1.0. On Windows the process declares
    per-monitor DPI awareness so the OS stops bitmap-stretching the window and
    we can render at physical resolution instead. On macOS / Linux the scale is
    measured from an SDL high-DPI window: *window* if given (the sketch's own),
    else a hidden probe window that is destroyed again. UNVERIFIED on real
    macOS / Wayland hardware: the teaching machine is Windows (S-038.2).
    """
    forced = os.environ.get("FUNGROUND_BACKING_SCALE")
    if forced:
        return max(0.5, float(forced))
    if os.environ.get("SDL_VIDEODRIVER", "").lower() == "dummy":
        return 1.0
    if sys.platform == "win32":
        try:
            import ctypes

            try:
                ctypes.windll.shcore.SetProcessDpiAwareness(2)  # PROCESS_PER_MONITOR_DPI_AWARE
            except OSError:
                pass  # already set for this process; keep whatever it is
            return ctypes.windll.user32.GetDpiForSystem() / 96.0
        except Exception:
            return 1.0
    if _uses_sdl_highdpi_window():
        if window is not None:
            return _drawable_ratio(window)
        try:
            pygame.display.init()
            probe = pygame.Window("funground", (64, 64), hidden=True, allow_high_dpi=True)
        except Exception:
            return 1.0
        try:
            return _drawable_ratio(probe)
        finally:
            probe.destroy()
    return 1.0


class PygamePlatform:
    def __init__(self) -> None:
        self._screen: pygame.Surface | None = None
        self._window: pygame.Window | None = None   # SDL high-DPI route only (S-038)
        self._clock: pygame.time.Clock | None = None
        self._scale = 1.0
        self._input_scale = 1.0   # divisor for mouse coordinates (see input_state)
        self._events: list[InputEvent] = []
        self._held_keys: set[int] = set()     # key codes currently down (for f.is_key_pressed)

    @property
    def backing_scale(self) -> float:
        return self._scale

    # ---- window
    def open_window(self, width: int, height: int, title: str) -> tuple[int, int]:
        pygame.display.init()
        if self._window is not None:
            # resize_canvas() on the SDL high-DPI route: resize this window, never open a second one
            self._window.set_windowed()
            self._window.size = (width, height)
            self._window.title = title
            self._screen = self._window.get_surface()
            self._scale = detect_backing_scale(self._window)
            return self._screen.get_size()
        if _uses_sdl_highdpi_window():
            # macOS / Linux: ask SDL for a high-DPI window at the *logical* size;
            # the window surface comes back at drawable (physical) size and the
            # scale is whatever ratio SDL actually gave us. Mouse coordinates on
            # this route are already in screen units, so they are not divided.
            self._window = pygame.Window(title, (width, height), allow_high_dpi=True)
            self._screen = self._window.get_surface()
            self._scale = detect_backing_scale(self._window)
            self._input_scale = 1.0
            return self._screen.get_size()
        self._window = None
        self._scale = detect_backing_scale()
        self._input_scale = self._scale
        physical = (round(width * self._scale), round(height * self._scale))
        self._screen = pygame.display.set_mode(physical)
        pygame.display.set_caption(title)
        return physical

    def display_size(self) -> tuple[int, int]:
        """The main display in logical pixels, with no window (a script's full_screen, S-085)."""
        was_open = pygame.display.get_init()
        pygame.display.init()
        try:
            width, height = pygame.display.get_desktop_sizes()[0]
        finally:
            if not was_open:
                pygame.display.quit()
        scale = detect_backing_scale()
        return round(width / scale), round(height / scale)

    def open_full_screen(self, title: str) -> tuple[int, int]:
        pygame.display.init()
        if self._window is None and _uses_sdl_highdpi_window():
            self.open_window(640, 400, title)
        if self._window is not None:
            self._window.set_fullscreen(desktop=True)
            self._screen = self._window.get_surface()
            self._scale = detect_backing_scale(self._window)
            return self._screen.get_size()
        self._scale = detect_backing_scale()
        self._input_scale = self._scale
        physical = pygame.display.get_desktop_sizes()[0]          # physical pixels of the main display
        self._screen = pygame.display.set_mode(physical, pygame.FULLSCREEN)
        pygame.display.set_caption(title)
        return self._screen.get_size()

    _CURSORS = {"arrow": "SYSTEM_CURSOR_ARROW", "cross": "SYSTEM_CURSOR_CROSSHAIR", "hand": "SYSTEM_CURSOR_HAND",
                "move": "SYSTEM_CURSOR_SIZEALL", "text": "SYSTEM_CURSOR_IBEAM", "wait": "SYSTEM_CURSOR_WAIT"}

    def set_cursor(self, kind: str | None) -> None:
        if kind is None:
            pygame.mouse.set_visible(False)
            return
        pygame.mouse.set_visible(True)
        try:
            pygame.mouse.set_cursor(getattr(pygame, self._CURSORS[kind]))
        except pygame.error:
            pass                    # a display without system cursors (e.g. the dummy driver)

    @property
    def target(self) -> pygame.Surface | None:
        return self._screen

    # ---- loop services
    def start(self) -> None:
        pygame.init()
        self._clock = pygame.time.Clock()

    def poll(self) -> bool:
        keep_running = True
        self._events = []
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                keep_running = False
                continue
            if event.type == pygame.KEYDOWN:
                self._held_keys.add(event.key)
                if event.key == pygame.K_ESCAPE:
                    keep_running = False
            elif event.type == pygame.KEYUP:
                self._held_keys.discard(event.key)
            elif event.type == pygame.WINDOWFOCUSLOST:
                self._held_keys.clear()           # key-ups are not delivered while unfocused
            translated = self._translate(event)
            if translated is not None:
                self._events.append(translated)
        return keep_running

    def events(self) -> list[InputEvent]:
        return self._events

    _BUTTONS = {1: "left", 2: "center", 3: "right"}

    def _logical(self, pos) -> tuple[int, int]:
        s = self._input_scale
        return round(pos[0] / s), round(pos[1] / s)

    def _translate(self, event) -> InputEvent | None:
        t = event.type
        if t in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP):
            button = self._BUTTONS.get(event.button)
            if button is None:          # 4/5 are the legacy wheel, 6+ side buttons: not mouse presses
                return None
            x, y = self._logical(event.pos)
            kind = "mouse_pressed" if t == pygame.MOUSEBUTTONDOWN else "mouse_released"
            return InputEvent(kind, x, y, button=button)
        if t == pygame.MOUSEMOTION:
            x, y = self._logical(event.pos)
            return InputEvent("mouse_dragged" if any(event.buttons[:3]) else "mouse_moved", x, y)
        if t == pygame.MOUSEWHEEL:
            x, y = self._logical(pygame.mouse.get_pos())
            return InputEvent("mouse_wheel", x, y, delta=-float(getattr(event, "precise_y", event.y)))
        if t in (pygame.KEYDOWN, pygame.KEYUP):
            ch = getattr(event, "unicode", "") or ""
            printable = len(ch) == 1 and ch.isprintable()
            name = ch if printable else _KEY_NAMES_BY_CODE.get(event.key) or pygame.key.name(event.key)
            kind = "key_pressed" if t == pygame.KEYDOWN else "key_released"
            return InputEvent(kind, key=name, key_code=event.key)
        return None

    def input_state(self) -> InputState:
        x, y = pygame.mouse.get_pos()
        s = self._input_scale
        return InputState(round(x / s), round(y / s), any(pygame.mouse.get_pressed(3)),
                          bool(self._held_keys))

    def key_down(self, key: str | int) -> bool:
        return bool(pygame.key.get_pressed()[key_code(key)])

    def present(self, pixels: Pixels) -> None:
        if self._screen is None:
            raise RuntimeError("no window to present to")
        image = pygame.image.frombuffer(pixels.data, (pixels.width, pixels.height), pixels.format)
        self._screen.blit(image, (0, 0))
        if self._window is not None:
            self._window.flip()
        else:
            pygame.display.flip()

    def tick(self, fps: int) -> float:
        if self._clock is None:
            self._clock = pygame.time.Clock()
        return self._clock.tick(fps) / 1000.0

    def capture(self) -> tuple[tuple[int, int], bytes]:
        if self._screen is None:
            raise RuntimeError("no window to capture")
        return (self._screen.get_size(), pygame.image.tobytes(self._screen, "RGB"))

    def close(self) -> None:
        # The display surface dies with pygame.quit(); forget it so a later
        # run creates a fresh window (v0.5 defect, fixed in Sprint 0).
        if self._window is not None:
            try:
                self._window.destroy()
            except Exception:
                pass  # already gone with the display
        pygame.quit()
        self._window = None
        self._screen = None
        self._clock = None
