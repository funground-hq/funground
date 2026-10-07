"""Rhythm: five ways to repeat one beat (studio 3)

A rhythm is a repeat with a pattern in its spacing or its size. Each row repeats the same beat, a
stem with a round head: evenly, faster and faster, long and short, with an accent on every fourth,
and in groups of three and two. The same picture is written without the studio words in
examples/studios/03_rhythm_before.py.

How it works:
- f.size("A4", landscape=True, margin=f.mm(15)) makes a landscape A4 page with a margin.
- f.grid(1, 5, gutter=f.mm(4)) gives five rows. row.inset(left=LABEL) leaves room for the name.
- with f.mark() as beat: records the beat once. Its head is at its own (0, 0) and its stem hangs
  down from it.
- beat.place(x, y, anchor="bottom", scale=s) stands the beat on the line at y: the bottom of the
  stem lands there, and scaling grows it upwards from that point.
- The rhythms themselves are lists of gaps and sizes, made by small Python functions.

Make it yours:
- Change the gaps in long_short() to 70 and 14. When does it stop sounding even?
- Add an accent to grouped(): make the first beat of each group bigger.
- Draw the beat differently, for example a diamond head, inside the with f.mark() block.
- Turn every beat with rotate=10 in beat.place().
"""
import funground as f

f.size("A4", landscape=True, margin=f.mm(15))
f.background("#fbf8f1")

LABEL = 120                         # room on the left of each row for its name

with f.mark() as beat:              # the head at (0, 0), the stem hanging down from it
    f.no_stroke()
    f.fill("#3d405b")
    f.rect(-2, 0, 4, 60)
    f.fill("#e07a5f")
    f.circle(0, 0, 18)


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
for row, (name, beats) in zip(f.grid(1, 5, gutter=f.mm(4)), RHYTHMS):
    line = row.inset(left=LABEL, bottom=8)
    f.stroke("#d8d2c4")
    f.stroke_width(1)
    f.line(line.left, line.bottom, line.right, line.bottom)
    x = line.left
    for gap, size in beats:
        x += gap
        if x > line.right:
            break
        beat.place(x, line.bottom, anchor="bottom", scale=size)
    f.no_stroke()
    f.fill("#3d405b")
    f.text(name, row.left, line.bottom)

f.show()
