"""Rotating squares

translate moves the origin, rotate turns everything drawn afterwards (in degrees), scale grows
it. push() saves the current transform and style, pop() brings them back.
"""
import funground as f


def setup():
    f.size(640, 400)


def draw():
    f.background("white")
    f.no_stroke()
    for i in range(5):
        f.push()
        f.translate(80 + i * 120, 200)
        f.rotate(f.frame_count * 3 + i * 18)
        f.scale(1 + i * 0.2)
        f.fill((40 + i * 50, 90, 200))
        f.rect(-25, -25, 50, 50)
        f.pop()


f.run()
