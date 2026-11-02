"""The models library, as a small stub (ADR-007, D-125).

The code is in the separate package ``funground-ml`` (``funground_ml``). ``from funground import ml`` brings in its
names, or says in one sentence that it is a separate install. The core never imports onnxruntime or the models.
"""
from __future__ import annotations

try:
    import funground_ml as _library
except ModuleNotFoundError as _error:
    if _error.name != "funground_ml":           # funground_ml is installed but something inside it is missing: say so
        raise
    raise ImportError("The models library is a separate install: run `python -m pip install funground-ml`") from None

from funground_ml import *  # noqa: F401,F403,E402

__all__ = list(_library.__all__)
