"""setup() once, draw() every frame

setup() runs once; draw() runs again and again. p.frame_count counts the frames, p.width and
p.height are the window size, and p.stop() ends the sketch.
"""
import playground as p


def setup():
    p.size(640, 400, title="setup and draw")


def draw():
    p.background("midnightblue")
    p.fill("gold")
    p.no_stroke()
    # a dot that walks across the window, one step per frame
    p.circle(40 + p.frame_count * 8, p.height / 2, 30)
    p.fill("white")
    p.text_size(20)
    p.text(f"frame {p.frame_count} of a {p.width} x {p.height} window", 20, 20)
    if p.frame_count > 600:
        p.stop()


p.run()
