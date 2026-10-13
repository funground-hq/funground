# Project 1: Event poster series

Schools, clubs and festivals need posters. They need a lot of them, and they should all look like
a family. Computer code is good at that. You write one poster, and the code makes the rest. In this
project the poster is a small **designer**: you flip through the events, type a new headline, change the
colours and save the files.

## How it works

The full poster designer in the gallery has a few ideas at its core.

**The layers.** The poster is three layers: `background`, `art` and `words`. Each has its own
function. It wipes the layer with `f.clear()` and draws it again. A layer keeps its drawing, so a
set of "dirty" names says which layers have changed. Only those are drawn again. The tick boxes call
`f.hide_layer()` and `f.show_layer()`.

```py
def background_layer(event):
    top, bottom, accent, ink = theme_of(event)
    with f.layer("background"):
        f.clear()                                  # a layer keeps its drawing, so wipe it first
        f.fill(f.linear_gradient(0, 0, 0, HEIGHT, [top, bottom]))
        f.rect(0, 0, WIDTH, HEIGHT)

if "art" in dirty:                                 # in draw(): only what changed
    art_layer(event)
```

**The typed headline.** The title lives in the event's dictionary. `key_typed()` adds a letter to it
and `key_pressed()` takes one away on Backspace. Each change marks the `words` layer as dirty, so
the headline is drawn again. A `FormattedString` makes the first word white and the rest gold.

```py
def key_typed():
    event = EVENTS[index]
    if (f.key.isalnum() or f.key == " ") and len(event["title"]) < MAX_TITLE:
        event["title"] += f.key
        title_changed()                            # the words layer is drawn again
```

**The save buttons.** A poster in an animated sketch is one page. So "save PDF" puts one job per
event in a list, and `draw()` does one job on each frame: it draws that event, then calls
`f.save()`. The layers and the real text go into the file. The last button passes `text="shapes"`.

```py
jobs.append((index, "poster.svg", "live"))         # selectable text, for editing
jobs.append((index, "poster_final.svg", "shapes")) # every letter a shape, for handing over

number, name, mode = jobs.pop(0)                   # one job for each frame
f.save(name, text=mode)
```

## Stage 1: make it work

A list of events, one poster, and two buttons to flip through them. The background is a gradient.
The headline is text. The panel is a rounded rectangle. The buttons sit in a panel under the canvas.
The left and right arrow keys flip the events too.

```python
import funground as f

EVENTS = [
    {"title": "Book Fair", "date": "Sat 14 March, 10 am", "colour": (38, 70, 140)},
    {"title": "Music Night", "date": "Fri 21 March, 7 pm", "colour": (20, 90, 90)},
    {"title": "Spring Mela", "date": "Sun 30 March, 11 am", "colour": (170, 40, 90)},
]
index = 0


def setup():
    global previous, next_one
    f.size(480, 680)
    previous = f.create_button("previous")
    next_one = f.create_button("next")


def key_pressed():
    global index
    if f.key == "left":
        index = (index - 1) % len(EVENTS)
    if f.key == "right":
        index = (index + 1) % len(EVENTS)


def draw():
    global index
    if previous.clicked():                  # true once for each click
        index = (index - 1) % len(EVENTS)
    if next_one.clicked():
        index = (index + 1) % len(EVENTS)
    event = EVENTS[index]

    f.no_stroke()
    f.fill(f.linear_gradient(0, 0, 0, 680, [event["colour"], (120, 70, 170)]))
    f.rect(0, 0, 480, 680)
    f.fill(255, 196, 61)                    # a big yellow circle
    f.circle(240, 250, 300)
    f.fill(255, 255, 255, 235)              # a rounded panel for the details
    f.rect(36, 440, 408, 200, 34)
    f.fill(38, 40, 90)
    f.text_align("center", "top")
    f.text_size(24)
    f.text(event["date"], 240, 480)
    f.fill(255)
    f.text_size(54)
    f.text(event["title"], 240, 40)


f.run()
```

Run it and press the buttons. Each event is a dictionary, so a new event is one more line in the list.

## Stage 2: make it yours

Here are some ways to make it more yours.

**Type the headline.** `key_typed()` is called for each letter you type. Add it to the title.
Backspace arrives in `key_pressed()` as `"backspace"`. The edit goes into the event itself, so
anything you save later uses it.

```py
def key_typed():
    event = EVENTS[index]
    if f.key.isalnum() or f.key == " ":
        event["title"] += f.key


def key_pressed():
    if f.key == "backspace":
        EVENTS[index]["title"] = EVENTS[index]["title"][:-1]
```

**Add sliders.** A slider can turn the colours or change the size of the sun. Make it once in
`setup()` and read it in `draw()`. Keep each setting in the event, so every event can look different.

```py
hue = f.create_slider(-180, 180, 0, step=1, label="hue")
sun = f.create_slider(90, 190, 150, step=1, label="sun size")
```

**Use layers.** A layer is a see-through sheet. In a PDF or SVG it stays a layer, so a designer can
switch it on and off or change it. Put the background, the artwork and the words on their own layers.
A layer keeps what you drew on it, so you only draw it again when something it shows changes. That
keeps the poster quick. `f.hide_layer()` and `f.show_layer()` switch a layer on and off. Add a tick
box for each one, and you can see what each layer does.

```py
with f.layer("art"):
    f.clear()                               # wipe the layer, then draw it again
    f.circle(240, 250, 300)
f.hide_layer("art")                         # it keeps its drawing; it is just not shown
```

**Use mixed text.** A `FormattedString` can hold a bold word and an italic word in two colours.

```py
headline = f.FormattedString()
headline.append("Spring ", size=54, style="bold", color="white")
headline.append("Mela", size=54, style="bold_italic", color="gold")
f.text(headline, 240, 40)
```

**Use more scripts.** The text in a poster does not have to be English. Add a line in Hindi, and an
emoji. funground's fallback fonts draw them. A "Hindi line" tick box can switch the line on and off.

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

**Shuffle the art.** `f.random_seed(n)` makes the random numbers the same each time, for the same
`n`. Keep a seed in each event. A "shuffle art" button adds one to it and draws the confetti again.

```py
if shuffle.clicked():
    event["seed"] += 1
    f.random_seed(event["seed"])
    x, y = f.random(20, 460), f.random(20, 420)
```

**Save the files.** `f.save("poster.svg")` in an animated sketch writes the file at the end of the
frame, with the canvas and its layers as they are. A button can call it. The files keep the layers,
and the text stays real text, which you can select and search for.

A page belongs to a script, not to an animated sketch, so `f.new_page()` does not work here. To
save every event, draw one event on each frame and save a file for it: `events_1.pdf`,
`events_2.pdf` and so on. Keep a list of jobs, and do one job on each frame.

```py
jobs = [(0, "events_1.pdf"), (1, "events_2.pdf"), (2, "events_3.pdf")]

def draw():
    if jobs:
        number, name = jobs.pop(0)
        draw_poster(EVENTS[number])         # draw everything for this event
        f.save(name)                        # written at the end of this frame
        return
```

**Hand it over.** Save one copy for yourself and one copy to give away. The copy with
`text="shapes"` turns every letter into a shape, so it looks right on any computer, even one
without your fonts. See chapter 13 for the golden rule of handoffs.

```py
f.save("poster.svg")                        # live text, for editing
f.save("poster_final.svg", text="shapes")   # for handing over
```

If you would rather make a printed series in one go, a script can do it. A script can have many
pages. Loop over the events, call `f.new_page(480, 680)` for each, and `f.save("events.pdf")` writes
one PDF with every page.

## Stage 3: make it shine

The full version is in the gallery: `examples/gallery/projects/01_event_posters.py`. It is a poster
designer. The buttons and the arrow keys flip the events, and typing changes the headline, with a
blinking caret. Sliders turn the hue and change the size of the sun and the number of its rays. A
tick box shows or hides the Hindi line. A button shuffles the confetti. Three tick boxes show or
hide the background, the art and the words, so you can see the layers. The burst of shapes is made
with booleans. The headline has two styles, the details sit in a text box, and there is a Hindi line
and an emoji. Three buttons save the files: `events_1.pdf`, `events_2.pdf` and `events_3.pdf` (the
posters, with layers and real text), `poster.svg` (live text) and `poster_final.svg` (letters as
shapes). A note on the poster says where the files went. Run it, then open the files in a PDF
viewer or in Inkscape.

The designer saves files you can look at and share. To print the posters, go on to Stage 4.

## Stage 4: make it print-ready

You have posters on the screen and files to share. Now suppose the school wants them **printed**, on
big A3 sheets, by a print shop. A print shop cuts the paper after printing, so it needs a little extra
picture past the edge (a **bleed**) and lines that show where to cut (**crop marks**). Chapter 13 has
a section, [Preparing a file for print](../13_saving_your_work.md#preparing-a-file-for-print), that
explains both. This stage uses it.

A printed series is a good job for a **script**, because a script can have many pages. This one
draws every event on its own A3 page and saves one PDF.

```python
import os
import tempfile

import funground as f

EVENTS = [
    {"title": "BOOK FAIR", "date": "Sat 14 March, 10 am", "colour": (38, 70, 140)},
    {"title": "MUSIC NIGHT", "date": "Fri 21 March, 7 pm", "colour": (20, 90, 90)},
    {"title": "SPRING MELA", "date": "Sun 30 March, 11 am", "colour": (170, 40, 90)},
]
BLEED = f.mm(3)                         # the strip past the edge that the blade may cut into
MARGIN = f.mm(20)                       # keep words well inside the page

f.size("A3")                            # 842 x 1191 points: the finished page


def poster(event):
    w, h = f.width, f.height
    f.no_stroke()
    f.fill(f.linear_gradient(0, 0, 0, h, [event["colour"], (120, 70, 170)]))
    f.rect(-BLEED, -BLEED, w + 2 * BLEED, h + 2 * BLEED)     # runs into the bleed
    f.fill(255, 196, 61)
    f.circle(w / 2, h * 0.52, w * 0.85)

    f.fill(255)
    f.text_style("bold")
    f.text_align("left", "top")
    width = w - 2 * MARGIN
    f.text_size(f.fit_text_size(event["title"], width, 260))   # fills the width, up to 260 tall
    f.text(event["title"], MARGIN, MARGIN)

    f.text_style("normal")
    f.fill(255)
    f.text_align("center", "top")
    f.text_size(36)
    f.text(event["date"], w / 2, h - 2 * MARGIN)


for number, event in enumerate(EVENTS):
    if number:
        f.new_page()                    # the same size again
    poster(event)

folder = tempfile.mkdtemp()
f.save(os.path.join(folder, "events_print.pdf"), bleed=BLEED, marks=True)
print("one PDF with", f.page_count(), "pages in", folder)
f.show()
```

What is new:

- **A3 pages.** `f.size("A3")` is the finished size, the trim. `f.new_page()` starts the next
  poster at the same size.
- **Bleed.** The gradient and the sun are drawn from `-BLEED`, past the page's edge. That strip is
  not on the screen. In the PDF it is the extra picture the blade can cut into.
- **Crop marks.** `marks=True` adds them in the corners, outside the bleed.
- **A fitted headline.** `f.fit_text_size(title, width, 260)` makes each title fill the page's
  width, whether it is "BOOK FAIR" or "SPRING MELA". Short words stop at 260 points tall. See chapter 6.
- **Safe margins.** Keep words and logos inside `MARGIN`. The edge of a poster can be cut a little off.

**Optional: CMYK.** Ask the print shop whether they want CMYK. If so, change the colours in the
list to `f.cmyk()` colours, such as `f.cmyk(100, 80, 10, 10)` for a deep blue, and the sun to
`f.cmyk(0, 25, 90, 0)`. The PDF then holds exactly your inks. (Your screen shows the nearest match.) Black words
are best as `f.cmyk(0, 0, 0, 100)`. If they say RGB is fine, change nothing.

```py
EVENTS = [
    {"title": "BOOK FAIR", "date": "Sat 14 March, 10 am", "colour": f.cmyk(100, 80, 10, 10)},
    # ...
]
f.fill(f.cmyk(0, 25, 90, 0))        # the sun
```

A gradient between two `f.cmyk()` colours stays CMYK. A gradient that mixes one with an ordinary
colour is turned into inks by funground, so the file is all CMYK.

If the shop wants a picture and not a PDF, save a page as a PNG with `dpi=300`. A script with several
pages writes one file for each page, numbered after your file name: `events_1.png`, `events_2.png` and so on.

## Challenge cards

- **Can you** add a fourth event, with its own colours? You should only have to change the list.
- **Can you** let the date be edited as well as the title? Press Enter to switch between them.
- **Can you** add a slider for the size of the confetti?
- **Can you** add a layer called "notes" with a reminder for the person who prints the poster?
  Hide it so it is in the file but not on the page.
- **Can you** make the print version in A4 as well as A3? Only the size in `f.size()` should change.
- **Can you** save a landscape poster as well? A script can give `new_page` two different sizes.

## Credits and ideas

Event posters are an everyday kind of design, and this project has no single source or inspiration to credit. The code is written for funground (CC0). See [CREDITS.md](../../../CREDITS.md#ideas-the-examples-build-on).

**Back to:** [18. Projects](../18_projects.md)
