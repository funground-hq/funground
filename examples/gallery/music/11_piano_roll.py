"""Music: a piano roll of a tune you wrote

The tune is a string of notes, shown at the top. This sketch reads the string itself and draws
each note as a bar: time goes across, and higher notes sit higher up. The roll scrolls past a
fixed line as the tune plays, and each note lights up while it sounds. Tick the box to draw
f.draw_pitch_line() on top: the pitch that sound.pitch() hears, which should run along the bars
that have just played. This works because the notes were written in code, so the sketch already
knows them. A piano roll made from a recording would need a program that listens and guesses
the notes, which means machine learning. Change the string, and the roll changes too.
"""
# gallery: time-dependent
import math
import re

import funground as f

MELODY = ("E4 G4 C5:2 B4 G4 E4:2 - F4 A4 D5:2 C5 A4 F4:2 - "
          "G4:0.5 A4:0.5 B4 C5 D5 E5:2 D5:0.5 C5:0.5 B4 G4 [C4 E4 G4 C5]:4 -:2")
TEMPO = 108
BEAT = 60 / TEMPO
ROLL_X, ROLL_Y, ROLL_W = 60, 112, 560
HEAD = 200                       # the playhead: notes are here when they sound
PPS = 80                         # pixels for each second
NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


def parse(text):
    """Read a melody string into notes: (token, start beat, beats, [pitch numbers]).
    A rest is - and a chord is [ notes ]. :beats after a token says how long (1 if left off)."""
    notes = []
    beat = 0.0
    for token in re.findall(r"\[[^\[\]]*\]\S*|\S+", text):
        names, _, length = token.partition(":")
        beats = float(length or 1)
        if names == "-":
            pitches = []
        else:
            pitches = [pitch_number(n) for n in names.strip("[]").split()]
        notes.append((token, beat, beats, pitches))
        beat += beats
    return notes, beat


def pitch_number(name):
    """A note name as a number of semitones, from f.note_to_frequency(): 69 is A4 (440 Hz)."""
    return round(69 + 12 * math.log2(f.note_to_frequency(name) / 440))


notes, total_beats = parse(MELODY)
ALL = [p for _, _, _, pitches in notes for p in pitches]
LOW, HIGH = min(ALL), max(ALL)
ROWS = HIGH - LOW + 1
ROW = 238 / ROWS                 # height of one row
LENGTH = total_beats * BEAT      # seconds in one time round
tune = f.melody(MELODY, tempo=TEMPO).reverb(0.2)
tune.set_volume(0.8)


def note_name(number):
    return NAMES[number % 12] + str(number // 12 - 1)


def row_top(number):
    return ROLL_Y + (HIGH - number) * ROW


def setup():
    global heard_box
    f.size(640, 440)
    heard_box = f.create_checkbox("draw the pitch that is heard on top", True)
    tune.loop()


def draw():
    now = tune.current_time() % LENGTH if tune.is_playing() else 0.0
    f.background("#12182b")
    f.no_stroke()
    f.text_align("left", "top")
    f.fill("white")
    f.text_size(22)
    f.text("A piano roll of a tune written in code", 20, 10)

    # the melody string, with the token that is sounding now lit
    f.text_size(14)
    x, y = 20, 46
    for token, start, beats, _ in notes:
        width = f.text_width(token + "  ")
        if x + width > 620:
            x, y = 20, y + 20
        lit = start * BEAT <= now < (start + beats) * BEAT
        f.fill("gold" if lit else "#8fa3cc")
        f.text(token, x, y)
        x += width

    # the keys on the left, then the rows
    for number in range(LOW, HIGH + 1):
        top = row_top(number)
        black = NAMES[number % 12].endswith("#")
        sounding = any(s * BEAT <= now < (s + b) * BEAT and number in p for _, s, b, p in notes)
        f.fill("gold" if sounding else "#1c2440" if black else "#d8deef")
        f.rect(ROLL_X - 52, top + 1, 48, ROW - 1.5, 3)
        f.fill("#d8deef" if black and not sounding else "#222a44")
        f.text_size(10)
        if NAMES[number % 12] in ("C", "E", "G") or sounding:
            f.text(note_name(number), ROLL_X - 48, top + ROW / 2 - 5)
        f.fill("#1a2340" if black else "#1f2a4a")
        f.rect(ROLL_X, top + 1, ROLL_W, ROW - 1.5)

    # the bars: the tune, and the start of the next time round if it is in view
    for shift in (0, LENGTH):
        for _, start, beats, pitches in notes:
            left = HEAD + (start * BEAT + shift - now) * PPS
            right = left + beats * BEAT * PPS - 2
            if right < ROLL_X or left > ROLL_X + ROLL_W:
                continue
            left = max(left, ROLL_X)
            on = shift == 0 and start * BEAT <= now < (start + beats) * BEAT
            f.fill("gold" if on else "#6c8cff")
            for number in pitches:
                f.rect(left, row_top(number) + 1.5, right - left, ROW - 3.5, 3)

    # the beat lines
    f.stroke(255, 255, 255, 25)
    f.stroke_width(1)
    for beat in range(-8, int(total_beats * 2) + 12):
        gx = HEAD + (beat * BEAT - now) * PPS
        if ROLL_X <= gx <= ROLL_X + ROLL_W and beat % 4 == 0:
            f.line(gx, ROLL_Y, gx, ROLL_Y + ROWS * ROW)

    # the pitch that sound.pitch() hears, over the past, which sits left of the playhead
    if heard_box.checked():
        f.no_fill()
        f.stroke("#ff6ec7")
        f.stroke_width(3)
        f.draw_pitch_line(tune, ROLL_X, ROLL_Y + ROW / 2, HEAD - ROLL_X, (ROWS - 1) * ROW,
                          seconds=(HEAD - ROLL_X) / PPS, low=note_name(LOW), high=note_name(HIGH))

    # the playhead
    f.stroke("white")
    f.stroke_width(2)
    f.line(HEAD, ROLL_Y - 6, HEAD, ROLL_Y + ROWS * ROW + 6)
    f.no_stroke()
    f.text_size(13)
    f.fill("#9fb4d8")
    f.text("The sketch reads the string above, so it knows every note before it plays.", 20, 366)
    f.text("This works for tunes made in code. A roll from a recording would need machine learning.", 20, 386)
    f.text("The pink line is the one note heard now. A chord has no single pitch, so it leaves a gap.", 20, 406)


f.run()
