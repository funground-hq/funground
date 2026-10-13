# Project 9: Generative posters

A dark page, a grid of glowing shapes, a big headline and a quiet line of small print. Posters like
this are everywhere: festivals, talks, album covers, exhibition walls. They look different from each
other, but most of them are built from the same few design ideas. In this project you build one,
step by step, on a real A3 page, and learn the ideas as you go. At the end, your code makes a whole
**series**: a family of posters that belong together, each one different.

The poster is a **script**: it draws once, from top to bottom, and `f.show()` at the end shows it.
There is no `draw()`, so there is nothing to start or stop: `f.no_loop()` and `f.loop()` are for
animated sketches.

## The ideas behind it

Shapes, grids and colours can all change. These principles stay the same.

**1. The format and the margin.** Start from a real page size. A3 is 297 by 420 mm, and funground
knows it: `f.size("A3")` gives a canvas of 842 by 1191 units, where one unit is one point (1/72 inch),
as in a PDF. `f.mm()` and `f.inch()` turn real measurements into units, so a 15 mm margin is
`margin=f.mm(15)`. The margin is empty space that frames the work. Generous margins look calm and
confident; tiny ones look cramped.

**2. The grid.** A grid divides the page into columns and rows with gaps (gutters) between them.
It gives every element a place, so things line up, and lining up is most of what makes a layout look
designed. A shape that sits in a cell, a headline that spans four columns, a footer on the last row:
all of them share edges, and the eye feels that order even when the grid lines are not drawn.

**3. Repetition with variation.** One rule, repeated, makes a pattern: "a circle in every cell". A
little chance makes it alive: "a circle in every cell, with a random size and a random colour from a
small range". Too much order is dull; too much chance is noise. The art is in the ranges you allow.
A **seed** makes the chance repeatable, so you can keep a poster you like.

**4. A limited palette.** A few colours that belong together look stronger than many. Two easy
families: **analogous** colours sit next to each other on the colour wheel (blue, violet, pink) and
feel harmonious; **complementary** colours sit opposite (blue and orange) and give energy. Choose
one background value (very dark or very light) and keep the shapes away from it, so they stand out.
Thinking in hue, saturation and brightness (`f.color_mode("hsb")`) makes this easy: the hue picks the
family, the other two control mood.

**5. Hierarchy.** A reader should know what to read first. Make the most important thing much
bigger (a ratio of 5 or more between the headline and the small print), heavier or brighter, and
give it space. Everything secondary gets smaller, lighter, quieter. Two or three levels are enough.

**6. Figure and ground, and space.** Every shape is also a hole in the background. Empty areas are
not wasted: they let the busy parts breathe and lead the eye. Leaving a row of the grid empty is a
design decision.

**7. Alignment and the edge.** Text usually aligns to one strong edge (flush left), and that edge is
a grid line. Images may run off the page (a **bleed**); text should stay inside the margin.

**8. Type.** Display type (headlines) wants tight leading (about 1.0 to 1.15 times the size),
capitals and bold weights. Small print wants normal leading (1.3 or more) and a calm weight. One
typeface in two weights is often enough.

## Stage 1: the page and the grid

An A3 page with a 15 mm margin, and a grid of 6 columns and 8 rows inside it. `grid.show()` draws
thin guide lines: you see them on the screen, but they are left out of saved files.

```python
import funground as f

f.size("A3", margin=f.mm(15))          # 842 x 1191 points, 15 mm kept free on every side
grid = f.grid(6, 8, gutter=f.mm(4))     # 6 columns, 8 rows, 4 mm between the cells

f.background("ivory")
grid.show()                             # guide lines: on screen only
f.fill("tomato")
f.no_stroke()
cell = grid.cell(2, 3)                  # column 2, row 3, counted from 0
f.rect(cell.left, cell.top, cell.width, cell.height)
f.show()
```

`f.ground.content` is the area inside the margins, and the grid covers it. Each cell knows its
`left`, `top`, `width`, `height` and its centre, `cx` and `cy`. Try `f.grid(4, 6)` or
`f.grid(12, 16)` and watch the cells change while the margin stays.

## Stage 2: a pattern in the grid

One rule for every cell: a circle at its centre. Then variation: a random size and a hue from a
narrow range. `f.random_seed(7)` makes the same poster every time; change the 7 for another.

```python
import funground as f

f.size("A3", margin=f.mm(15))
grid = f.grid(6, 8, gutter=f.mm(4))
f.random_seed(7)
f.color_mode("hsb")                     # hue 0-360, saturation and brightness 0-100, opacity 0-1

f.background(235, 60, 12)               # a very dark blue, not black
f.no_stroke()
f.blend_mode("screen")                  # overlaps get lighter, like overlapping lights
for cell in grid:
    hue = f.random(200, 330)            # blue to pink: an analogous palette
    f.fill(hue, 55, 85, 0.45)
    diameter = min(cell.width, cell.height) * f.random(0.6, 1.6)
    f.circle(cell.cx, cell.cy, diameter)
f.blend_mode("normal")
f.show()
```

The diameters go up to 1.6 times a cell, so neighbours overlap and glow where they meet. The circles
in the outer cells reach into the margin: the pattern may break the frame, the text will not.

## Stage 3: hierarchy and type

Now the poster gets a reading order. The pattern moves down to rows 2 to 6. The top two rows hold the
headline, one word per line, each word as big as it can be with `f.fit_text_size()`: no wider than
the grid and no taller than its share of the two rows. Long words are held by the width, short ones
by the height, so the block has a ragged right edge, a classic stacked headline. The last row holds
the small print, on the bottom margin and the same left edge.

```python
import funground as f

WORDS = ["MAKE", "SOMETHING", "GLOW"]
DETAILS = "Open studio night · Friday 24 October · 7 pm\nThe old print works, Canal Street"

f.size("A3", margin=f.mm(15))
grid = f.grid(6, 8, gutter=f.mm(4))
f.random_seed(7)
f.color_mode("hsb")
f.background(235, 60, 12)

# the pattern: rows 2 to 6 only
f.no_stroke()
f.blend_mode("screen")
for cell in grid:
    if 2 <= cell.row <= 6:
        f.fill(f.random(200, 330), 55, 85, 0.45)
        f.circle(cell.cx, cell.cy, min(cell.width, cell.height) * f.random(0.6, 1.6))
f.blend_mode("normal")

# the headline: rows 0 and 1, each word as big as the width and its share of the height allow
title = grid.span(0, 0, 6, 2)           # columns 0-5, rows 0-1, as one area
band = title.height / len(WORDS)        # the height each word may take
f.fill(0, 0, 100)
f.text_style("bold")
f.text_align("left", "baseline")
y = title.top
for word in WORDS:
    f.text_size(f.fit_text_size(word, title.width, band))
    y += f.text_ascent()
    f.text(word, title.left, y)
    y += f.text_descent() + f.mm(2)

# the small print: the last row, quieter and smaller, standing on the bottom margin
footer = grid.span(0, 7, 6, 1)
f.text_style("normal")
f.text_size(14)
f.text_leading(20)
f.text_align("left", "bottom")             # in a text box: the lines sit at the bottom of the box
f.fill(0, 0, 75)
f.text_box(DETAILS, footer.left, footer.top, footer.width, footer.height)
f.show()
```

Look at the levels: the headline is several times the size of the small print, white against light
grey, bold against normal. Everything starts at `title.left`, one grid line, so the page has a
strong left edge.

## Stage 4: a series

A poster series shares its rules and varies its chances. Put the poster in a function that takes
a seed and a hue, then draw four pages, one per event, into one PDF. Every page is the same design;
no two are the same picture.

```python
import funground as f

EVENTS = [("MAKE", "SOMETHING", "GLOW", 210), ("DRAW", "WITH", "CODE", 300),
          ("PRINT", "THE", "NIGHT", 20), ("SHAPE", "AND", "SOUND", 150)]


def poster(words, hue, seed):
    grid = f.grid(6, 8, gutter=f.mm(4))
    f.random_seed(seed)
    f.background(hue + 25, 60, 12)
    f.no_stroke()
    f.blend_mode("screen")
    for cell in grid:
        if 2 <= cell.row <= 6:
            f.fill(hue + f.random(-40, 60), 55, 85, 0.45)
            f.circle(cell.cx, cell.cy, min(cell.width, cell.height) * f.random(0.6, 1.6))
    f.blend_mode("normal")
    title = grid.span(0, 0, 6, 2)
    band = title.height / len(words)
    f.fill(0, 0, 100)
    f.text_style("bold")
    f.text_align("left", "baseline")
    y = title.top
    for word in words:
        f.text_size(f.fit_text_size(word, title.width, band))
        y += f.text_ascent()
        f.text(word, title.left, y)
        y += f.text_descent() + f.mm(2)


f.size("A3", margin=f.mm(15))
f.color_mode("hsb")
for number, (*words, hue) in enumerate(EVENTS):
    if number:
        f.new_page()                    # the same size and margin as the first page
    poster(words, hue % 360, seed=number + 1)
f.save("poster_series.pdf")             # four pages, text kept as real text
f.show()                                # the arrow keys turn the pages
```

The hues stay in range with `% 360`, so a family that starts near red can wrap round past 360. For
the print shop, `f.save("poster_series.pdf", bleed=f.mm(3), marks=True)` adds a bleed and crop marks
(see [13. Saving your work](../13_saving_your_work.md)).

## Challenge cards

Each card changes one thing. Do them one at a time and look at what changes, and what does not.

- **Can you** swap the circle for a square, a triangle or `f.ellipse()` with a random width and
  height? The page should still feel like the same family.
- **Can you** make a complementary palette: most shapes blue, one in ten orange? (Hint: compare
  `f.random(0, 1)` with 0.1.) Notice where your eye goes first.
- **Can you** change the grid to 3 by 4, then 12 by 16? Which feels calmer? Which is more like a
  texture than a pattern?
- **Can you** leave one cell empty on purpose, in an unexpected place? Empty space can be the focal
  point.
- **Can you** make the headline span only four columns and put a date in the other two? Keep both
  on grid lines.
- **Can you** turn it into a light poster: an ivory background, `"multiply"` instead of `"screen"`,
  and dark ink for the text?
- **Can you** use a font from Google Fonts? Download the family, put the `.ttf` next to your file and
  use `f.text_font(f.load_font("YourFont-Bold.ttf"))` before the headline.
- **Can you** make it A2 or Letter? Only `f.size()` should change: the grid, the margins and the
  fitted headline follow.
- **Can you** use `f.variations()` to see the same poster with 12 seeds side by side, and keep the
  best one? (See [18. Projects](../18_projects.md) and the Play section of the reference.)
- **Look at real posters.** Find three you like, and for each one write down its grid (how many
  columns?), its palette (how many colours, which family?) and its levels of hierarchy. Then rebuild
  one of them in funground with your own content.

## Credits and ideas

The ideas here are the common ground of graphic design teaching: the grid (Josef Müller-Brockmann's
*Grid Systems in Graphic Design* is the classic book), colour relationships on the colour wheel, and
generative series as in many design studios. The poster that started this project was a DrawBot
sketch, rewritten for funground. The code is written for funground (CC0). See
[CREDITS.md](../../../CREDITS.md#ideas-the-examples-build-on).

**Back to:** [18. Projects](../18_projects.md)
