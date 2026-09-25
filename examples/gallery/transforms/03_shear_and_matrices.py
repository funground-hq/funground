"""Shear and matrices

shear_x and shear_y slant everything drawn afterwards; apply_matrix multiplies in any transform
at once; reset_matrix forgets all transforms until the end of the saved_state block.
"""
import math

import playground as p


def setup():
    p.size(640, 400)


def checker(size=8, cell=12):
    for row in range(size):
        for col in range(size):
            p.fill("navy" if (row + col) % 2 else "gold")
            p.rect(col * cell, row * cell, cell, cell)


def draw():
    p.background("white")
    p.no_stroke()
    with p.saved_state():
        p.translate(40, 60)
        p.shear_x(25)                     # leans to the right
        checker()
    with p.saved_state():
        p.translate(230, 40)
        p.shear_y(20)                     # climbs to the right
        checker()
    with p.saved_state():
        a = math.radians(20)              # rotate by 20 degrees and stretch sideways, in one matrix
        p.apply_matrix(1.4 * math.cos(a), math.sin(a), -1.4 * math.sin(a), math.cos(a), 470, 60)
        checker()
        with p.saved_state():
            p.reset_matrix()              # back to plain window coordinates
            p.fill("tomato")
            p.circle(320, 330, 60)


p.run()
