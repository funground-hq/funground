from funground import *


def cross(x, y):
    stroke(colors.RED)
    stroke_width(1)
    line(x - 6, y, x + 6, y)
    line(x, y - 6, x, y + 6)


def setup():
    size(640, 400)


def draw():
    background(colors.WHITE)
    fill(colors.BLACK)
    no_stroke()
    text_size(20)
    for row, vertical in enumerate([TOP, CENTER, BASELINE, BOTTOM]):
        y = 50 + row * 80
        for column, horizontal in enumerate([LEFT, CENTER, RIGHT]):
            x = 70 + column * 250
            text_align(horizontal, vertical)
            fill(colors.BLACK)
            text(f"{horizontal} {vertical}", x, y)
            cross(x, y)
            no_stroke()

    # the measurements behind the alignment
    text_align(LEFT, BASELINE)
    text_size(14)
    fill(colors.GRAY)
    text(f"ascent {text_ascent():.1f} px, descent {text_descent():.1f} px at size 14", 10, 390)
