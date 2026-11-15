"""Teach a remote

Teach the computer three things, then steer a boat with them. Hold up a hand pointing left and press 1, a hand pointing right
and press 2, and a hand held still or no hand at all and press 3. Press each key a few times, moving a little each time.
Then show it a direction and the boat goes that way. Sail through the gaps in the walls to score. Until the camera is ready, and in
the tests, it shows a photo, so the keys teach the photo. It needs the models library, which is a separate install: funground-ml.

How it works:
- ml.teach(name, source) keeps what is in the picture as one example of name.
- ml.guess(source) names the taught thing the picture is most like, or gives None before you teach anything.
- guess.name is the best guess. The boat turns that name into a move: "left" is 5 less, "right" is 5 more.
- The wall falls down the screen. When it reaches the boat, the boat has to be inside the gap.
- "still" is taught too. Without it, the boat would always be steered one way or the other.
- What you taught lasts while the sketch runs. The first teach downloads the picture model (10 MB, once).

Make it yours:
- Teach other things, such as a cup for "left" and a book for "right". Change the names in both places.
- Make the gap wider: change 70 in three places.
- Make the boat faster: change 5 to 8.
- Show guess.score on the screen to see how sure the computer is.
"""
import random

import funground as f
from funground import camera
from funground import ml

cam = camera.open()
photo = f.load_image("data/standing_woman_640.jpg")     # shown until the camera is ready
source = photo
boat_x = 320
gate_x = 320
gate_y = 0
points = 0


def setup():
    f.size(640, 480)
    cam.start(640, 480)


def key_pressed():
    if f.key == "1":
        ml.teach("left", source)
    elif f.key == "2":
        ml.teach("right", source)
    elif f.key == "3":
        ml.teach("still", source)


def draw():
    global source, boat_x, gate_y, points, gate_x
    if cam.is_ready():
        source = cam
    else:
        source = photo
    guess = ml.guess(source)
    if guess:
        if guess.name == "left":
            boat_x = boat_x - 5
        elif guess.name == "right":
            boat_x = boat_x + 5
    gate_y = gate_y + 4
    if gate_y > 440:
        if boat_x > gate_x - 70 and boat_x < gate_x + 70:
            points = points + 1
        else:
            points = 0
        gate_y = 0
        gate_x = random.randint(100, 540)
    f.background("deepskyblue")
    f.no_stroke()
    f.fill("slategray")
    f.rect(0, gate_y, gate_x - 70, 30)
    f.rect(gate_x + 70, gate_y, f.width - gate_x - 70, 30)
    f.fill("white")
    f.circle(boat_x, 440, 40)
    f.fill("black")
    f.text_size(28)
    f.text("Points: " + str(points), 20, 40)
    f.text_size(20)
    if guess:
        f.text("I see: " + guess.name, 20, 75)
    else:
        f.text("Teach me first: keys 1, 2 and 3", 20, 75)


f.run(fps=30)
