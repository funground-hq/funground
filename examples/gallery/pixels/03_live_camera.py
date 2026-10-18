"""From pixels to marks, step 3: the live camera

Step 2's dots, drawn from your camera, again and again. Move, and the dots follow. With no camera it keeps using
the photo, so the sketch still works.

How it works:
- The drawing from step 2 moved into draw(), which runs many times a second.
- cam.picture() gives the camera's latest frame as a picture, so the rest of the code does not change at all:
  only the line that chooses the picture is new.
- f.camera() and cam.start() open the camera. If there is none, the try and except keep the photo instead.
- f.run(fps=15) asks for 15 frames a second: the dots are a lot of work, and 15 is plenty.

Make it yours:
- Change CELL while it runs: try 8 for detail or 24 for a bold poster.
- Add f.filter("blur", 1) to the picture before reading it, for smoother dots.
- Save a frame with f.save("dots.png") in key_pressed().
- Use squares, or the photo's own colours, as in the earlier steps.
"""
import funground as f

CELL = 12
WIDTH, HEIGHT = 400, 300
photo = f.load_image("data/photo.jpg")      # used when there is no camera
cam = None


def setup():
    global cam
    f.size(WIDTH, HEIGHT)
    f.no_stroke()
    try:
        cam = f.camera()
        cam.start(WIDTH, HEIGHT)
    except RuntimeError:
        cam = None


def draw():
    picture = cam.picture() if cam is not None and cam.is_ready() else photo
    f.background("white")
    f.fill("black")
    for y in range(0, HEIGHT, CELL):
        for x in range(0, WIDTH, CELL):
            brightness = picture.get(min(x + CELL // 2, WIDTH - 1), min(y + CELL // 2, HEIGHT - 1)).brightness
            f.circle(x + CELL / 2, y + CELL / 2, f.map_range(brightness, 0, 100, CELL, 0))


f.run(fps=15)
