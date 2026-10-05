"""Scratch-card reveal game

A silver foil hides three symbols. Hold the mouse button down and scratch the foil away. When most of
the foil over a symbol is gone, the symbol counts as found, a soft chime plays, and the counter
goes up. Find three that match and you win. Press N for a new card. Every card number always hides
the same symbols, so card 1 is the same each time. With no sound device the game is simply silent.

How it works:
- The foil is a layer: `with f.layer("foil"):`. A layer keeps its drawing from frame to frame, so
  the foil is painted once for each card, and the scratches stay.
- To scratch, the sketch calls f.erase() inside the foil layer and then draws circles along the
  mouse's path. Drawing now removes the foil and does not paint it, so the card under it shows
  through. f.no_erase() is not needed: every `with` block starts with painting again.
- The symbols are on the canvas under the layer. f.random_seed(card) and f.random_choice() pick the
  same three symbols for the same card number. Stars, hearts, moons and diamonds are drawn with
  f.polygon() and with paths joined by | and -.
- A layer cannot be read back, so the sketch keeps its own list of sample points inside each symbol.
  A point is cleared when a scratch passes close to it (f.distance()). At 60% cleared, the symbol is found.
- f.pluck() makes the chime, and sound.play() plays it. Three notes rise as you find them. f.melody()
  plays a little tune for a win.
- f.mouse_x, f.mouse_y and f.is_mouse_pressed give the scratch. f.key reads N in key_pressed().

Make it yours:
- Change BRUSH from 17 to 30 for a coin-sized scratch, or to 10 for a pin.
- Change the 0.6 in FOUND_AT. A smaller number finds symbols sooner.
- Change WIN_CHANCE for easier or harder cards. 1 means every card wins.
- Add a fifth symbol: write a function like draw_heart() and add its name to KINDS and to draw_symbol().
- Change the notes in CHIMES, or the tune in win_tune.
"""
import math

import funground as f

W, H = 640, 440
CARD = (50, 90, 540, 250)                  # x, y, width, height of the card
CELLS = [(140, 215), (320, 215), (500, 215)]   # the middle of each hiding place
SYMBOL = 46                                # how big a symbol is
BRUSH = 17                                 # the radius of the scratch
FOUND_AT = 0.6                             # this part of a symbol's points must be cleared
WIN_CHANCE = 0.4                           # how often a card has three that match
KINDS = ["star", "heart", "moon", "diamond"]
COLOURS = {"star": (255, 190, 40), "heart": (230, 60, 90), "moon": (90, 120, 230), "diamond": (40, 180, 150)}
DEMO_FRAMES = 30                           # the card scratches itself a little, to show how

# Sounds made from numbers, soft and quiet.
CHIMES = [f.pluck("C5", 0.7, volume=0.4), f.pluck("E5", 0.7, volume=0.4), f.pluck("G5", 0.7, volume=0.4)]
win_tune = f.melody("C5 E5 G5 C6:2", tempo=200, volume=0.35)
miss_sound = f.pluck("D4", 0.8, volume=0.3)

card_number = 1
symbols = []                               # one name for each hiding place
points = []                                # for each place, a list of [x, y, cleared]
found = []                                 # True for each symbol that is found
last = None                                # where the last scratch stamp was, or None
touched = False                            # has the player used the mouse on this card?


def play(sound):
    """Play a sound. With no sound device this does nothing, so the game never stops."""
    try:
        sound.play()
    except Exception:
        pass


def sample_points(cx, cy):
    """A grid of points inside a symbol's circle, 12 pixels apart."""
    out = []
    for dx in range(-60, 61, 12):
        for dy in range(-60, 61, 12):
            if math.hypot(dx, dy) <= 60:
                out.append([cx + dx, cy + dy, False])
    return out


def new_card(number):
    """Choose the symbols for this card number, then cover them with fresh foil."""
    global card_number, symbols, points, found, last, touched
    card_number = number
    f.random_seed(number)
    if f.random() < WIN_CHANCE:
        symbols = [f.random_choice(KINDS)] * 3
    else:
        symbols = [f.random_choice(KINDS) for _ in range(3)]
        while len(set(symbols)) == 1:
            symbols = [f.random_choice(KINDS) for _ in range(3)]
    points = [sample_points(cx, cy) for cx, cy in CELLS]
    found = [False, False, False]
    last = None
    touched = False
    make_foil()


def make_foil():
    """Paint the foil once. It is a layer, so it stays until the next card."""
    x, y, w, h = CARD
    with f.layer("foil"):
        f.clear()                          # wipe the layer, then paint it again
        f.no_stroke()
        f.fill(f.linear_gradient(x, y, x + w, y + h, [(196, 200, 208), (232, 235, 240), (170, 176, 188)]))
        f.rect(x, y, w, h, 18)
        for _ in range(70):                # little bright and dark flecks
            fx = f.random(x + 10, x + w - 40)
            fy = f.random(y + 10, y + h - 10)
            if f.random() < 0.5:
                f.stroke(255, 255, 255, 120)
            else:
                f.stroke(120, 126, 140, 70)
            f.stroke_width(1)
            f.line(fx, fy, fx + f.random(8, 30), fy - f.random(2, 8))
        f.no_stroke()
        f.fill(120, 126, 140)
        f.text_size(34)
        f.text_align("center", "center")
        f.text("SCRATCH HERE", x + w / 2, y + h / 2)


def draw_symbol(kind, cx, cy, r):
    """One symbol, centred at (cx, cy)."""
    f.fill(*COLOURS[kind])
    f.no_stroke()
    if kind == "star":
        corners = []
        for i in range(10):
            radius = r if i % 2 == 0 else r * 0.45
            angle = math.radians(-90 + i * 36)
            corners.append((cx + radius * math.cos(angle), cy + radius * math.sin(angle)))
        f.polygon(corners)
    elif kind == "heart":
        f.circle(cx - r * 0.3, cy - r * 0.2, r * 0.75)
        f.circle(cx + r * 0.3, cy - r * 0.2, r * 0.75)
        f.polygon([(cx - r * 0.66, cy + r * 0.02), (cx + r * 0.66, cy + r * 0.02), (cx, cy + r * 0.95)])
    elif kind == "moon":
        moon = f.path().circle(cx, cy, r * 2) - f.path().circle(cx + r * 0.5, cy - r * 0.2, r * 1.7)
        f.draw_path(moon)
    else:
        f.polygon([(cx, cy - r), (cx + r * 0.7, cy), (cx, cy + r), (cx - r * 0.7, cy)])


def scratch(x1, y1, x2, y2):
    """Erase the foil along a line from (x1, y1) to (x2, y2), and see which symbols this uncovers."""
    stamps = max(1, int(math.hypot(x2 - x1, y2 - y1) / 5))
    spots = [(f.lerp(x1, x2, i / stamps), f.lerp(y1, y2, i / stamps)) for i in range(stamps + 1)]
    with f.layer("foil"):
        f.erase()                          # drawing now removes the foil
        f.no_stroke()
        for sx, sy in spots:
            f.circle(sx, sy, BRUSH * 2)
    for place in range(3):
        if found[place]:
            continue
        for p in points[place]:
            if not p[2] and any(f.distance(p[0], p[1], sx, sy) <= BRUSH for sx, sy in spots):
                p[2] = True
        cleared = sum(1 for p in points[place] if p[2]) / len(points[place])
        if cleared >= FOUND_AT:
            reveal(place)


def reveal(place):
    """A symbol is found: clear the rest of its foil, chime, and count it."""
    found[place] = True
    cx, cy = CELLS[place]
    with f.layer("foil"):
        f.erase()
        f.no_stroke()
        f.circle(cx, cy, 2 * (SYMBOL + 20))
    if sum(found) == 3 and len(set(symbols)) == 1:
        play(win_tune)
    elif sum(found) == 3:
        play(miss_sound)
    else:
        play(CHIMES[sum(found) - 1])


def demo_path(frame):
    """Where the little demonstration scratch is on this frame: a wave across the first symbol."""
    distance = frame * 14
    if distance < 250:
        x = 80 + distance
        return x, 215 + 12 * math.sin(x / 22)
    x = 330 - (distance - 250)
    return x, 258 + 6 * math.sin(x / 18)


def setup():
    f.size(W, H)
    new_card(1)


def key_pressed():
    if f.key in ("n", "N"):
        new_card(card_number + 1)


def update():
    """The scratching: the mouse, or the demonstration on the first frames."""
    global last, touched
    x, y, w, h = CARD
    if f.is_mouse_pressed and x <= f.mouse_x <= x + w and y <= f.mouse_y <= y + h:
        touched = True
        if last is None:
            last = (f.mouse_x, f.mouse_y)
        scratch(last[0], last[1], f.mouse_x, f.mouse_y)
        last = (f.mouse_x, f.mouse_y)
        return
    last = None
    if not touched and f.frame_count < DEMO_FRAMES:
        before = demo_path(f.frame_count - 1) if f.frame_count > 0 else demo_path(0)
        now = demo_path(f.frame_count)
        scratch(before[0], before[1], now[0], now[1])


def draw():
    update()
    f.background(34, 38, 60)

    f.fill(255)
    f.text_align("center", "center")
    f.text_size(28)
    f.text(f"Scratch card {card_number}", W / 2, 38)
    f.text_size(18)
    f.fill(255, 214, 120)
    f.text(f"Found {sum(found)} of 3", W / 2, 68)

    x, y, w, h = CARD                      # the card, and the symbols under the foil
    f.fill(250, 244, 228)
    f.rect(x, y, w, h, 18)
    for place, (cx, cy) in enumerate(CELLS):
        f.fill(236, 228, 206)
        f.circle(cx, cy, 2 * (SYMBOL + 14))
        draw_symbol(symbols[place], cx, cy, SYMBOL)

    f.fill(255)
    f.text_size(18)
    if sum(found) == 3:
        if len(set(symbols)) == 1:
            f.fill(255, 214, 120)
            f.text_size(30)
            f.text("Three the same. You win!", W / 2, 378)
        else:
            f.text("No match this time.", W / 2, 378)
        f.fill(190)
        f.text_size(16)
        f.text("Press N for a new card", W / 2, 412)
    else:
        f.fill(190)
        f.text("Hold the mouse button and scratch", W / 2, 378)
        f.text_size(16)
        f.text("Press N for a new card", W / 2, 412)


f.run()
