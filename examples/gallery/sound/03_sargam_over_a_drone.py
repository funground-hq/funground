"""Making sound: a sargam phrase over a drone

With sa="D4", f.melody() reads swaras instead of note names: S r R g G m M P d D n N.
A ' after a swara is the octave above and a comma is the octave below. Here the notes
use just tuning, the pure ratios from Sa. Under the phrase, a drone of plucked strings
plays Pa, Sa, Sa, Sa over and over. sound.reverb() gives the phrase and the strings a
room to ring in. The ladder shows the swara that sound.pitch() hears. The pink line follows the phrase only: it
folds each reading into one octave, takes the middle of the last five, and breaks at rests.
"""
# gallery: time-dependent
import math

import funground as f

SA = "D4"
TEMPO = 80
PHRASE = "S R G:2 R S,:2 N,:1 D,:1 P,:2 - S:1 R:1 G:1 P:2 G:1 R:1 S:3"
SWARAS = "SrRgGmMPdDnN"

# The soft voice (melody's own) suits a sung line; reverb adds a room around it.
phrase = f.melody(PHRASE, tempo=TEMPO, sa=SA, tuning="just").reverb(0.3)
phrase.set_volume(0.7)

# The drone: the four strings of a tanpura, plucked in turn, to last as long as the phrase.
# Each pluck gets its own reverb, which adds 0.45 s of ringing, so the pluck is made that much
# shorter to keep the drone the same length as the phrase.
strings = ["P,", "S", "S", "S,"]
string_seconds = phrase.duration() / (2 * len(strings))
plucks = [f.pluck(f.note_to_frequency(s, sa=SA), string_seconds - 0.45).reverb(0.3) for s in strings]
cycle = f.sequence(*plucks)
drone = f.sequence(cycle, cycle)
drone.set_volume(0.6)

# A quiet hum under it, made from numbers: three sine waves added up.
hum_hz = f.note_to_frequency("S,", sa=SA)
sa_hz = f.note_to_frequency("S", sa=SA)
hum = f.create_sound([0.2 * (math.sin(2 * math.pi * hum_hz * t / 44100)
                             + 0.5 * math.sin(4 * math.pi * hum_hz * t / 44100)
                             + 0.25 * math.sin(6 * math.pi * hum_hz * t / 44100))
                      for t in range(int(phrase.duration() * 44100))])
hum.set_volume(0.4)
trail = []
recent = []

# When each note of the phrase sounds, in seconds: (start, end) for notes, not rests.
beat = 60 / TEMPO
notes = []
clock = 0.0
for token in PHRASE.split():
    name, _, beats = token.partition(":")
    length = float(beats or 1) * beat
    if name != "-":
        notes.append((clock + 0.1, clock + length - 0.02))    # skip the soft start, where notes overlap
    clock += length

STEP = 25                                  # height of one row
BASE = 335                                 # text baseline of the bottom row, S


def in_a_note():
    t = phrase.current_time()
    return phrase.is_playing() and any(a <= t <= b for a, b in notes)


def swara_height(hz):
    """Where the voice is on the ladder, in rows above S, in one octave: 0 is S and 11 is N."""
    steps = 12 * math.log2(hz / sa_hz)
    return (steps + 0.5) % 12 - 0.5        # an octave slip lands on the right row, not off the ladder


def trace():
    """The next point of the line: a height in rows, or None for a gap."""
    hz = phrase.pitch() if in_a_note() else None
    if hz is None:
        del recent[:]
        return None
    here = swara_height(hz)
    if recent and abs(here - sorted(recent)[len(recent) // 2]) > 2:
        recent[:] = [here]                 # a jump: break the line and start again
        return None
    recent.append(here)
    del recent[:-5]
    return sorted(recent)[len(recent) // 2]


def setup():
    f.size(640, 400)
    for s in (phrase, drone, hum):
        s.loop()


def draw():
    f.background("#1d0f24")
    f.text_size(16)
    f.text_align("left", "center")
    height = trace()
    trail.append(height)
    del trail[:-120]
    heard = None
    if height is not None:
        heard = SWARAS[round(height) % 12]

    # the ladder: one row for each swara, S at the bottom
    f.no_stroke()
    for i, swara in enumerate(SWARAS):
        y = BASE - i * STEP
        f.fill("orange" if swara == heard else "#3a2147")
        f.rect(20, y - 18, 600, 22, 6)
        f.fill("white" if swara == heard else "#c9a7d9")
        f.text(swara, 30, y - 7)

    # the path of the voice, newest on the right; a gap wherever the line breaks
    f.stroke("hotpink")
    f.stroke_width(3)
    f.no_fill()
    last = None
    for k, step in enumerate(trail):
        if step is None:
            last = None
            continue
        point = (60 + k * 4.5, BASE - 7 - step * STEP)
        if last:
            f.line(*last, *point)
        last = point

    f.no_stroke()
    f.fill("white")
    f.text(f"Sa is {SA}   (now: {heard if heard else 'rest'})", 20, 380)


f.run()
