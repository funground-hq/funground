"""Rhythm, without the studio words (studio 3, before)

The same picture as examples/gallery/studios/03_rhythm.py: five rows that repeat the same beat
evenly, faster and faster, long and short, with accents, and in groups. This version uses only what
funground had before the studio words: numbers for the page and the rows, and push, translate and
scale to stand each beat on its line.

How it works:
- A landscape A4 page is 842 by 595 points, and a millimetre is 72 / 25.4 points.
- beat(x, y, size) draws the beat with the bottom of its stem on (x, y). Its head is drawn at its
  own (0, 0), so the code moves up by the stem's length, STEM, after scaling.
- The rows' tops come from the margin, the gutter and the row height, worked out by hand.
- The rhythms themselves are the same lists of gaps and sizes as in the other version.

Make it yours:
- Make the stem longer. Change STEM too, or the beats will no longer stand on the line.
- Change the gaps in long_short() to 70 and 14.
- Compare the two versions: where does each one say "stand on the line"?
"""
import funground as f

MM = 72 / 25.4
W, H = 842, 595                    # A4, on its side
MARGIN = 15 * MM
GUTTER = 4 * MM
LABEL = 120                        # room on the left of each row for its name
STEM = 60                          # from the head's centre to the bottom of the stem

f.size(W, H)
f.background("#fbf8f1")


def beat(x, y, size):
    """The beat standing on (x, y), scaled by size from that point."""
    f.push()
    f.translate(x, y)
    f.scale(size)
    f.translate(0, -STEM)          # the head is at (0, 0): move it up by the stem
    f.no_stroke()
    f.fill("#3d405b")
    f.rect(-2, 0, 4, STEM)
    f.fill("#e07a5f")
    f.circle(0, 0, 18)
    f.pop()


def even():
    return [(40, 0.7)] * 16


def faster():
    gaps, gap = [], 90
    while gap > 8:
        gaps.append((gap, 0.7))
        gap *= 0.8
    return gaps


def long_short():
    return [(56 if i % 2 else 22, 0.7) for i in range(18)]


def accents():
    return [(40, 1.0 if i % 4 == 0 else 0.6) for i in range(16)]


def grouped():
    return [(64 if i % 5 in (0, 3) else 26, 0.7) for i in range(20)]


RHYTHMS = [("even", even()), ("faster", faster()), ("long, short", long_short()),
           ("accents", accents()), ("3 + 2", grouped())]

f.text_size(16)
f.text_align("left", "bottom")
row_h = (H - 2 * MARGIN - 4 * GUTTER) / 5
for i, (name, beats) in enumerate(RHYTHMS):
    top = MARGIN + i * (row_h + GUTTER)
    left = MARGIN + LABEL
    right = W - MARGIN
    base = top + row_h - 8
    f.stroke("#d8d2c4")
    f.stroke_width(1)
    f.line(left, base, right, base)
    x = left
    for gap, size in beats:
        x += gap
        if x > right:
            break
        beat(x, base, size)
    f.no_stroke()
    f.fill("#3d405b")
    f.text(name, MARGIN, base)

f.show()
