"""Make the two sample drawings for the cut-out puppet examples (S-321): hero.png and friend.png.

The puppet examples need a character drawn on paper, as a learner would draw one and photograph it. Examples are
original (D-026), so the drawings are made here, with funground itself: a felt-pen outline that wobbles a little, crayon
colours, on paper that is not quite white and not quite even. The joints are known because the drawing is built from
them; the script prints each drawing's JOINTS line, which the examples carry.

Run it from the repository root with the venv's Python:
    .venv/Scripts/python.exe tools/make_puppet_drawings.py
It writes examples/gallery/models/data/hero.png and friend.png. Run it again only to change the drawings; the gallery's
goldens follow from them.
"""
from __future__ import annotations

import math
from pathlib import Path

import funground as f

DATA = Path(__file__).resolve().parent.parent / "examples" / "gallery" / "models" / "data"
PAPER = "#f2ede1"
PEN = "#26221f"

# The thirteen joints, in the order the marking sketch asks for them. "left" is the character's own left, which is on
# the right of the picture, as a pose model names a person who faces the camera.
NAMES = ["nose", "left_shoulder", "right_shoulder", "left_elbow", "right_elbow", "left_wrist", "right_wrist",
         "left_hip", "right_hip", "left_knee", "right_knee", "left_ankle", "right_ankle"]

HERO = {"nose": (240, 132), "right_shoulder": (172, 262), "left_shoulder": (308, 262),
        "right_elbow": (112, 318), "left_elbow": (368, 318), "right_wrist": (64, 382), "left_wrist": (416, 382),
        "right_hip": (196, 432), "left_hip": (284, 432), "right_knee": (178, 518), "left_knee": (302, 518),
        "right_ankle": (166, 596), "left_ankle": (314, 596)}

FRIEND = {"nose": (200, 96), "right_shoulder": (178, 196), "left_shoulder": (222, 196),
          "right_elbow": (104, 200), "left_elbow": (296, 200), "right_wrist": (46, 186), "left_wrist": (354, 186),
          "right_hip": (178, 352), "left_hip": (222, 352), "right_knee": (154, 446), "left_knee": (246, 446),
          "right_ankle": (140, 540), "left_ankle": (262, 540)}


def paper(width: int, height: int, seed: int) -> None:
    """Paper as a phone photographs it: off-white, a little darker towards one corner, with faint grain."""
    f.size(width, height)
    f.random_seed(seed)
    f.noise_seed(seed)
    f.background(PAPER)
    f.no_stroke()
    for ring in range(12):                                   # a soft shadow from the top-right corner
        f.fill(0, 0, 0, 3)
        f.circle(width, 0, (12 - ring) * width / 6)
    for _ in range(900):                                     # grain
        f.fill(0, 0, 0, f.random(4, 12))
        f.circle(f.random(width), f.random(height), f.random(0.6, 1.6))


def wobbly(points: list[tuple[float, float]], amount: float, closed: bool) -> list[tuple[float, float]]:
    """The points moved a little each, smoothly along the line, as a hand moves a pen."""
    moved = []
    for n, (x, y) in enumerate(points):
        dx = (f.noise(n * 0.15, 1.0) - 0.5) * 2 * amount
        dy = (f.noise(n * 0.15, 7.0) - 0.5) * 2 * amount
        moved.append((x + dx, y + dy))
    if closed:
        moved.append(moved[0])
    return moved


def oval(cx: float, cy: float, rx: float, ry: float, colour: str, pen: float) -> None:
    """A filled oval with a hand-drawn outline."""
    steps = 72
    ring = [(cx + rx * math.cos(math.tau * n / steps), cy + ry * math.sin(math.tau * n / steps)) for n in range(steps)]
    shape = f.path()
    first, *rest = wobbly(ring, pen * 0.9, closed=True)
    shape.move_to(*first)
    for point in rest:
        shape.line_to(*point)
    shape.close()
    f.fill(colour)
    f.stroke(PEN)
    f.stroke_width(pen)
    f.draw_path(shape)


def limb(points: list[tuple[float, float]], width: float, colour: str, pen: float) -> None:
    """A thick arm or leg through its joints: a dark line, then the crayon colour inside it."""
    for line_width, line_colour in ((width + 2 * pen, PEN), (width, colour)):
        f.no_fill()
        f.stroke(line_colour)
        f.stroke_width(line_width)
        f.stroke_cap("round")
        f.stroke_join("round")
        bent = wobbly(points, pen * 0.4, closed=False)
        f.begin_shape()
        for x, y in bent:
            f.vertex(x, y)
        f.end_shape()


def face(cx: float, cy: float, size: float) -> None:
    f.no_stroke()
    f.fill(PEN)
    f.circle(cx - size * 0.32, cy - size * 0.12, size * 0.16)
    f.circle(cx + size * 0.32, cy - size * 0.12, size * 0.16)
    f.no_fill()
    f.stroke(PEN)
    f.stroke_width(size * 0.07)
    f.arc(cx, cy + size * 0.12, size * 0.8, size * 0.5, 20, 160)


def draw_hero() -> None:
    """A round character with a big head, a striped jumper and short thick legs."""
    j = HERO
    paper(480, 640, seed=21)
    pen = 5
    for side in ("left", "right"):
        limb([j[side + "_hip"], j[side + "_knee"], j[side + "_ankle"]], 40, "#3f6fb5", pen)
        ax, ay = j[side + "_ankle"]
        oval(ax + (10 if side == "left" else -10), ay + 6, 30, 16, "#7a4a2a", pen)          # shoes
    limb([(240, 200), (240, 262)], 44, "#f0c49a", pen)                                         # neck
    oval(240, 352, 92, 108, "#d9483b", pen)                                                    # body
    f.stroke("#f2b134")
    f.stroke_width(9)
    for y in (300, 340, 380):                                                                  # stripes
        f.line(160, y, 320, y)
    for side in ("left", "right"):
        limb([j[side + "_shoulder"], j[side + "_elbow"], j[side + "_wrist"]], 34, "#d9483b", pen)
        wx, wy = j[side + "_wrist"]
        oval(wx, wy, 19, 19, "#f0c49a", pen)                                                   # hands
    oval(240, 150, 86, 82, "#f0c49a", pen)                                                     # head
    oval(240, 84, 70, 26, "#5a3a22", pen)                                                      # hair
    face(240, 150, 60)


def draw_friend() -> None:
    """A thin character: a stick body with a tunic and arms held out."""
    j = FRIEND
    paper(400, 600, seed=34)
    pen = 4
    for side in ("left", "right"):
        limb([j[side + "_hip"], j[side + "_knee"], j[side + "_ankle"]], 12, "#2f8f5b", pen)
    limb([(200, 140), (200, 190)], 14, "#e8b48a", pen)                                         # neck
    dress = f.path()
    dress.move_to(172, 180)
    dress.line_to(228, 180)
    dress.line_to(242, 372)
    dress.line_to(158, 372)
    dress.close()
    f.fill("#8e5bc4")
    f.stroke(PEN)
    f.stroke_width(pen)
    f.draw_path(dress)
    for side in ("left", "right"):
        limb([j[side + "_shoulder"], j[side + "_elbow"], j[side + "_wrist"]], 12, "#8e5bc4", pen)
    oval(200, 110, 46, 50, "#e8b48a", pen)                                                     # head
    face(200, 112, 34)


def main() -> None:
    for name, maker, joints in (("hero", draw_hero, HERO), ("friend", draw_friend, FRIEND)):
        maker()
        f.save(str(DATA / f"{name}.png"))
        print(f"{name.upper()} =", joints)


if __name__ == "__main__":
    main()
