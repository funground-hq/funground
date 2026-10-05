# Project 5: Typographic portrait

A typographic portrait is a picture made of letters. Look close and you see words. Step back and
you see a face, a house or a sunset. In this project you cut a photo into a grid, put one letter in
each cell, and make the letter big where the photo is bright and small where it is dark. Then you
save it as a PDF, which stays sharp on a poster as big as a wall.

You will learn how to read the pixels of a picture, how to turn a colour into one number for its
brightness, how to draw letters at many sizes, and how to save a vector file.

## Run it

```sh
python examples/gallery/projects/05_typographic_portrait.py
```

Or open the gallery browser with `python -m funground.gallery` and pick **Typographic portrait** in
the Projects area. Move the "cell size" slider. Click "change letters" to try the Devanagari word.
Tick "invert", and untick "colour". Press P to save `portrait.pdf`.

## How it works

The full version in the gallery rests on three ideas.

**One pixel for each cell.** You do not need to look at every pixel of a big photo. Make a small
copy, with exactly one pixel for each cell of your grid. `picture.resize()` does the shrinking, and
`picture.load_pixels()` fills `picture.pixels` with four numbers for each pixel: red, green, blue
and alpha. The copy keeps the photo itself safe.

```py
small = photo.copy()                     # never change the photo itself
small.resize(columns, rows)              # one pixel for each cell
small.load_pixels()
pixels = bytes(small.pixels)
i = (row * columns + column) * 4         # where this cell starts
r, g, b = pixels[i], pixels[i + 1], pixels[i + 2]
```

**Brightness sets the size.** Red, green and blue are three numbers. A letter's size needs one.
Our eyes see green as the brightest and blue as the darkest, so the sum is not even. A good
recipe is a weighted sum. The result runs from 0 for black to 1 for white.

```py
def brightness(r, g, b):
    return (0.299 * r + 0.587 * g + 0.114 * b) / 255

f.text_size(brightness(r, g, b) * cell * 1.5)       # a bit bigger than the cell for white
```

**Paint only when something changes.** A portrait has thousands of letters. Painting them 60 times
a second would be slow, and the picture does not change. In an animated sketch the canvas keeps what
was drawn, so `draw()` can leave it alone. The sketch remembers the controls it last painted, and
paints again only when a slider, a tick box or a button has changed them.

```py
state = (cell_slider.value(), invert_box.checked(), colour_box.checked())
if state != last_state:
    last_state = state
    paint()
```

## Stage 1: make it work

A small stand-in picture, drawn in code, a grid of letters, and size from brightness. There is no
file to find, so it runs anywhere. Later you swap in a real photo.

```python
import funground as f

COLUMNS, ROWS, CELL = 40, 30, 12


def setup():
    f.size(COLUMNS * CELL, ROWS * CELL)
    f.no_loop()                                  # nothing moves, so draw once


def draw():
    art = f.create_graphics(COLUMNS, ROWS)       # a stand-in picture: one pixel for each cell
    art.background(0)
    art.no_stroke()
    art.fill(150)
    art.circle(20, 15, 26)
    art.fill(255)
    art.circle(15, 11, 10)
    art.load_pixels()

    f.background(20, 20, 30)
    f.no_stroke()
    f.fill(240)
    f.text_style("bold")
    f.text_align("center", "center")
    word = "funground"
    for row in range(ROWS):
        for column in range(COLUMNS):
            i = (row * COLUMNS + column) * 4
            amount = art.pixels[i] / 255          # grey: red, green and blue are the same
            if amount < 0.08:
                continue
            f.text_size(amount * CELL * 1.5)
            f.text(word[(row * COLUMNS + column) % len(word)], (column + 0.5) * CELL, (row + 0.5) * CELL)


f.run()
```

Run it. You should see a glowing ball made of letters. Change `"funground"` to your name.

To use a real photo, put it beside your sketch and replace the stand-in with these lines:

```py
photo = f.load_image("me.jpg")               # found next to your sketch file
art = photo.copy()
art.resize(COLUMNS, ROWS)
art.load_pixels()
```

For a photo, use the red, green and blue of each cell, and the `brightness()` function above.

## Stage 2: make it yours

Here are some ways to make it more yours.

**Add sliders and tick boxes.** Make them once in `setup()` and read them when you paint. A
slider for the cell size is the most fun: big cells look like a poster and small cells look like a
photograph. Each cell size needs its own small copy of the picture, so keep the copies in a
dictionary and make each one only once.

```py
cell_slider = f.create_slider(8, 30, 14, step=1, label="cell size")
invert_box = f.create_checkbox("invert", False)
colour_box = f.create_checkbox("colour", True)
```

**Choose the letters.** Keep a list of pieces. Cell number n gets piece n, round and round, so
the word runs along each row. The pieces do not have to be letters of English. A piece of Devanagari
is a whole syllable, so split the word into syllables, not into single marks.

```py
LETTER_SETS = [
    ("funground", ["f", "u", "n", "g", "r", "o", "u", "n", "d"]),
    ("रंग", ["रं", "ग", " ", "भ", "रो"]),
]
piece = pieces[(row * columns + column) % len(pieces)]
```

A button changes the set. `clicked()` is true once for each click.

```py
if letters_button.clicked():
    which = (which + 1) % len(LETTER_SETS)
    dirty = True
```

**Invert.** In a normal portrait on a dark page, bright cells get big letters. On a light page it
looks better the other way round: dark cells get big letters, in dark ink. Invert flips the amount
and the two colours.

```py
if inverted:
    amount = 1 - amount
```

**Colour or mono.** In colour, each letter takes the colour of its cell. In mono there is one ink
colour, and only the size draws the picture. Try both. Mono is often the better print.

```py
if in_colour:
    f.fill(r, g, b)
else:
    f.fill(240, 236, 226)
```

**Save the files.** `f.save("portrait.pdf")` in an animated sketch writes the file at the end
of the frame. Paint the portrait on that same frame, so the file has everything. The letters are
real text, and a PDF or SVG is made of shapes, not pixels, so it stays sharp when printed large.
Chapter 13 says more about saving.

```py
def key_pressed():
    if f.key in ("p", "P"):
        jobs.append("portrait.pdf")

def draw():
    if jobs:
        paint()
        f.save(jobs.pop(0))
        return
```

A "note" about where the file went is a nice touch. Draw it on its own layer, and hide the layer
before you save, so the note is never in the file. The gallery example does this.

## Stage 3: make it shine

The full version is in the gallery: `examples/gallery/projects/05_typographic_portrait.py`. It loads
the picture that comes with the gallery, found with a path that starts at the sketch file. The
"cell size" slider runs from 8 to 30 pixels. The "change letters" button goes through three sets: the
word "funground", a Devanagari word, and the alphabet. "invert" swaps dark and light, and "colour"
switches between the photo's own colours and one ink. The "save PDF" and "save SVG" buttons, and the
P key, write `portrait.pdf` and `portrait.svg` with live text. A note on the canvas says where the
file went. Open the PDF in a viewer and zoom in as far as you like.

## Challenge cards

- **Can you** make the biggest letters bold and the smaller ones light?
- **Can you** use a picture of your own, and set the canvas to the same shape?
- **Can you** add a slider for how much bigger than the cell the biggest letter may be?
- **Can you** turn each letter a little, using the brightness for the angle?
- **Can you** draw the letters in two colours, one for light cells and one for dark cells?
- **Can you** make the word appear letter by letter, as if it were being typed?

**Back to:** [18. Projects](../18_projects.md). Useful chapters: [6. Text](../06_text.md),
[9. Paths, clipping and pictures](../09_paths_and_clipping.md), [4. Colour](../04_colour.md) and
[13. Saving your work](../13_saving_your_work.md).
