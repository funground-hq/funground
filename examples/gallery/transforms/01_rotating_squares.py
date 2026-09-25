"""Rotating squares

translate moves the origin, rotate turns everything drawn afterwards (in degrees), scale grows
it. push() saves the current transform and style, pop() brings them back.
"""
import playground as p


def setup():
    p.size(640, 400)


def draw():
    p.background("white")
    p.no_stroke()
    for i in range(5):
        p.push()
        p.translate(80 + i * 120, 200)
        p.rotate(p.frame_count * 3 + i * 18)
        p.scale(1 + i * 0.2)
        p.fill((40 + i * 50, 90, 200))
        p.rect(-25, -25, 50, 50)
        p.pop()


p.run()
