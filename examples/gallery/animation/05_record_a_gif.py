"""Record an animation as a GIF

f.save_gif("spinner.gif", 2) records the next 2 seconds of the sketch and writes them as a GIF
that loops for ever. Each frame is shown for 1 divided by the frame rate. f.save_movie("spinner.mp4", 2)
does the same for an MP4, which needs the free program ffmpeg. Call either one once; here it is on
the first frame. The animation turns once in 60 frames, so the GIF loops without a jump.
"""
import math

import funground as f


def setup():
    f.size(240, 240, fps=30)


def draw():
    f.background("black")
    f.no_stroke()
    for i in range(8):
        angle = f.frame_count * 6 + i * 45             # 60 frames turn 360 degrees
        f.fill(f.hsb(i * 45, 70, 100))
        f.circle(120 + 80 * math.cos(f.radians(angle)), 120 + 80 * math.sin(f.radians(angle)), 24)
    if f.frame_count == 0:
        f.save_gif("spinner.gif", 2)


f.run()
