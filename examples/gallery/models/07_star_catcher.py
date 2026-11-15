"""Star catcher

Stars fall from the sky. Move your nose to move the basket, and catch as many as you can. Miss five and the game starts
again. Until the camera is ready, and in the tests, it shows a photo, so the basket stays still. It needs the models library, which is a separate
install: funground-ml.

How it works:
- ml.pose(source) looks for a body in the picture. body.nose.x is how far across the picture the nose is.
- The basket is a rectangle. Its middle is set to the nose every frame, so it follows you.
- The star's y grows every frame, so it falls. It falls a little faster for every star you catch.
- When the star is low enough and over the basket, you caught it. When it reaches the bottom, you missed it.
- Either way, a new star starts at the top, in a place chosen by random.randint().
- The camera is mirrored, so the basket moves the way you move.

Make it yours:
- Use body.right_wrist.x instead of body.nose.x, and catch the stars with your hand.
- Make the basket wider: change 60 in three places, or make it a variable.
- Change "gold" to another colour, or draw the star bigger.
- Change 5 to give yourself more chances.
"""
import random

import funground as f
from funground import camera
from funground import ml

cam = camera.open()
photo = f.load_image("data/standing_woman_640.jpg")     # shown until the camera is ready
basket_x = 320
star_x = 320
star_y = 0
caught = 0
missed = 0


def setup():
    f.size(640, 480)
    cam.start(640, 480)


def draw():
    global basket_x, star_y, caught, star_x, missed
    if cam.is_ready():
        source = cam
    else:
        source = photo
    f.image(source, 0, 0)
    body = ml.pose(source)
    if body:
        basket_x = body.nose.x
    star_y = star_y + 4 + caught / 2
    if star_y > 430 and star_x > basket_x - 60 and star_x < basket_x + 60:
        caught = caught + 1
        star_y = 0
        star_x = random.randint(30, 610)
    elif star_y > f.height:
        missed = missed + 1
        star_y = 0
        star_x = random.randint(30, 610)
    if missed > 4:
        caught = 0
        missed = 0
    f.stroke("white")
    f.stroke_width(3)
    f.fill("gold")
    f.circle(star_x, star_y, 30)
    f.fill("sienna")
    f.rect(basket_x - 60, 440, 120, 30)
    f.no_stroke()
    f.fill("white")
    f.text_size(28)
    f.text("Caught: " + str(caught) + "   Missed: " + str(missed), 20, 40)


f.run(fps=30)
