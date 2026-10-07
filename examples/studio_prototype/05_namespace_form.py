"""Rhythm again, written with f.play (Play prototype)

This is 01_rhythm_variations.py written the other way: f.play.variations() instead of
f.variations(). Both ways work in this prototype so that they can be compared; one of them will be
removed. The bar heights differ from 01's only because this file fixes the random seed.

How it works:
- f.play holds the two exploring functions, f.play.variations() and f.play.keep().
- They are the same functions as f.variations() and f.keep(), under one name.
- f.random_seed(4) is set here, so this sheet is the same on every run.
"""
import funground as f

f.size(720, 400, margin=24)
f.background("#f4f1ea")
f.random_seed(4)


def rhythm(gap):
    area = f.ground.content
    f.background("#fbfaf6")
    f.no_stroke()
    x = area.left + 20
    count = 0
    while x < area.right - 20:
        tall = 60 + f.random(0, 120)
        f.fill("#d1495b" if count % 4 == 0 else "#2b4c7e")
        f.rect(x, area.cy - tall / 2, 16, tall, 4)
        x += gap
        count += 1


f.play.variations(rhythm, gap=[20, 28, 36, 50, 72])
f.show()
