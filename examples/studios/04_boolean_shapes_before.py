"""Boolean shapes, without the studio words (studio 4, before)

The same picture as examples/gallery/studios/04_boolean_shapes.py: a circle and a square, and the
union, intersection, difference and xor made from them. The path operators were in funground
already; this version places the shapes with numbers, path.bounds() and push, translate and scale.

How it works:
- f.path().circle() and f.path().rect() make the two shapes as paths, around (0, 0).
- The operators | & - and ^ are union, intersection, difference and xor. Each gives a new path.
- To fit the pair into the top row, path.bounds() gives its size. The outline is 2 wide, so half of
  it, 1, sticks out on every side and is added by hand.
- Each result is drawn inside f.push() and f.pop(), moved and scaled to its cell.

Make it yours:
- Change the outline to f.stroke_width(6). Then change STROKE too, or the fit is off.
- Move the square: change -25 in f.path().rect() and watch all four results change.
- Compare the two versions: where does each one work out the size of the pair?
"""
import funground as f

MM = 72 / 25.4
W, H = 595, 420                    # A5, on its side
MARGIN = 10 * MM
GUTTER = 6 * MM
STROKE = 2

f.size(W, H)
f.background("white")

circle = f.path().circle(-25, 0, 120)
square = f.path().rect(-25, -50, 100, 100)
RESULTS = [("union", circle | square, "#264653"), ("intersection", circle & square, "#2a9d8f"),
           ("difference", circle - square, "#e9c46a"), ("xor", circle ^ square, "#e76f51")]

cell_w = (W - 2 * MARGIN - 3 * GUTTER) / 4
cell_h = (H - 2 * MARGIN - GUTTER) / 2

# the pair, fitted into the whole top row: its size from the paths, plus the outline
x, y, w, h = (circle | square).bounds()
x, y, w, h = x - STROKE / 2, y - STROKE / 2, w + STROKE, h + STROKE
k = (cell_h - 20) / h
f.push()
f.translate(W / 2, MARGIN + cell_h / 2)
f.scale(k)
f.translate(-(x + w / 2), -(y + h / 2))
f.fill(29, 53, 87, 40)
f.stroke("#1d3557")
f.stroke_width(STROKE)
f.draw_path(circle)
f.draw_path(square)
f.pop()

ux, uy, uw, uh = RESULTS[0][1].bounds()
scale = (cell_w - 16) / uw                                 # one scale for all four
f.text_size(13)
f.text_align("center", "bottom")
for i, (name, shape, colour) in enumerate(RESULTS):
    cx = MARGIN + i * (cell_w + GUTTER) + cell_w / 2
    top = MARGIN + cell_h + GUTTER
    f.push()
    f.translate(cx, top + cell_h / 2 - 8)
    f.scale(scale)
    f.fill(colour)
    f.no_stroke()
    f.draw_path(shape)
    f.pop()
    f.fill("#495057")
    f.text(name, cx, top + cell_h)

f.show()
