"""Music: a tala goes round

A tala is a cycle of beats that comes round again and again. f.tala_info(name) gives its
beats, its vibhags (the groups the beats fall in), the beats you clap (tali) and wave
(khali), and the bols: the syllables a tabla player says for each stroke. f.tala(name)
plays one cycle with simple drum sounds. Here the bols sit round a circle and the beat
playing now glows. The sam, beat 1, is marked X; a wave is marked 0. Keys 1 to 6 pick a tala.
"""
# gallery: time-dependent
import math

import funground as f

TEMPO = 80
NAMES = f.talas()
info = None
cycle = None


def choose(index):
    global info, cycle
    if cycle:
        cycle.stop()
    info = f.tala_info(NAMES[index])
    cycle = f.tala(info.name, tempo=TEMPO)
    cycle.loop()


def setup():
    f.size(560, 480)
    choose(0)


def key_pressed():
    if f.key and f.key in "123456":
        choose(int(f.key) - 1)


def marks():
    """The sign over each beat: X for the sam, 0 for a wave, 2, 3, ... for the other claps."""
    out = {}
    clap = 2
    for beat in sorted(info.tali + info.khali):
        if beat == info.sam:
            out[beat] = "X 0" if beat in info.khali else "X"
        elif beat in info.khali:
            out[beat] = "0"
        else:
            out[beat] = str(clap)
            clap += 1
    return out


def draw():
    f.background("#10202a")
    now = int(cycle.current_time() / (60 / TEMPO)) % info.beats + 1
    signs = marks()
    waved = set()                     # the beats of each vibhag that starts with a wave
    start = 1
    for size in info.vibhag:
        if start in info.khali:
            waved.update(range(start, start + size))
        start += size
    f.text_align("center", "center")
    for beat, bol in enumerate(info.bols, start=1):
        angle = math.radians(360 * (beat - 1) / info.beats - 90)
        x = 280 + 150 * math.cos(angle)
        y = 230 + 150 * math.sin(angle)
        f.no_stroke()
        if beat == now:
            f.fill(255, 200, 80, 90)
            f.circle(x, y, 64)
        f.fill("gold" if beat == now else "#7fa6b8" if beat in waved else "#e0f0f0")
        f.text_size(17 if len(bol) < 6 else 12)
        f.text(bol, x, y)
        if beat in signs:
            f.fill("tomato" if beat == info.sam else "#7fd0c0")
            f.text_size(15)
            f.text(signs[beat], 280 + 196 * math.cos(angle), 230 + 196 * math.sin(angle))

    f.fill("white")
    f.text_size(28)
    f.text(info.name, 280, 218)
    f.text_size(15)
    f.text(f"{info.beats} beats: {' + '.join(map(str, info.vibhag))}", 280, 248)
    f.fill("#7fa6b8")
    f.text_size(13)
    f.text("keys:  " + "   ".join(f"{i + 1} {n}" for i, n in enumerate(NAMES)), 280, 462)


f.run()
