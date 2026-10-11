from funground import *

x = 50
speed = 3


def setup():
    size(640, 400)


def draw():
    global x, speed

    background(colors.WHITE)
    circle(x, height / 2, 40)

    x += speed
    if x > width - 20 or x < 20:
        speed = -speed
