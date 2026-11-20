"""Print a flip book

Your dance on paper: eight frames of it on one A4 page, saved as flipbook.pdf. Print it, cut out the eight cards along
the lines, stack them in order with card 1 on top, staple the left edge, and flick through them with your thumb. It does
not need a camera or the models library. Until you have recorded a dance of your own, it prints one made up from sine
waves.

How it works:
- This is a script, not an animation: it draws one page from top to bottom, saves it and shows it.
- f.size("A4", margin=f.mm(12)) makes the page an A4 sheet with a 12 mm margin. f.grid(2, 4, gutter=f.mm(6)) cuts the
  inside of the margins into eight cards with 6 mm between them. The grid goes row by row, left to right.
- The eight frames are spread evenly through the dance: card n shows frame n * len(frames) // 8.
- hero.draw(..., zoom=0.28) draws the puppet small enough for a card. The hips are put the same distance from the top of
  every card, so the puppet does not jump about when you flick.
- f.save("flipbook.pdf") writes the page. A PDF keeps the shapes sharp at any printer's size. The drawing is stored in
  the file once, however many pieces of it the page shows, so the file stays small.

Make it yours:
- Use the friend instead: copy its FRIEND line and its Puppet(...) from 17_replay_on_any_drawing.py.
- Make a thicker flip book: f.grid(3, 6, ...) gives 18 smaller cards, and a smoother flick.
- Write the card's number on the right edge instead, if you staple on the right.
- Print a second page with the next eight frames: draw it after f.new_page().
"""
import json

import funground as f
from puppet import Puppet, made_up_dance

JOINTS = {"nose": (240, 132), "right_shoulder": (172, 262), "left_shoulder": (308, 262),
          "right_elbow": (112, 318), "left_elbow": (368, 318), "right_wrist": (64, 382), "left_wrist": (416, 382),
          "right_hip": (196, 432), "left_hip": (284, 432), "right_knee": (178, 518), "left_knee": (302, 518),
          "right_ankle": (166, 596), "left_ankle": (314, 596)}
CARDS = 8

try:
    with open("dance.json") as file:
        frames = json.load(file)["frames"]
except FileNotFoundError:
    frames = made_up_dance()

f.size("A4", margin=f.mm(12))
f.background("white")
drawing = f.load_image("data/hero.png")
drawing.remove_color(drawing.get(4, 4), 60, tidy=True)
hero = Puppet(drawing, JOINTS, arm=26, leg=28, head=92, grow=1.3)

cards = f.grid(2, 4, gutter=f.mm(6))
for n, card in enumerate(cards):
    f.no_fill()
    f.stroke("silver")
    f.stroke_width(1)
    f.rect(card.left, card.top, card.width, card.height)
    frame = frames[n * len(frames) // CARDS]
    hero.draw(frame["angles"], card.cx + f.mm(6), card.top + f.mm(42), zoom=0.28, lengths=frame.get("lengths"))
    f.no_stroke()
    f.fill("gray")
    f.text_size(11)
    f.text_align("left", "top")
    f.text(str(n + 1), card.left + f.mm(3), card.top + f.mm(3))

f.save("flipbook.pdf")
f.show()
