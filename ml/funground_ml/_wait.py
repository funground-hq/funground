"""Telling the sketch that a model is being fetched or started (D-149).

A model can take a while to download or to start. The running sketch (on a computer) shows that in its window's title and
keeps the window answering: it puts a function in ``host_services.waiting``. In a web page nothing is set here, because the page
shows the wait itself. Without a sketch nothing happens, so the same calls are safe anywhere.
"""
from __future__ import annotations

import contextlib
from collections.abc import Iterator

from funground import host_services


def progress(text: str) -> None:
    """Show *text* as the wait now, when a sketch listens."""
    if host_services.waiting is not None:
        host_services.waiting(text)


@contextlib.contextmanager
def waiting(text: str) -> Iterator[None]:
    """Show *text* for as long as the block runs, then end the wait (also when the block fails)."""
    progress(text)
    try:
        yield
    finally:
        if host_services.waiting is not None:
            host_services.waiting(None)
