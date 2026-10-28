"""Spike S-227, question (b): cut yourself out, then drag the outline's points to correct it.

Drag a red point. The photo is drawn only inside the outline, in front of a new background.
Change SCENE to "plain_wall" or "striped_wall" to see the other photos.
"""
import funground as f
from cutout import mask_from_picture, outline_points, tidy

SCENE = "busy_background"
photo = f.load_image(f"scenes/{SCENE}_person.jpg")
empty = f.load_image(f"scenes/{SCENE}_empty.jpg")
points = []                                    # the outline: a list of (x, y)
grabbed = None                                 # the point being dragged


def setup():
    global points
    f.size(640, 480)
    me = photo.copy()
    me.remove_background(empty, tolerance=30)                  # what S-218 gives
    points = outline_points(tidy(mask_from_picture(me)), 80)   # tidy it, then take the outline


def mouse_pressed():
    global grabbed
    grabbed = min(range(len(points)), key=lambda i: (points[i][0] - f.mouse_x) ** 2 + (points[i][1] - f.mouse_y) ** 2)


def mouse_dragged():
    if grabbed is not None:
        points[grabbed] = (f.mouse_x, f.mouse_y)


def mouse_released():
    global grabbed
    grabbed = None


def draw():
    f.background(250, 160, 90)                                 # the new background
    f.no_stroke()
    f.fill(255, 220, 120)
    f.circle(500, 110, 120)
    outline = f.path().polygon(points)
    with f.saved_state():
        f.clip(outline)                                        # draw only inside the outline
        f.image(photo, 0, 0)
    f.no_fill()
    f.stroke("yellow")
    f.draw_path(outline)
    f.no_stroke()
    f.fill("red")
    for x, y in points:
        f.circle(x, y, 7)


f.run()
