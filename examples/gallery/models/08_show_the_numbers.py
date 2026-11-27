"""Show the numbers

The angle at each elbow and knee, written beside the joint. It also counts squats and draws the knee angle as a graph over time. The picture becomes a measuring tool. This is a teaching tool, not accurate enough for medical or sports decisions. With no camera, it uses a photo, so it still works. It needs the models library, which is a separate install: funground-ml.

How it works:
- MEASURED lists four joints. Each entry names three points: the joint in the middle and its two neighbours. For the left elbow these are the shoulder, the elbow and the wrist.
- angle_at(a, b, c) makes the arrow from b to a and the arrow from b to c, then asks for the turn between them. A straight arm gives 180 degrees, a fully bent arm a small number. abs removes the sign.
- knee is the average of the two knee angles. Standing straight gives about 175 and a deep squat gives less than 100. A squat is counted when knee first drops below 100 and then rises above 160. The variable is_down remembers the drop. With one threshold, a small wobble around it would be counted many times.
- history keeps the last 200 knee angles, and del history[:-200] throws away everything older. f.map_range turns an angle between 40 and 180 into a height between 470 and 400, and each frame moves 3 pixels to the right.
- The camera sees a flat picture, so these are angles as they look on the screen. For a true knee angle, stand side-on to the camera, so the leg bends in the plane of the picture. Compare a slow squat with a fast one: the slow one makes a wide dip.

Make it yours:
- Change 100 to 120 to count shallower squats.
- Measure the shoulder: add ("left_hip", "left_shoulder", "left_elbow") to MEASURED.
- Save the graph as numbers. Add print(round(knee)) and copy the output into a spreadsheet.
- Ask two friends to squat at different speeds and compare their graphs.
"""
import funground as f
from funground import camera, ml

BONES = [("left_shoulder", "right_shoulder"), ("left_shoulder", "left_elbow"), ("left_elbow", "left_wrist"),
         ("right_shoulder", "right_elbow"), ("right_elbow", "right_wrist"), ("left_shoulder", "left_hip"),
         ("right_shoulder", "right_hip"), ("left_hip", "right_hip"), ("left_hip", "left_knee"),
         ("left_knee", "left_ankle"), ("right_hip", "right_knee"), ("right_knee", "right_ankle")]
MEASURED = [("left_shoulder", "left_elbow", "left_wrist"), ("right_shoulder", "right_elbow", "right_wrist"),
            ("left_hip", "left_knee", "left_ankle"), ("right_hip", "right_knee", "right_ankle")]

still = f.load_image("data/standing_woman_640.jpg")      # used when there is no camera
still.resize(320, 480)
cam = None
history = []                                   # the knee angle, frame after frame
squats = 0
is_down = False


def setup():
    global cam
    f.size(640, 480)
    try:
        cam = camera.open()
        cam.start(640, 480)
    except RuntimeError:
        cam = None


def angle_at(a, b, c):
    """The angle at b, between the line to a and the line to c: 0 to 180 degrees."""
    return abs((a - b).angle_between(c - b))


def draw():
    global squats, is_down
    source = cam if cam is not None and cam.is_ready() else still
    f.background("black")
    f.image(source, 0, 0)
    body = ml.pose(source)
    if body is None:
        return
    f.no_fill()
    f.stroke("lime")
    f.stroke_width(3)
    for first, second in BONES:
        a, b = body.points[first], body.points[second]
        f.line(a.x, a.y, b.x, b.y)
    f.no_stroke()
    f.text_size(18)
    for first, middle, last in MEASURED:
        a, b, c = body.points[first], body.points[middle], body.points[last]
        angle = angle_at(a, b, c)
        x = b.x - 62 if middle.startswith("right") else b.x + 10   # outside the body, so the two knees don't overlap
        f.fill("black")
        f.rect(x, b.y - 12, 52, 24, 6)
        f.fill("gold")
        f.text(str(round(angle)) + "°", x + 6, b.y - 10)
    knee = (angle_at(body.left_hip, body.left_knee, body.left_ankle)
            + angle_at(body.right_hip, body.right_knee, body.right_ankle)) / 2
    if knee < 100:
        is_down = True
    if knee > 160 and is_down:
        is_down = False
        squats += 1
    f.fill("white")
    f.text_size(28)
    f.text("Squats: " + str(squats), 340, 16)
    f.text_size(18)
    f.text("Knee angle: " + str(round(knee)) + "°", 340, 56)
    history.append(knee)
    del history[:-200]
    f.fill(0, 0, 0, 150)
    f.rect(0, 390, 640, 90)                    # a dark strip, so the graph can be read over the photo
    f.no_fill()
    f.stroke("gold")
    f.stroke_width(2)
    for i in range(1, len(history)):
        f.line(20 + (i - 1) * 3, f.map_range(history[i - 1], 40, 180, 470, 400),
               20 + i * 3, f.map_range(history[i], 40, 180, 470, 400))


f.run(fps=24)
