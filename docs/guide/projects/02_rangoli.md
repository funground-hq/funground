# Project 2: Rangoli and mandala generator

A rangoli is a pattern of colour on the floor, made for a festival. A mandala is a round pattern
that is the same all the way round. Both are good for code: you draw one part, and a loop turns it
again and again.

## How it works

**The petal.** Two overlapping circles make a lens, and `&` keeps only the part they share. A
smaller lens is cut out with `-`, so each petal has a hole. The petal is built once for each ring,
and drawn many times.

```py
def lens(length, width):
    r = (length * length + width * width) / (4 * width)
    c = r - width / 2
    left = f.path().circle(-c, -length / 2, 2 * r)
    right = f.path().circle(c, -length / 2, 2 * r)
    return left & right

cut_petal = lens(length, width) - lens(length * 0.6, width * 0.5)   # a petal with a hole
```

**The symmetry.** A pattern that looks the same when it turns is one piece, drawn again and again.
Move to the middle of the canvas once. Then loop. Each time round, `f.push()` saves the place,
`f.rotate()` turns by one share of the circle, the petal is drawn, and `f.pop()` turns back.

```py
f.translate(CX, CY)                                # the middle of the pattern
for i in range(count):
    f.push()
    f.rotate(360 * i / count)                      # 360 divided by the number of petals
    f.translate(0, -base)                          # out from the middle
    f.draw_path(cut_petal)
    f.pop()
```

**The rings.** Several rings are drawn, the outer ones first, so the inner ones sit on top. Rings
next to each other turn in opposite directions (`direction = 1` or `-1`), and each turns at its own
speed. The turn comes from `f.frame_count`.

**One seed, one design.** `f.random_seed(seed)` comes before the random choices. The same seed always
gives the same design, and "new design" adds one to the seed.

## Stage 1: make it work

One petal, turned eight times. `f.rotate()` turns everything drawn after it. `f.push()` and
`f.pop()` put the turn back each time.

```python
import funground as f


def setup():
    f.size(480, 480)


def draw():
    f.background(40, 20, 60)
    f.no_stroke()
    f.translate(240, 240)
    for i in range(8):
        f.push()
        f.rotate(45 * i)
        f.fill(255, 150, 40)
        f.ellipse(0, -90, 50, 150)
        f.fill(255, 220, 90)
        f.circle(0, -170, 14)
        f.pop()
    f.fill(255, 80, 120)
    f.circle(0, 0, 50)


f.run()
```

## Stage 2: make it yours

**Add controls.** A slider can set the number of petals. Make it once in `setup()`. Ask it for its
value in `draw()`. The controls sit in a panel under the canvas.

```python
import funground as f


def setup():
    global petals, spin
    f.size(480, 480)
    f.color_mode("hsb", 360, 100, 100)
    petals = f.create_slider(4, 16, 8, step=1, label="petals")
    spin = f.create_checkbox("spin")


def draw():
    f.background(285, 70, 22)
    f.no_stroke()
    f.translate(240, 240)
    if spin.checked():
        f.rotate(f.frame_count * 0.5)
    count = petals.value()
    for i in range(count):
        f.push()
        f.rotate(360 * i / count)
        f.fill(38 + i * 6, 90, 100)              # hue, saturation, brightness
        f.ellipse(0, -90, 50, 150)
        f.pop()


f.run()
```

In `"hsb"` colour mode a colour is a hue (the colour itself, 0 to 360), how strong it is, and how
bright it is. It is easy to make a family of colours that go well together: keep the strength and
brightness, and move the hue a little.

**Cut a shape out of a shape.** Two circles that overlap make a petal. `&` keeps only the part they
share. `-` cuts one away. These are path booleans.

```py
def lens(length, width):
    """A petal pointing up. Its base is at (0, 0) and its tip at (0, -length)."""
    r = (length * length + width * width) / (4 * width)
    c = r - width / 2
    return f.path().circle(-c, -length / 2, 2 * r) & f.path().circle(c, -length / 2, 2 * r)

petal = lens(150, 60)
hole = lens(90, 30).translate(0, -20)
f.draw_path(petal - hole)                      # a petal with a hole in it
```

**Pick festival colours.** Keep a list of palettes. Each is a background and some colours. A
slider picks which one to use. Diwali is gold, orange and magenta on deep purple. Holi is bright
colours on cream. Make your own.

**Make a new design.** `f.random_seed(n)` makes the random numbers the same each time, for the same
`n`. A "new design" button can add one to `n` and pick fresh shapes. Every number always gives the
same design, so you can find one you like again.

```py
if new_design.clicked():
    seed += 1
    f.random_seed(seed)
    fatness = f.random(0.4, 0.7)
```

**Draw with dots.** `f.text_to_points("Shubh", x, y, 5)` gives a list of points along the outline of
the letters, one every five pixels. Draw a small circle at each one and the letters are made of dots.

**Save it.** `f.save("rangoli.svg")` and `f.save("rangoli.pdf")` write the pattern as shapes. An SVG
or a PDF can be printed as big as you like, or sent to a laser cutter. Call it from a button or a key.

```py
def key_pressed():
    if f.key == "s":
        f.save("rangoli.svg")
```

## Stage 3: make it shine

The full version is in the gallery: `examples/gallery/projects/02_rangoli.py`. It has sliders for the
petals, the rings and the palette, a checkbox for the dots, a "new design" button and a "save"
button. The petals have holes cut by booleans. The centre is a rosette of joined circles. The
rings turn slowly, one way and then the other. The words at the bottom are made of dots. Press S
or click "save" to write `rangoli.svg` and `rangoli.pdf`.

## Challenge cards

- **Can you** make the petals pointed at one end and round at the other?
- **Can you** add a slider for how fast the rings turn?
- **Can you** add a fifth palette from the colours of a festival you love?
- **Can you** add a ring of dots between the petals?
- **Can you** save every new design as its own file, `rangoli_1.svg`, `rangoli_2.svg`, and so on?

**Back to:** [18. Projects](../18_projects.md)
