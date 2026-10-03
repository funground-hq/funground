"""Sound: a tuner that listens

f.microphone() listens to your computer's microphone. mic.start() begins, and then
mic.pitch() gives the pitch of the one note you sing or play, or None when it is quiet.
f.frequency_to_note() turns that pitch into a name like "A4". The needle shows whether
you are a little flat (left) or sharp (right). The bar at the bottom is mic.level().
Nothing is recorded or played back. With no microphone to hear, the sketch still runs,
and just waits.
"""
# gallery: time-dependent
import math

import funground as f

mic = f.microphone()
listen_to = (f.microphones() or ["no microphone"])[0]     # shown at the top
needle = 0.0              # cents sharp (+) or flat (-), smoothed
name = "-"
quiet_frames = 0


def cents_off(hz, note_name):
    """How far the pitch is from the named note, in hundredths of a semitone."""
    return 1200 * math.log2(hz / f.note_to_frequency(note_name))


def setup():
    f.size(520, 360)
    mic.start()
    f.text_align("center")


def draw():
    global needle, name, quiet_frames
    hz = mic.pitch()
    if hz is None:
        quiet_frames += 1
        if quiet_frames > 20:           # wait a moment before saying "nothing"
            name = "-"
            needle *= 0.9
    else:
        quiet_frames = 0
        name = f.frequency_to_note(hz)
        target = max(-50, min(50, cents_off(hz, name)))
        needle += (target - needle) * 0.3

    in_tune = name != "-" and abs(needle) < 5
    f.background("black")

    # which microphone, then the note name
    f.fill("gray")
    f.text_size(14)
    f.text(listen_to, 260, 24)
    f.fill("limegreen" if in_tune else "white")
    f.text_size(80)
    f.text(name, 260, 110)

    # the dial: flat on the left, in tune in the middle, sharp on the right
    f.stroke("gray")
    f.stroke_width(2)
    f.no_fill()
    f.arc(260, 300, 360, 360, 225, 315)
    angle = math.radians(needle * 0.9)       # 50 cents is 45 degrees
    if name != "-":                          # no needle when nothing is heard
        f.stroke("limegreen" if in_tune else "tomato")
        f.stroke_width(4)
        f.line(260, 300, 260 + 160 * math.sin(angle), 300 - 160 * math.cos(angle))

    # the level
    f.no_stroke()
    f.fill("dimgray")
    f.rect(20, 330, 480, 14)
    f.fill("deepskyblue")
    f.rect(20, 330, 480 * min(1, mic.level() * 4), 14)


f.run()
