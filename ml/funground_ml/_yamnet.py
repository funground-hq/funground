"""Sound names on a computer: YAMNet with onnxruntime, numpy for the sums (S-250; desktop only).

YAMNet takes the raw waveform as float32 at 16 kHz (input ``waveform``) and works out its own spectrogram. It gives one row of 521
scores for every 0.96 s window, with a new window every 0.48 s. A sound of less than 0.96 s is padded by the model into one
window. The answer for a sound is the mean of its rows (Google's own demo does this); for a microphone's 0.96 s it is the one row.
``_sound.choose`` turns the 521 scores into names. In a page the host does these steps (``models-glue.js``).
"""
from __future__ import annotations

import threading

import numpy as np

from . import _runtime
from ._whisper import to_model_rate


class Yamnet:
    """The model file, loaded. ``scores`` is safe to call from more than one thread."""

    def __init__(self, paths: dict[str, str]) -> None:
        self._session = _runtime.session(paths["model"])
        self._input = self._session.get_inputs()[0].name

    def scores(self, samples, rate: int) -> tuple[float, ...]:
        """The 521 scores (0 to 1) for mono *samples* (floats, -1 to 1) at *rate* samples a second: the mean over the windows."""
        waveform = to_model_rate(samples, rate)
        rows = self._session.run(None, {self._input: waveform})[0]
        return tuple(float(v) for v in rows.mean(axis=0, dtype=np.float64))


_loaded: dict[tuple, Yamnet] = {}
_loading = threading.Lock()


def load(paths: dict[str, str]) -> Yamnet:
    """The Yamnet for these files, loaded on first use (the sketch's thread, or the listener's) and kept."""
    key = tuple(sorted(paths.items()))
    with _loading:
        found = _loaded.get(key)
        if found is None:
            found = _loaded[key] = Yamnet(paths)
        return found
