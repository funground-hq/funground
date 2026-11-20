"""A cut-out puppet: one drawing, thirteen marked joints, ten bones that turn.

This is not an example of its own. It is a second file that the puppet examples import with
from puppet import Puppet, bone_angles, ease. Keep it in the same folder as your sketch. In Play it opens as a second tab.

How it works:
- bone_angles(points) takes a dictionary of named points and gives ten directions in degrees: the body, the head and
  the eight arm and leg bones. It works on the joints you marked on your drawing and on the points of a real body alike.
- A Puppet remembers the directions as you drew them (rest). To pose it, each piece is turned by the difference
  between the direction it should point in and the direction it was drawn in.
- box(a, b, half) gives the four corners of a box around the line from a to b. The drawing is clipped to that box,
  so only that piece of it shows: one bone of the puppet.
- part() moves, turns and draws one clipped piece. The second piece of an arm hangs from the end of the first.
- Pieces are drawn legs first, then the body, then the arms, then the head, so later pieces cover earlier ones.
- Only directions are copied, never lengths. The puppet keeps its own shape however long your arms are.
- made_up_dance() makes a short dance from sine waves, for when you have not recorded one of your own yet.
"""
import math

import funground as f

BONES = {   # bone: (the joint it starts at, the joint it ends at)
    "left_upper_arm": ("left_shoulder", "left_elbow"), "left_forearm": ("left_elbow", "left_wrist"),
    "right_upper_arm": ("right_shoulder", "right_elbow"), "right_forearm": ("right_elbow", "right_wrist"),
    "left_thigh": ("left_hip", "left_knee"), "left_shin": ("left_knee", "left_ankle"),
    "right_thigh": ("right_hip", "right_knee"), "right_shin": ("right_knee", "right_ankle"),
}


def middle(a, b):
    return (a + b) / 2


def bone_angles(points):
    """Ten directions in degrees from a dictionary of named points. 0 points right, 90 points down."""
    hips = middle(points["left_hip"], points["right_hip"])
    neck = middle(points["left_shoulder"], points["right_shoulder"])
    angles = {"body": (neck - hips).heading(), "head": (points["nose"] - neck).heading()}
    for bone, (start, end) in BONES.items():
        angles[bone] = (points[end] - points[start]).heading()
    return angles


def ease(old, new, amount=0.5):
    """Move an angle part of the way towards a new one, the short way round the circle."""
    return old + ((new - old + 180) % 360 - 180) * amount


def box(a, b, half, extra=0):
    """The four corners of a box around the line from a to b, half wide on each side, longer by extra at b."""
    along = (b - a).normalize()
    across = f.Vector(-along.y, along.x) * half
    start = a - along * half
    end = b + along * (half + extra)
    return [[p.x, p.y] for p in (start + across, end + across, end - across, start - across)]


class Puppet:
    def __init__(self, drawing, joints, arm=26, leg=30, head=60, grow=1.3):
        self.drawing = drawing
        self.joints = {name: f.Vector(x, y) for name, (x, y) in joints.items()}
        self.rest = bone_angles(self.joints)        # the bone directions as drawn
        self.arm, self.leg, self.head, self.grow = arm, leg, head, grow

    def part(self, shape, pivot, where, degrees, zoom):
        """Draw the piece of the drawing inside shape, moved so pivot lands on where, and turned."""
        with f.saved_state():
            f.translate(where.x, where.y)
            f.rotate(degrees)
            f.scale(zoom)
            f.translate(-pivot.x, -pivot.y)
            f.clip(shape)
            f.image(self.drawing, 0, 0)

    def limb(self, first, second, third, upper, lower, half, where, turn, zoom):
        """Draw a two-bone limb, such as shoulder, elbow, wrist. where is the screen place of the first joint."""
        j = self.joints
        reach = (j[second] - j[first]) * zoom
        reach.rotate(turn[upper])
        self.part(f.path().polygon(box(j[first], j[second], half)), j[first], where, turn[upper], zoom)
        self.part(f.path().polygon(box(j[second], j[third], half, extra=half * 1.5)), j[second], where + reach,
                  turn[lower], zoom)

    def draw(self, angles, x, y, zoom=1.0):
        """Draw the puppet with the middle of its hips at x, y, and its bones pointing along angles."""
        j = self.joints
        turn = {bone: angles[bone] - self.rest[bone] for bone in self.rest}
        hips = middle(j["left_hip"], j["right_hip"])
        neck = middle(j["left_shoulder"], j["right_shoulder"])
        here = f.Vector(x, y)

        def placed(point):                           # where a point of the body lands on the screen
            offset = (point - hips) * zoom
            offset.rotate(turn["body"])
            return here + offset

        for side in ("left", "right"):
            self.limb(side + "_hip", side + "_knee", side + "_ankle", side + "_thigh", side + "_shin",
                      self.leg, placed(j[side + "_hip"]), turn, zoom)
        centre = middle(hips, neck)
        corners = [centre + (j[name] - centre) * self.grow
                   for name in ("left_shoulder", "right_shoulder", "right_hip", "left_hip")]
        self.part(f.path().polygon([[p.x, p.y] for p in corners]), hips, here, turn["body"], zoom)
        for side in ("left", "right"):
            self.limb(side + "_shoulder", side + "_elbow", side + "_wrist", side + "_upper_arm", side + "_forearm",
                      self.arm, placed(j[side + "_shoulder"]), turn, zoom)
        self.part(f.path().circle(j["nose"].x, j["nose"].y, self.head * 2), neck, placed(neck), turn["head"], zoom)


def made_up_dance(count=48):
    """A dance of count frames, made with sine waves: the arms wave up and down, the legs step, the body sways. Each frame is a
    dictionary of the ten directions, just like a recorded one."""
    frames = []
    for n in range(count):
        beat = math.sin(math.tau * n / count)
        twice = math.sin(2 * math.tau * n / count)
        frames.append({
            "body": round(-90 + 8 * beat), "head": round(-90 + 14 * beat),
            "right_upper_arm": round(180 + 50 * twice), "right_forearm": round(180 + 80 * twice),
            "left_upper_arm": round(-50 * twice), "left_forearm": round(-80 * twice),
            "right_thigh": round(100 + 12 * beat), "right_shin": round(95 - 10 * beat),
            "left_thigh": round(80 + 12 * beat), "left_shin": round(85 - 10 * beat),
        })
    return frames
