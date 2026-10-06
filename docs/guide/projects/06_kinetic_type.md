# Project 6: Kinetic type

Kinetic type is writing that moves. In this project a word is made of dots. When the mouse comes
near, the dots fly away. When it leaves, springs pull them home and the word is whole again. You can
type any word you like, tune the push and the springs with sliders, and record the result as a GIF
to send to a friend.

You will learn how to get points from letters, how to move many things with vectors and simple
forces, how to use noise to make things feel alive, and how to record an animation.

## Run it

```sh
python examples/gallery/projects/06_kinetic_type.py
```

Or open the gallery browser with `python -m funground.gallery` and pick **Kinetic type** in the
Projects area. Move the mouse over the word. Press Enter, type a new word, and press Enter again.
Move the "scatter" and "spring" sliders. Press G, or click "record GIF", to write `kinetic.gif`.

## How it works

The full version in the gallery rests on four ideas.

**A word is a list of points.** `f.text_to_points(word, x, y, spacing)` walks along the outline of
the letters and gives back a point every few pixels. Each point becomes a dot. A dot remembers three
things: its home (where it belongs), its position (where it is now) and its speed.

```py
for x, y in f.text_to_points("FUNGROUND", 320, 150, 8):
    home = f.Vector(x, y)
    dots.append({"home": home, "pos": home.copy(), "speed": f.Vector(0, 0)})
```

**Two forces.** The mouse pushes a dot away. The nearer the mouse, the harder the push, and past a
set distance there is no push at all. A spring pulls the dot home. The further it has gone, the
harder the pull. Both forces change the speed. Then the speed is multiplied by a number a little
below 1, which is friction. Without it a dot would swing for ever. Then the speed moves the dot.

```py
away = dot["pos"] - mouse                              # an arrow from the mouse to the dot
d = away.mag()
if 0 < d < REACH:
    dot["speed"] += away.set_mag(strength * (1 - d / REACH))
dot["speed"] += (dot["home"] - dot["pos"]) * spring     # the spring
dot["speed"] *= DAMPING                                 # friction
dot["pos"] += dot["speed"]
```

**Noise makes it breathe.** `f.noise(x, y, z)` gives smooth random numbers. Dots that are near each
other get nearly the same number, so a small shift of each home, taken from noise, moves a whole
patch of the word together. Change the third number as time passes, and the patch drifts.

```py
t = f.frame_count * 0.02
drift = f.Vector(f.noise(home.x * 0.02, home.y * 0.02, t) - 0.5,
                 f.noise(home.x * 0.02 + 40, home.y * 0.02, t) - 0.5) * 8
```

**Record a GIF.** `f.save_gif("kinetic.gif", 3)` records the next three seconds of the sketch. You
call it once, and then it records without any more help. It needs the free Pillow library.

```py
if f.key in ("g", "G"):
    f.save_gif("kinetic.gif", 3)
```

## Stage 1: make it work

One word of dots, a mouse push and a spring. Move the mouse over the word to scatter it.

```python
import funground as f

W, H = 640, 240
REACH = 100
dots = []


def setup():
    f.size(W, H)
    f.text_style("bold")
    f.text_size(120)
    f.text_align("center", "center")
    for x, y in f.text_to_points("HELLO", W / 2, H / 2, 7):
        home = f.Vector(x, y)
        dots.append({"home": home, "pos": home.copy(), "speed": f.Vector(0, 0)})


def draw():
    f.background(14, 16, 30)
    f.no_stroke()
    f.fill(90, 160, 255)
    mouse = f.Vector(f.mouse_x, f.mouse_y)
    for dot in dots:
        away = dot["pos"] - mouse
        d = away.mag()
        if 0 < d < REACH:
            dot["speed"] += away.set_mag(5 * (1 - d / REACH))
        dot["speed"] += (dot["home"] - dot["pos"]) * 0.06
        dot["speed"] *= 0.86
        dot["pos"] += dot["speed"]
        f.circle(dot["pos"].x, dot["pos"].y, 5)


f.run()
```

Run it. Try a bigger `REACH`, a bigger push (the 5) and a weaker spring (the 0.06). Each change gives
the word a different feel.

## Stage 2: make it yours

Here are some ways to make it more yours.

**Add sliders.** Let the player tune the feel, and not you. Make the sliders once in `setup()` and
read them each frame. The push strength and the spring are the two numbers worth playing with.

```py
scatter_slider = f.create_slider(1, 12, 5, step=0.5, label="scatter")
spring_slider = f.create_slider(0.01, 0.2, 0.06, step=0.01, label="spring")
strength, spring = scatter_slider.value(), spring_slider.value()
```

**Type a word.** `key_typed()` is called for each letter. A project that uses letter keys for typing
has a problem: what if G should record? The gallery example solves it with a mode. Enter switches
typing on. Enter again switches it off and makes the new dots. While typing is off, G records.
Backspace arrives in `key_pressed()` as `"backspace"`.

```py
def key_pressed():
    global typing, word, dots
    if f.key == "enter":
        typing = not typing
        if not typing and word.strip():
            dots = make_dots(word)
    elif typing and f.key == "backspace":
        word = word[:-1]


def key_typed():
    global word
    if typing and len(word) < 10 and len(f.key) == 1:
        word += f.key.upper()
```

**Make a long word fit.** A long word is wider than the canvas. Measure it with `f.text_width()`,
and make the text smaller until it fits, before you ask for the points.

```py
size = 170
f.text_size(size)
if f.text_width(word) > W - 60:
    size = int(size * (W - 60) / f.text_width(word))
```

**New dots fly in.** When the word changes, start each new dot at a random place. Its spring pulls
it home, so the word builds itself.

```py
start = f.Vector(f.random(0, W), f.random(0, H))
```

**Colour from speed.** A dot that is still is cool and calm. A dot that is flying is hot.
`f.lerp_color(a, b, amount)` mixes two colours. Use the speed, kept between 0 and 1, as the amount.

```py
heat = f.constrain(dot["speed"].mag() / 6, 0, 1)
f.fill(f.lerp_color((70, 140, 230), (255, 130, 60), heat))
```

**Record a GIF.** Calling `f.save_gif()` while a recording is running is an error, so keep a note of
when the recording ends. If the mouse is not over the canvas, a GIF would show a word that does not
move. The gallery example fixes that with a ghost mouse that sweeps across the word while it records.

```py
ghost = f.Vector(W * (0.1 + 0.8 * t), H / 2 + 50 * math.sin(t * 9))    # t goes from 0 to 1
```

## Stage 3: make it shine

The full version is in the gallery: `examples/gallery/projects/06_kinetic_type.py`. It starts with the
word FUNGROUND, made smaller to fit the canvas. The mouse scatters the dots, and sliders set the push
and the spring. Noise makes every home drift a little, so the word is never quite still, and each dot
turns from blue to orange with its speed. Press Enter to type a word of up to ten letters. Press
Enter again and the new dots fly in. Press G, or click "record GIF", and it records three seconds as
`kinetic.gif`, with a ghost mouse if yours is elsewhere. A note says when the file is saved.

## Challenge cards

- **Can you** make the dots come toward the mouse and not run away from it?
- **Can you** add a third slider for friction? It is the 0.86 in the code.
- **Can you** make the dots change size as they fly: big when fast, small when still?
- **Can you** colour each dot by where its home is, using `f.hsb()`, so the word is a rainbow?
- **Can you** use two words, one above the other, and press Tab to swap them?
- **Can you** make a click send out a ring of push that spreads from the mouse?

## Credits and ideas

This project builds on the idea of a spring that pulls each dot home ([Hooke's law](https://en.wikipedia.org/wiki/Hooke%27s_law)), a standard way to animate motion also taught in Daniel Shiffman's [The Nature of Code](https://natureofcode.com/). The code is written for funground (CC0). See [CREDITS.md](../../../CREDITS.md#ideas-the-examples-build-on).

**Back to:** [18. Projects](../18_projects.md). Useful chapters: [6. Text](../06_text.md),
[7. Animation and time](../07_animation_and_time.md), [10. Interaction](../10_interaction.md),
[11. Randomness and noise](../11_randomness_and_noise.md) and
[13. Saving your work](../13_saving_your_work.md).
