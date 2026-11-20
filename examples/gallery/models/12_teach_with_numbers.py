"""Teach with numbers

Teach the computer two gestures, "hands up" and "namaste", and then let it name the one you make. A pose becomes seven numbers, and the sketch compares them with the poses it was taught. You write the teaching and the guessing yourself, so you see how it works inside. With no camera, it uses a photo, so it still works. It needs the models library, which is a separate install: funground-ml.

How it works:
- describe(body) turns a pose into seven numbers: four joint angles (both elbows and both shoulders), how far each wrist is above its shoulder, and the distance between the wrists.
- Every number is a ratio. Angles are divided by 180, heights by the torso length, and the wrist distance by the shoulder width. So the numbers stay the same when you step closer, further or sideways. Pixel positions would not.
- teach(name, numbers) only remembers. It adds the seven numbers to the list for that name. There is no training step.
- guess(numbers) finds the nearest memory. math.dist measures how far apart two lists of numbers are, and the name with the closest example wins. The score compares the best with the runner-up: 0.5 is a coin toss and 1 is an exact match. This is called nearest neighbour.
- You cannot press a button and pose at the same time. So a button starts a countdown of 3 seconds, counted in frames, and then the sketch teaches that name on every 4th frame for one second: 6 examples. Teach "hands up", then "namaste", then "nothing".
- "Nothing" must be taught too. The sketch always names the nearest thing it knows, so an untaught pose gets a name with a low score. A low score means "I am guessing". Act on a gesture only when the score is high.

Make it yours:
- Act on a gesture only when you are sure: if name == "namaste" and score > 0.7:.
- Teach each name from two different distances, and watch the score stay high. Ratios make this work.
- Add a fourth name, such as "arms wide", with its own button.
- Add an eighth number to describe(), such as the angle at one knee, and see if the guesses improve.
"""
import math

import funground as f
from funground import camera, ml

NAMES = ["hands up", "namaste", "nothing"]
COUNT = 72                                     # 3 seconds at 24 frames a second, counted in frames
TEACH = 24                                     # then 1 second of teaching, one example on every 4th frame
LABELS = ["left elbow", "right elbow", "left shoulder", "right shoulder", "left hand height", "right hand height", "hands apart"]

examples = {name: [] for name in NAMES}        # each name's taught poses, as lists of numbers
still = f.load_image("data/standing_woman_640.jpg")      # used when there is no camera
still.resize(320, 480)
cam = None
buttons = {}
teaching = None                                # the name being taught, or None
countdown = 0                                  # frames left of the count and the teaching


def setup():
    global cam
    f.size(640, 480)
    for name in NAMES:
        buttons[name] = f.create_button("Teach " + name)
    try:
        cam = camera.open()
        cam.start(640, 480)
    except RuntimeError:
        cam = None


def angle_at(a, b, c):
    """The angle at b, between the line to a and the line to c: 0 to 180 degrees."""
    return abs((a - b).angle_between(c - b))


def describe(body):
    """A pose as seven numbers that do not change when you step sideways, nearer or further."""
    torso = body.left_shoulder.dist(body.left_hip)
    wide = body.left_shoulder.dist(body.right_shoulder)
    return [
        angle_at(body.left_shoulder, body.left_elbow, body.left_wrist) / 180,
        angle_at(body.right_shoulder, body.right_elbow, body.right_wrist) / 180,
        angle_at(body.left_hip, body.left_shoulder, body.left_elbow) / 180,
        angle_at(body.right_hip, body.right_shoulder, body.right_elbow) / 180,
        (body.left_shoulder.y - body.left_wrist.y) / torso,
        (body.right_shoulder.y - body.right_wrist.y) / torso,
        body.left_wrist.dist(body.right_wrist) / wide,
    ]


def teach(name, numbers):
    examples[name].append(numbers)


def guess(numbers):
    """The taught name with the nearest example, and a score: 0.5 is a coin toss, 1 is certain."""
    nearest = {name: min(math.dist(numbers, row) for row in rows) for name, rows in examples.items() if rows}
    if not nearest:
        return None, 0
    ranked = sorted(nearest, key=nearest.get)
    if len(ranked) == 1:
        return ranked[0], 0.5
    best, second = nearest[ranked[0]], nearest[ranked[1]]
    return ranked[0], second / (best + second) if best + second > 0 else 0.5


def draw():
    global teaching, countdown
    for name, button in buttons.items():
        if button.clicked():
            teaching, countdown = name, COUNT + TEACH
    source = cam if cam is not None and cam.is_ready() else still
    f.background("black")
    f.image(source, 0, 0)
    body = ml.pose(source)
    f.no_stroke()
    f.fill("white")
    f.text_size(16)
    for i, name in enumerate(NAMES):
        f.text(name + ": " + str(len(examples[name])) + " taught", 20, 400 + i * 24)
    if body is None:
        return
    numbers = describe(body)
    f.fill(0, 0, 0, 150)
    f.rect(330, 100, 300, 190, 8)              # the seven numbers, as bars
    for i, number in enumerate(numbers):
        f.fill("white")
        f.text(LABELS[i], 340, 110 + i * 25)
        f.fill("darkslateblue")
        f.rect(500, 112 + i * 25, 120, 10)
        f.fill("gold")
        f.rect(500, 112 + i * 25, 120 * f.constrain(abs(number) / 2, 0, 1), 10)
    if countdown > 0:
        countdown -= 1
        f.fill("white")
        if countdown >= TEACH:
            f.text_size(140)
            f.text(str((countdown - TEACH) // 24 + 1), 130, 160)
            f.text_size(20)
            f.text("Get ready to show: " + teaching, 340, 60)
        else:
            f.text_size(20)
            f.text("Hold it! Teaching: " + teaching, 340, 60)
            if countdown % 4 == 0:
                teach(teaching, numbers)
    name, score = guess(numbers)
    f.fill("white")
    if name is None:
        f.text_size(24)
        f.text("Teach me first", 340, 16)
        return
    f.text_size(40)
    f.text(name, 340, 12)
    f.fill("darkslateblue")
    f.rect(340, 330, 260, 14)
    f.fill("gold")
    f.rect(340, 330, 260 * score, 14)


f.run(fps=24)
