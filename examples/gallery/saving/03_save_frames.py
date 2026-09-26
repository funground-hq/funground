"""Saving an animation as frames

f.save_frames("frames/####.png", 30) saves this frame and the next 29 as numbered pictures:
frames/0001.png, frames/0002.png and so on. A program such as ffmpeg can join them into a video
or a GIF - see chapter 13 of the guide.
"""
import math

import funground as f


def setup():
    f.size(640, 400)


def draw():
    f.background("black")
    f.no_stroke()
    for i in range(12):
        angle = f.frame_count + i * 30              # 30 frames turn 30 degrees: back to the start
        x = 320 + 140 * math.cos(f.radians(angle))
        y = 200 + 140 * math.sin(f.radians(angle))
        f.fill(f.hsb(angle % 360, 80, 100))          # colour and size depend on the angle only
        f.circle(x, y, 30 + 10 * math.sin(f.radians(angle * 3)))
    if f.frame_count == 0:
        f.save_frames("frames/####.png", 30)      # 30 pictures that loop seamlessly


f.run()
