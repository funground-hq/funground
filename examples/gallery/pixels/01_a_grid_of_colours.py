"""From pixels to marks, step 1: a grid of colours

A photo, cut into a grid of squares. Each square takes the colour of the photo at its centre, so the picture
becomes a mosaic, like a picture made of tiles or a very old computer game. This is the first step of the project
From pixels to marks in the guide.

How it works:
- A picture is a grid of pixels, and each pixel is a colour. photo.get(x, y) gives the colour at one point.
- Two loops walk over the canvas in steps of CELL: the outer loop goes down, the inner loop goes across.
- For each cell the sketch reads the colour at the cell's centre and fills a square of that colour.
- Nothing is drawn of the photo itself: the squares are the whole picture.

Make it yours:
- Change CELL to 10 for more detail, or to 40 for big, bold tiles.
- Draw circles with f.circle() instead of squares.
- Leave a gap between tiles: draw each square 2 pixels smaller than CELL.
- Put f.stroke("white") before the loops for a grid of lines.
"""
import funground as f

CELL = 20
photo = f.load_image("data/photo.jpg")

f.size(400, 300)
f.no_stroke()
for y in range(0, 300, CELL):
    for x in range(0, 400, CELL):
        colour = photo.get(x + CELL // 2, y + CELL // 2)      # the colour at the centre of this cell
        f.fill(colour)
        f.rect(x, y, CELL, CELL)
f.show()
