"""HeadlessPlatform: run a sketch with no window at all (story S-034).

Selected by FUNGROUND_HEADLESS=1. No OS, no SDL, no waiting: `tick` returns
real elapsed time without sleeping, input is always idle, and `present`
keeps the last frame so `capture()` and `f.save()` work.
"""
from __future__ import annotations

import os
import time

from .base import KEY_NAMES, InputEvent, InputState, Pixels


class HeadlessPlatform:
    # full_screen() with no display: a fixed, repeatable size in logical pixels (contract R12).
    SCREEN_SIZE = (1920, 1080)

    def __init__(self) -> None:
        self.cursor: str | None = "arrow"
        self.full_screen = False
        self._last: Pixels | None = None
        self._queue: list[InputEvent] = []     # events posted for the next poll()
        self._events: list[InputEvent] = []
        self._mouse = (0, 0)
        self._buttons: set[str] = set()
        self._keys: set[str] = set()
        self._t = time.perf_counter()
        self._size = (0, 0)

    @property
    def backing_scale(self) -> float:
        forced = os.environ.get("FUNGROUND_BACKING_SCALE")
        return max(0.5, float(forced)) if forced else 1.0

    def open_window(self, width: int, height: int, title: str) -> tuple[int, int]:
        s = self.backing_scale
        self._size = (round(width * s), round(height * s))
        return self._size

    def display_size(self) -> tuple[int, int]:
        return self.SCREEN_SIZE

    def open_full_screen(self, title: str) -> tuple[int, int]:
        self.full_screen = True
        return self.open_window(*self.SCREEN_SIZE, title)

    def set_cursor(self, kind: str | None) -> None:
        self.cursor = kind

    def start(self) -> None:
        self._t = time.perf_counter()

    def post(self, *events: InputEvent) -> None:
        """Script input: the events are delivered by the next poll(), in order."""
        self._queue.extend(events)

    def poll(self) -> bool:
        self._events, self._queue = self._queue, []
        for ev in self._events:                # keep the polled state consistent with the events
            if ev.kind.startswith("mouse"):
                self._mouse = (ev.x, ev.y)
            if ev.kind == "mouse_pressed" and ev.button:
                self._buttons.add(ev.button)
            elif ev.kind == "mouse_released" and ev.button:
                self._buttons.discard(ev.button)
            elif ev.kind == "key_pressed" and ev.key:
                self._keys.add(ev.key.lower())
            elif ev.kind == "key_released" and ev.key:
                self._keys.discard(ev.key.lower())
        return True

    def events(self) -> list[InputEvent]:
        return self._events

    def input_state(self) -> InputState:
        return InputState(self._mouse[0], self._mouse[1], bool(self._buttons), bool(self._keys))

    def key_down(self, key: str | int) -> bool:
        if isinstance(key, str) and key.lower() not in KEY_NAMES and len(key) != 1:
            raise ValueError(f"unknown key name: {key!r}")
        return isinstance(key, str) and key.lower() in self._keys

    def present(self, pixels: Pixels) -> None:
        self._last = pixels

    def tick(self, fps: int) -> float:
        now = time.perf_counter()
        dt, self._t = now - self._t, now
        return dt

    def capture(self) -> tuple[tuple[int, int], bytes]:
        if self._last is None:
            raise RuntimeError("no frame presented yet")
        p = self._last
        data = bytes(p.data)
        if p.format == "BGRA":
            rgb = bytes(b for i in range(0, len(data), 4) for b in (data[i + 2], data[i + 1], data[i]))
        elif p.format == "RGBA":
            rgb = bytes(b for i in range(0, len(data), 4) for b in data[i : i + 3])
        else:
            raise ValueError(f"unsupported pixel format {p.format}")
        return ((p.width, p.height), rgb)

    def close(self) -> None:
        self._last = None
