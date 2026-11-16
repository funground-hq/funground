"""The only module that imports onnxruntime (the provider boundary, D-124).

It sets ``ORT_DISABLE_TELEMETRY=1`` before the first import, brings the library in on first use (so ``import funground_ml``
stays quick), and keeps one session for each model file.
"""
from __future__ import annotations

import contextlib
import os
from typing import Any

from . import _wait
from ._models import SAYS

_sessions: dict[str, Any] = {}          # model file path -> onnxruntime.InferenceSession


def _onnxruntime():
    """The onnxruntime module, imported after the telemetry switch is set."""
    os.environ["ORT_DISABLE_TELEMETRY"] = "1"
    import onnxruntime

    return onnxruntime


def session(path: str, task: str | None = None):
    """The inference session for the model file at *path* (CPU), made once and kept.

    Starting a model takes a moment. Pass the *task* (a key of ``TASKS``) when this runs in the sketch's own thread: the
    window's title then says "Starting the ... model" while it does (D-149). A worker thread passes nothing, because the
    sketch goes on drawing and answering meanwhile."""
    key = os.fspath(path)
    found = _sessions.get(key)
    if found is None:
        with _wait.waiting(f"Starting the {SAYS.get(task, task)} model") if task else contextlib.nullcontext():
            found = _sessions[key] = _onnxruntime().InferenceSession(key, providers=["CPUExecutionProvider"])
    return found
