"""Text as geometry, without the studio words (studio 5, before)

The same picture as examples/gallery/studios/05_text_as_geometry.py: one word cut into stripes,
traced with dots and crossed with a circle, each fitted to its row. f.text_path(), the path booleans
and f.text_to_points() were in funground already; this version fits each version with its own
bounds and push, translate and scale.

How it works:
- f.text_path("FUN", 0, 0) gives the outlines of the word as a path. word - stripes and
  word ^ ring are path booleans.
- fit(bounds, row) works out the scale and the move that make a shape as large as fits in a row,
  centred. The rows come from the margin and the gutter, by hand.
- A path has bounds(), but a list of dots does not, so the dots' extent is found from the points,
  plus the dots' radius.
- Each version is drawn inside f.push() and f.pop(), moved and scaled.

Make it yours:
- Change "FUN" to your own word.
- Change the dots to 5 across. Change DOT too, or the dots no longer fit their row exactly.
- Compare the two versions: how much of this one is fit()?
"""
import funground as f

MM = 72 / 25.4
W, H = 420, 595                    # an A5 page
MARGIN = 12 * MM
GUTTER = 8 * MM
DOT = 2.5

f.size(W, H)
f.background("#14213d")

f.text_style("bold")
f.text_size(100)
word = f.text_path("FUN", 0, 0)
x, y, w, h = word.bounds()

stripes = f.path()
for i in range(8):                                   # eight thin bands across the word
    stripes.rect(x - 5, y + h * (i + 0.6) / 8, w + 10, h / 32)
striped = word - stripes
ring = f.path().circle(x + w / 2, y + h / 2, h * 1.2)
crossed = word ^ ring
points = f.text_to_points("FUN", 0, 0, 4)

row_w = W - 2 * MARGIN
row_h = (H - 2 * MARGIN - 2 * GUTTER) / 3


def fit(bounds, row):
    """Move and scale so a shape with these bounds is as large as fits in the row, centred."""
    bx, by, bw, bh = bounds
    k = min(row_w / bw, row_h / bh)
    f.translate(MARGIN + row_w / 2, MARGIN + row * (row_h + GUTTER) + row_h / 2)
    f.scale(k)
    f.translate(-(bx + bw / 2), -(by + bh / 2))


f.no_stroke()
f.push()
fit(striped.bounds(), 0)
f.fill("#fca311")
f.draw_path(striped)
f.pop()

xs = [px for px, py in points]
ys = [py for px, py in points]
r = DOT / 2
f.push()
fit((min(xs) - r, min(ys) - r, max(xs) - min(xs) + DOT, max(ys) - min(ys) + DOT), 1)
f.fill("#8ecae6")
for px, py in points:
    f.circle(px, py, DOT)
f.pop()

f.push()
fit(crossed.bounds(), 2)
f.fill("#e5e5e5")
f.draw_path(crossed)
f.pop()

f.show()
