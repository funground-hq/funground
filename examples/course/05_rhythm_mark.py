# Original Funground course sketch. CC0; see ../LICENSE.
# Extend: the same experiment as 05_rhythms.py, with one mark placed along each rhythm.

import funground as f

f.size(650, 330)
f.background("#f3efe6")

# Draw the mark once. Its centre, (0, 0), is the point that lands where you place it.
with f.mark() as bead:
    f.no_stroke()
    f.fill("#264653")
    f.circle(0, 0, 18)                     # the size of the dots in 05_rhythms.py
    f.fill("#f3efe6")
    f.circle(-3, -3, 5)

patterns = [
    ("Steady", [42, 42, 42, 42, 42, 42]),
    ("A longer pause", [30, 30, 90, 30, 30, 30]),
    ("Intervals grow", [18, 27, 36, 45, 54, 63]),
]
f.fill("#264653")
f.text_align("left", "top")
f.text_size(17)
for row, (label, gaps) in enumerate(patterns):
    y = 60 + row * 100
    f.text(label, 20, y - 9)
    x = 210
    bead.place(x, y)
    for gap in gaps:
        x += gap
        bead.place(x, y)

f.save("05_rhythm_mark.png")
f.show()
