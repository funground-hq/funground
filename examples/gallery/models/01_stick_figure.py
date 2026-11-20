"""A stick figure from your own photo

A photograph with a green stick figure on it, and the same stick figure alone beside it. The computer finds the body,
and the sketch joins the points it found. Press the button to keep the stick figure by itself as a picture. It uses
your own photo when you give it one, and a photograph of Mahatma Gandhi arriving in England in 1931 until then. It
needs the models library, which is a separate install: funground-ml.

How it works:
- The sketch tries my_photo.jpg, my_photo.png and my_photo.jpeg in turn. When there is no file of those names, it opens the Gandhi photograph instead.
- ml.pose(photo) looks for a body in a picture. It gives a body with 33 named points, or None if no one is there. The first run downloads the pose model (once) into a models folder beside the sketch.
- draw() asks for the body until it has one (in Play the answer comes a few frames later, while the model starts). Then draw_figure() draws the figure once, on a see-through picture the size of the photo (f.create_graphics). Each point is in the photo's own pixels, so the figure lines up with the body.
- BONES is a list of pairs of names. The loop looks each name up in body.points and draws a line between the two points.
- draw() shows the photo with the figure over it on the left, and the figure alone on the right. f.image(picture, x, y, w, h) scales both to the canvas.
- The button saves only the figure's picture, so stick_figure.png has the figure on a see-through background and no photo. In Play it shows up under the canvas: press Keep to put it in My files. On your computer it goes in the folder you ran the sketch from.

Make it yours:
- Use your own photo. In Play: open My files, press Add file and choose a photo of one whole person, then press Rename beside it and call it my_photo (the .jpg or .png ending stays). On your computer: put the photo beside this sketch and call it my_photo.jpg or my_photo.png. Run the sketch again.
- Add the ears and the mouth: body.left_ear, body.right_ear, body.mouth_left and body.mouth_right.
- Change figure.stroke("lime") and the line's thickness to give the figure a new look.
- Draw a small circle at every point in body.points.values() instead of lines.
- Give the right half a colour of its own: change f.fill(30) before the rect.
"""
import funground as f
from funground import ml

HEIGHT = 480                       # the canvas is this tall; the photo is scaled to fit it
BONES = [("left_shoulder", "right_shoulder"), ("left_shoulder", "left_elbow"), ("left_elbow", "left_wrist"),
         ("right_shoulder", "right_elbow"), ("right_elbow", "right_wrist"), ("left_shoulder", "left_hip"),
         ("right_shoulder", "right_hip"), ("left_hip", "right_hip"), ("left_hip", "left_knee"),
         ("left_knee", "left_ankle"), ("right_hip", "right_knee"), ("right_knee", "right_ankle")]

photo = None
for name in ["my_photo.jpg", "my_photo.png", "my_photo.jpeg"]:
    try:
        photo = f.load_image(name)
        break                      # found one: stop looking
    except FileNotFoundError:
        pass                       # not this one: try the next name
if photo is None:
    print("No my_photo yet, so this is the Gandhi photograph. Add your own photo and call it my_photo.jpg or my_photo.png.")
    photo = f.load_image("data/gandhi_london_rain.jpg")

figure = None
found = False                      # True once the figure is drawn
save_button = None
half = 0                           # the width of each half of the canvas


def setup():
    global figure, save_button, half
    half = round(photo.width * HEIGHT / photo.height)
    f.size(2 * half, HEIGHT)
    save_button = f.create_button("Save the stick figure")
    figure = f.create_graphics(photo.width, photo.height)


def draw_figure(body):
    figure.stroke("lime")
    figure.stroke_width(photo.height / 100)          # the same look on a small photo and a big one
    figure.stroke_cap("round")
    figure.no_fill()
    for first, second in BONES:
        a, b = body.points[first], body.points[second]
        figure.line(a.x, a.y, b.x, b.y)
    figure.circle(body.nose.x, body.nose.y, photo.height / 20)


def draw():
    global found
    if not found:
        body = ml.pose(photo)
        if body:
            draw_figure(body)
            found = True

    f.image(photo, 0, 0, half, HEIGHT)
    f.image(figure, 0, 0, half, HEIGHT)

    f.no_stroke()
    f.fill(30)                     # a dark paper, so the green figure stands out
    f.rect(half, 0, half, HEIGHT)
    f.image(figure, half, 0, half, HEIGHT)
    if not found:
        f.fill("white")
        f.text("Looking for a body...", half + 20, HEIGHT / 2)

    if save_button.clicked():
        figure.save("stick_figure.png")
        print("Saved stick_figure.png")


f.run()
