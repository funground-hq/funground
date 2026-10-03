"""Drawing sound (S-111, contract A7, D-061).

Ready-made views of a sound or a microphone. Each one is only a convenience: it draws with
ordinary drawing calls (shapes, lines, rects, text) on the sketch it is given, in the current fill,
stroke and transform, so it works in layers, in pictures, and in PDF and SVG files. The one
exception is the spectrogram, which is a picture made from pixels.
"""
from __future__ import annotations

import math

from . import sound as _sound, synth

WAVE_SECONDS = 0.5            # how much of a microphone draw_wave() shows
SPECTROGRAM_FLOOR_DB = -60.0  # a bin this quiet or quieter is black
HISTORY_KEEP = 30.0           # seconds of pitch history kept for a source
BREAK_SECONDS = 0.3           # a longer wait between two pitch readings breaks the line
GUIDE_SPACING = 10.0          # fewer pixels than this between guides: label only the main ones


# ---- checking arguments
def _number(value, who: str, what: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"{who}: {what} must be a number, not {value!r}")
    return float(value)


def _box(who: str, x, y, w, h) -> tuple[float, float, float, float]:
    x, y = _number(x, who, "x"), _number(y, who, "y")
    w, h = _number(w, who, "w"), _number(h, who, "h")
    if w <= 0 or h <= 0:
        raise ValueError(f"{who}: w and h must be more than 0, not {w!r} and {h!r}")
    return x, y, w, h


def _is_microphone(source) -> bool:
    from .microphone_input import Microphone

    return isinstance(source, Microphone)


# ---- the waveform
def _envelope(values, columns: int) -> tuple[list[float], list[float]]:
    """The lowest and highest sample in each of *columns* equal slices of *values*."""
    n = len(values)
    lows, highs = [], []
    for i in range(columns):
        a = min(n - 1, i * n // columns)
        b = max(a + 1, (i + 1) * n // columns)
        chunk = values[a:b]
        lows.append(min(chunk))
        highs.append(max(chunk))
    return lows, highs


def _wave_numbers(source, who: str) -> list[float]:
    """The numbers to draw for a microphone or a list."""
    if _is_microphone(source):
        return source._window(max(1, round(source._rate * WAVE_SECONDS)))
    try:
        values = [float(v) for v in source]
    except (TypeError, ValueError):
        raise ValueError(f"{who}: the source must be a sound, a microphone or a list of numbers, "
                         f"not {source!r}") from None
    if not values:
        raise ValueError(f"{who}: the list of samples is empty, so there is nothing to draw")
    if not all(math.isfinite(v) for v in values):
        raise ValueError(f"{who}: the samples must be numbers, not nan or infinity")
    return values


def draw_wave(sk, source, x, y, w, h) -> None:
    who = "f.draw_wave()"
    x, y, w, h = _box(who, x, y, w, h)
    columns = max(1, round(w))
    is_sound = isinstance(source, _sound.Sound)
    if is_sound:                                              # a sound's envelope is made once per width
        cache = source.__dict__.setdefault("_views", {})
        if ("wave", columns) not in cache:
            cache[("wave", columns)] = _envelope(source.samples(), columns)
        lows, highs = cache[("wave", columns)]
    else:
        lows, highs = _envelope(_wave_numbers(source, who), columns)
    mid, half = y + h / 2, h / 2
    step = w / columns
    sk.begin_shape()
    for i in range(columns):                                  # along the top, left to right
        sk.vertex(x + (i + 0.5) * step, mid - max(-1.0, min(1.0, highs[i])) * half)
    for i in range(columns - 1, -1, -1):                      # back along the bottom
        sk.vertex(x + (i + 0.5) * step, mid - max(-1.0, min(1.0, lows[i])) * half)
    sk.end_shape(True)
    if is_sound and source.is_playing() and source.duration() > 0:
        at = x + w * min(1.0, source.current_time() / source.duration())
        sk.line(at, y, at, y + h)                             # the playhead


# ---- the spectrum
def draw_spectrum(sk, source, x, y, w, h, bands) -> None:
    who = "f.draw_spectrum()"
    x, y, w, h = _box(who, x, y, w, h)
    if not callable(getattr(source, "spectrum", None)):
        raise ValueError(f"{who}: the source must be a sound or a microphone, not {source!r}")
    values = source.spectrum(bands)
    step = w / len(values)
    with sk.saved_state():
        sk.rect_mode("corner")                                # bars sit on the box, whatever the mode
        for i, v in enumerate(values):
            bar = h * v
            sk.rect(x + i * step, y + h - bar, step * 0.85, bar)


# ---- the spectrogram
def _row_plan(height: int, rate: int):
    """For each picture row (top first): how to read its pitch range from the FFT bins."""
    bin_hz = rate / _sound.FFT_SIZE
    top_hz = min(_sound.HIGH_HZ, rate / 2)
    ratio = _sound.HIGH_HZ / _sound.LOW_HZ
    plan = []
    for row in range(height):
        lo_hz = _sound.LOW_HZ * ratio ** ((height - row - 1) / height)
        hi_hz = _sound.LOW_HZ * ratio ** ((height - row) / height)
        if lo_hz >= top_hz:
            plan.append(None)                                 # above what this sound can hold
            continue
        first = max(1, math.ceil(lo_hz / bin_hz))
        last = int(min(hi_hz, top_hz) / bin_hz)
        if last >= first:                                     # the row covers whole bins: take the loudest
            plan.append(("max", first, last))
        else:                                                 # narrower than a bin: read between bins
            centre = max(1.0, math.sqrt(lo_hz * hi_hz) / bin_hz)   # never the DC bin
            lo = int(centre)
            plan.append(("lerp", lo, centre - lo))
    return plan


def spectrogram_columns(snd, width: int, height: int) -> list[list[float]]:
    """Loudness, from 0 to 1, of each row (top first), for each of *width* columns."""
    values = snd.samples()
    rate = snd._sample_rate()
    n = len(values)
    size = _sound.FFT_SIZE
    plan = _row_plan(height, rate)
    norm = 4.0 / size
    floor = SPECTROGRAM_FLOOR_DB
    columns = []
    for col in range(width):
        centre = int((col + 0.5) / width * n)
        start = centre - size // 2
        if start >= 0 and start + size <= n:
            window = values[start:start + size]
        else:
            window = [values[i] if 0 <= i < n else 0.0 for i in range(start, start + size)]
        mags = None
        if any(window):
            result = _sound._fft([v * wt + 0j for v, wt in zip(window, _sound._HANN)])
            mags = [abs(result[k]) * norm for k in range(size // 2 + 1)]
        column = []
        for step in plan:
            if step is None or mags is None:
                column.append(0.0)
                continue
            if step[0] == "max":
                m = max(mags[step[1]:step[2] + 1])
            else:
                lo = step[1]
                m = mags[lo] * (1 - step[2]) + mags[min(lo + 1, len(mags) - 1)] * step[2]
            db = 20.0 * math.log10(m) if m > 1e-9 else floor
            bright = max(0.0, min(1.0, (db - floor) / -floor))
            column.append(bright * bright)            # squared: a clear note stands out from its spread
        columns.append(column)
    return columns


def spectrogram(canvas, current, snd, width, height):
    """A picture of the whole sound. *canvas* makes the picture; *current* gives the fill."""
    who = "f.spectrogram()"
    if not isinstance(snd, _sound.Sound):
        raise ValueError(f"{who}: give it a sound, not {snd!r}")
    for what, value in (("width", width), ("height", height)):
        if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= 8192:
            raise ValueError(f"{who}: {what} must be a whole number from 1 to 8192, not {value!r}")
    fill = current.style.fill
    red, green, blue = (fill.r, fill.g, fill.b) if fill is not None else (255, 255, 255)
    columns = spectrogram_columns(snd, width, height)
    picture = canvas.create_graphics(width, height)
    picture.load_pixels()
    buf = picture.pixels
    for col, column in enumerate(columns):
        for row, v in enumerate(column):
            i = (row * width + col) * 4
            buf[i] = round(red * v)
            buf[i + 1] = round(green * v)
            buf[i + 2] = round(blue * v)
            buf[i + 3] = 255
    picture.update_pixels()
    return picture


# ---- the pitch line
def _guides(low_hz: float, high_hz: float, sa: str | None):
    """(hz, label, main) for the notes (the white keys) or swaras (S R G m P D N) in the range."""
    out = []
    who = "f.draw_pitch_line()"
    if sa is None:
        for octave in range(-1, 10):
            for name in "CDEFGAB":
                label = f"{name}{octave}"
                hz = synth.note_to_frequency(label, who=who)
                if low_hz * 0.999 <= hz <= high_hz * 1.001:
                    out.append((hz, label, name == "C"))
    else:
        for octave in range(-4, 5):
            mark = "'" * octave if octave > 0 else "," * -octave
            for name in "SRGmPDN":
                label = name + mark
                hz = synth.note_to_frequency(label, sa, who=who)
                if low_hz * 0.999 <= hz <= high_hz * 1.001:
                    out.append((hz, label, name == "S"))
    return sorted(out)


def _history(source) -> list:
    """The pitch readings kept on the source: a list of (clock time, hertz or None)."""
    held = getattr(source, "_pitch_history", None)
    if held is None:
        held = []
        try:
            source._pitch_history = held
        except AttributeError:
            raise ValueError("f.draw_pitch_line(): the source must be a sound or a microphone "
                             f"(something with pitch()), not {source!r}") from None
    return held


def draw_pitch_line(sk, frame: int, source, x, y, w, h, seconds, low, high, sa) -> None:
    who = "f.draw_pitch_line()"
    x, y, w, h = _box(who, x, y, w, h)
    seconds = _number(seconds, who, "seconds")
    if seconds <= 0:
        raise ValueError(f"{who}: seconds must be more than 0, not {seconds!r}")
    if not callable(getattr(source, "pitch", None)):
        raise ValueError(f"{who}: the source must be a sound or a microphone, not {source!r}")
    low_hz = synth.note_to_frequency(low, who=who)
    high_hz = synth.note_to_frequency(high, who=who)
    if high_hz <= low_hz:
        raise ValueError(f"{who}: high ({high!r}) must be a higher note than low ({low!r})")
    if sa is not None:
        synth.note_to_frequency("S", sa, who=who)             # checks sa
    span = math.log2(high_hz / low_hz)

    history = _history(source)
    now = _sound.clock()
    if frame == 0 or getattr(source, "_pitch_frame", None) != frame:   # one reading a frame
        history.append((now, source.pitch()))
        source._pitch_frame = frame
    while history and now - history[0][0] > HISTORY_KEEP:
        history.pop(0)

    def y_of(hz: float) -> float:
        up = max(0.0, min(1.0, math.log2(hz / low_hz) / span))
        return y + h * (1.0 - up)

    guides = _guides(low_hz, high_hz, sa)
    crowded = len(guides) > 1 and min(
        abs(y_of(b[0]) - y_of(a[0])) for a, b in zip(guides, guides[1:])) < GUIDE_SPACING
    with sk.saved_state():                                    # faint guides, in their own style
        sk.color_mode("rgb", 255)
        sk.stroke(128, 128, 128, 70)
        sk.stroke_width(1)
        sk.fill(128, 128, 128, 200)
        sk.text_size(10)
        sk.text_align("left", "center")
        sk.no_dash()
        for hz, label, main in guides:
            if crowded and not main:
                continue
            gy = y_of(hz)
            sk.line(x, gy, x + w, gy)
            sk.text(label, x + 2, gy - 6)

    run: list[tuple[float, float]] = []

    def finish() -> None:
        if len(run) == 1:
            sk.point(*run[0])
        elif run:
            sk.begin_shape()
            for px, py in run:
                sk.vertex(px, py)
            sk.end_shape(False)
        run.clear()

    previous = None
    for t, hz in history:
        if hz is None or now - t > seconds:
            finish()
            previous = None
            continue
        if previous is not None and t - previous > BREAK_SECONDS:
            finish()
        run.append((x + w * (1.0 - (now - t) / seconds), y_of(hz)))
        previous = t
    finish()
