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
a family. Computer code is good at that. You write one poster, and the code makes the rest. In this
project the poster is a small **designer**: you flip through the events, type a new headline, change the
colours and save the files.

### Stage 1: make it work

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

### Stage 2: make it yours

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
f.layer("art").clear()                      # wipe the layer, then draw it again
with f.layer("art"):
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

### Stage 3: make it shine

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

### Challenge cards

- **Can you** add a fourth event, with its own colours? You should only have to change the list.
- **Can you** let the date be edited as well as the title? Press Enter to switch between them.
- **Can you** add a slider for the size of the confetti?
- **Can you** add a layer called "notes" with a reminder for the person who prints the poster?
  Hide it so it is in the file but not on the page.
- **Can you** save a landscape poster as well? A script can give `new_page` two different sizes.

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

This project is for music learners, and it is only possible in funground. You pick a raga. You hear
its way up and its way down over a drone, and you watch each swara light up. Then you sing it, and
the page shows which swaras you sang.

Read [chapter 17](17_ragas_and_talas.md) first if you have not. A raga is more than its notes. This
project works with the notes, and it says so on the screen.

### Stage 1: make it work

Hear one raga. `f.raga("Bhupali")` gives its facts. Its aroha and avaroha are sargam strings, so
they go straight into `f.melody`. A ladder of the twelve swaras lights the one that is sounding.
Rows the raga does not use stay dark.

```python
import funground as f

SA = "D4"
TEMPO = 80
SWARAS = "SrRgGmMPdDnN"
raga = f.raga("Bhupali")
steps = (raga.aroha + " - " + raga.avaroha).split()      # "-" is a rest
tune = f.melody(" ".join(steps), tempo=TEMPO, sa=SA, tuning="just")
drone = f.drone("D3", 8, volume=0.4)


def setup():
    f.size(420, 370)
    f.text_size(16)
    f.text_align("left", "center")
    tune.loop()
    drone.loop()


def draw():
    f.background("#1b1424")
    step = min(int(tune.current_time() / (60 / TEMPO)), len(steps) - 1)
    sounding = steps[step].rstrip("',")            # S' and N, are S and N on the ladder
    f.no_stroke()
    for i, swara in enumerate(SWARAS):
        y = 330 - i * 28
        if swara == sounding:
            f.fill("gold")
        elif swara in raga.swaras:
            f.fill("#7a4fa0")
        else:
            f.fill("#2c2236")
        f.rect(20, y - 12, 380, 24, 6)
        f.fill("black" if swara == sounding else "white")
        f.text(swara, 30, y)


f.run()
```

The drone is quieter than the tune, as a tanpura is under a singer. Change `"Bhupali"` to
another name from `f.ragas()` and listen to how it changes.

### Stage 2: make it yours

**Choose the raga.** Make a slider over the list of names. Make it in `setup()`. When its value
changes, make the tune again.

```py
NAMES = f.ragas()
picker = f.create_slider(0, len(NAMES) - 1, 0, step=1, label="raga")

if NAMES[picker.value()] != raga.name:
    raga = f.raga(NAMES[picker.value()])         # then make the tune and the drone again
```

**Show the facts.** The raga has `thaat`, `vadi`, `samvadi` and `time`. Draw them as text, and
draw a ring round the vadi row and the samvadi row on the ladder.

**Add a glide.** In Indian music the voice slides between notes. `S~G` in a melody is a meend, a
glide from S to G. Glide into the last note of the avaroha:

```py
down = raga.avaroha.split()
ending = down[-2] + "~" + down[-1] + ":2"      # for example R~S:2, a glide over two beats
tune = f.melody(" ".join(down[:-2] + [ending]), tempo=80, sa=SA, tuning="just")
```

**Give it a room.** `.reverb(0.3)` on the tune and `.reverb(0.4)` on the drone make them sound
warmer. A drone with reverb rings on after its end, and it would stop with a gap when it loops.
Fold the ringing back onto the start. The gallery example has a small function, `room()`, that does it.

**Sing it back.** Now add the microphone. It gives `mic.pitch()`, the pitch of the note you sing.
Turn it into a row on the ladder: how many semitones above Sa, folded into one octave. Then you
can sing in any octave that suits you.

A raw pitch line jumps about. Three small steps make it calm. They are the same ones as in the
gallery example "A sargam phrase over a drone".

1. **Gate.** Ignore the microphone when `mic.level()` is low. That is breath and room noise.
2. **Fold.** Keep the pitch in one octave, so a slip to the next octave lands on the right row.
3. **Smooth.** Take the middle one of the last five readings. Break the line when the voice jumps.

```python
import math

import funground as f

SA = "D4"
SA_HZ = f.note_to_frequency(SA)
SWARAS = "SrRgGmMPdDnN"
raga = f.raga("Bhupali")
mic = f.microphone()
drone = f.drone("D3", 8, volume=0.4)
trail = []                                       # the pitch line, in rows above Sa
recent = []


def next_point():
    """A row above Sa (0 is S, 11 is N), or None when there is nothing to draw."""
    hz = mic.pitch() if mic.level() > 0.001 else None       # gate
    if hz is None:
        del recent[:]
        return None
    here = (12 * math.log2(hz / SA_HZ) + 0.5) % 12 - 0.5    # fold into one octave
    if recent and abs(here - sorted(recent)[len(recent) // 2]) > 2:
        recent[:] = [here]                       # a jump: break the line
        return None
    recent.append(here)
    del recent[:-5]
    return sorted(recent)[len(recent) // 2]      # smooth: the middle of the last five


def setup():
    f.size(420, 370)
    f.text_size(16)
    f.text_align("left", "center")
    drone.loop()
    mic.start()


def draw():
    trail.append(next_point())
    del trail[:-90]
    f.background("#1b1424")
    f.no_stroke()
    for i, swara in enumerate(SWARAS):
        y = 330 - i * 28
        f.fill("#7a4fa0" if swara in raga.swaras else "#2c2236")
        f.rect(20, y - 12, 380, 24, 6)
        f.fill("white")
        f.text(swara, 30, y)
    f.stroke("hotpink")
    f.stroke_width(3)
    last = None
    for k, row in enumerate(trail):
        point = None if row is None else (60 + k * 4, 330 - row * 28)
        if point and last:
            f.line(*last, *point)
        last = point


f.run()
```

Wear headphones, so the drone does not get into the microphone. Sing with Sa on D. If the line
does not move, lower `0.001` in the gate. If it jumps about in a noisy room, raise it, to `0.005`
for example. (`0.001` is very quiet. Laptop microphones are.)

**Count what you sang.** `mic.capture(seconds)` gives a sound of the last few seconds you sang.
Count the swaras in it, and let `f.match_ragas` say which ragas use those notes.

```py
heard = mic.capture(10)                          # the last 10 seconds, as a sound
shares = heard.swara_histogram(SA)               # 12 numbers: how long each swara sounded
if sum(shares) > 0:                              # all zeros means nothing was heard
    for name, score in f.match_ragas(shares)[:3]:
        print(name, round(score, 2))
```

The first call takes a second or two, so call it once, when the singer presses "stop". Do not call
it in every frame. Draw the 12 shares as bars and the three scores as longer bars.

Be honest in what you write on screen. `match_ragas` compares notes. Bhupali and Deshkar use the
same five swaras, so it cannot tell them apart. What makes a raga is how it moves, and the
program does not hear that. Say so on the page.

### Stage 3: make it shine

The full version is in the gallery: `examples/gallery/projects/03_raga_explorer.py`. It has the
slider, the facts, the drone with reverb that loops without a gap, the tune with a meend into Sa,
the ladder that lights, and a "sing" mode with the calm pitch line. A row turns red when you sing a
swara the raga does not use. After "stop" it draws your swaras as bars and the three closest ragas
as longer bars, with a note that it compares notes only. Marwa has no Pa, so its drone has Ni on
the first string. The sounds are made the first time you press "listen", so that press takes a
moment.

### Challenge cards

- **Can you** change `SA` so the whole page suits your own voice? Use `"C#4"` or `"A3"`.
- **Can you** add a tala? Play `f.tala("Teentaal", tempo=80)` under the tune, and light the beat.
- **Can you** play the raga's `pakad` as well as the aroha and avaroha?
- **Can you** show the time of day as a sun or a moon, drawn with shapes?
- **Can you** keep the best match from each singing in a list, and show the last five?

## Project 4: Voice-controlled game

A bird flies through gates. Your voice is the control. This project uses the microphone,
collisions, a score and some sound effects. It works with the space bar too, so it also runs on a
computer with no microphone, and in a room too quiet for shouting.

### Stage 1: make it work

The bird. `mic.level()` is how loud the sound is, from 0 to 1. Laptop microphones can be very
quiet: a voice may only read 0.01. So the code turns the level into decibels, which show small
sounds as clearly as big ones, and the bird's height comes from that. Loud should mean up. The bird moves a part of the way each frame, so it glides and does not
jump. The space bar adds a hop. A computer with no microphone gives an error from `f.microphone()`,
so the sketch catches it and carries on with the keyboard.

```python
import math

import funground as f

try:
    mic = f.microphone()
except RuntimeError:                  # no microphone on this computer
    mic = None
bird_y = 300.0
hop = 0.0


def setup():
    f.size(480, 360)
    if mic:
        mic.start()


def key_pressed():
    global hop
    if f.key == " ":
        hop = 1.0


def draw():
    global bird_y, hop
    db = 20 * math.log10(mic.level() + 1e-9) if mic else -99     # decibels: -65 is a quiet room
    voice = f.constrain((db + 65) / 35, 0, 1)                    # 0 is quiet and 1 is loud
    voice = max(voice, hop)
    hop *= 0.93                                          # a hop fades away
    target = 330 - voice * 280                           # loud is up
    bird_y += (target - bird_y) * 0.14                   # move a part of the way
    f.background(150, 205, 245)
    f.no_stroke()
    f.fill("gold")
    f.circle(120, bird_y, 30)
    f.fill("black")
    f.circle(128, bird_y - 4, 5)
    f.fill(0, 0, 0, 60)
    f.rect(16, 330 - voice * 280, 14, voice * 280 + 1)    # the voice meter


f.run()
```

Say "aaah" and the bird goes up. If it does not rise much, make the `65` smaller. If it rises for
the slightest noise, make it bigger.

### Stage 2: make it yours

**Choose what controls the bird.** There are two good choices.

- **Loudness**, `mic.level()`. Any sound moves the bird, so it always answers. Use this.
- **Pitch**, `mic.pitch()`. High notes could be up. But the microphone only gives a pitch when it
  hears one clear note. Breath and noise give `None`, and the bird would fall at the wrong moment.

If you want a pitch game, treat `None` as "do nothing" and smooth the pitch first, as in project 3.

**Learn the room.** Rooms and microphones are not equally quiet. In the first half second, listen
and keep the middle reading, in decibels. Then measure how many decibels you are above it. A voice
8 decibels above the room counts as 0, and 33 decibels above counts as 1.

```py
db = 20 * math.log10(mic.level() + 1e-9)
if f.frame_count < 30:
    quiet.append(db)                                  # stay quiet for half a second
    floor = sorted(quiet)[len(quiet) // 2]            # the middle one: a click does not move it
else:
    voice = f.constrain((db - floor - 8) / 25, 0, 1)
```

**Add gates.** A gate is a dictionary: where it is, and the height of its gap. Each frame, move
every gate left. When one is off the screen, take it away and add a new one on the right.

**Check for a crash.** The bird is a circle and the parts of a gate are rectangles. Find the point
in the rectangle that is nearest to the bird, with `f.constrain`. If that point is closer than the
bird's radius, the bird has touched the gate.

```py
near_x = f.constrain(BIRD_X, gate_x, gate_x + GATE_W)
near_y = f.constrain(bird_y, top, bottom)
touching = math.hypot(BIRD_X - near_x, bird_y - near_y) < BIRD_R
```

**Score and best score.** Add one when a gate goes past the bird. Keep `best = max(best, score)`.

**Sound effects.** Make them once, at the top of the file, and play them when something happens.
Quiet is nicer, so give each a `volume`.

```py
sound_point = f.note("G5", 0.18, volume=0.35)          # a short bright note for a point
sound_crash = f.tone(120, 0.45, wave="triangle", volume=0.45, release=0.3)   # a low thud
sound_start = f.pluck("C5", 0.5, volume=0.4)           # a plucked string to begin

sound_point.play()
```

Here is the game in short: gates, a crash, a score, a best score and a space bar to start.

```python
import math

import funground as f

W, H = 480, 360
BIRD_X, BIRD_R, GATE_W, GAP = 100, 14, 56, 130

try:
    mic = f.microphone()
except RuntimeError:
    mic = None
sound_point = f.note("G5", 0.18, volume=0.35)
sound_crash = f.tone(120, 0.45, wave="triangle", volume=0.45, release=0.3)

bird_y, hop, score, best = 200.0, 0.0, 0, 0
playing = False
gates = []
quiet = []
floor = -80.0


def new_gate(x):
    return {"x": x, "gap": f.random(110, 260), "passed": False}


def restart():
    global gates, score, playing
    gates = [new_gate(400 + i * 190) for i in range(3)]
    score, playing = 0, True


def setup():
    global playing
    f.size(W, H)
    f.random_seed(5)
    if mic:
        mic.start()
    restart()
    playing = False                    # wait for the space bar


def key_pressed():
    global hop
    if f.key == " ":
        hop = 1.0
        if not playing:
            restart()


def touches(gate):
    for top, bottom in ((0, gate["gap"] - GAP / 2), (gate["gap"] + GAP / 2, H)):
        near_x = f.constrain(BIRD_X, gate["x"], gate["x"] + GATE_W)
        near_y = f.constrain(bird_y, top, bottom)
        if math.hypot(BIRD_X - near_x, bird_y - near_y) < BIRD_R:
            return True
    return False


def draw():
    global bird_y, hop, score, best, floor, playing
    voice = 0
    if mic:
        db = 20 * math.log10(mic.level() + 1e-9)       # loudness in decibels
        if f.frame_count < 30:                     # learn how quiet the room is
            quiet.append(db)
            floor = sorted(quiet)[len(quiet) // 2]    # the middle reading
        else:
            voice = f.constrain((db - floor - 8) / 25, 0, 1)
    voice = max(voice, hop)
    hop *= 0.93
    if playing:
        bird_y += ((H - 30 - voice * (H - 80)) - bird_y) * 0.14
        for gate in gates:
            gate["x"] -= 3
            if not gate["passed"] and gate["x"] + GATE_W < BIRD_X:
                gate["passed"] = True
                score += 1
                best = max(best, score)
                sound_point.play()
        if gates[0]["x"] < -GATE_W:
            gates.pop(0)
            gates.append(new_gate(gates[-1]["x"] + 190))
        if any(touches(g) for g in gates):
            playing = False
            sound_crash.play()

    f.background(150, 205, 245)
    f.no_stroke()
    f.fill(70, 150, 100)
    for gate in gates:
        f.rect(gate["x"], 0, GATE_W, gate["gap"] - GAP / 2)
        f.rect(gate["x"], gate["gap"] + GAP / 2, GATE_W, H)
    f.fill("gold")
    f.circle(BIRD_X, bird_y, BIRD_R * 2)
    f.fill(40, 60, 90)
    f.text_size(30)
    f.text(f"{score}   best {best}", 20, 40)
    if not playing:
        f.text_size(16)
        f.text("press the space bar to fly", 130, 200)


f.run()
```

### Stage 3: make it shine

The full version is in the gallery: `examples/gallery/projects/04_voice_game.py`. It has a sky with
a gradient, clouds and hills, a bird with a wing that flaps, and gates with caps. It learns the
room's quiet in the first half second, then measures your voice in decibels above the room, so a
quiet laptop microphone works. A small "mic" bar at the top shows what the microphone hears, so you
can see it hears you, and a bar on the left shows what the game uses. The game also shows the
name of the microphone. The game gets a little faster with
each point. After a crash it waits a moment before it starts again, so the shout that crashed you
does not start it at once. It plays a pluck to begin, a note for each point and a thud at the end.
The best score is kept while the game is open. The first screen is always the same.

### Challenge cards

- **Can you** make the gap smaller for each point, until it is only 100 pixels high?
- **Can you** use pitch and not loudness? Higher is up. Smooth it, and do nothing on `None`.
- **Can you** add a coin between the gates? Score two points if the bird touches it.
- **Can you** save the best score in a file, so it is still there next time?
- **Can you** swap the bird for a kite, a balloon or a rocket, and the gates for something else?

**Previous:** [17. Ragas and talas](17_ragas_and_talas.md)
