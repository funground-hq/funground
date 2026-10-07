"""A poster series, without the studio words (studio 6, before)

The same picture as examples/gallery/studios/06_poster_series.py: four event posters drawn by one
function, side by side on one sheet. This version uses only what funground had before the studio
words. The sheet is laid out by hand: each poster is drawn inside a clip, moved and scaled into its
cell, with the random seed set again before each one. Press K to save the sheet and a small note.

How it works:
- poster(event) draws one poster on the whole A4 page. Its grid of spots, its title and its date
  on a band are placed with numbers worked out from the margin, the gutter and the cell size.
- background() always fills the whole window, so the poster paints its paper with f.rect() instead:
  inside a moved and scaled cell, background() would cover the whole sheet.
- spot() draws the ring and the dot. To size it to a cell, the code must know how wide it is:
  SPOT, the ring's 40 plus its stroke of 6.
- draw() works out the sheet: two columns and two rows, one scale for every poster, a clip, a frame
  and a label under each one. f.random_seed(SEED) before each poster makes the spots fall in the
  same cells.
- key_pressed() finds the next free number and saves the sheet with f.save(), and a note in a JSON
  file.

Make it yours:
- Add a fifth event to EVENTS. Then make room for it: the sheet's rows are fixed at two.
- Change SEED to scatter the spots differently.
- Compare the two versions: which part of this one is about the sheet, not the posters?
"""
import json
import os

import funground as f

MM = 72 / 25.4
W, H = 595, 842                    # an A4 page
MARGIN = 12 * MM
GUTTER = 4 * MM
SEED = 2026
SPOT = 46                          # the ring is 40 across, and its stroke of 6 adds 3 on each side

# event: (paper, ink, accent, date)
EVENTS = {
    "Book fair": ("#264653", "#f4f1de", "#e9c46a", "12 - 14 March"),
    "Science week": ("#1d3557", "#f1faee", "#e63946", "3 - 7 June"),
    "Music night": ("#3c1642", "#fdf0d5", "#f4a261", "21 June"),
    "Sports day": ("#0b3d2e", "#f0efeb", "#90be6d", "9 September"),
}


def spot(x, y, width, colour, ink):
    """A ring with a dot in it, centred on (x, y) and scaled to be width across."""
    f.push()
    f.translate(x, y)
    f.scale(width / SPOT)
    f.no_fill()
    f.stroke(colour)
    f.stroke_width(6)
    f.circle(0, 0, 40)
    f.no_stroke()
    f.fill(ink)
    f.circle(0, 0, 12)
    f.pop()


def poster(event):
    paper, ink, accent, date = EVENTS[event]
    f.no_stroke()
    f.fill(paper)
    f.rect(0, 0, W, H)
    cell_w = (W - 2 * MARGIN - 3 * GUTTER) / 4
    cell_h = (H - 2 * MARGIN - 5 * GUTTER) / 6
    for row in range(4):                                # the top four rows
        for col in range(4):
            if f.random() < 0.55:
                cx = MARGIN + col * (cell_w + GUTTER) + cell_w / 2
                cy = MARGIN + row * (cell_h + GUTTER) + cell_h / 2
                spot(cx, cy, cell_w * f.random(0.35, 1), accent, ink)
    f.fill(ink)
    f.text_style("bold")
    f.text_size(54)
    f.text_align("left", "bottom")
    f.text(event, MARGIN, MARGIN + 5 * cell_h + 4 * GUTTER)
    footer = MARGIN + 5 * (cell_h + GUTTER)
    f.fill(accent)
    f.rect(0, footer - 3 * MM, W, H - footer + 3 * MM)    # full bleed: from edge to edge of the page
    f.fill(paper)
    f.text_style("normal")
    f.text_size(24)
    f.text_align("left", "top")
    f.text(date + "  ·  Town hall  ·  all welcome", MARGIN, footer)


def setup():
    f.size(W, H)


def draw():
    f.background("#e9e5dc")
    gap, strip = 10, 16                                 # between cells, and under each poster for its label
    cell_w = (W - 2 * MARGIN - gap) / 2
    cell_h = (H - 2 * MARGIN - gap) / 2
    k = min(cell_w / W, (cell_h - strip) / H)           # one scale for every poster
    for i, event in enumerate(EVENTS):
        left = MARGIN + (i % 2) * (cell_w + gap)
        top = MARGIN + (i // 2) * (cell_h + gap)
        x = left + cell_w / 2 - W * k / 2
        y = top + (cell_h - H * k - strip) / 2
        with f.saved_state():
            f.clip(f.path().rect(x, y, W * k, H * k))
            f.translate(x, y)
            f.scale(k)
            f.random_seed(SEED)
            poster(event)
        with f.saved_state():
            f.no_fill()
            f.stroke("#9a9a9a")
            f.stroke_width(1)
            f.rect(x, y, W * k, H * k)
            f.no_stroke()
            f.fill("#555555")
            f.text_size(11)
            f.text("event = " + event, x, y + H * k + 3)


def key_pressed():
    if f.key == "k":
        number = 1
        while os.path.exists(f"sheet_{number:03}.png"):
            number += 1
        f.save(f"sheet_{number:03}.png")
        with open(f"sheet_{number:03}.json", "w", encoding="utf-8") as note:
            json.dump({"note": "the series so far", "seed": SEED, "events": len(EVENTS)}, note)


f.run()
