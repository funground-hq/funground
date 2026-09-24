"""HeadlessPlatform: run a sketch with no window at all (story S-034).

Selected by PLAYGROUND_HEADLESS=1. No OS, no SDL, no waiting: `tick` returns
real elapsed time without sleeping, input is always idle, and `present`
keeps the last frame so `capture()` and `p.save()` work.
"""
from __future__ import annotations

import os
import time

from .base import KEY_NAMES, InputState, Pixels


class HeadlessPlatform:
    def __init__(self) -> None:
        self._last: Pixels | None = None
        self._t = time.perf_counter()
        self._size = (0, 0)

    @property
    def backing_scale(self) -> float:
        forced = os.environ.get("PLAYGROUND_BACKING_SCALE")
        return max(0.5, float(forced)) if forced else 1.0

    def open_window(self, width: int, height: int, title: str) -> tuple[int, int]:
        s = self.backing_scale
        self._size = (round(width * s), round(height * s))
        return self._size

    def start(self) -> None:
        self._t = time.perf_counter()

    def poll(self) -> bool:
        return True

    def input_state(self) -> InputState:
        return InputState()

    def key_down(self, key: str | int) -> bool:
        if isinstance(key, str) and key.lower() not in KEY_NAMES and len(key) != 1:
            raise ValueError(f"unknown key name: {key!r}")
        return False

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
