"""The only module that imports onnxruntime (the provider boundary, D-124).

It sets ``ORT_DISABLE_TELEMETRY=1`` before the first import, brings the library in on first use (so ``import funground_ml``
stays quick), and keeps one session for each model file.
"""
from __future__ import annotations

import os
from typing import Any

_sessions: dict[str, Any] = {}          # model file path -> onnxruntime.InferenceSession


def _onnxruntime():
    """The onnxruntime module, imported after the telemetry switch is set."""
    os.environ["ORT_DISABLE_TELEMETRY"] = "1"
    import onnxruntime

    return onnxruntime


def session(path: str):
    """The inference session for the model file at *path* (CPU), made once and kept."""
    key = os.fspath(path)
    found = _sessions.get(key)
    if found is None:
        found = _sessions[key] = _onnxruntime().InferenceSession(key, providers=["CPUExecutionProvider"])
    return found
