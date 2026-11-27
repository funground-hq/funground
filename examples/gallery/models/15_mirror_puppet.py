"""Mirror puppet

You move, and a character drawn on paper copies you. The camera finds your body, the sketch measures the direction of
ten of your bones, and the drawing's own bones are turned to point the same way. The drawing is cut into pieces like a
cardboard puppet held together with paper fasteners. With no camera, it uses a photo, so it still works. It needs the
models library, which is a separate install: funground-ml.

How it works:
- This sketch has a second file, puppet.py, beside it. from puppet import Puppet, bone_angles, arm_lengths, ease, mirrored reads it. In Play it
  opens as a second tab; on a computer, keep the two files in the same folder.
- JOINTS is the line 14_mark_the_joints.py printed for the drawing: where its thirteen joints are.
- picture.remove_color(picture.get(4, 4), 60, tidy=True) takes away the paper: every colour close to the corner's colour
  becomes see-through, and tidy keeps only the character.
- bone_angles(body.points) gives the directions of your ten bones, and arm_lengths(body.points) how long your arms
  are for your size, so the puppet reaches as high as you do. A camera shows you as a mirror does: your left arm is on the picture's left, where the
  drawing has its right arm. mirrored() swaps left and right, so the puppet moves as your reflection does. Tick Fingers
  and a second model, ml.hand(), finds one hand: its wrist is more exact, so it takes the place of the nearer wrist.
- ease() moves each angle half of the way towards the new one in each frame, and each length moves half of the way too. A pose model's points jump a little from
  frame to frame, and easing smooths the jumps away.
- hero.draw(angles, 620, 300, zoom=0.62) draws the puppet with its hips at 620, 300, at 62 % of the drawing's size.

Make it yours:
- Draw your own character, mark its joints with 14_mark_the_joints.py and paste your JOINTS line here.
- Change 0.5 in ease() to 0.2 for a slow, floaty puppet, or to 1 for no smoothing at all.
- Make the arm and leg pieces wider or narrower: they are the arm=26 and leg=28 of Puppet(...). Too narrow cuts off the
  outline; too wide takes a bit of the body with each arm.
- Look at the shoulders when you lift your arms. The pieces are cut with straight edges, so a joint shows a small gap or
  a stub. puppet.py is yours to change: try drawing a circle over each joint.
"""
import funground as f
from funground import camera, ml
from puppet import Puppet, bone_angles, arm_lengths, ease, mirrored

JOINTS = {"nose": (240, 132), "right_shoulder": (172, 262), "left_shoulder": (308, 262),
          "right_elbow": (112, 318), "left_elbow": (368, 318), "right_wrist": (64, 382), "left_wrist": (416, 382),
          "right_hip": (196, 432), "left_hip": (284, 432), "right_knee": (178, 518), "left_knee": (302, 518),
          "right_ankle": (166, 596), "left_ankle": (314, 596)}

drawing = f.load_image("data/hero.png")
drawing.remove_color(drawing.get(4, 4), 60, tidy=True)
hero = Puppet(drawing, JOINTS, arm=26, leg=28, head=92, grow=1.3)
angles = dict(hero.rest)                         # start as drawn
lengths = dict(hero.lengths)
still = f.load_image("data/standing_woman_640.jpg")      # used when there is no camera
still.resize(320, 480)
cam = None
fingers = None


def setup():
    global cam, fingers
    f.size(900, 480)
    fingers = f.create_checkbox("Fingers")
    try:
        cam = camera.open()
        cam.start(320, 240)
    except RuntimeError:
        cam = None


def draw():
    f.background("oldlace")
    source = cam if cam is not None and cam.is_ready() else still
    f.image(source, 0, 0)
    body = ml.pose(source)
    if body is not None:
        f.no_stroke()
        f.fill("gold")
        for point in body.points.values():
            f.circle(point.x, point.y, 8)
        points = dict(body.points)
        hand = ml.hand(source) if fingers.checked() else None
        if hand:                                 # give the hand model's wrist to the nearer side
            side = "left" if hand.wrist.dist(points["left_wrist"]) < hand.wrist.dist(points["right_wrist"]) else "right"
            points[side + "_wrist"] = hand.wrist
        seen, sizes = bone_angles(points), arm_lengths(points)
        if source is cam:                        # a camera is a mirror: copy the picture, as your reflection would
            seen, sizes = mirrored(seen), mirrored(sizes)
        for bone, angle in seen.items():
            angles[bone] = ease(angles[bone], angle, 0.5)
        for bone, size in sizes.items():
            lengths[bone] += (size - lengths[bone]) * 0.5
    hero.draw(angles, 620, 300, zoom=0.62, lengths=lengths)


f.run(fps=24)
