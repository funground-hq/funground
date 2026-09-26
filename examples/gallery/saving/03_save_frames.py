"""Saving an animation as frames

p.save_frames("frames/####.png", 30) saves this frame and the next 29 as numbered pictures:
frames/0001.png, frames/0002.png and so on. A program such as ffmpeg can join them into a video
or a GIF - see chapter 13 of the guide.
"""
import math

import playground as p


def setup():
    p.size(640, 400)


def draw():
    p.background("black")
    p.no_stroke()
    for i in range(12):
        angle = p.frame_count + i * 30              # 30 frames turn 30 degrees: back to the start
        x = 320 + 140 * math.cos(p.radians(angle))
        y = 200 + 140 * math.sin(p.radians(angle))
        p.fill(p.hsb(angle % 360, 80, 100))          # colour and size depend on the angle only
        p.circle(x, y, 30 + 10 * math.sin(p.radians(angle * 3)))
    if p.frame_count == 0:
        p.save_frames("frames/####.png", 30)      # 30 pictures that loop seamlessly


p.run()
