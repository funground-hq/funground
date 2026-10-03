# 18. Projects

You have learned the pieces. Now put them together. A project is a bigger piece of work that uses
many things at once. Each one here comes in three stages.

1. **Make it work.** A small version. It does one thing, and it runs.
2. **Make it yours.** Change it. Add the things you care about.
3. **Make it shine.** The full version in the examples gallery. Read it, run it, and borrow from it.

At the end of each project there are **challenge cards**. Each card is one short job to try on your own.
There is no right answer. If it looks good to you, it is done.

## Project 1: Event poster series

Schools, clubs and festivals need posters. They need a lot of them, and they should all look like
a family. Computer code is good at that. You write one poster, and the code makes the rest.

### Stage 1: make it work

One poster, one page. A script is enough, because nothing moves. The background is a gradient. The
headline is text. The panel is a rounded rectangle.

```python
import funground as f

f.size(480, 680)
f.no_stroke()

# the background: a gradient from top to bottom
f.fill(f.linear_gradient(0, 0, 0, 680, [(38, 70, 140), (120, 70, 170)]))
f.rect(0, 0, 480, 680)

# a big yellow circle
f.fill(255, 196, 61)
f.circle(240, 250, 300)

# a rounded panel for the details, then the words
f.fill(255, 255, 255, 235)
f.rect(36, 440, 408, 200, 34)
f.fill(38, 40, 90)
f.text_align("center", "top")
f.text_size(54)
f.text("Book Fair", 240, 40)
f.text_size(24)
f.text("Sat 14 March, 10 am", 240, 480)

f.save("poster.pdf")
f.show()
```

Run it and open `poster.pdf`. The text in it is real text. You can select it and search for it.

### Stage 2: make it yours

Now make a **list of events**. Each event is a dictionary: a title, a date and a place. A loop makes
one page for each. `f.new_page()` ends one page and starts the next.

```python
import funground as f

EVENTS = [
    {"title": "Book Fair", "date": "Sat 14 March", "colour": (38, 70, 140)},
    {"title": "Music Night", "date": "Fri 21 March", "colour": (20, 90, 90)},
    {"title": "Spring Mela", "date": "Sun 30 March", "colour": (170, 40, 90)},
]

for event in EVENTS:
    f.new_page(480, 680)
    f.no_stroke()
    f.background(event["colour"])
    f.fill(255)
    f.text_align("center", "center")
    f.text_size(54)
    f.text(event["title"], 240, 300)
    f.text_size(24)
    f.text(event["date"], 240, 370)

f.save("events.pdf")        # every page, in one PDF
f.save("events.svg")        # events_1.svg, events_2.svg, events_3.svg
f.show()
```

Here are some ways to make it more yours.

**Use layers.** A layer is a see-through sheet. In a PDF or SVG it stays a layer, so a designer can
switch it on and off or change it. Put the background, the artwork and the words on their own layers.

```py
with f.layer("background"):
    f.background(event["colour"])
with f.layer("art"):
    f.circle(240, 250, 300)
with f.layer("words"):
    f.text(event["title"], 240, 40)
```

**Use mixed text.** A `FormattedString` can hold a bold word and an italic word in two colours.

```py
headline = f.FormattedString()
headline.append("Spring ", size=54, style="bold", color="white")
headline.append("Mela", size=54, style="bold_italic", color="gold")
f.text(headline, 240, 40)
```

**Use more scripts.** The text in a poster does not have to be English. Add a line in Hindi, and an
emoji. funground's fallback fonts draw them.

```py
f.text("किताबें पढ़ो, सपने गढ़ो", 240, 600)
f.text("📚", 240, 250)
```

**Wrap the details.** `f.text_box(details, x, y, width, height)` wraps long text inside a box.

**Make shapes with booleans.** A path can be joined to another with `|`, cut with `-` and overlapped
with `&`. A circle with a smaller circle cut out of it is a ring or a crescent.

```py
crescent = f.path().circle(240, 250, 200) - f.path().circle(290, 215, 160)
f.draw_path(crescent)
```

**Hand it over.** Save one copy for yourself and one copy to give away. The copy with
`text="shapes"` turns every letter into a shape, so it looks right on any computer, even one
without your fonts. See chapter 13 for the golden rule of handoffs.

```py
f.save("events.svg")                        # live text, for editing
f.save("events_final.svg", text="shapes")   # for handing over
```

### Stage 3: make it shine

The full version is in the gallery: `examples/gallery/projects/01_event_posters.py`. It has a
burst of shapes made with booleans, three layers, a headline with two styles, a text box for the
details, a Hindi line and an emoji. It saves `events.pdf`, one live SVG for each page and one
SVG with shapes for each page. Run it, then open the files in a PDF viewer or in Inkscape.

### Challenge cards

- **Can you** add a fourth event, with its own colours? You should only have to change the list.
- **Can you** make a poster in portrait and one in landscape in the same PDF? Give `new_page`
  two different sizes.
- **Can you** put the event's date in a round badge in the corner of the poster?
- **Can you** add a hidden layer called "notes" with a reminder for the person who prints the poster?
- **Can you** make the artwork different for each event? Use a different number of points in the burst.

## Project 2: Rangoli and mandala generator

A rangoli is a pattern of colour on the floor, made for a festival. A mandala is a round pattern
that is the same all the way round. Both are good for code: you draw one part, and a loop turns it
again and again.

### Stage 1: make it work

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

### Stage 2: make it yours

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

### Stage 3: make it shine

The full version is in the gallery: `examples/gallery/projects/02_rangoli.py`. It has sliders for the
petals, the rings and the palette, a checkbox for the dots, a "new design" button and a "save"
button. The petals have holes cut by booleans. The centre is a rosette of joined circles. The
rings turn slowly, one way and then the other. The words at the bottom are made of dots. Press S
or click "save" to write `rangoli.svg` and `rangoli.pdf`.

### Challenge cards

- **Can you** make the petals pointed at one end and round at the other?
- **Can you** add a slider for how fast the rings turn?
- **Can you** add a fifth palette from the colours of a festival you love?
- **Can you** add a ring of dots between the petals?
- **Can you** save every new design as its own file, `rangoli_1.svg`, `rangoli_2.svg`, and so on?

## Project 3: Raga explorer

*Coming in this release.*

## Project 4: Voice-controlled game

*Coming in this release.*

**Previous:** [17. Ragas and talas](17_ragas_and_talas.md)
