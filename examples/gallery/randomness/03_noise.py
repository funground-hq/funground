"""Noise: smooth randomness

noise(x) gives a value from 0 to 1 that changes smoothly as x changes: hills instead of static.
noise(x, y) makes a smooth 2-D pattern. noise_seed(n) picks the pattern; noise_detail sets how
rough it is. The same seed gives the same values as p5.js.
"""
import playground as p


def setup():
    p.size(640, 400)
    p.noise_seed(2026)


def draw():
    p.background("white")
    p.no_stroke()

    # a 2-D noise texture: each tile's shade comes from noise(x, y)
    for row in range(16):
        for col in range(26):
            v = p.noise(col * 0.15, row * 0.15)
            p.fill((40, 90 + v * 150, 60 + v * 120))
            p.rect(col * 12, row * 12, 12, 12)

    # a landscape: the height of each column comes from noise(x), and it scrolls over time
    p.fill("steelblue")
    p.begin_shape()
    p.vertex(320, 400)
    for x in range(320, 641, 4):
        p.vertex(x, 80 + p.noise(x * 0.01 + p.frame_count * 0.02) * 260)
    p.vertex(640, 400)
    p.end_shape(close=True)

    # the same line with less detail: smoother
    p.noise_detail(1)
    p.no_fill()
    p.stroke("tomato")
    p.stroke_width(3)
    p.begin_shape()
    for x in range(0, 321, 4):
        p.vertex(x, 230 + p.noise(x * 0.03) * 160)
    p.end_shape()
    p.noise_detail(4)


p.run()
