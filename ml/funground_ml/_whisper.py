"""Speech to words on a computer: Whisper tiny.en with onnxruntime, numpy for the sums (S-234; desktop only).

The steps, as OpenAI's Whisper does them:

1. **Resample** the sound to 16 kHz (``to_model_rate``) and pad it with silence, or cut it, to exactly 30 s.
2. **Log-mel**: the sound becomes a picture of 80 rows (pitch bands on the mel scale) and 3000 columns (10 ms each), the
   logarithm of how loud each band is (``log_mel``).
3. The **encoder** turns that picture into the model's idea of the sound.
4. The **decoder** chooses the words one piece at a time, the likeliest each time (greedy), until it chooses "end", starts to
   repeat itself (``_speech.loop_tail``) or has chosen as many as the sound can hold (``_speech.token_limit``). It keeps what it has worked out so far (the "past key values"), so each new piece costs one small step.
5. ``_speech.decode`` turns the chosen numbers into text.

The answer is the text and a score: the mean probability of the pieces the model chose. This is the same arithmetic as the
S-231 spike (``spikes/16_models/speech_sounds/whisper_desktop.py``), and it gives the same words for the same sound.
"""
from __future__ import annotations

import threading
from functools import cache

import numpy as np

from . import _runtime
from ._speech import (END_OF_TEXT, FIRST_WORD_BANNED, NO_TIMESTAMPS, SAMPLE_RATE, START_OF_TEXT, SUPPRESSED, WINDOW_SECONDS, decode,
                      load_vocabulary, loop_tail, token_limit)

# ---- the log-mel picture (Whisper's feature extractor)
FFT_SIZE = 400                 # 25 ms of sound at 16 kHz for each column
HOP = 160                      # a new column every 10 ms
MEL_BANDS = 80                 # rows
WINDOW_SAMPLES = WINDOW_SECONDS * SAMPLE_RATE
LOG_RANGE = 8.0                # a band quieter than the loudest by more than this (powers of ten) is lifted to that
LOG_SHIFT, LOG_SCALE = 4.0, 4.0        # the picture is (log + 4) / 4, which is about -1 to 1
FLOOR = 1e-10                  # the smallest power taken a logarithm of

# ---- the decoder's shape (tiny.en: 4 layers; each past key or value is (1, 6 heads, length, 64))
HEADS, HEAD_SIZE = 6, 64


def to_model_rate(samples, rate: int) -> np.ndarray:
    """The samples as float32 at 16 kHz, by linear interpolation.

    The formula, so that any other language can do exactly the same (the web page's worker does)::

        count = floor(len(x) * 16000 / rate)
        for j in 0 .. count - 1:
            p = j * rate / 16000          # where output sample j falls among the input samples
            i = floor(p)                  # the input sample at or before it
            t = p - i                     # how far on the way to the next one
            y[j] = x[i] * (1 - t) + x[min(i + 1, len(x) - 1)] * t

    At the same rate the samples are returned as they are. There is no filter before it, so the top of a sound with
    frequencies above 8 kHz folds down a little; speech has little up there.
    """
    x = np.asarray(samples, np.float32)
    if rate == SAMPLE_RATE or len(x) == 0:
        return x
    count = int(len(x) * SAMPLE_RATE // rate)
    position = np.arange(count, dtype=np.float64) * rate / SAMPLE_RATE
    before = np.floor(position).astype(np.int64)
    fraction = (position - before).astype(np.float32)
    after = np.minimum(before + 1, len(x) - 1)
    return x[before] * (1 - fraction) + x[after] * fraction


@cache
def _mel_filters() -> np.ndarray:
    """The Slaney mel filter bank (what librosa and Whisper use): shape (80, 201), each row a triangle in frequency."""
    def hertz_to_mel(hz):
        hz = np.asarray(hz, np.float64)
        return np.where(hz < 1000, hz / (200 / 3), 15 + np.log(np.maximum(hz, 1e-9) / 1000) / (np.log(6.4) / 27))

    def mel_to_hertz(mel):
        mel = np.asarray(mel, np.float64)
        return np.where(mel < 15, mel * (200 / 3), 1000 * np.exp((np.log(6.4) / 27) * (mel - 15)))

    frequencies = np.linspace(0, SAMPLE_RATE / 2, FFT_SIZE // 2 + 1)
    edges = mel_to_hertz(np.linspace(hertz_to_mel(0), hertz_to_mel(SAMPLE_RATE / 2), MEL_BANDS + 2))
    widths = np.diff(edges)
    ramps = edges[:, None] - frequencies[None, :]
    triangles = np.maximum(0, np.minimum(-ramps[:-2] / widths[:-1, None], ramps[2:] / widths[1:, None]))
    return (triangles * (2.0 / (edges[2:MEL_BANDS + 2] - edges[:MEL_BANDS]))[:, None]).astype(np.float32)


def log_mel(audio: np.ndarray) -> np.ndarray:
    """The encoder's input for 16 kHz *audio*: shape (1, 80, 3000), float32. Sound past 30 s is cut; less is padded with silence."""
    window = np.zeros(WINDOW_SAMPLES, np.float32)
    kept = audio[:WINDOW_SAMPLES]
    window[:len(kept)] = kept
    padded = np.pad(window, FFT_SIZE // 2, mode="reflect")
    frames = np.lib.stride_tricks.sliding_window_view(padded, FFT_SIZE)[::HOP][:-1]
    hann = np.hanning(FFT_SIZE + 1)[:-1].astype(np.float32)
    power = np.abs(np.fft.rfft(frames * hann, axis=1)) ** 2
    log = np.log10(np.maximum(_mel_filters() @ power.T, FLOOR))
    log = np.maximum(log, log.max() - LOG_RANGE)
    return ((log + LOG_SHIFT) / LOG_SCALE).astype(np.float32)[None]


class Whisper:
    """The two model files and the token table, loaded. ``transcribe`` is safe to call from more than one thread."""

    def __init__(self, paths: dict[str, str]) -> None:
        self._encoder = _runtime.session(paths["encoder"])
        self._decoder = _runtime.session(paths["decoder"])
        self._vocabulary = load_vocabulary(paths["vocabulary"])
        self._past_names = [i.name for i in self._decoder.get_inputs() if i.name.startswith("past_key_values")]
        self._present_names = [o.name for o in self._decoder.get_outputs()][1:]
        self._suppressed = np.array(SUPPRESSED)

    def transcribe(self, samples, rate: int) -> tuple[str, float]:
        """(the words heard, the score) for mono *samples* (floats, -1 to 1) at *rate* samples a second.

        The score is the mean probability of the pieces the model chose, 0 to 1. No words at all gives ("", 0.0).
        """
        hidden = self._encoder.run(None, {"input_features": log_mel(to_model_rate(samples, rate))})[0]
        empty = np.zeros((1, HEADS, 0, HEAD_SIZE), np.float32)
        past = {name: empty for name in self._past_names}
        chosen: list[int] = []
        probabilities: list[float] = []
        feed = np.array([[START_OF_TEXT, NO_TIMESTAMPS]], np.int64)
        first = True
        limit = token_limit(len(samples) / rate)
        while len(chosen) < limit:
            outputs = self._decoder.run(None, {"input_ids": feed, "encoder_hidden_states": hidden,
                                               "use_cache_branch": np.array([not first]), **past})
            logits = outputs[0][0, -1].astype(np.float64)
            logits[self._suppressed] = -np.inf
            if not chosen:
                logits[list(FIRST_WORD_BANNED)] = -np.inf
            best = int(logits.argmax())
            if best == END_OF_TEXT:
                break
            chosen.append(best)
            probabilities.append(float(np.exp(logits[best] - logits.max()) / np.exp(logits - logits.max()).sum()))
            if extra := loop_tail(chosen):
                del chosen[-extra:], probabilities[-extra:]
                break
            for name, value in zip(self._present_names, outputs[1:]):
                key = name.replace("present", "past_key_values")
                if first or ".decoder." in key:         # the encoder's keys and values are worked out once
                    past[key] = value
            feed, first = np.array([[best]], np.int64), False
        if not chosen:
            return "", 0.0
        return decode(chosen, self._vocabulary), sum(probabilities) / len(probabilities)


_loaded: dict[tuple, Whisper] = {}
_loading = threading.Lock()


def load(paths: dict[str, str]) -> Whisper:
    """The Whisper for these files, loaded on first use (the sketch's thread, or the words thread) and kept."""
    key = tuple(sorted(paths.items()))
    with _loading:
        found = _loaded.get(key)
        if found is None:
            found = _loaded[key] = Whisper(paths)
        return found
