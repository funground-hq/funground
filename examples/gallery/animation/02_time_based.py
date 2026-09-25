"""Time-based motion

p.delta_time is the number of seconds the last frame took. Moving by speed * delta_time keeps
the same speed on a fast or a slow computer.
"""
# gallery: time-dependent
import playground as p

x = 0


def setup():
    p.size(640, 400)


def draw():
    global x
    p.background("white")
    p.fill("seagreen")
    p.circle(x, p.height / 2, 60)
    x += 150 * p.delta_time          # 150 pixels per second
    if x > p.width:
        x = 0


p.run()
