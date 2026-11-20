"""Replay on any drawing

The dance you recorded is only numbers: ten directions for each frame. So any drawing with marked joints can dance it.
Here two characters who look nothing alike dance the same dance side by side. It does not need a camera or the models
library. Until you have recorded a dance of your own, they dance one made up from sine waves.

How it works:
- json.load() reads dance.json back into a dictionary: the frame rate and the list of frames. If there is no
  dance.json yet, open() fails with FileNotFoundError, and made_up_dance() from puppet.py makes one instead.
- f.frame_count counts the frames drawn so far. f.frame_count % len(frames) counts 0, 1, 2 ... up to the last frame,
  then starts at 0 again, so the dance loops.
- Each puppet has its own JOINTS, measured on its own drawing, and its own piece sizes. The angles and lengths are
  the same for both, so they move together. frame.get("lengths") is None for the made-up dance: each keeps its own.
- The friend is thin, so its arm and leg pieces are narrow (arm=12, leg=11). Its body piece grows more (grow=1.75)
  because its tunic is wider than the line between its shoulders and hips.

Make it yours:
- Record a dance with 16_record_a_dance.py, then run this again.
- Draw a third character, mark it with 14_mark_the_joints.py, and add it to the line-up.
- Play the friend's dance a quarter of a second behind the hero's: use frames[(f.frame_count - 6) % len(frames)].
- Mirror the friend: give it 180 - angle for every bone, and swap left and right.
"""
import json

import funground as f
from puppet import Puppet, made_up_dance

HERO = {"nose": (240, 132), "right_shoulder": (172, 262), "left_shoulder": (308, 262),
        "right_elbow": (112, 318), "left_elbow": (368, 318), "right_wrist": (64, 382), "left_wrist": (416, 382),
        "right_hip": (196, 432), "left_hip": (284, 432), "right_knee": (178, 518), "left_knee": (302, 518),
        "right_ankle": (166, 596), "left_ankle": (314, 596)}
FRIEND = {"nose": (200, 96), "right_shoulder": (178, 196), "left_shoulder": (222, 196),
          "right_elbow": (104, 200), "left_elbow": (296, 200), "right_wrist": (46, 186), "left_wrist": (354, 186),
          "right_hip": (178, 352), "left_hip": (222, 352), "right_knee": (154, 446), "left_knee": (246, 446),
          "right_ankle": (140, 540), "left_ankle": (262, 540)}

try:
    with open("dance.json") as file:
        dance = json.load(file)
    where = "your dance.json"
except FileNotFoundError:
    dance = {"fps": 24, "frames": made_up_dance()}
    where = "a made-up dance (no dance.json yet)"
frames = dance["frames"]


def cut_out(path):
    picture = f.load_image(path)
    picture.remove_color(picture.get(4, 4), 60, tidy=True)
    return picture


hero = Puppet(cut_out("data/hero.png"), HERO, arm=26, leg=28, head=92, grow=1.3)
friend = Puppet(cut_out("data/friend.png"), FRIEND, arm=12, leg=11, head=66, grow=1.75)


def setup():
    f.size(900, 480)


def draw():
    f.background("oldlace")
    frame = frames[f.frame_count % len(frames)]
    hero.draw(frame["angles"], 280, 300, zoom=0.62, lengths=frame.get("lengths"))
    friend.draw(frame["angles"], 640, 300, zoom=0.62, lengths=frame.get("lengths"))
    f.fill("black")
    f.text_size(16)
    f.text_align("left", "top")
    f.text(f"Frame {f.frame_count % len(frames) + 1} of {len(frames)} from {where}", 16, 16)


f.run(fps=dance["fps"])
