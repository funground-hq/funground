"""A stick figure from your own photo

A photograph with a green stick figure on it, and the same stick figure alone beside it. The computer finds the body,
and the sketch joins the points it found. Press the button to keep the stick figure by itself as a picture. It uses
your own photo when you give it one, and a photograph of Mahatma Gandhi arriving in England in 1931 until then. It
needs the models library, which is a separate install: funground-ml.

How it works:
- The sketch tries my_photo.jpg, my_photo.png, my_photo.jpeg and my_photo.svg in turn. A photo opens with f.load_image(); a drawing made in a vector app (.svg) opens with f.load_svg(), and the model looks at it as it is drawn. When there is no file of those names, it opens the Gandhi photograph instead.
- ml.pose(photo) looks for a body in a picture. It gives a body with 33 named points, or None if no one is there. The first run downloads the pose model (once) into a models folder beside the sketch.
- draw() asks for the body until it has one (in Play the answer comes a few frames later, while the model starts). Then draw_figure() draws the figure once, on a see-through picture the size of the photo (f.create_graphics). Each point is in the photo's own pixels, so the figure lines up with the body.
- BONES is a list of pairs of names. The loop looks each name up in body.points and draws a line between the two points. A bone is bright when the model is sure of both ends (body.scores says how sure it is of each point, from 0 to 1) and faint when one end is a guess: in the Gandhi photograph his left arm and leg are hidden behind him, and the model guesses where they are. Tick All 33 points and draw_figure() draws again with MORE_BONES too (the face, the hands and the feet) and a dot on every point the model gives.
- draw() shows the photo with the figure over it on the left, and the figure alone on the right. f.image(picture, x, y, w, h) scales both to the canvas.
- The button saves only the figure's picture, so stick_figure.png has the figure on a see-through background and no photo. In Play it shows up under the canvas: press Keep to put it in My files. On your computer it goes in the folder you ran the sketch from.

Make it yours:
- Use your own photo. In Play: open My files, press Add file and choose a photo of one whole person, then press Rename beside it and call it my_photo (the .jpg or .png ending stays). On your computer: put the photo beside this sketch and call it my_photo.jpg or my_photo.png. Run the sketch again.
- Try a drawing instead of a photo: draw a whole person in a vector app, save it as my_photo.svg and use it as above. The model looks for a real body, so a figure drawn with arms, legs and a head works best.
- Tick All 33 points and look at the hands and feet. Then give them a colour of their own: draw MORE_BONES with another figure.stroke().
- Change "lime" and the line's thickness to give the figure a new look.
- Change SURE to 0.9 and more bones go faint; change it to 0 and every bone is bright.
- Give the right half a colour of its own: change f.fill(30) before the rect.
"""
import funground as f
from funground import ml

HEIGHT = 480                       # the canvas is this tall; the photo is scaled to fit it
SURE = 0.5                         # a point the model is less sure of than this is a guess
BONES = [("left_shoulder", "right_shoulder"), ("left_shoulder", "left_elbow"), ("left_elbow", "left_wrist"),
         ("right_shoulder", "right_elbow"), ("right_elbow", "right_wrist"), ("left_shoulder", "left_hip"),
         ("right_shoulder", "right_hip"), ("left_hip", "right_hip"), ("left_hip", "left_knee"),
         ("left_knee", "left_ankle"), ("right_hip", "right_knee"), ("right_knee", "right_ankle")]
MORE_BONES = [("nose", "left_eye_inner"), ("left_eye_inner", "left_eye"), ("left_eye", "left_eye_outer"),
              ("left_eye_outer", "left_ear"), ("nose", "right_eye_inner"), ("right_eye_inner", "right_eye"),
              ("right_eye", "right_eye_outer"), ("right_eye_outer", "right_ear"), ("mouth_left", "mouth_right"),
              ("left_wrist", "left_thumb"), ("left_wrist", "left_index"), ("left_wrist", "left_pinky"),
              ("left_index", "left_pinky"), ("right_wrist", "right_thumb"), ("right_wrist", "right_index"),
              ("right_wrist", "right_pinky"), ("right_index", "right_pinky"), ("left_ankle", "left_heel"),
              ("left_heel", "left_foot_index"), ("left_ankle", "left_foot_index"), ("right_ankle", "right_heel"),
              ("right_heel", "right_foot_index"), ("right_ankle", "right_foot_index")]   # the face, the hands and the feet

photo = None
for name in ["my_photo.jpg", "my_photo.png", "my_photo.jpeg", "my_photo.svg"]:
    try:
        if name.endswith(".svg"):
            photo = f.load_svg(name)       # a drawing of shapes
        else:
            photo = f.load_image(name)     # a photo
        break                      # found one: stop looking
    except FileNotFoundError:
        pass                       # not this one: try the next name
if photo is None:
    print("No my_photo yet, so this is the Gandhi photograph. Add your own photo and call it my_photo.jpg or my_photo.png.")
    photo = f.load_image("data/gandhi_london_rain.jpg")

figure = None
found = False                      # True once the figure is drawn
save_button = None
all_points = None                  # the box that adds the face, the hands and the feet
body = None
drawn_all = None                   # what the figure was last drawn with, so it is drawn again only when the box changes
half = 0                           # the width of each half of the canvas


def setup():
    global figure, save_button, all_points, half
    half = round(photo.width * HEIGHT / photo.height)
    f.size(2 * half, HEIGHT)
    save_button = f.create_button("Save the stick figure")
    all_points = f.create_checkbox("All 33 points")
    figure = f.create_graphics(photo.width, photo.height)


def draw_figure(body, every):
    figure.clear()
    figure.stroke_width(photo.height / 100)          # the same look on a small photo and a big one
    figure.stroke_cap("round")
    figure.no_fill()
    for first, second in BONES + MORE_BONES if every else BONES:
        if body.scores[first] < SURE or body.scores[second] < SURE:
            figure.stroke(0, 255, 0, 90)             # a faint lime: one end is a guess
        else:
            figure.stroke("lime")
        a, b = body.points[first], body.points[second]
        figure.line(a.x, a.y, b.x, b.y)
    figure.stroke("lime")
    if every:
        figure.no_stroke()
        figure.fill("white")
        for p in body.points.values():
            figure.circle(p.x, p.y, photo.height / 120)
    else:
        figure.circle(body.nose.x, body.nose.y, photo.height / 20)


def draw():
    global found, body, drawn_all
    if not found:
        body = ml.pose(photo)
        found = body is not None
    if found and all_points.checked() != drawn_all:
        drawn_all = all_points.checked()
        draw_figure(body, drawn_all)

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
