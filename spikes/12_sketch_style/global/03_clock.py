from funground import *


def setup():
    size(640, 400)


def hand(angle, length, width, colour):
    with saved_state():
        translate(200, 200)
        rotate(angle - 90)             # 0 degrees points right; clock hands start at 12
        stroke(colour)
        stroke_width(width)
        line(0, 0, length, 0)


def draw():
    background(colors.WHITE)
    fill(colors.WHITESMOKE)
    stroke(colors.BLACK)
    stroke_width(4)
    circle(200, 200, 320)
    hand((hour() % 12) * 30 + minute() * 0.5, 90, 10, colors.BLACK)
    hand(minute() * 6, 130, 6, colors.BLACK)
    hand(second() * 6, 140, 2, colors.TOMATO)

    fill(colors.BLACK)
    text_size(20)
    text(f"{day():02d}.{month():02d}.{year()}", 400, 150)
    text(f"{hour():02d}:{minute():02d}:{second():02d}", 400, 190)
    text_size(14)
    text(f"running for {millis() / 1000:.1f} s at {frame_rate():.0f} fps", 400, 240)
