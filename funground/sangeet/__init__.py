"""The sangeet library: the ragas and talas of Hindustani music.

Bring it in with one line, then every call says ``sangeet.``::

    import funground as f
    from funground import sangeet

    sangeet.tala("Teentaal", tempo=100).loop()

New in 0.2 as a library; in 0.1 these were on ``f``. The sangeet library imports the sound library to make
sounds. The sound library never imports sangeet (ADR-007, S-246). The table is in ``_tables``.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ..api import canvas_sketch
from ..sound import _engine
from . import _tables

if TYPE_CHECKING:
    from ..sound._engine import Sound
    from ._tables import Raga, Tala

__all__ = ["raga", "ragas", "match_ragas", "tala", "tala_info", "talas"]


def _sound_frame() -> int:
    return canvas_sketch().frame_count


def ragas() -> list[str]:
    """Return the names of the ragas in funground's small built-in table.

    For example "Yaman" and "Bhupali".

    Returns:
        A list of names.

    See also: raga, match_ragas, talas
    """
    return _tables.raga_names()


def raga(name: str) -> Raga:
    """Return one raga from the built-in table.

    Arguments:
        name: the raga's name. Capitals do not matter.

    Returns:
        A read-only record with name, thaat, swaras, aroha, avaroha and pakad (sargam strings for melody(sa=...)), vadi, samvadi, time, notes and sources.

    Raises:
        ValueError: the name is not in the table. The message lists the table.

    Example:
        sound.melody(sangeet.raga("Yaman").aroha, sa="D4").play()

    See also: ragas, melody, match_ragas
    """
    return _tables.find_raga(name, "sangeet.raga()")


def talas() -> list[str]:
    """Return the names of the talas in the built-in table.

    They are Teentaal, Ektaal, Jhaptaal, Rupak, Dadra and Keherwa.

    Returns:
        A list of names.

    See also: tala_info, tala, ragas
    """
    return _tables.tala_names()


def tala_info(name: str) -> Tala:
    """Return one tala from the built-in table.

    Arguments:
        name: the tala's name. Capitals do not matter.

    Returns:
        A read-only record with name, beats, vibhag (the divisions), tali (claps) and khali (waves) as beat numbers, sam (beat 1), bols (the theka, one bol a beat), notes and sources.

    Raises:
        ValueError: the name is not in the table.

    Example:
        print(sangeet.tala_info("Rupak").khali)

    See also: talas, tala
    """
    return _tables.find_tala(name, "sangeet.tala_info()")


def tala(name: str, tempo: float = 80, cycles: int = 1) -> Sound:
    """Make a sound of a tala's theka played with simple drum sounds.

    The sam is accented, and the khali part is softer. The sound is exactly beats * 60 / tempo * cycles seconds long.

    Arguments:
        name: the tala's name, such as "Teentaal". See talas().
        tempo: beats a minute. The default is 80.
        cycles: how many times round the tala. The default is 1.

    Returns:
        A Sound: play(), loop() and so on.

    Raises:
        ValueError: the name is not in the table.

    Example:
        sangeet.tala("Teentaal", tempo=100).loop()

    See also: talas, tala_info, drone
    """
    return _engine.make(_tables.tala(name, tempo, cycles, None, "sangeet.tala()"), _sound_frame, "sangeet.tala()")


def match_ragas(histogram: Any) -> list[tuple[str, float]]:
    """Rank the table's ragas by how well their swaras fit a histogram.

    It compares note sets only, so ragas with the same swaras score almost the same (for example Bhupali and Deshkar). It is a learning aid, not a judge.

    Arguments:
        histogram: twelve numbers, as from the swara_histogram(sa) method of a sound.

    Returns:
        A list of (name, score) pairs, best first, with scores from 0 to 1.

    Example:
        h = song.swara_histogram("C#4")
        print(sangeet.match_ragas(h)[0])

    See also: ragas, raga
    """
    return _tables.match(histogram, "sangeet.match_ragas()")
