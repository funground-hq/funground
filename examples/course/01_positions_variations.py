# Original Funground course sketch. CC0; see ../LICENSE.
# Extend: the same experiment as 01_positions.py, with funground laying out the versions.

import funground as f

f.size(660, 440)
f.background("#f3efe6")


def study(y):
    # One version: a circle close to the left edge of the frame. Only y changes.
    f.no_stroke()
    f.fill("#264653")
    f.circle(70, y, 120)


f.variations(study, y=[70, 220, 370])

# When one version is the one you choose, keep it with a sentence:
# f.keep("I kept the low circle because ...", y=370)

f.save("01_positions_variations.png")
f.show()
