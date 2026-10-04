"""Music: draw a wave and hear it

Every sound is a wave, and the shape of the wave is what makes a flute sound different from a
violin. Drag the mouse inside the box on the left to draw one period of a wave. f.create_sound()
repeats your shape 220 times a second, so you hear it as a note, and it starts again when you
let go. The right box is the spectrum: a bar for each pitch in the sound. A smooth wave has one
tall bar. A sharp, jagged wave has many. Try the buttons for a sine, a square, a saw and a soft
wave, then draw your own. It is the same note each time, only the shape changes.
"""
# gallery: time-dependent
import math

import funground as f

N = 48                       # points across one period
RATE = 44100
PITCH = 220                  # the note is A3: this many repeats of the shape every second
BX, BY, BW, BH = 20, 66, 300, 160          # the drawing box
SX, SW = 340, 280                          # the spectrum box (same top and height)

shape = [math.sin(2 * math.pi * i / N) for i in range(N)]     # heights from -1 (bottom) to 1 (top)
sound = None
dirty = False                # the shape changed and the sound is out of date
last = None                  # where the mouse was a moment ago, while drawing
buttons = {}


def preset(name):
    """One period of a classic wave, as N heights."""
    out = []
    for i in range(N):
        p = i / N
        if name == "sine":
            out.append(math.sin(2 * math.pi * p))
        elif name == "square":
            out.append(1.0 if p < 0.5 else -1.0)
        elif name == "saw":
            out.append(2 * p - 1)
        else:       # soft: a sine with a little of its second and third harmonics
            out.append(math.sin(2 * math.pi * p) + 0.4 * math.sin(4 * math.pi * p)
                       + 0.15 * math.sin(6 * math.pi * p))
    peak = max(abs(v) for v in out)
    return [v / peak for v in out]


def rebuild():
    """Make one second of sound by repeating the shape, and play it on a loop."""
    global sound, dirty
    dirty = False
    mean = sum(shape) / N                       # a wave that sits above zero would only push the speaker
    period = [v - mean for v in shape]
    peak = max(abs(v) for v in period)
    if peak < 1e-6:
        period = [0.0] * N                      # a flat line is silence
    else:
        period = [0.5 * v / peak for v in period]       # leave plenty of room below the loudest
    numbers = []
    for t in range(RATE):
        place = (t * PITCH / RATE) % 1 * N      # where in the period this moment falls
        i = int(place)
        a, b = period[i], period[(i + 1) % N]
        numbers.append(a + (b - a) * (place - i))       # a line between two points
    if sound:
        sound.stop()
    sound = f.create_sound(numbers)
    sound.set_volume(0.8)
    sound.loop()


def paint(x, y):
    """Move the point nearest to x to the height of y."""
    i = min(max(round((x - BX) / (BW / N)), 0), N - 1)
    shape[i] = min(1.0, max(-1.0, 1 - 2 * (y - BY) / BH))


def in_box(x, y):
    return BX - 6 <= x <= BX + BW + 6 and BY - 6 <= y <= BY + BH + 6


def mouse_pressed():
    global last, dirty
    if in_box(f.mouse_x, f.mouse_y):
        last = (f.mouse_x, f.mouse_y)
        paint(*last)
        dirty = True


def mouse_dragged():
    global last, dirty
    if last is None:
        return
    # fill in the points the mouse jumped over, so a quick drag leaves no gaps
    x0, y0 = last
    steps = max(1, int(abs(f.mouse_x - x0) / (BW / N)) + 1)
    for k in range(1, steps + 1):
        paint(x0 + (f.mouse_x - x0) * k / steps, y0 + (f.mouse_y - y0) * k / steps)
    last = (f.mouse_x, f.mouse_y)
    dirty = True


def mouse_released():
    global last
    if last is not None:
        last = None
        if dirty:
            rebuild()              # hear it when you let go


def setup():
    f.size(640, 420)
    for name in ("sine", "square", "saw", "soft"):
        buttons[name] = f.create_button(name)
    rebuild()


def draw():
    global shape
    for name, button in buttons.items():
        if button.clicked():
            shape = preset(name)
            rebuild()
    f.background("#121a2b")
    f.text_align("left", "top")
    f.text_size(22)
    f.no_stroke()
    f.fill("white")
    f.text("The shape of a wave is its sound", 20, 16)
    f.text_size(13)
    f.fill("#9fb4d8")
    f.text("drag in the left box to draw the wave, then let go to hear it", 20, 44)

    # the drawing box, with the middle line
    f.fill("#1b2742")
    f.rect(BX, BY, BW, BH, 6)
    f.stroke("#3b4d78")
    f.stroke_width(1)
    f.line(BX, BY + BH / 2, BX + BW, BY + BH / 2)
    f.no_fill()
    f.stroke("deepskyblue")
    f.stroke_width(3)
    f.begin_shape()
    for i, v in enumerate(shape):
        f.vertex(BX + (i + 0.5) * BW / N, BY + BH / 2 - v * BH / 2)
    f.end_shape()
    f.no_stroke()
    f.fill("white")
    for i, v in enumerate(shape):
        f.circle(BX + (i + 0.5) * BW / N, BY + BH / 2 - v * BH / 2, 5)

    # the spectrum of what is playing
    f.fill("#1b2742")
    f.rect(SX, BY, SW, BH, 6)
    f.fill("orange")
    f.draw_spectrum(sound, SX + 6, BY + 8, SW - 12, BH - 16, bands=48)

    f.fill("#9fb4d8")
    f.text("one period (drag here)", BX, BY + BH + 6)
    f.text("spectrum: low pitch left, high right", SX, BY + BH + 6)

    # the shape repeated, which is what the speaker follows
    f.fill("#1b2742")
    f.rect(20, 270, 600, 110, 6)
    f.no_fill()
    f.stroke("#7be0a8")
    f.stroke_width(2)
    f.begin_shape()
    for i in range(N * 4 + 1):
        v = shape[i % N]
        f.vertex(20 + i * 600 / (N * 4), 325 - v * 46)
    f.end_shape()
    f.no_stroke()
    f.fill("#9fb4d8")
    f.text("the same shape, over and over: the speaker follows this", 20, 388)
    f.text(f"{PITCH} repeats a second is the note A3", 20, 404)


f.run()
