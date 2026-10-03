"""Music: sing with the drone

f.drone() makes a sound like a tanpura: plucked strings on Pa and Sa that ring on and on.
Sing along with it. The microphone hears you, and your pitch is drawn as a line that moves
to the left. The bright lines are Sa and Pa. Try to hold your voice on them, and watch the
line go flat when you are in tune. f.frequency_to_note(hz, sa=SA) names the swara you sing.
sound.reverb() lets the strings ring in a room. Change SA to suit your voice. With no
microphone the drone still plays and the line waits.
"""
# gallery: time-dependent
import math

import funground as f

SA = "D3"                                  # a comfortable Sa for many voices; try "C3" or "A3"
SA_HZ = f.note_to_frequency(SA)


def room(sound, amount):
    """sound.reverb(amount), with the echo that runs past the end added back onto the start,
    so the sound still loops with no gap."""
    length = len(sound.samples())
    wet = sound.reverb(amount).samples()
    looped = wet[:length]
    for i, value in enumerate(wet[length:]):
        looped[i % length] += value
    return f.create_sound(looped)


# Two rounds of the strings. A drone loops without a gap; room() keeps it that way with reverb,
# which makes the strings sound warmer and fuller.
drone = room(f.drone(SA, 7), 0.4)
mic = f.microphone()
line = []                                  # cents above Sa for each frame, or None when quiet

# The lines to sing to: (cents above Sa, swara, colour)
GUIDES = [(-500, "P,", "#2f6f6a"), (0, "S", "gold"), (700, "P", "#58c4b8"), (1200, "S'", "gold")]


def y_for(cents):
    return 335 - (cents + 600) * 0.15      # from P, (low) to S' (high)


def setup():
    f.size(640, 360)
    drone.loop()
    mic.start()


def draw():
    f.background("#141a26")
    hz = mic.pitch()
    if hz:
        cents = 1200 * math.log2(hz / SA_HZ)
        line.append(cents if -650 < cents < 1300 else None)
    else:
        line.append(None)
    del line[:-280]

    f.text_size(14)
    f.text_align("left", "center")
    for cents, swara, colour in GUIDES:
        f.stroke(colour)
        f.stroke_width(2 if swara.startswith("S") else 1)
        f.line(40, y_for(cents), 620, y_for(cents))
        f.no_stroke()
        f.fill(colour)
        f.text(swara, 12, y_for(cents))

    f.stroke("hotpink")
    f.stroke_width(3)
    last = None
    for i, cents in enumerate(line):
        point = None if cents is None else (620 - (len(line) - 1 - i) * 2, y_for(cents))
        if point and last:
            f.line(*last, *point)
        last = point

    f.no_stroke()
    f.fill("white")
    sung = f.frequency_to_note(hz, sa=SA) if hz else "-"
    f.text(f"Sa is {SA}.   You sing: {sung}", 40, 25)


f.run()
