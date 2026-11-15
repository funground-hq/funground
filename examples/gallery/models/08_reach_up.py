"""Reach up

Hold both hands above your head to fill the bar. When it is full, you score a point and the bar starts again. Put your
hands down and the bar slowly empties. Until the camera is ready, and in the tests, it shows a photo, where nobody is reaching, so the bar stays empty. It
needs the models library, which is a separate install: funground-ml.

How it works:
- ml.pose(source) gives a body. body.left_wrist.y and body.right_wrist.y say how far down each wrist is.
- In a picture, y gets bigger going down. So "above" means a smaller y.
- When both wrists are higher than the nose, the bar level goes up by 2. Otherwise it goes down by 1, but never below 0.
- A full bar is 300 tall. Then the points go up by 1 and the level goes back to 0.

Make it yours:
- Change 2 to 4 for a quicker bar, or to 1 for a harder game.
- Count only one hand: use just the left wrist.
- Change 300 to make the bar shorter or taller. Remember to change both rectangles.
- Draw the bar in a colour that changes as it fills.
"""
import funground as f
from funground import camera
from funground import ml

cam = camera.open()
photo = f.load_image("data/standing_woman_640.jpg")     # shown until the camera is ready
level = 0
points = 0


def setup():
    f.size(640, 480)
    cam.start(640, 480)


def draw():
    global level, points
    if cam.is_ready():
        source = cam
    else:
        source = photo
    f.image(source, 0, 0)
    body = ml.pose(source)
    if body and body.left_wrist.y < body.nose.y and body.right_wrist.y < body.nose.y:
        level = level + 2
    elif level > 0:
        level = level - 1
    if level >= 300:
        points = points + 1
        level = 0
    f.stroke("white")
    f.stroke_width(4)
    f.fill("midnightblue")
    f.rect(560, 90, 50, 300)
    f.no_stroke()
    f.fill("gold")
    f.rect(560, 390 - level, 50, level)
    f.fill("white")
    f.text_size(32)
    f.text("Points: " + str(points), 20, 40)
    f.text_size(20)
    f.text("Hands up!", 20, 75)


f.run(fps=30)
