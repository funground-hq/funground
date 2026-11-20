"""Change the costume

The same body points, drawn three ways: as a Warli figure, as a robot, and as brush strokes. Press a button to change the costume. The points say where the body is. They say nothing about what it looks like. With no camera, it uses a photo, so it still works. It needs the models library, which is a separate install: funground-ml.

How it works:
- Warli is a painting tradition of the Warli people of Maharashtra, made in white on an earth-coloured wall. Its people are two triangles joined at the waist, a circle for the head and thin lines for limbs. It is worth showing learners real Warli paintings next to this sketch.
- middle(a, b) gives the point halfway between two points: add them and halve the result. The waist is halfway between the middle of the shoulders and the middle of the hips, and both triangles meet there. wide_left and wide_right push the hips out to 1.8 times their distance from the centre, because a Warli skirt is wide.
- block(a, b, thickness) draws a bar from one point to another. It moves the drawing origin to a, turns the page to face b, and draws a plain rectangle along the x axis. The with f.saved_state(): line undoes the move and the turn afterwards. Move, turn, draw is a very useful pattern.
- stroke_through(points, width) draws one smooth brush stroke with f.curve_vertex. The first and last points are given twice, because the curve needs a neighbour on each side of every point it passes through. The red square is a seal, as on an ink painting.
- Each button is made once in setup(). In draw(), button.clicked() is True once for each click, and the sketch remembers which costume you chose.

Make it yours:
- Draw the camera picture nowhere at all, as here, and ask a friend to guess the pose from the costume alone.
- Give the Warli figure a hair bun: a small circle beside the head.
- Invent a fourth costume: write a function, make a fourth button in setup(), and add one more elif in draw().
- Draw two costumes side by side with f.translate to compare them.
"""
import funground as f
from funground import camera, ml

ARMS_AND_LEGS = [("left_shoulder", "left_elbow", "left_wrist"), ("right_shoulder", "right_elbow", "right_wrist"),
                 ("left_hip", "left_knee", "left_ankle"), ("right_hip", "right_knee", "right_ankle")]

still = f.load_image("data/standing_woman_640.jpg")      # used when there is no camera
still.resize(320, 480)
cam = None
costume = "Warli"
buttons = {}


def setup():
    global cam
    f.size(640, 480)
    for name in ("Warli", "Robot", "Brush"):
        buttons[name] = f.create_button(name)
    try:
        cam = camera.open()
        cam.start(640, 480)
    except RuntimeError:
        cam = None


def middle(a, b):
    return (a + b) / 2


def warli(body):
    f.background("#7a3b1c")
    shoulders = middle(body.left_shoulder, body.right_shoulder)
    hips = middle(body.left_hip, body.right_hip)
    waist = middle(shoulders, hips)
    wide_left = hips + (body.left_hip - hips) * 1.8
    wide_right = hips + (body.right_hip - hips) * 1.8
    f.no_stroke()
    f.fill("white")
    f.triangle(body.left_shoulder.x, body.left_shoulder.y, body.right_shoulder.x, body.right_shoulder.y, waist.x, waist.y)
    f.triangle(waist.x, waist.y, wide_left.x, wide_left.y, wide_right.x, wide_right.y)
    f.circle(body.nose.x, body.nose.y, body.left_shoulder.dist(body.right_shoulder) * 0.5)
    f.no_fill()
    f.stroke("white")
    f.stroke_width(5)
    f.stroke_cap("round")
    f.line(shoulders.x, shoulders.y, body.nose.x, body.nose.y)
    for first, second, third in ARMS_AND_LEGS:
        a, b, c = body.points[first], body.points[second], body.points[third]
        f.line(a.x, a.y, b.x, b.y)
        f.line(b.x, b.y, c.x, c.y)


def block(a, b, thickness):
    """A rounded bar from a to b."""
    with f.saved_state():
        f.translate(a.x, a.y)
        f.rotate((b - a).heading())
        f.rect(-thickness / 2, -thickness / 2, a.dist(b) + thickness, thickness, 8)


def robot(body):
    f.background("midnightblue")
    f.stroke("black")
    f.stroke_width(2)
    f.fill("silver")
    for first, second, third in ARMS_AND_LEGS:
        block(body.points[first], body.points[second], 26)
        block(body.points[second], body.points[third], 20)
    f.fill("lightsteelblue")
    f.quad(body.left_shoulder.x - 14, body.left_shoulder.y - 14, body.right_shoulder.x + 14, body.right_shoulder.y - 14,
           body.right_hip.x + 10, body.right_hip.y + 10, body.left_hip.x - 10, body.left_hip.y + 10)
    head = body.left_shoulder.dist(body.right_shoulder) * 0.7
    f.square(body.nose.x - head / 2, body.nose.y - head / 2, head, 10)
    f.fill("tomato")
    f.circle(body.left_eye.x, body.left_eye.y, 10)
    f.circle(body.right_eye.x, body.right_eye.y, 10)
    for name in ("left_elbow", "right_elbow", "left_knee", "right_knee"):
        f.circle(body.points[name].x, body.points[name].y, 14)


def stroke_through(points, width):
    """One smooth brush stroke through a list of points."""
    f.stroke_width(width)
    f.begin_shape()
    f.curve_vertex(points[0].x, points[0].y)
    for p in points:
        f.curve_vertex(p.x, p.y)
    f.curve_vertex(points[-1].x, points[-1].y)
    f.end_shape()


def brush(body):
    f.background("oldlace")
    f.no_fill()
    f.stroke(20, 20, 20, 210)
    f.stroke_cap("round")
    shoulders = middle(body.left_shoulder, body.right_shoulder)
    hips = middle(body.left_hip, body.right_hip)
    stroke_through([body.left_wrist, body.left_elbow, body.left_shoulder, shoulders,
                    body.right_shoulder, body.right_elbow, body.right_wrist], 14)
    stroke_through([body.nose, shoulders, hips], 22)
    stroke_through([body.left_ankle, body.left_knee, body.left_hip, hips,
                    body.right_hip, body.right_knee, body.right_ankle], 16)
    f.no_stroke()
    f.fill(20, 20, 20, 210)
    f.circle(body.nose.x, body.nose.y, 44)
    f.fill("crimson")
    f.square(560, 400, 36, 4)


def draw():
    global costume
    for name, button in buttons.items():
        if button.clicked():
            costume = name
    source = cam if cam is not None and cam.is_ready() else still
    body = ml.pose(source)
    if body is None:
        f.background("black")
        return
    if costume == "Warli":
        warli(body)
    elif costume == "Robot":
        robot(body)
    else:
        brush(body)


f.run(fps=24)
