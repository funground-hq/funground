"""Mark the joints

Before a drawing can dance, the computer must know where its joints are. Tap the drawing once for each joint, in the
order the sketch asks: the nose, then the shoulders, elbows, wrists, hips, knees and ankles. Tap a dot to pick it up and
tap again to put it down somewhere better. When all thirteen are marked, press Save: the puppet sketches read the
joints from the file it writes, and your drawing is ready to move. It works with a finger on a phone too.

How it works:
- This sketch has a second file, puppet.py, beside it. load_drawing() opens your own drawing, my_drawing.png, when there
  is one, and data/hero.png until then. Its name, "hero" or "my_drawing", names the file the joints are saved in.
- NAMES is the list of the thirteen joints, in the order they are asked for. "left" is the character's own left, so a
  character who faces you has its left shoulder on your right. A pose model names a person's joints the same way, which
  is what lets the puppet copy you arm for arm.
- joints is a dictionary that starts empty. mouse_pressed() adds the next name with the place you tapped, so the next
  name to ask for is NAMES[len(joints)].
- A finger hides the spot it taps, so a dot is easy to put a little wrong. A tap close to a dot (nearer than REACH)
  picks it up instead: held remembers its name, and the next tap moves it there. Tapping is all it needs, so it works on
  a phone, where dragging a finger would move the page instead.
- The Undo button takes back the last dot: joints.popitem() removes the newest entry of a dictionary.
- Save writes the dictionary into hero_joints.json (or my_drawing_joints.json) with json.dump(). In Play the file shows
  up under the canvas: press Keep to put it in My files, where the puppet sketches find it. On your computer it goes in
  the folder you ran the sketch from. Save also prints the JOINTS line, which you can paste into a sketch instead.

Make it yours:
- Mark your own character. Draw it standing with its arms a little away from its body (every piece must be clear of the
  others) on a plain sheet of paper and take a photo. In Play: open My files, press Add file, choose the photo, then
  Rename it to my_drawing. On your computer: put it beside this sketch as my_drawing.png. Mark it, Save (and Keep), then
  run 15_mirror_puppet.py: it opens my_drawing too.
- Mark data/friend.png: change "data/hero.png" to "data/friend.png" and check your numbers against the FRIEND line in
  17_replay_on_any_drawing.py.
- Make REACH bigger if picking up a dot is hard with your finger, or smaller if the joints are close together.
"""
import json

import funground as f
from puppet import load_drawing

NAMES = ["nose", "left_shoulder", "right_shoulder", "left_elbow", "right_elbow", "left_wrist", "right_wrist",
         "left_hip", "right_hip", "left_knee", "right_knee", "left_ankle", "right_ankle"]
BONES = [("left_shoulder", "right_shoulder"), ("left_hip", "right_hip"), ("left_shoulder", "left_hip"),
         ("right_shoulder", "right_hip"), ("left_shoulder", "left_elbow"), ("left_elbow", "left_wrist"),
         ("right_shoulder", "right_elbow"), ("right_elbow", "right_wrist"), ("left_hip", "left_knee"),
         ("left_knee", "left_ankle"), ("right_hip", "right_knee"), ("right_knee", "right_ankle")]
DOT = 30                           # how big a dot is drawn, big enough to see beside a finger
REACH = 24                         # a tap nearer than this to a dot picks it up

drawing, name = load_drawing("data/hero.png")
joints = {}
held = None                        # the name of the dot picked up, or None
undo = None
save = None


def setup():
    global undo, save
    f.size(drawing.width, drawing.height + 60)
    undo = f.create_button("Undo")
    save = f.create_button("Save")


def nearest_dot():
    """The name of the dot nearest the tap, if the tap is within REACH of it, else None."""
    tap = f.Vector(f.mouse_x, f.mouse_y)
    for joint, (x, y) in joints.items():
        if tap.dist(f.Vector(x, y)) < REACH:
            return joint
    return None


def mouse_pressed():
    global held
    if f.mouse_y >= drawing.height:
        return                     # below the drawing: not a joint
    place = (round(f.mouse_x), round(f.mouse_y))
    if held is not None:
        joints[held] = place       # put the dot that was picked up down here
        held = None
    elif nearest_dot() is not None:
        held = nearest_dot()       # pick it up: the next tap says where it goes
    elif len(joints) < len(NAMES):
        joints[NAMES[len(joints)]] = place


def draw():
    global held
    if undo.clicked() and joints:
        joints.popitem()
        held = None
    if save.clicked() and len(joints) == len(NAMES):
        with open(name + "_joints.json", "w") as file:
            json.dump(joints, file)
        print("JOINTS =", joints)
    f.background("white")
    f.image(drawing, 0, 0)
    f.stroke("deepskyblue")
    f.stroke_width(3)
    for a, b in BONES:
        if a in joints and b in joints:
            f.line(*joints[a], *joints[b])
    f.text_size(16)
    f.text_align("center", "center")
    for number, (joint, (x, y)) in enumerate(joints.items(), start=1):
        f.no_stroke()
        f.fill("orange" if joint == held else "crimson")
        f.circle(x, y, DOT)
        f.fill("white")
        f.text(str(number), x, y)
    f.fill("black")
    f.text_size(20)
    if held is not None:
        f.text(f"Tap where the {held.replace('_', ' ')} goes", f.width / 2, f.height - 30)
    elif len(joints) < len(NAMES):
        joint = NAMES[len(joints)]
        side = "  (its left is on your right)" if joint.startswith("left") else ""
        f.text(f"{len(joints) + 1} of 13: tap the {joint.replace('_', ' ')}{side}", f.width / 2, f.height - 30)
    else:
        f.text("All 13 marked: tap a dot to move it, or press Save", f.width / 2, f.height - 30)


f.run(fps=30)
