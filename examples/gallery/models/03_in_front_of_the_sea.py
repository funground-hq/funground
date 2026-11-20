"""In front of the sea

A person is cut out of a photograph and put in front of a sunset sea that the sketch draws itself. The computer finds the
person, and everything else in the photograph becomes see-through. It uses your own photo when you give it one, and a woman on
a catwalk until then. It needs the models library, which is a separate install: funground-ml.

How it works:
- The sketch tries my_photo.jpg, my_photo.png, my_photo.jpeg and my_photo.svg in turn. When there is none, it opens the catwalk
  photograph instead. An SVG is read with f.load_svg(), so only its shapes count: a photo saved inside an SVG is left out.
- The canvas is always HEIGHT tall. A photo of another size is drawn scaled, f.image(cutout, 0, 0, WIDTH, HEIGHT), so a big
  phone photo fits too.
- ml.person(photo) gives a new picture the size of the photo. Only the person is left in it. The rest is see-through. The
  edge is soft: a pixel on the edge is a little see-through, so the cut-out blends into what is behind it.
- The sky is a stack of thin bands. Each band is a step of f.lerp_color() between two colours. The sea is built the same way,
  with wavy lines drawn on it by f.begin_shape(), f.vertex() and a sine wave.
- draw() asks for the cut-out until it has one, then keeps it (in Play the answer comes a few frames later, while the model
  starts). The background is drawn first, and the person last, so they stand in front.
- With a camera, ml.person(cam) works the same way. Use f.image(ml.person(cam), 0, 0) to put yourself in front of the sea.

Make it yours:
- Use your own photo. In Play: open My files, press Add file and choose a photo of one whole person, then press Rename beside it
  and call it my_photo (the ending stays). On your computer: put the photo beside this sketch and call it my_photo.jpg or
  my_photo.png. Run the sketch again.
- Change the four colours at the top for a morning, or a night.
- Move HORIZON to put the sea higher or lower behind the person.
- Add stars to the sky with f.circle() and f.random_seed().
- Draw the person twice: first with f.opacity(80) and a shift in x, then normally, for a shadow.
"""
import math

import funground as f
from funground import ml

photo = None
for name in ["my_photo.jpg", "my_photo.png", "my_photo.jpeg", "my_photo.svg"]:
    try:
        photo = f.load_svg(name) if name.endswith(".svg") else f.load_image(name)
        break                      # found one: stop looking
    except FileNotFoundError:
        pass                       # not this one: try the next name
if photo is None:
    print("No my_photo yet, so this is the catwalk photograph. Add your own photo and call it my_photo.jpg or my_photo.png.")
    photo = f.load_image("data/standing_woman_640.jpg")

HEIGHT = 960                                  # the canvas is this tall; the photo is scaled to fit it
WIDTH = round(photo.width * HEIGHT / photo.height)
HORIZON = 600
TOP, LOW_SKY = "#2d3a8c", "#ff9a5a"          # the sky: high up, and at the horizon
NEAR, FAR = "#0a2a4a", "#2f7f9f"             # the sea: close to us, and at the horizon
BANDS = 48                                    # how many thin bands each of them is made of


def sky():
    height = HORIZON / BANDS
    for i in range(BANDS):
        f.fill(f.lerp_color(TOP, LOW_SKY, (i / (BANDS - 1)) ** 1.6))
        f.rect(0, i * height, WIDTH, height + 1)


def sun():
    for i in range(12):
        f.fill(255, 240, 200, 26)
        f.circle(WIDTH * 0.72, HORIZON - 40, 260 - i * 20)


def sea():
    depth = HEIGHT - HORIZON
    height = depth / BANDS
    for i in range(BANDS):
        f.fill(f.lerp_color(FAR, NEAR, i / (BANDS - 1)))
        f.rect(0, HORIZON + i * height, WIDTH, height + 1)
    f.no_fill()
    f.stroke_width(2)
    for row in range(14):
        y = HORIZON + 14 + row * row * 2.2
        f.stroke(255, 220, 170, 150 - row * 8)
        f.begin_shape()
        for x in range(0, WIDTH + 20, 20):
            f.vertex(x, y + math.sin(x * 0.03 + row) * (2 + row * 0.5))
        f.end_shape()
    f.no_stroke()


cutout = None                                 # the person alone, once the model has found them


def setup():
    f.size(WIDTH, HEIGHT)


def draw():
    global cutout
    if cutout is None:
        cutout = ml.person(photo)
    f.no_stroke()
    sky()
    sun()
    sea()
    if cutout is not None:
        f.image(cutout, 0, 0, WIDTH, HEIGHT)


f.run()
