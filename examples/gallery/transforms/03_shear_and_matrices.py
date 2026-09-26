"""Shear and matrices

shear_x and shear_y slant everything drawn afterwards; apply_matrix multiplies in any transform
at once; reset_matrix forgets all transforms until the end of the saved_state block.
"""
import math

import funground as f


def setup():
    f.size(640, 400)


def checker(size=8, cell=12):
    for row in range(size):
        for col in range(size):
            f.fill("navy" if (row + col) % 2 else "gold")
            f.rect(col * cell, row * cell, cell, cell)


def draw():
    f.background("white")
    f.no_stroke()
    with f.saved_state():
        f.translate(40, 60)
        f.shear_x(25)                     # leans to the right
        checker()
    with f.saved_state():
        f.translate(230, 40)
        f.shear_y(20)                     # climbs to the right
        checker()
    with f.saved_state():
        a = math.radians(20)              # rotate by 20 degrees and stretch sideways, in one matrix
        f.apply_matrix(1.4 * math.cos(a), math.sin(a), -1.4 * math.sin(a), math.cos(a), 470, 60)
        checker()
        with f.saved_state():
            f.reset_matrix()              # back to plain window coordinates
            f.fill("tomato")
            f.circle(320, 330, 60)


f.run()
