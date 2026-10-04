"""Time-based motion

f.delta_time is the number of seconds the last frame took. Moving by speed * delta_time keeps
the same speed on a fast or a slow computer.

How it works:
- f.delta_time is the time the last frame took, in seconds. At 60 frames a second it is about
  0.017.
- x += 150 * f.delta_time adds 150 pixels for every second. A slow computer takes bigger steps less
  often and the circle still covers the same distance.
- Moving by a fixed number of pixels in each frame would be faster on a fast computer. This way is
  fair on every computer.
- When x passes f.width, the sketch sets x back to 0 and the circle starts again.
- f.background(), f.fill() and f.circle() draw each frame from scratch.

Make it yours:
- Change 150 to another speed, in pixels per second.
- Change the colour in f.fill("seagreen").
- Make the circle go up and down as well. Use math.sin(f.millis() / 500) in the y value, with
  import math at the top.
- Add a second circle that moves at 300 pixels per second.
- Make the circle grow as it crosses: use 20 + x / 10 as its size.
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
