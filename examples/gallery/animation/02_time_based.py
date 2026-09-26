"""Time-based motion

f.delta_time is the number of seconds the last frame took. Moving by speed * delta_time keeps
the same speed on a fast or a slow computer.
"""
# gallery: time-dependent
import funground as f

x = 0


def setup():
    f.size(640, 400)


def draw():
    global x
    f.background("white")
    f.fill("seagreen")
    f.circle(x, f.height / 2, 60)
    x += 150 * f.delta_time          # 150 pixels per second
    if x > f.width:
        x = 0


f.run()
