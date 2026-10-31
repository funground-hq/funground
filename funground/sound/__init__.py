"""The sound library: tones, notes, files, the microphone and drawings of sound.

Bring it in with one line, then every call says ``sound.``::

    import funground as f
    from funground import sound

    sound.note("C4", 1).play()

New in 0.2 as a library; in 0.1 these were on ``f``. ``create`` and ``load`` were ``f.create_sound`` and
``f.load_sound``. The library imports the core, and the core never imports it (ADR-007, S-246). The code
is in the underscore modules beside this file: ``_engine`` (the Sound class and its device), ``_synth`` (sound
from numbers), ``_swaras`` (drone and singing), ``_microphone`` and ``_views`` (drawings of sound).
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .. import analysis
from .._options import Tuning, Wave
from ..api import _sketch_folder, active_sketch, canvas_sketch
from . import _engine, _microphone, _swaras, _synth as synth, _views

if TYPE_CHECKING:
    from ..picture import Picture
    from ._engine import Sound
    from ._microphone import Microphone

__all__ = [
    "create", "load", "tone", "note", "pluck", "drone", "melody", "sequence", "mix", "chord_notes",
    "note_to_frequency", "frequency_to_note", "microphone", "microphones", "draw_wave", "draw_spectrum",
    "draw_pitch_line", "spectrogram",
]


def _sound_frame() -> int:
    return canvas_sketch().frame_count


def load(path: str) -> Sound:
    """Read a sound file and return a sound.

    A relative path is looked for next to your sketch file first, then in the current folder. With no sound device (or FUNGROUND_HEADLESS=1) it plays silently and keeps time.

    Arguments:
        path: a WAV, OGG or MP3 file.

    Returns:
        A Sound: play(), loop(), stop(), pause(), set_volume(v), is_playing(), duration(), current_time(), level(), spectrum(bands), pitch(), pan(p), reverb(amount), samples() and save(path).

    Raises:
        FileNotFoundError: the file is not found in either place.
        ValueError: the file is not sound.

    Example:
        beep = sound.load("beep.wav")
        beep.play()

    See also: create, tone, note, draw_wave
    """
    return _engine.load(path, _sketch_folder(), lambda: canvas_sketch().frame_count)


def create(samples: Any, rate: int = 44100) -> Sound:
    """Make a sound from a list of numbers.

    It is an ordinary sound. Its samples() method gives the numbers back.

    Arguments:
        samples: a list of numbers from -1 to 1, one channel. Numbers outside that range are clipped.
        rate: how many numbers make one second. The default is 44100.

    Returns:
        A Sound: play(), loop(), stop(), level(), spectrum(bands), samples() and so on.

    Raises:
        ValueError: the list is empty or has things that are not numbers.

    Example:
        import math
        s = sound.create([math.sin(i / 9) for i in range(44100)])
        s.play()

    See also: tone, load, mix
    """
    return _engine.create(samples, rate, _sound_frame)


def tone(frequency: float, seconds: float, wave: Wave = "sine", volume: float = 0.5,
         attack: float = 0.01, release: float = 0.15, decay: float = 0.15, sustain: float = 0.7) -> Sound:
    """Make a sound that is one steady tone.

    The loudness follows an envelope. It rises to full over the attack, falls to the sustain level over the decay, holds, and fades out over the last release seconds. If attack and release do not fit, they are made shorter. Noise repeats after random_seed().

    Arguments:
        frequency: the pitch, in hertz.
        seconds: how long the sound lasts.
        wave: "sine" (the default), "soft", "triangle", "square", "saw" or "noise".
        volume: from 0 to 1. The default 0.5 is half, so sounds can play together without clipping.
        attack: seconds to rise to full. The default is 0.01.
        release: seconds to fade out at the end. The default is 0.15.
        decay: seconds to fall to the sustain level. The default is 0.15.
        sustain: the level held after the decay, 0 to 1. The default is 0.7.

    Returns:
        A Sound: play(), loop(), stop(), level() and so on.

    Example:
        sound.tone(440, 1, "square").play()

    See also: note, pluck, melody, create
    """
    rng = canvas_sketch()._rng
    return _engine.make(synth.tone(frequency, seconds, wave, volume, attack, release, rng, "sound.tone()",
                                 decay, sustain), _sound_frame, "sound.tone()")


def note(name: str, seconds: float, wave: Wave = "sine", volume: float = 0.5,
         attack: float = 0.01, release: float = 0.15, decay: float = 0.15, sustain: float = 0.7) -> Sound:
    """Make a sound that is one named note.

    It takes the same options as tone().

    Arguments:
        name: a note name such as "A4" (440 hertz), "C#5" or "Bb3".
        seconds: how long the sound lasts.
        wave: "sine" (the default), "soft", "triangle", "square", "saw" or "noise".
        volume: from 0 to 1. The default is 0.5.
        attack: seconds to rise to full. The default is 0.01.
        release: seconds to fade out at the end. The default is 0.15.
        decay: seconds to fall to the sustain level. The default is 0.15.
        sustain: the level held after the decay, 0 to 1. The default is 0.7.

    Returns:
        A Sound: play(), loop(), stop(), level() and so on.

    Raises:
        ValueError: the note name is not understood.

    Example:
        sound.note("C4", 2, attack=0.5, sustain=1).play()

    See also: tone, melody, note_to_frequency
    """
    rng = canvas_sketch()._rng
    hz = synth.note_to_frequency(name, who="sound.note()")
    return _engine.make(synth.tone(hz, seconds, wave, volume, attack, release, rng, "sound.note()",
                                 decay, sustain), _sound_frame, "sound.note()")


def pluck(name_or_frequency: float | str, seconds: float, volume: float = 0.5) -> Sound:
    """Make a sound like a plucked string.

    It dies away by itself. It repeats after random_seed().

    Arguments:
        name_or_frequency: a note name such as "E3", or a frequency in hertz.
        seconds: how long the sound lasts.
        volume: from 0 to 1. The default is 0.5.

    Returns:
        A Sound: play(), loop(), stop(), reverb() and so on.

    Example:
        sound.pluck("E3", 2).play()

    See also: tone, note, drone
    """
    values = synth.pluck(name_or_frequency, seconds, volume, canvas_sketch()._rng, "sound.pluck()")
    return _engine.make(values, _sound_frame, "sound.pluck()")


def melody(text: str, tempo: float = 120, wave: Wave = "soft", sa: str | None = None,
           tuning: Tuning = "equal", volume: float = 0.5) -> Sound:
    """Make a sound from a string of notes.

    Separate the tokens with spaces. A token is a note name, "-" for a rest, or "[C4 E4 G4]" for a chord. Add ":2" after a token for how many beats it lasts (1 if left off). Notes are smooth: each one fades out over 0.15 seconds while the next begins, so the sound lasts that much longer than its beats when it ends on a note. With sa given, the notes are sargam: S r R g G m M P d D n N, with ' for the octave above and a comma for the octave below. In sargam, "S~G" glides from S to G over the token's beats, and "(R)G" touches R for about 60 milliseconds and then plays G.

    Arguments:
        text: the notes, such as "C4 E4 G4:2 - [C4 E4 G4]:4".
        tempo: beats a minute. The default is 120.
        wave: the tone, as for tone(). The default is "soft".
        sa: a note name such as "C4" that makes the notes sargam, with that note as Sa. The default None reads note names.
        tuning: "equal" (the default) or "just". "just" uses just-intonation ratios from Sa, and needs sa.
        volume: from 0 to 1. The default is 0.5.

    Returns:
        A Sound: play(), loop(), stop() and so on.

    Raises:
        ValueError: a token cannot be read. The message names it.

    Example:
        sound.melody("C4 E4 G4:2 -", tempo=100).play()

    See also: note, sequence, mix, raga
    """
    values = synth.melody_samples(text, tempo, wave, sa, tuning, canvas_sketch()._rng, "sound.melody()", volume)
    return _engine.make(values, _sound_frame, "sound.melody()")


def sequence(*sounds: Sound) -> Sound:
    """Make a new sound that plays the given sounds one after another.

    Arguments:
        *sounds: the sounds to join, in order.

    Returns:
        A Sound that lasts as long as all of them together.

    Example:
        sound.sequence(sound.note("C4", 1), sound.note("E4", 1)).play()

    See also: mix, melody
    """
    return _engine.sequence(sounds, _sound_frame)


def mix(*sounds: Sound) -> Sound:
    """Make a new sound that plays the given sounds together.

    A soft limiter keeps the loudest moments at or below 0.9, so the sum never clips. Quiet sums are not changed.

    Arguments:
        *sounds: the sounds to play together.

    Returns:
        A Sound as long as the longest of them.

    Example:
        sound.mix(sound.note("C4", 2), sound.note("E4", 2), sound.note("G4", 2)).play()

    See also: sequence, chord_notes
    """
    return _engine.mix(sounds, _sound_frame)


def note_to_frequency(name: str, sa: str | None = None) -> float:
    """Return the frequency of a note, in hertz.

    Arguments:
        name: a note name such as "A4". With sa given, a swara such as "G" or "N,".
        sa: a note name such as "C4" that the swara is counted from. The default None reads an ordinary note name.

    Returns:
        The frequency in hertz. note_to_frequency("A4") is 440.

    Raises:
        ValueError: the name is not understood.

    Example:
        print(sound.note_to_frequency("A4"))

    See also: frequency_to_note, note, tone
    """
    return synth.note_to_frequency(name, sa)


def frequency_to_note(hz: float, sa: str | None = None) -> str:
    """Return the name of the note nearest to a frequency.

    Sharps are used, such as "C#5".

    Arguments:
        hz: the frequency, in hertz.
        sa: a note name such as "C4". With it, the answer is the nearest swara, such as "G'". The default None gives an ordinary note name.

    Returns:
        A note name, such as "A4".

    Example:
        print(sound.frequency_to_note(440))

    See also: note_to_frequency
    """
    return synth.frequency_to_note(hz, sa)


def chord_notes(name: str) -> list[str]:
    """Return the note names in a chord.

    Arguments:
        name: a note (with # or b), followed by nothing, m, dim, aug, 7, maj7 or m7. For example "C", "Am" or "Bdim".

    Returns:
        A list of note names, with sharps. chord_notes("C") is ["C", "E", "G"], and chord_notes("Am") is ["A", "C", "E"].

    Raises:
        ValueError: the chord name is not understood.

    Example:
        print(sound.chord_notes("Am"))

    See also: mix, note
    """
    return analysis.chord_notes(name)


def drone(sa: float | str, seconds: float, pattern: str = "P S' S' S", volume: float = 0.5) -> Sound:
    """Make a tanpura-like drone.

    It is plucked strings that ring on, played in turn over and over. It loops smoothly with the sound's loop() method. It repeats after random_seed().

    Arguments:
        sa: the base note: a note name such as "D3", or a frequency in hertz.
        seconds: how long the sound lasts.
        pattern: the strings to pluck, as swaras. The default is "P S' S' S". It may start with m or N instead of P.
        volume: its loudest point, 0 to 1. The default is 0.5.

    Returns:
        A Sound: loop(), play(), reverb() and so on.

    Example:
        sound.drone("D3", 8).loop()

    See also: pluck, tala, raga
    """
    values = _swaras.drone(sa, seconds, pattern, canvas_sketch()._rng, "sound.drone()", volume)
    return _engine.make(values, _sound_frame, "sound.drone()")


def microphone(name: str | None = None) -> Microphone:
    """Make a microphone object for the computer's default input.

    Call mic.start() to listen. While it listens, mic.level(), mic.spectrum(bands) and mic.pitch() work as they do on a sound. mic.capture(seconds) returns the last few seconds as a sound. It is never played back. With FUNGROUND_HEADLESS=1 it is silent and hears nothing. On a Mac, allow microphone access in System Settings.

    Arguments:
        name: part of the name of the input to use. The default None uses the default input. See microphones().

    Returns:
        A Microphone: start(), stop(), is_listening(), level(), spectrum(bands), pitch(), capture(seconds), is_onset(), chroma() and chord().

    Raises:
        RuntimeError: there is no microphone, or access is refused.

    Example:
        mic = sound.microphone()
        mic.start()

    See also: microphones, draw_wave, draw_spectrum, draw_pitch_line
    """
    return _microphone.make(name, _sound_frame)


def microphones() -> list[str]:
    """Return the names of the computer's microphones (inputs).

    Returns:
        A list of names. Give part of one to microphone().

    Example:
        print(sound.microphones())

    See also: microphone
    """
    return _microphone.microphones()


def draw_wave(source: Any, x: float, y: float, w: float, h: float) -> None:
    """Draw the wave of a sound, a microphone or a list of numbers.

    It is drawn inside a box, with the current fill, stroke and transform. For a sound it shows the whole sound, with a line at the place it is playing. For a microphone it shows the last half second. A sound's shape is worked out once for each width, so it is quick.

    Arguments:
        source: a Sound, a Microphone or a list of numbers.
        x, y: the top-left corner of the box.
        w, h: the width and height of the box, in pixels.

    Example:
        sound.draw_wave(song, 20, 20, 400, 80)

    See also: draw_spectrum, spectrogram, draw_pitch_line
    """
    _views.draw_wave(active_sketch(), source, x, y, w, h)


def draw_spectrum(source: Any, x: float, y: float, w: float, h: float, bands: int = 32) -> None:
    """Draw bars for a spectrum, as it is now.

    The bars stand on the bottom of a box, in the current style.

    Arguments:
        source: a Sound or a Microphone.
        x, y: the top-left corner of the box.
        w, h: the width and height of the box, in pixels.
        bands: how many bars. The default is 32.

    Example:
        sound.draw_spectrum(mic, 20, 120, 400, 80)

    See also: draw_wave, spectrogram
    """
    _views.draw_spectrum(active_sketch(), source, x, y, w, h, bands)


def spectrogram(sound: Sound, width: int, height: int) -> Picture:
    """Make a picture of a whole sound.

    Time goes across. Pitch goes up (about 40 hertz to 16 kilohertz, spaced like notes). Louder is brighter. The brightest colour is the current fill. It takes a moment (about a second for 10 seconds of sound at 400 by 200), so make it once, in setup().

    Arguments:
        sound: the Sound to look at.
        width, height: the size of the picture, in pixels.

    Returns:
        A Picture. Draw it with image(), or save it.

    Example:
        pic = sound.spectrogram(song, 400, 200)
        f.image(pic, 20, 20)

    See also: draw_wave, draw_spectrum, image
    """
    return _views.spectrogram(canvas_sketch(), active_sketch(), sound, width, height)


def draw_pitch_line(source: Any, x: float, y: float, w: float, h: float, seconds: float = 5,
                    low: str = "C3", high: str = "C6", sa: str | None = None) -> None:
    """Draw the pitch of a sound or microphone as a scrolling line.

    Call it once in every frame, because it reads source.pitch() each time. The line scrolls left. Faint guide lines are labelled with note names, or with swaras when sa is given. The line has a gap where pitch() is None.

    Arguments:
        source: a Sound or a Microphone.
        x, y: the top-left corner of the box.
        w, h: the width and height of the box, in pixels.
        seconds: how much time the box shows. The default is 5.
        low: the note at the bottom. The default is "C3".
        high: the note at the top. The default is "C6".
        sa: a note name such as "C4". With it the guide lines are swaras. The default None uses note names.

    Example:
        sound.draw_pitch_line(mic, 20, 20, 400, 150)

    See also: draw_wave, microphone, frequency_to_note
    """
    _views.draw_pitch_line(active_sketch(), canvas_sketch().frame_count, source,
                                x, y, w, h, seconds, low, high, sa)
