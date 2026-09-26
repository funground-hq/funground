"""Noise: smooth randomness

noise(x) gives a value from 0 to 1 that changes smoothly as x changes: hills instead of static.
noise(x, y) makes a smooth 2-D pattern. noise_seed(n) picks the pattern; noise_detail sets how
rough it is. The same seed gives the same values as p5.js.
"""
import funground as f


def setup():
    f.size(640, 400)
    f.noise_seed(2026)


def draw():
    f.background("white")
    f.no_stroke()

    # a 2-D noise texture: each tile's shade comes from noise(x, y)
    for row in range(16):
        for col in range(26):
            v = f.noise(col * 0.15, row * 0.15)
            f.fill((40, 90 + v * 150, 60 + v * 120))
            f.rect(col * 12, row * 12, 12, 12)

    # a landscape: the height of each column comes from noise(x), and it scrolls over time
    f.fill("steelblue")
    f.begin_shape()
    f.vertex(320, 400)
    for x in range(320, 641, 4):
        f.vertex(x, 80 + f.noise(x * 0.01 + f.frame_count * 0.02) * 260)
    f.vertex(640, 400)
    f.end_shape(close=True)

    # the same line with less detail: smoother
    f.noise_detail(1)
    f.no_fill()
    f.stroke("tomato")
    f.stroke_width(3)
    f.begin_shape()
    for x in range(0, 321, 4):
        f.vertex(x, 230 + f.noise(x * 0.03) * 160)
    f.end_shape()
    f.noise_detail(4)


f.run()
