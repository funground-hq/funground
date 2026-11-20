"""Record a dance

Dance in front of the camera while the puppet copies you, and the sketch writes your dance down: the ten bone directions
of every frame, as numbers. Save, and the numbers go into a file, dance.json, that the next sketch replays on any
drawing. With no camera, it uses a photo, so it still works, but the dance is a very still one. It needs the models
library, which is a separate install: funground-ml.

How it works:
- This is the mirror puppet with a recorder. Press Record, dance, press Stop, then Save.
- While recording is True, each frame adds one dictionary to the list frames: the ten angles, rounded to whole degrees,
  and the four arm lengths. Twenty-four frames make one second of dance.
- json is the Python library for writing lists and dictionaries as text. json.dump() writes the frames and the frame rate
  into dance.json. Open the file and look: it is only numbers, so it is small, and any drawing can dance it.
- Recording keeps the eased angles, mirrored as the puppet showed them, so the replay looks like what you saw.
- In Play, dance.json appears in My files. On a computer, it is written in the folder the sketch runs in.

Make it yours:
- Record a short dance: two or three seconds of one clear move, done twice, replays best.
- Add a count-in: wait three seconds after Record before the first frame is kept.
- Record at 12 frames a second (fps=12 in f.run, and in the file) and see whether the replay still looks smooth.
"""
import json

import funground as f
from funground import camera, ml
from puppet import Puppet, bone_angles, arm_lengths, ease, mirrored

JOINTS = {"nose": (240, 132), "right_shoulder": (172, 262), "left_shoulder": (308, 262),
          "right_elbow": (112, 318), "left_elbow": (368, 318), "right_wrist": (64, 382), "left_wrist": (416, 382),
          "right_hip": (196, 432), "left_hip": (284, 432), "right_knee": (178, 518), "left_knee": (302, 518),
          "right_ankle": (166, 596), "left_ankle": (314, 596)}
FPS = 24

drawing = f.load_image("data/hero.png")
drawing.remove_color(drawing.get(4, 4), 60, tidy=True)
hero = Puppet(drawing, JOINTS, arm=26, leg=28, head=92, grow=1.3)
angles = dict(hero.rest)
lengths = dict(hero.lengths)
still = f.load_image("data/standing_woman_640.jpg")      # used when there is no camera
still.resize(320, 480)
cam = None
frames = []
recording = False
message = "Press Record and dance"
buttons = {}


def setup():
    global cam
    f.size(900, 480)
    for name in ("Record", "Stop", "Save"):
        buttons[name] = f.create_button(name)
    try:
        cam = camera.open()
        cam.start(320, 240)
    except RuntimeError:
        cam = None


def press_buttons():
    global recording, message
    if buttons["Record"].clicked():
        frames.clear()
        recording = True
    if buttons["Stop"].clicked() and recording:
        recording = False
        message = f"{len(frames)} frames: press Save, or Record again"
    if buttons["Save"].clicked() and frames:
        with open("dance.json", "w") as file:
            json.dump({"fps": FPS, "frames": frames}, file)
        message = f"Saved {len(frames)} frames in dance.json"


def draw():
    press_buttons()
    f.background("oldlace")
    source = cam if cam is not None and cam.is_ready() else still
    f.image(source, 0, 0)
    body = ml.pose(source)
    if body is not None:
        seen, sizes = bone_angles(body.points), arm_lengths(body.points)
        if source is cam:                        # a camera is a mirror: copy the picture, as your reflection would
            seen, sizes = mirrored(seen), mirrored(sizes)
        for bone, angle in seen.items():
            angles[bone] = ease(angles[bone], angle, 0.5)
        for bone, size in sizes.items():
            lengths[bone] += (size - lengths[bone]) * 0.5
    if recording:
        frames.append({"angles": {bone: round(angle) for bone, angle in angles.items()},
                       "lengths": {bone: round(size, 2) for bone, size in lengths.items()}})
    hero.draw(angles, 620, 300, zoom=0.62, lengths=lengths)
    f.no_stroke()
    f.fill("black")
    f.text_size(18)
    f.text_align("left", "top")
    if recording:
        f.fill("crimson")
        f.circle(350, 30, 18)
        f.text(f"Recording: {len(frames) / FPS:.1f} s", 368, 20)
    else:
        f.text(message, 340, 20)


f.run(fps=FPS)
