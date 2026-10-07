"""Keeping two versions of a tile pattern (Play prototype)

f.keep() saves the picture as it is now into a folder called studio, next to this file. With it go
a copy of this file and a record of what made the picture, so the version can be found and made
again later.

How it works:
- tiles(count) fills the canvas with a grid of quarter circles that turn by chance.
- f.random_seed(12) makes the turns the same every time this file runs.
- The first f.keep() saves 001.png, 001.py and 001.json, with a note and the setting count=6.
- The canvas is then drawn again with more tiles. The second f.keep() also asks for a PDF, so it
  saves 002.pdf as well, a vector drawing that stays sharp when printed.
- Run the file again and the numbers go on: 003, 004, and so on.
"""
import funground as f

f.size(400, 400)
f.random_seed(12)


def tiles(count):
    f.background("#1d3557")
    f.no_stroke()
    f.fill("#f1faee")
    side = f.width / count
    for row in range(count):
        for col in range(count):
            with f.saved_state():
                f.translate(col * side + side / 2, row * side + side / 2)
                f.rotate(90 * int(f.random(4)))
                f.arc(-side / 2, -side / 2, side * 2, side * 2, 0, 90, "pie")


tiles(6)
f.keep("big tiles: bold, almost a logo", count=6)

tiles(10)
f.keep("small tiles read as a maze", pdf=True, count=10)
f.show()
