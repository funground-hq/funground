"""From pixels to marks, step 2: dots by brightness

The same grid, but now every cell is a black dot on white paper, and the colour decides only its size: dark parts
of the photo give big dots, light parts small ones. From a step back the dots become the picture again. Printers
have used this trick, called halftone, for over a hundred years.

How it works:
- colour.brightness is a number from 0 (black) to 100 (white).
- f.map_range() turns brightness into a diameter: 0 becomes the whole cell, 100 becomes nothing.
- The dot is drawn at the centre of its cell, with no outline.
- min() keeps the point read inside the photo: 400 is not a whole number of cells, so the last column of
  cells reaches past its edge.
- The background is white, so where the photo is light there is mostly paper.

Make it yours:
- Swap the colours: white dots on black, with big dots where the photo is light.
- Change CELL. Small cells give a finer picture, big ones an abstract pattern.
- Draw squares with f.rect() instead of dots, centred in the cell.
- Colour each dot with the photo's own colour, as in step 1, and keep the size from brightness.
"""
import funground as f

CELL = 12
WIDTH, HEIGHT = 400, 300
photo = f.load_image("data/photo.jpg")

f.size(WIDTH, HEIGHT)
f.background("white")
f.no_stroke()
f.fill("black")
for y in range(0, HEIGHT, CELL):
    for x in range(0, WIDTH, CELL):
        brightness = photo.get(min(x + CELL // 2, WIDTH - 1), min(y + CELL // 2, HEIGHT - 1)).brightness
        diameter = f.map_range(brightness, 0, 100, CELL, 0)        # dark: a big dot, light: a small one
        f.circle(x + CELL / 2, y + CELL / 2, diameter)
f.show()
