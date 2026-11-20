"""Go live

A green stick figure that follows you. The computer looks at the camera, finds your body, and the sketch joins the points it found. Raise your left hand and the gold dot rises. With no camera, it uses a photo, so it still works. It needs the models library, which is a separate install: funground-ml.

How it works:
- Every pose sketch has the same three steps: get a picture, ask for the body in it, and draw with the 33 points you get back. Only the third step changes from one project to the next.
- The first line of draw() chooses the picture for this frame: the camera if it has a frame ready, the photo if not. cam.is_ready() is false for the first moments, before the first frame arrives.
- ml.pose(source) gives a body, or None when it sees no one. Always check for None before you use the body. Here the sketch writes a hint and leaves draw() early with return.
- BONES is a list of pairs of point names. The loop looks up both points of each pair and draws a line between them. Twelve pairs make the figure. Tick All 33 points and MORE_BONES joins in (the face, the hands and the feet), with a dot on every point.
- The gold and blue dots mark your left and right wrists. The camera is mirrored, but left is your own left: raise your left hand and the gold dot rises.
- f.run(fps=24) asks for 24 frames a second. Finding a body is real work for the computer, and 24 is smooth enough.

Make it yours:
- Hide the camera picture by deleting the f.image(source, 0, 0) line. Only the figure remains.
- Tick All 33 points and wave. The fingers and toes wobble more than the elbows: they are small, and the model is less sure of them.
- Show how sure the model is: f.text(round(body.score, 2), 20, 440).
- Walk half out of the picture and watch what the model does with the points it cannot see. It guesses them.
"""
import funground as f
from funground import camera, ml

BONES = [("left_shoulder", "right_shoulder"), ("left_shoulder", "left_elbow"), ("left_elbow", "left_wrist"),
         ("right_shoulder", "right_elbow"), ("right_elbow", "right_wrist"), ("left_shoulder", "left_hip"),
         ("right_shoulder", "right_hip"), ("left_hip", "right_hip"), ("left_hip", "left_knee"),
         ("left_knee", "left_ankle"), ("right_hip", "right_knee"), ("right_knee", "right_ankle")]
MORE_BONES = [("nose", "left_eye_inner"), ("left_eye_inner", "left_eye"), ("left_eye", "left_eye_outer"),
              ("left_eye_outer", "left_ear"), ("nose", "right_eye_inner"), ("right_eye_inner", "right_eye"),
              ("right_eye", "right_eye_outer"), ("right_eye_outer", "right_ear"), ("mouth_left", "mouth_right"),
              ("left_wrist", "left_thumb"), ("left_wrist", "left_index"), ("left_wrist", "left_pinky"),
              ("left_index", "left_pinky"), ("right_wrist", "right_thumb"), ("right_wrist", "right_index"),
              ("right_wrist", "right_pinky"), ("right_index", "right_pinky"), ("left_ankle", "left_heel"),
              ("left_heel", "left_foot_index"), ("left_ankle", "left_foot_index"), ("right_ankle", "right_heel"),
              ("right_heel", "right_foot_index"), ("right_ankle", "right_foot_index")]   # the face, the hands and the feet

still = f.load_image("data/standing_woman_640.jpg")      # used when there is no camera
still.resize(320, 480)
cam = None
all_points = None


def setup():
    global cam, all_points
    f.size(640, 480)
    all_points = f.create_checkbox("All 33 points")
    try:
        cam = camera.open()
        cam.start(640, 480)
    except RuntimeError:
        cam = None


def draw():
    source = cam if cam is not None and cam.is_ready() else still      # the pattern
    f.background("black")
    f.image(source, 0, 0)
    body = ml.pose(source)
    if body is None:
        f.fill("white")
        f.text("Step back until the camera can see all of you", 20, 20)
        return
    f.no_fill()
    f.stroke("lime")
    f.stroke_width(4)
    f.stroke_cap("round")
    every = all_points.checked()
    for first, second in BONES + MORE_BONES if every else BONES:
        a, b = body.points[first], body.points[second]
        f.line(a.x, a.y, b.x, b.y)
    if not every:
        f.circle(body.nose.x, body.nose.y, 24)          # with all 33 points the face is drawn instead
    f.no_stroke()
    if every:
        f.fill("white")
        for p in body.points.values():
            f.circle(p.x, p.y, 5)
    f.fill("gold")
    f.circle(body.left_wrist.x, body.left_wrist.y, 16)
    f.fill("deepskyblue")
    f.circle(body.right_wrist.x, body.right_wrist.y, 16)


f.run(fps=24)
