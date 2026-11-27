"""Leave trails

The last 20 poses stay on screen, the older ones fainter, like one photographic plate with many moments on it. In the 1880s Eadweard Muybridge and Étienne-Jules Marey photographed people and animals many times a second to see how they move. Marey put all the moments on one plate, so a walking man became a row of overlapping figures. This sketch does the same with stick figures. With no camera, it uses a photo, so it still works. It needs the models library, which is a separate install: funground-ml.

How it works:
- trail is a list of poses. Each entry is body.points, the dictionary of all 33 points at one moment.
- f.frame_count % EVERY == 0 is true on every third frame. Keeping every frame would pack the figures too close together to read. At 24 frames a second, 20 kept poses cover two and a half seconds. del trail[:-KEEP] removes everything except the last 20.
- The fourth number in f.stroke(255, 255, 255, ...) is how solid the line is, from 0 to 255. Older poses have a smaller i, so they are fainter. The newest pose is drawn in gold and thicker.
- The camera picture is not drawn at all. The black background is what makes the white figures look like an old photographic plate.
- The Save button writes the picture with f.save("trails.pdf"). A PDF holds lines, not pixels, so the poster stays sharp at any print size. For a good poster, choose one clear movement, such as a jump or one step of a dance, and cross the camera's view from one side to the other. Press Clear, perform, and press Save at the end.

Make it yours:
- Change EVERY to 6 for figures that are further apart, or KEEP to 40 for a longer memory.
- Colour the figures by age with f.hsb: f.stroke(f.hsb(i * 12, 80, 100)).
- Draw only one point's path, such as the right wrist, as a single curved line. This is how sports coaches study a throw.
- Use a white background and black figures for a poster that uses less ink.
"""
import funground as f
from funground import camera, ml

BONES = [("left_shoulder", "right_shoulder"), ("left_shoulder", "left_elbow"), ("left_elbow", "left_wrist"),
         ("right_shoulder", "right_elbow"), ("right_elbow", "right_wrist"), ("left_shoulder", "left_hip"),
         ("right_shoulder", "right_hip"), ("left_hip", "right_hip"), ("left_hip", "left_knee"),
         ("left_knee", "left_ankle"), ("right_hip", "right_knee"), ("right_knee", "right_ankle")]
KEEP = 20                                      # how many poses stay on screen
EVERY = 3                                      # keep one pose out of every 3 frames

still = f.load_image("data/standing_woman_640.jpg")      # used when there is no camera
still.resize(320, 480)
cam = None
trail = []                                     # the kept poses, oldest first
save_button = None
clear_button = None


def setup():
    global cam, save_button, clear_button
    f.size(640, 480)
    save_button = f.create_button("Save the poster")
    clear_button = f.create_button("Clear")
    try:
        cam = camera.open()
        cam.start(640, 480)
    except RuntimeError:
        cam = None


def draw():
    source = cam if cam is not None and cam.is_ready() else still
    f.background("black")
    body = ml.pose(source)
    if body and f.frame_count % EVERY == 0:
        trail.append(body.points)
        del trail[:-KEEP]
    f.no_fill()
    f.stroke_cap("round")
    for i, points in enumerate(trail):
        newest = i == len(trail) - 1
        f.stroke_width(4 if newest else 2)
        if newest:
            f.stroke("gold")
        else:
            f.stroke(255, 255, 255, 40 + 180 * i // len(trail))
        for first, second in BONES:
            a, b = points[first], points[second]
            f.line(a.x, a.y, b.x, b.y)
        f.circle(points["nose"].x, points["nose"].y, 22)
    if save_button.clicked():
        f.save("trails.pdf")
    if clear_button.clicked():
        trail.clear()


f.run(fps=24)
