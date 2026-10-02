"""Making sound: a sargam phrase over a drone

With sa="D4", f.melody() reads swaras instead of note names: S r R g G m M P d D n N.
A ' after a swara is the octave above and a comma is the octave below. Here the notes
use just tuning, the pure ratios from Sa. Under the phrase, a drone of plucked strings
plays Pa, Sa, Sa, Sa over and over. The ladder shows the swara that sound.pitch() hears.
"""
# gallery: time-dependent
import math

import funground as f

SA = "D4"
TEMPO = 80
PHRASE = "S R G:2 R S,:2 N,:1 D,:1 P,:2 - S:1 R:1 G:1 P:2 G:1 R:1 S:3"
SWARAS = "SrRgGmMPdDnN"

phrase = f.melody(PHRASE, tempo=TEMPO, wave="saw", sa=SA, tuning="just")
phrase.set_volume(0.35)

# The drone: the four strings of a tanpura, plucked in turn, to last as long as the phrase.
strings = ["P,", "S", "S", "S,"]
string_seconds = phrase.duration() / (2 * len(strings))
cycle = f.sequence(*[f.pluck(f.note_to_frequency(s, sa=SA), string_seconds) for s in strings])
drone = f.sequence(cycle, cycle)
drone.set_volume(0.5)

# A quiet hum under it, made from numbers: three sine waves added up.
sa_hz = f.note_to_frequency("S,", sa=SA)
hum = f.create_sound([0.2 * (math.sin(2 * math.pi * sa_hz * t / 44100)
                             + 0.5 * math.sin(4 * math.pi * sa_hz * t / 44100)
                             + 0.25 * math.sin(6 * math.pi * sa_hz * t / 44100))
                      for t in range(int(phrase.duration() * 44100))])
hum.set_volume(0.3)
trail = []


def setup():
    f.size(640, 400)
    for s in (phrase, drone, hum):
        s.loop()


def draw():
    f.background("#1d0f24")
    f.text_size(16)
    hz = phrase.pitch()
    heard = None
    if hz:
        heard = f.frequency_to_note(hz, sa=SA).rstrip("',")
        trail.append(12 * math.log2(hz / f.note_to_frequency("S", sa=SA)) % 12)
    else:
        trail.append(None)
    del trail[:-120]

    # the ladder: one row for each swara
    f.no_stroke()
    for i, swara in enumerate(SWARAS):
        y = 350 - i * 26
        f.fill("orange" if swara == heard else "#3a2147")
        f.rect(20, y - 18, 600, 22, 6)
        f.fill("white" if swara == heard else "#c9a7d9")
        f.text(swara, 30, y)

    # the path of the voice, newest on the right
    f.stroke("hotpink")
    f.stroke_width(3)
    f.no_fill()
    last = None
    for k, step in enumerate(trail):
        if step is None:
            last = None
            continue
        point = (60 + k * 4.5, 340 - step * 26)
        if last:
            f.line(*last, *point)
        last = point

    f.no_stroke()
    f.fill("white")
    f.text(f"Sa is {SA}   (now: {f.frequency_to_note(hz, sa=SA) if hz else 'rest'})", 20, 385)


f.run()
