"""The parts of ``ml.sound()`` that need no numpy and no model: choosing the names and cutting a microphone into windows (S-250, ML7).

Nothing here imports numpy or onnxruntime, so a web page (Pyodide) uses it too. The model gives 521 scores; ``choose`` is the
one place that turns them into an answer, on the desktop and in Play. The level rule (``is_quiet``) is applied before a window is
sent to the model, on both.

* ``choose`` applies the rules of D-129: the broad umbrella names are hidden, ``Silence`` first means nothing, a best guess under
  ``MIN_SCORE`` means nothing, and the answer is the best name plus up to ``MAX_NEXT`` next guesses.
* ``is_quiet`` is the level rule: the loudest 30 ms of a window below ``QUIET_LEVEL``.
"""
from __future__ import annotations

from ._sound_names import NAMES
from ._speech import level

SAMPLE_RATE = 16000            # the model hears 16 kHz (the same resampling as ml.words)
WINDOW_SECONDS = 0.96          # a microphone is heard in windows this long ...
HOP_SECONDS = 0.48             # ... and a new window is worked on this often
MAX_SOUND_SECONDS = 30         # the longest Sound that ml.sound() takes
QUIET_LEVEL = 0.02             # a window whose loudest 30 ms (RMS, 0 to 1) is under this is quiet
QUIET_BLOCK_SECONDS = 0.03
MIN_SCORE = 0.1                # a best guess scoring under this is not given
MAX_NEXT = 4                   # more guesses after the best one

# The broad names that are not shown (D-129). ``Speech`` and ``Music`` stay.
HIDDEN = frozenset((
    "Animal", "Domestic animals, pets", "Livestock, farm animals, working animals", "Wild animals", "Vehicle",
    "Motor vehicle (road)", "Rail transport", "Liquid", "Mechanisms", "Sound effect", "Inside, small room",
    "Inside, large room or hall", "Inside, public space", "Outside, urban or manmade", "Outside, rural or natural"))
SILENCE = "Silence"

_SHOWN = tuple(i for i, name in enumerate(NAMES) if name not in HIDDEN)

Guesses = list[tuple[str, float]]       # the best guess first, then up to MAX_NEXT more: (name, score)


def choose(scores) -> Guesses | None:
    """The answer for the model's 521 *scores* (0 to 1, in the order of ``NAMES``), or None when there is nothing to name.

    None when the likeliest name shown is ``Silence``, or when the best one scores under ``MIN_SCORE``. Otherwise
    the best shown name and up to ``MAX_NEXT`` next ones, likeliest first (a tie keeps the model's order).
    """
    if len(scores) != len(NAMES):
        raise ValueError(f"the sound model gives {len(NAMES)} scores, not {len(scores)}")
    values = [float(v) for v in scores]
    ranked = sorted(_SHOWN, key=lambda i: (-values[i], i))
    if NAMES[ranked[0]] == SILENCE or values[ranked[0]] < MIN_SCORE:
        return None
    return [(NAMES[i], values[i]) for i in ranked if NAMES[i] != SILENCE][:1 + MAX_NEXT]


def is_quiet(samples, rate: int) -> bool:
    """True when the loudest 30 ms of *samples* (mono floats) is under ``QUIET_LEVEL``. No samples are quiet."""
    size = max(1, round(QUIET_BLOCK_SECONDS * rate))
    count = len(samples)
    if count == 0:
        return True
    if count <= size:
        return level(samples) < QUIET_LEVEL
    return all(level(samples[at:at + size]) < QUIET_LEVEL for at in range(0, count - size + 1, size))
