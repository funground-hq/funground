"""Sound: a tuner that listens

Sing or play one note into your microphone. The big letters show its name, like A4. The needle
shows whether you are a little flat (left) or sharp (right), and it turns green when you are in
tune. The bar at the bottom is how loud you are. Nothing is recorded or played back. With no
microphone, the sketch still runs and waits.

How it works:
- f.microphone() makes the microphone, and mic.start() begins listening. f.microphones() lists
  the ones the computer has, and the first is named at the top.
- mic.pitch() gives the pitch of the one note it hears, in hertz, or None when it is quiet.
  mic.level() says how loud it is, from 0 to 1.
- f.frequency_to_note() turns the pitch into a name. cents_off() then measures how far the pitch is
  from that note. A cent is one hundredth of a semitone, so 50 cents is halfway to the next note.
- The needle moves a third of the way to its target each frame, which smooths the shaking.
- f.arc() draws the dial, and sin() and cos() put the needle at the right angle. 50 cents is 45
  degrees.
- A note needs 20 quiet frames before the name goes back to "-", so a short gap does not wipe it.

Make it yours:
- Change the 5 in abs(needle) < 5 to 10 and the tuner is easier to please.
- Change the 0.3 in needle += (target - needle) * 0.3. A smaller number is calmer, a bigger one
  is quicker.
- Change quiet_frames > 20 to hold the name for longer or shorter.
- Change the colours: "limegreen" and "tomato" in draw().
- Change f.text_size(80) to make the note name bigger or smaller.
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
