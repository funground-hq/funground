# 9. Paths and clipping

## Shapes from points

List the corners between `f.begin_shape()` and `f.end_shape()`:

```python
import math

import funground as f


def setup():
    f.size(640, 400)


def draw():
    f.background("white")
    f.fill("gold")
    f.stroke("darkorange")
    f.stroke_width(4)
    f.begin_shape()
    for i in range(10):
        r = 140 if i % 2 == 0 else 60
        a = math.pi * i / 5 - math.pi / 2
        f.vertex(200 + r * math.cos(a), 200 + r * math.sin(a))
    f.end_shape(close=True)


f.run()
```

![A star from vertices](../gallery/images/paths-01_star.png)

`end_shape(close=True)` joins the last point to the first and fills the shape.
`end_shape()` leaves it **open**: open shapes are only stroked, never filled.

## Reusable paths

`f.path()` builds a shape once so you can draw it many times:

```py
leaf = f.path().move_to(0, -40).line_to(24, 0).line_to(0, 40).line_to(-24, 0).close()
f.draw_path(leaf)
```

`move_to`, `line_to`, `curve_to` and `quad_to` add to the path; `close()` closes it.
`f.draw_path(path)` fills (if closed) and strokes it with the current style, and transforms
apply to it like to any shape.

## Clipping

`f.clip(path)` keeps everything drawn afterwards **inside** the path. It lasts until the end of
the `saved_state` block (or the matching `pop()`), so always clip inside one:

```py
with f.saved_state():
    f.clip(window)
    ...                       # drawn only inside window
```

![Paths and clipping](../gallery/images/paths-02_path_and_clip.png)

`f.no_clip()` switches clipping off until the end of its own `saved_state` block; when that block
ends, the clip from outside it comes back.

![Clipping on and off](../gallery/images/paths-03_no_clip.png)

## Curves

Inside a shape, three kinds of curve follow Processing's names:

| Function | What it does |
|---|---|
| `f.bezier_vertex(cx1, cy1, cx2, cy2, x, y)` | A curve from the previous point to `(x, y)` that bends toward two control points |
| `f.quadratic_vertex(cx, cy, x, y)` | The same with one control point |
| `f.curve_vertex(x, y)` | A smooth curve **through** the points. The first and last points only steer the curve, so give at least four |
| `f.curve_tightness(t)` | 0 (default) for smooth curves, up to 1 for straight lines |

For a single curve there are `f.bezier(x1, y1, cx1, cy1, cx2, cy2, x2, y2)` and
`f.curve(x1, y1, x2, y2, x3, y3, x4, y4)` (from point 2 to point 3). They are open, so they
are drawn as lines, never filled. `f.bezier_point(a, b, c, d, t)` gives one coordinate of a point
along the curve for `t` from 0 to 1 — call it once for x and once for y.

![Curves](../gallery/images/curves-01_curves.png)

## Holes

List a hole's corners between `f.begin_contour()` and `f.end_contour()`, inside the shape:

```python
import funground as f


def setup():
    f.size(320, 320)


def draw():
    f.background("white")
    f.fill("gold")
    f.begin_shape()
    for x, y in [(40, 40), (280, 40), (280, 280), (40, 280)]:
        f.vertex(x, y)
    f.begin_contour()
    for x, y in [(100, 100), (220, 100), (220, 220), (100, 220)]:
        f.vertex(x, y)
    f.end_contour()
    f.end_shape(close=True)


f.run()
```

funground cuts the hole out whichever way round you list its corners.

![Holes](../gallery/images/paths-04_holes.png)

## Drawing off-screen

`f.create_graphics(width, height)` makes a **picture**: a canvas of its own, the same size
as you ask for, that starts transparent. It has the same drawing commands as `f.` - fill,
circle, text, push/pop, transforms, clip, everything above - but its own state, its own
transform, and its own pixels, completely separate from the window. Unlike the window,
**nothing about a picture resets between frames**: whatever you drew last time is still
there, so you can build it up gradually.

`f.image(picture, x, y, width=None, height=None)` draws a picture into the window (or into
another picture), at (x, y), stretched to `width` x `height` if you give them (its own size
otherwise). It draws the picture **as it is at that moment** - drawing on the picture
afterwards never changes what was already placed.

A common trick, borrowed from Processing's `PGraphics`: paint a translucent rectangle over
a picture every frame, instead of clearing it, so older drawing fades instead of vanishing:

```python
import math

import funground as f

trail = None


def setup():
    global trail
    f.size(640, 400)
    trail = f.create_graphics(400, 400)


def draw():
    f.background("black")

    trail.no_stroke()
    trail.fill((0, 0, 0, 24))          # translucent: painted over the old trail, it fades
    trail.rect(0, 0, trail.width, trail.height)

    angle = f.radians(f.frame_count * 6)
    x = trail.width / 2 + math.cos(angle) * 150
    y = trail.height / 2 + math.sin(angle) * 150
    trail.fill("gold")
    trail.circle(x, y, 24)

    f.image(trail, 0, 0)                    # full size
    f.image(trail, 480, 20, 140, 140)       # a second, smaller copy: image() can scale


f.run()
```

![Drawing off-screen](../gallery/images/compositing-02_graphics.png)

| Call | What it does |
|---|---|
| `f.create_graphics(w, h)` | A new picture, `w` x `h`, transparent to start. It has the same drawing commands as `f.` |
| `f.image(picture, x, y, w=None, h=None)` | Draw *picture* at (x, y), stretched to `w` x `h` (default: its own size) |

A picture can hold another picture too, but never itself: `f.image(g, ...)` where `g` is
drawing onto itself raises `ValueError`. Save a picture on its own with `g.save(path)`,
exactly like `f.save(path)` for the window.

## Pictures and images

A picture does not have to be drawn by you. `f.load_image(path)` reads an image file and
gives you a picture. It reads PNG, JPEG, GIF, BMP and TGA files. Transparency is kept. A GIF
gives you its first frame.

```py
photo = f.load_image("holiday.jpg")
f.image(photo, 0, 0)
```

**Where files are looked for.** A path like `"holiday.jpg"` is looked for in the folder of
your sketch file first. Then it is looked for in the folder you ran Python from. If it is in
neither place, funground tells you both places it looked.

**Phone photos.** Phones often save a photo sideways and add a note saying "turn this".
funground reads that note for JPEG files and turns the photo the right way up for you.

**Size.** `photo.width` and `photo.height` are the size of the file in pixels. Drawn with
`f.image(photo, x, y)`, the photo covers that many pixels of your canvas. Give a width and a
height to stretch it: `f.image(photo, x, y, 200, 150)`. It follows `f.translate()`,
`f.rotate()`, `f.clip()` and `f.opacity()` like everything else.

**Drawing on it.** A loaded picture is a picture like any other, so `photo.fill("red")` and
`photo.circle(50, 50, 20)` draw on it. The file on your disk never changes.

This sketch makes a small image file first, so that it runs anywhere, and then loads it:

```python
import funground as f

f.size(400, 200)

# Make an image file to load. You would normally bring your own.
stamp = f.create_graphics(60, 60)
stamp.background("gold")
stamp.fill("crimson")
stamp.circle(30, 30, 40)
stamp.save("stamp.png")

loaded = f.load_image("stamp.png")      # found next to this file, or in the current folder


def draw():
    f.background("white")
    f.image(loaded, 20, 20)                     # its own size
    f.image(loaded, 120, 20, 160, 160)          # stretched
    f.opacity(128)
    f.image(loaded, 300, 60)                    # half see-through


f.run()
```

![Loading an image](../gallery/images/images-01_load_image.png)

PDF and SVG files keep a loaded picture as pixels, because that is all it has. If you
paint an opaque `photo.background(...)` on it first, it becomes a normal drawing again.
SVG files cannot be loaded as images yet; funground tells you so.

| Call | What it does |
|---|---|
| `f.load_image(path)` | Read an image file and return a picture. |
| `photo.width`, `photo.height` | The image's size in pixels. |

### Tinting a picture

`f.tint(color)` colours every picture you draw with `f.image()` from then on. It takes a
colour in any form that `f.fill()` takes: a name, a hex string, numbers, a grey, and so on,
and it follows `f.color_mode()`. Each pixel's red, green and blue are **multiplied** by the
tint's. White changes nothing. A red tint turns a white picture red. The tint's alpha is
multiplied in too, so `f.tint(255, 128)` draws a picture half see-through. Parts of the
picture that were already see-through stay see-through.

`f.no_tint()` stops it. A tint only changes pictures. Shapes and text are not tinted. It
combines with `f.opacity()` and `f.blend_mode()`. Like `f.fill()`, it is kept by `f.push()`
and `f.pop()`, and it stays set from one frame to the next.

### Drawing part of a picture

Give `f.image()` four more numbers, `sx, sy, sw, sh`, and it draws only that part of the
picture: the rectangle that starts at (`sx`, `sy`) and is `sw` wide and `sh` high, in the
picture's own pixels. The part fills the box given by `x, y, width, height`. Without a
width and a height, the box is as big as the part.

```
f.image(picture, x, y, width, height, sx, sy, sw, sh)
```

You must give all four of `sx, sy, sw, sh` or none of them, and `sw` and `sh` must be above
0. If the part reaches outside the picture, only the inside is drawn, and it stays exactly
where it would have been. `f.image_mode()`, transforms, clips, tint and opacity all work
with parts. A picture made with `f.create_graphics()` can do it too: `g.image(...)`.

This sketch makes its own picture, then shows it tinted and in parts:

```python
import funground as f

f.size(400, 200)

art = f.create_graphics(40, 40)           # a small picture to play with
art.background("white")
art.no_stroke()
art.fill("crimson")
art.circle(20, 20, 24)
art.fill("navy")
art.rect(0, 30, 40, 10)



def draw():
    f.background("ivory")
    f.image(art, 10, 10, 80, 80)               # as it is
    f.tint("gold")                             # a gold tint
    f.image(art, 110, 10, 80, 80)
    f.tint(255, 100)                           # white, but almost see-through
    f.image(art, 210, 10, 80, 80)
    f.no_tint()

    f.image(art, 10, 110, 80, 80, 10, 10, 20, 20)    # a part: the middle, bigger
    f.image(art, 110, 110, 80, 40, 0, 30, 40, 10)    # a part: the navy stripe, stretched
    f.image(art, 210, 110, 80, 80, 20, 0, 60, 40)    # a part that reaches outside: clipped


f.run()
```

![Tinting a picture and drawing part of it](../gallery/images/images-02_tint_and_parts.png)

| Call | What it does |
|---|---|
| `f.tint(color)` | Multiply the colour (and alpha) of pictures drawn after it. |
| `f.no_tint()` | Stop tinting. |
| `f.image(picture, x, y, width, height, sx, sy, sw, sh)` | Draw only the part `sx, sy, sw, sh` of the picture. |

### Pixels

`f.get(x, y)` tells you the colour of one pixel. It gives back a colour object, the same kind
that `f.color()` makes, so you can use `.red`, `.green`, `.blue` and `.alpha`, or hand it to
`f.fill()`. It sees everything drawn so far, this frame included. Outside the canvas the answer
is transparent black. `x` and `y` are rounded down to whole pixels.

`f.get(x, y, w, h)` copies a whole rectangle into a **new picture**. Parts of the rectangle
outside the canvas are see-through.

`f.set(x, y, color)` makes one pixel exactly that colour. It takes any colour form that
`f.fill()` takes. It ignores the fill, the stroke, the transform, the clip, the tint, the
opacity and the blend mode: what you set is what you get. Outside the canvas it does nothing.
A picture has `g.get()` and `g.set()` too.

On a high-resolution screen, a pixel here is a **logical** pixel, as everywhere in funground.
It may cover several real pixels. `get` reads the top-left real one, and `set` paints all of
them.

To change many pixels, use the list `f.pixels`:

1. `f.load_pixels()` copies the canvas into `f.pixels`. Before that, `f.pixels` is `None`.
2. `f.pixels` is a `bytearray`. Each pixel takes four numbers, from 0 to 255: red, green, blue
   and alpha. They are not premultiplied. The pixels come row by row, from the top left. The
   pixel at (`x`, `y`) starts at index `(y * f.width + x) * 4`.
3. Change the numbers. Nothing on the canvas changes yet.
4. `f.update_pixels()` writes the whole list back. It is the same as calling `f.set()` for
   every pixel. Calling it before `f.load_pixels()` is an error.

Change the numbers in place (`f.pixels[i] = 0`). Do not replace the list with a new one. On a
picture it works the same way: `g.load_pixels()`, `g.pixels`, `g.update_pixels()`.

**Loops over every pixel are slow.** A Python loop that visits each pixel of a 640 by 400
canvas has 256 000 pixels to do, and takes a second or more. Loading and updating the pixels
without a loop is fast (a few hundredths of a second). So keep your loops to small areas, as
the example below does, or work on a small picture.

Pixel writes are raster. A saved PDF or SVG holds them as an image, not as vectors. A picture
that has had pixel writes loses its drawing history, so when it is drawn onto a PDF it is
embedded as an image too.

```python
import funground as f


def setup():
    f.size(400, 200)
    f.no_loop()


def draw():
    f.background("ivory")

    # A small picture, made one pixel at a time.
    tile = f.create_graphics(10, 10)
    for y in range(10):
        for x in range(10):
            tile.set(x, y, (x * 25, y * 25, 150))
    f.image(tile, 10, 10, 100, 100)

    # An eyedropper: read the colour at one point of the canvas.
    f.no_stroke()
    f.fill("tomato")
    f.circle(200, 60, 80)
    picked = f.get(200, 60)
    f.fill(picked)
    f.rect(160, 120, 80, 50)

    # A copy of part of the canvas, with red and blue swapped.
    part = f.get(160, 20, 80, 80)
    part.load_pixels()
    pixels = part.pixels
    for i in range(0, len(pixels), 4):
        pixels[i], pixels[i + 2] = pixels[i + 2], pixels[i]
    part.update_pixels()
    f.image(part, 300, 10)


f.run()
```

![Reading and writing single pixels](../gallery/images/images-03_pixels.png)

| Call | What it does |
|---|---|
| `f.get(x, y)` | The colour at one pixel (a colour object). |
| `f.get(x, y, w, h)` | A new picture copied from a rectangle of the canvas. |
| `f.set(x, y, color)` | Make one pixel exactly that colour. |
| `f.load_pixels()` | Copy the canvas into `f.pixels`. |
| `f.pixels` | Red, green, blue, alpha for every pixel, in a `bytearray`. |
| `f.update_pixels()` | Write `f.pixels` back onto the canvas. |

**Next:** [10. Interaction](10_interaction.md)
