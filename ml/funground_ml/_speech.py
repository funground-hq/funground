"""The parts of ``ml.words()`` that need no numpy and no model: cutting speech into phrases and reading the model's answer (S-234).

Nothing here imports numpy or onnxruntime, so a web page (Pyodide) can use the cutter. The rest of the work on a computer is in
``_whisper.py``; in a page the host does it.

* ``PhraseCutter`` watches the microphone's sound, 30 ms at a time, and cuts it into phrases: a phrase starts when the level
  rises and ends when it has been quiet for a while.
* ``load_vocabulary`` and ``decode`` turn the numbers the model chose back into text. Whisper writes its words in "byte-level" form
  (the same scheme as GPT-2): every byte of the text is shown as one printable character, so a space is shown as "Ġ".
  ``decode`` undoes that. It is the whole of what the ``tokenizers`` library does for us, so we do not install it.
"""
from __future__ import annotations

import json
import math
from array import array
from collections import deque
from operator import mul

# ---- the model's numbers (Whisper tiny.en; generation_config.json of the pinned repository)
SAMPLE_RATE = 16000            # the model hears 16 kHz
WINDOW_SECONDS = 30            # ... and at most 30 s at a time
END_OF_TEXT = 50256            # a chosen number at or above this is not a word
START_OF_TEXT = 50257          # the first of the model's start tokens
NO_TIMESTAMPS = 50362          # the second: "write the words only"
FIRST_WORD_BANNED = (220, 50256)       # the first word may not be a lone space, nor the end
MAX_TOKENS = 224               # at most this many pieces of words in one answer
# Pieces the model is told never to choose (symbols, runs of punctuation and its own control numbers).
SUPPRESSED = (
    1, 2, 7, 8, 9, 10, 14, 25, 26, 27, 28, 29, 31, 58, 59, 60, 61, 62, 63, 90, 91, 92, 93, 357, 366, 438, 532,
    685, 705, 796, 930, 1058, 1220, 1267, 1279, 1303, 1343, 1377, 1391, 1635, 1782, 1875, 2162, 2361, 2488,
    3467, 4008, 4211, 4600, 4808, 5299, 5855, 6329, 7203, 9609, 9959, 10563, 10786, 11420, 11709, 11907, 13163,
    13697, 13700, 14808, 15306, 16410, 16791, 17992, 19203, 19510, 20724, 22305, 22935, 27007, 30109, 30420,
    33409, 34949, 40283, 40493, 40549, 47282, 49146, 50257, 50357, 50358, 50359, 50360, 50361)

# ---- what counts as words
MIN_SCORE = 0.4                # an answer less sure than this is dropped (the model invents words in noise)
MAX_SOUND_SECONDS = 30         # the longest Sound that ml.words() takes

# ---- cutting a microphone's sound into phrases
BLOCK_SECONDS = 0.03           # the level is measured over blocks this long
START_LEVEL = 0.02             # a block louder than this (RMS, 0 to 1) is speech; one at or under it is quiet
END_SILENCE_SECONDS = 0.6      # a phrase ends after this much quiet
MIN_PHRASE_SECONDS = 0.3       # a phrase with less speech than this is a click or a cough, and is ignored
MAX_PHRASE_SECONDS = 10.0      # a longer phrase is cut here and the rest starts a new one
LEAD_BLOCKS = 3                # blocks of quiet kept before the start, so the first sound is not clipped


def level(block) -> float:
    """The RMS level of *block* (a sequence of floats): the square root of the mean of the squares."""
    return math.sqrt(sum(map(mul, block, block)) / len(block)) if len(block) else 0.0


class PhraseCutter:
    """Cuts a stream of mono samples into phrases.

    Give it the new samples with ``feed``; it returns the phrases that ended. It looks at whole blocks of 30 ms and keeps a
    part block for next time. A phrase is an ``array('f')`` of the speech with a little quiet before it (``LEAD_BLOCKS``)
    and the quiet that ended it after it. ``flush`` ends the phrase that is open (the microphone was stopped).
    """

    def __init__(self, rate: int) -> None:
        self.rate = rate
        self._block = max(1, round(BLOCK_SECONDS * rate))
        self._end_blocks = max(1, math.ceil(END_SILENCE_SECONDS * rate / self._block))
        self._min_speech = round(MIN_PHRASE_SECONDS * rate)
        self._max_length = round(MAX_PHRASE_SECONDS * rate)
        self._rest: list[float] = []                  # samples that do not fill a block yet
        self._lead: deque[list[float]] = deque(maxlen=LEAD_BLOCKS)
        self._phrase: array | None = None             # the open phrase, or None while it is quiet
        self._lead_length = 0
        self._speech_end = 0                          # where in the open phrase the last loud block ends
        self._quiet_blocks = 0                        # quiet blocks in a row at the end of the open phrase

    @property
    def is_open(self) -> bool:
        """True while a phrase has started and not ended."""
        return self._phrase is not None

    def feed(self, samples) -> list[array]:
        """Take new samples. Returns the phrases that ended in them, oldest first (often none)."""
        done: list[array] = []
        data = self._rest + list(samples) if self._rest else samples
        size, count = self._block, len(data)
        whole = count - count % size
        for at in range(0, whole, size):
            ended = self._block_in(data[at:at + size])
            if ended is not None:
                done.append(ended)
        self._rest = list(data[whole:])
        return done

    def flush(self) -> array | None:
        """End the open phrase now. Returns it, or None when there was none (or it was too short). Forgets the part block."""
        self._rest = []
        self._lead.clear()
        return self._finish()

    def _block_in(self, block) -> array | None:
        loud = level(block) > START_LEVEL
        if self._phrase is None:
            if not loud:
                self._lead.append(list(block))
                return None
            self._phrase = array("f")
            for quiet in self._lead:
                self._phrase.extend(quiet)
            self._lead.clear()
            self._lead_length = len(self._phrase)
            self._speech_end = self._lead_length
            self._quiet_blocks = 0
        self._phrase.extend(block)
        if loud:
            self._speech_end, self._quiet_blocks = len(self._phrase), 0
        else:
            self._quiet_blocks += 1
        if self._quiet_blocks >= self._end_blocks or len(self._phrase) >= self._max_length:
            return self._finish()
        return None

    def _finish(self) -> array | None:
        phrase, self._phrase = self._phrase, None
        self._quiet_blocks = 0
        if phrase is None or self._speech_end - self._lead_length < self._min_speech:
            return None
        return phrase


# ---- the model's numbers back to text
def _bytes_to_characters() -> dict[int, str]:
    """GPT-2's table: the character that stands for each of the 256 byte values.

    The bytes that are printable and not confusing (``!`` to ``~`` and two ranges of Latin-1) stand for themselves. The other
    bytes (control codes, the space, and so on) are given the characters from U+0100 up, in order.
    """
    printable = set(range(ord("!"), ord("~") + 1)) | set(range(0xA1, 0xAD)) | set(range(0xAE, 0x100))
    table, spare = {}, 0
    for byte in range(256):
        if byte in printable:
            table[byte] = chr(byte)
        else:
            table[byte] = chr(0x100 + spare)
            spare += 1
    return table


_BYTE_OF_CHARACTER = {character: byte for byte, character in _bytes_to_characters().items()}


def load_vocabulary(path: str) -> list[str]:
    """The model's table from ``vocab.json``: the text (in byte-level form) of each number, in a list indexed by number."""
    with open(path, encoding="utf-8") as fh:
        pieces = json.load(fh)
    table = [""] * (max(pieces.values()) + 1)
    for piece, number in pieces.items():
        table[number] = piece
    return table


def decode(numbers, vocabulary: list[str]) -> str:
    """The text for the numbers the model chose.

    A number at or above ``END_OF_TEXT`` is a control number and is skipped. The pieces are joined, the characters turned back
    into bytes, and the bytes read as UTF-8 (a character that two pieces share comes out right, because the join happens
    first). The text has no space at either end.
    """
    joined = "".join(vocabulary[n] for n in numbers if n < END_OF_TEXT)
    raw = bytes(_BYTE_OF_CHARACTER.get(character, 0x3F) for character in joined)
    return raw.decode("utf-8", errors="replace").strip()
