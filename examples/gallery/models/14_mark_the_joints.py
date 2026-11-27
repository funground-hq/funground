"""Mark the joints

Before a drawing can dance, the computer must know where its joints are. Tap the drawing once for each joint, in the
order the sketch asks: the nose, then the shoulders, elbows, wrists, hips, knees and ankles. When all thirteen are
marked, the sketch prints a JOINTS line. Copy it into the mirror puppet, and your drawing is ready to move.

How it works:
- NAMES is the list of the thirteen joints, in the order they are asked for. "left" is the character's own left, so a
  character who faces you has its left shoulder on your right. A pose model names a person's joints the same way, which
  is what lets the puppet copy you arm for arm.
- joints is a dictionary that starts empty. mouse_pressed() adds the next name with the place you tapped, so the next
  name to ask for is NAMES[len(joints)].
- The Undo button takes back the last dot: joints.popitem() removes the newest entry of a dictionary.
- Each dot is drawn with its number, so you can check the order. Lines join the dots that make one bone.
- When the last joint is marked, print() writes the dictionary as one line of code you can copy.

Make it yours:
- Photograph your own drawing on a plain sheet of paper, put the photo in the data folder, and change "data/hero.png" to
  its name. Draw your character standing with its arms a little away from its body: every piece must be clear of the others.
- Mark data/friend.png too, and check your numbers against the FRIEND line in 17_replay_on_any_drawing.py.
- Make the dots bigger if you mark them with a finger on a phone.
"""
import funground as f

NAMES = ["nose", "left_shoulder", "right_shoulder", "left_elbow", "right_elbow", "left_wrist", "right_wrist",
         "left_hip", "right_hip", "left_knee", "right_knee", "left_ankle", "right_ankle"]
BONES = [("left_shoulder", "right_shoulder"), ("left_hip", "right_hip"), ("left_shoulder", "left_hip"),
         ("right_shoulder", "right_hip"), ("left_shoulder", "left_elbow"), ("left_elbow", "left_wrist"),
         ("right_shoulder", "right_elbow"), ("right_elbow", "right_wrist"), ("left_hip", "left_knee"),
         ("left_knee", "left_ankle"), ("right_hip", "right_knee"), ("right_knee", "right_ankle")]

drawing = f.load_image("data/hero.png")
joints = {}
undo = None


def setup():
    global undo
    f.size(drawing.width, drawing.height + 60)
    undo = f.create_button("Undo")


def mouse_pressed():
    if len(joints) < len(NAMES) and f.mouse_y < drawing.height:
        joints[NAMES[len(joints)]] = (round(f.mouse_x), round(f.mouse_y))
        if len(joints) == len(NAMES):
            print("JOINTS =", joints)


def draw():
    if undo.clicked() and joints:
        joints.popitem()
    f.background("white")
    f.image(drawing, 0, 0)
    f.stroke("deepskyblue")
    f.stroke_width(3)
    for a, b in BONES:
        if a in joints and b in joints:
            f.line(*joints[a], *joints[b])
    f.text_size(14)
    f.text_align("center", "center")
    for number, (x, y) in enumerate(joints.values(), start=1):
        f.no_stroke()
        f.fill("crimson")
        f.circle(x, y, 22)
        f.fill("white")
        f.text(str(number), x, y)
    f.fill("black")
    f.text_size(20)
    if len(joints) < len(NAMES):
        name = NAMES[len(joints)]
        side = "  (its left is on your right)" if name.startswith("left") else ""
        f.text(f"{len(joints) + 1} of 13: tap the {name.replace('_', ' ')}{side}", f.width / 2, f.height - 30)
    else:
        f.text("Done: copy the JOINTS line printed below", f.width / 2, f.height - 30)


f.run(fps=30)
