"""Teach with a pose card

Teach the computer two gestures, "hands up" and "namaste", with the real ml.teach, and then let it name the one you make. ml.teach learns from pictures. If you give it the camera picture, it also learns your shirt and your room. So the sketch gives it a pose card instead: the stick figure alone, white on black, always the same size and in the same place. With no camera, it uses a photo, so it still works. It needs the models library, which is a separate install: funground-ml.

How it works:
- f.create_graphics(160, 160) makes a small second picture called card. It has the same drawing commands as f.
- draw_card subtracts the hip position from every point, so the figure is always centred. It multiplies by zoom, so the torso is always the same length on the card. This does for a picture what the ratios did in Teach with numbers.
- ml.teach(name, card) keeps the card as one example of that name and returns how many examples the name has now. The first ml.teach downloads a picture model of about 10 MB, once.
- ml.guess(card, k=2) gives a guess with a name, a score, and the runner-up in guess.next. It gives None until something has been taught.
- You cannot press a button and pose at the same time. So a button starts a countdown of 3 seconds, counted in frames, and then the sketch teaches that name on every 4th frame for one second. Teach "hands up", then "namaste", then "nothing". The same picture twice adds nothing, so move a little.
- "Nothing" must be taught too: the computer always names the nearest thing it knows. Compare this with Teach with numbers, and see which tells your poses apart better.

Make it yours:
- Make CARD bigger, such as 224, and draw the lines thicker. A bigger card shows more detail.
- Show the runner-up under the name, using guess.next[0].name and guess.next[0].score.
- Teach each name from two different distances, and see if the guess holds.
- Add a fourth name, such as "arms wide", with its own button.
"""
import funground as f
from funground import camera, ml

BONES = [("left_shoulder", "right_shoulder"), ("left_shoulder", "left_elbow"), ("left_elbow", "left_wrist"),
         ("right_shoulder", "right_elbow"), ("right_elbow", "right_wrist"), ("left_shoulder", "left_hip"),
         ("right_shoulder", "right_hip"), ("left_hip", "right_hip"), ("left_hip", "left_knee"),
         ("left_knee", "left_ankle"), ("right_hip", "right_knee"), ("right_knee", "right_ankle")]
NAMES = ["hands up", "namaste", "nothing"]
CARD = 160                                     # the size of the pose card, in pixels
COUNT = 72                                     # 3 seconds at 24 frames a second, counted in frames
TEACH = 24                                     # then 1 second of teaching, one example on every 4th frame

counts = {name: 0 for name in NAMES}
still = f.load_image("data/standing_woman_640.jpg")      # used when there is no camera
still.resize(320, 480)
cam = None
card = None
buttons = {}
teaching = None                                # the name being taught, or None
countdown = 0                                  # frames left of the count and the teaching


def setup():
    global cam, card
    f.size(640, 480)
    card = f.create_graphics(CARD, CARD)
    for name in NAMES:
        buttons[name] = f.create_button("Teach " + name)
    try:
        cam = camera.open()
        cam.start(640, 480)
    except RuntimeError:
        cam = None


def draw_card(body):
    """Draw the pose as a white stick figure on a black card, always the same size and in the same place."""
    card.background("black")
    if body is None:
        return
    hips = (body.left_hip + body.right_hip) / 2
    shoulders = (body.left_shoulder + body.right_shoulder) / 2
    zoom = CARD * 0.28 / max(hips.dist(shoulders), 1)
    card.no_fill()
    card.stroke("white")
    card.stroke_width(6)
    card.stroke_cap("round")
    for first, second in BONES:
        a = (body.points[first] - hips) * zoom
        b = (body.points[second] - hips) * zoom
        card.line(CARD / 2 + a.x, CARD * 0.6 + a.y, CARD / 2 + b.x, CARD * 0.6 + b.y)
    nose = (body.nose - hips) * zoom
    card.circle(CARD / 2 + nose.x, CARD * 0.6 + nose.y, 14)


def draw():
    global teaching, countdown
    for name, button in buttons.items():
        if button.clicked():
            teaching, countdown = name, COUNT + TEACH
    source = cam if cam is not None and cam.is_ready() else still
    f.background("midnightblue")
    f.image(source, 0, 0, source.width * 320 / source.height, 320)     # smaller, to leave room for the card
    draw_card(ml.pose(source))
    f.image(card, 450, 20)
    f.no_stroke()
    f.fill("white")
    f.text_size(16)
    for i, name in enumerate(NAMES):
        f.text(name + ": " + str(counts[name]) + " taught", 20, 400 + i * 24)
    if countdown > 0:
        countdown -= 1
        if countdown >= TEACH:
            f.text_size(110)
            f.text(str((countdown - TEACH) // 24 + 1), 270, 100)
            f.text_size(20)
            f.text("Get ready to show: " + teaching, 340, 240)
        else:
            f.text_size(20)
            f.text("Hold it! Teaching: " + teaching, 340, 240)
            if countdown % 4 == 0:
                counts[teaching] = ml.teach(teaching, card)
    guess = ml.guess(card, k=2)
    f.fill("white")
    if guess is None:
        f.text_size(24)
        f.text("Teach me first", 340, 270)
        return
    f.text_size(32)
    f.text(guess.name, 340, 270)
    f.fill("gold")
    f.rect(340, 316, 160 * guess.score, 12)


f.run(fps=24)
