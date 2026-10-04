"""Rangoli and mandala generator

A pattern that is the same all the way round, made from one petal that is turned again and again.
The rings turn slowly. Use the controls under the canvas to change the petals, rings and palette,
or press "new design". "save" (or the S key) writes rangoli.svg and rangoli.pdf for printing.

How it works:
- A petal is a lens: two overlapped f.path().circle() shapes joined with & (intersection). Only the
  part inside both circles is left.
- A smaller lens is cut out of the petal with - (difference), so each petal has a hole. The centre
  rosette is circles turned with .rotate() and joined with | (union).
- Each ring is a loop. f.push(), f.rotate(), f.translate() and f.pop() put the same petal at each
  angle around the middle.
- The spin comes from f.frame_count. Rings next to each other turn in opposite directions, and
  outer rings turn at a different speed.
- f.color_mode("hsb", 360, 100, 100) lets each palette hold simple hue, saturation and brightness
  numbers.
- f.random_seed(), f.random() and f.random_choice() pick the shapes, so one seed always gives the
  same design. f.text_to_points() finds dots along the words at the bottom.

Make it yours:
- Change the 0.25 in draw_pattern(f.frame_count * 0.25): a bigger number spins faster, and 0 holds
  it still.
- Add your own palette to PALETTES, and raise the palette slider's top value from 4 to 5.
- Put your name in f.text_to_points(), in place of "Shubh Rangoli".
- Change the hole: use a different size in lens(length * 0.6, width * 0.5), or cut out
  f.path().circle() instead of a lens.
- Draw only outlines: use f.no_fill() and f.stroke() in draw_petal_ring(), press save, and look at
  rangoli.svg.
"""
import math

import funground as f

W, H = 560, 620
CX, CY = 280, 290          # the middle of the pattern
RADIUS = 250               # how far the biggest petals reach

# Festival palettes: a background, then colours as (hue, saturation, brightness).
PALETTES = [
    ("Diwali", (285, 70, 22), [(38, 95, 100), (14, 90, 100), (335, 80, 95), (52, 90, 100)]),
    ("Holi", (35, 8, 98), [(325, 85, 95), (190, 80, 90), (50, 90, 100), (270, 70, 85)]),
    ("Monsoon", (215, 65, 18), [(170, 70, 90), (195, 60, 100), (140, 60, 85), (60, 70, 100)]),
    ("Vasant", (150, 45, 20), [(55, 90, 100), (95, 65, 90), (345, 60, 100), (28, 85, 100)]),
]

seed = 1
design = {}
dots = []                  # the points of the words at the bottom
key_save = False           # set by the S key, used and cleared in draw()


def lens(length, width):
    """A petal pointing up: two circles overlapped. Its base is at (0, 0) and its tip at (0, -length)."""
    r = (length * length + width * width) / (4 * width)
    c = r - width / 2
    left = f.path().circle(-c, -length / 2, 2 * r)
    right = f.path().circle(c, -length / 2, 2 * r)
    return left & right


def rosette(n, radius, size):
    """n circles around a point, joined into one shape."""
    shape = f.path()
    for i in range(n):
        shape = shape | f.path().circle(0, -radius, size).rotate(360 * i / n)
    return shape


def new_design():
    """Pick the shapes that stay the same until the next click on "new design"."""
    global design
    f.random_seed(seed)
    design = {
        "width": [f.random(0.42, 0.7) for _ in range(6)],      # how fat each ring of petals is
        "dot": [f.random_choice(["round", "diamond"]) for _ in range(6)],
        "shift": f.random(0, 30),                               # turns the whole pattern a little
    }


def setup():
    global petals, rings, palette, show_dots, new_button, save_button, dots
    f.size(W, H)
    f.color_mode("hsb", 360, 100, 100)
    petals = f.create_slider(4, 16, 8, step=1, label="petals")
    rings = f.create_slider(2, 6, 4, step=1, label="rings")
    palette = f.create_slider(1, 4, 1, step=1, label="palette")
    show_dots = f.create_checkbox("dots", True)
    new_button = f.create_button("new design")
    save_button = f.create_button("save")
    new_design()
    # The words, as dots: one point every 5 pixels along the outlines of the letters.
    f.text_size(44)
    f.text_align("center", "baseline")
    dots = f.text_to_points("Shubh Rangoli", W / 2, 604, 5)


def draw_petal_ring(k, count, colours, spin):
    step = (RADIUS - 30) / rings.value()
    base = 30 + k * step
    length = min(step * 1.55, RADIUS - base)
    width = length * design["width"][k]
    petal = lens(length, width)
    hole = lens(length * 0.6, width * 0.5).translate(0, -length * 0.14)
    cut_petal = petal - hole                    # a petal with a lens-shaped hole
    hue, sat, bri = colours[k % len(colours)]
    direction = 1 if k % 2 == 0 else -1
    for i in range(count):
        f.push()
        f.rotate(design["shift"] * k + spin * direction + 360 * i / count + 180 * (k % 2) / count)
        f.translate(0, -base)
        f.fill(hue, sat, bri, 230)
        f.draw_path(cut_petal)
        # a bright dot in the hole and a dot beyond the tip
        h2, s2, b2 = colours[(k + 1) % len(colours)]
        f.fill(h2, s2, b2)
        f.circle(0, -length * 0.45, width * 0.18)
        if show_dots.checked():
            tip = -length - 8
            if design["dot"][k] == "round":
                f.circle(0, tip, 7)
            else:
                f.push()
                f.translate(0, tip)
                f.rotate(45)
                f.rect_mode("center")
                f.rect(0, 0, 9, 9, 2)
                f.pop()
        f.pop()


def draw_pattern(spin):
    name, background, colours = PALETTES[palette.value() - 1]
    f.background(*background)
    f.no_stroke()
    f.push()
    f.translate(CX, CY)
    count = petals.value()
    # outer rings first, so the inner ones sit on top
    for k in reversed(range(rings.value())):
        draw_petal_ring(k, count, colours, spin * (1 + k * 0.4))
    # the centre: a rosette with a hole in the middle
    hue, sat, bri = colours[0]
    f.fill(hue, sat, bri)
    f.draw_path(rosette(count, 11, 24) - f.path().circle(0, 0, 14))
    f.pop()

    # the words, drawn as dots
    hue, sat, bri = colours[1 % len(colours)]
    f.fill(hue, sat, bri)
    for x, y in dots:
        f.circle(x, y, 3.6)


def draw():
    global seed, key_save
    if new_button.clicked():
        seed += 1
        new_design()
    draw_pattern(f.frame_count * 0.25)
    if save_button.clicked() or key_save:
        f.save("rangoli.svg")
        f.save("rangoli.pdf")
        key_save = False


def key_pressed():
    global key_save
    if f.key in ("s", "S"):
        key_save = True


f.run()
