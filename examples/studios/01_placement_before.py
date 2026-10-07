"""Placement, without the studio words (studio 1, before)

The same picture as examples/gallery/studios/01_placement.py: nine frames on an A5 page, each
holding the same small drawing at a different point of its frame. This version uses only what
funground had before the studio words: numbers for the page, a function for the drawing, and the
arithmetic for the margin, the cells and the drawing's own size written out.

How it works:
- An A5 page is 420 by 595 points, and a millimetre is 72 / 25.4 points.
- pebble(x, y) draws the pebble with its own (0, 0) at (x, y), inside f.push() and f.pop().
- To put a corner or an edge of the pebble on a point, the code must know how far the pebble
  reaches from its (0, 0): PEBBLE_LEFT, PEBBLE_TOP, PEBBLE_W and PEBBLE_H.
- Two loops over the rows and columns work out each cell's left and top from the margin, the
  gutter and the cell size.

Make it yours:
- Change the ellipse in pebble(). Then change the four PEBBLE_ numbers to match, or it will no
  longer sit in the corners.
- Change PAD to 0, so the pebble touches the frame.
- Compare the two versions: which numbers had to be worked out here?
"""
import funground as f

MM = 72 / 25.4                    # one millimetre in points
W, H = 420, 595                   # an A5 page
MARGIN = 12 * MM
GUTTER = 6 * MM
PAD = 4 * MM

f.size(W, H)
f.background("#f3efe6")


def pebble(x, y):
    f.push()
    f.translate(x, y)
    f.no_stroke()
    f.fill("#2f3e46")
    f.ellipse(0, 0, 46, 32)
    f.fill("#e76f51")
    f.circle(9, -4, 11)
    f.pop()


# How far the pebble reaches from its own (0, 0): the ellipse is 46 wide and 32 high.
PEBBLE_LEFT, PEBBLE_TOP, PEBBLE_W, PEBBLE_H = -23, -16, 46, 32

cell_w = (W - 2 * MARGIN - 2 * GUTTER) / 3
cell_h = (H - 2 * MARGIN - 2 * GUTTER) / 3
for row in range(3):
    for col in range(3):
        left = MARGIN + col * (cell_w + GUTTER)
        top = MARGIN + row * (cell_h + GUTTER)
        f.no_fill()
        f.stroke("#c9c0ae")
        f.stroke_width(1)
        f.rect(left, top, cell_w, cell_h)
        # the room the pebble can move in, inside the padding, and how far across and down it goes
        room_w = cell_w - 2 * PAD - PEBBLE_W
        room_h = cell_h - 2 * PAD - PEBBLE_H
        x = left + PAD + room_w * col / 2 - PEBBLE_LEFT
        y = top + PAD + room_h * row / 2 - PEBBLE_TOP
        pebble(x, y)

f.show()
