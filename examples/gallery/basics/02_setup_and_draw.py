"""setup() once, draw() every frame

setup() runs once; draw() runs again and again. f.frame_count counts the frames, f.width and
f.height are the window size, and f.stop() ends the sketch.
"""
import funground as f


def setup():
    f.size(640, 400, title="setup and draw")


def draw():
    f.background("midnightblue")
    f.fill("gold")
    f.no_stroke()
    # a dot that walks across the window, one step per frame, and starts again at the left edge
    x = (40 + f.frame_count * 8) % f.width
    f.circle(x, f.height / 2, 30)
    f.fill("white")
    f.text_size(20)
    f.text(f"frame {f.frame_count} of a {f.width} x {f.height} window", 20, 20)
    if f.frame_count > 600:
        f.stop()


f.run()
