"""From pixels to marks, step 4: grid and contrast

Now the mouse holds the controls. Left and right change the size of the grid, from fine to coarse. Up and down
change the contrast: at the top the dots are bold, with only big dots and paper, and at the bottom they are gentle
and grey-looking.

How it works:
- f.map_range() turns the mouse's x into a cell size from 6 to 30 pixels. round() keeps it a whole number.
- Contrast is a power: brightness from 0 to 1, raised to a power from 0.5 to 3. A power above 1 pushes middle
  greys towards dark, so more dots grow big; below 1 pushes them towards light.
- The two numbers are shown at the top, so you can write down the settings you like.
- With no camera the photo is used, as in step 3.

Make it yours:
- Swap the mouse directions, so up and down change the grid.
- Use the arrow keys instead of the mouse, with key_pressed().
- Show the settings only while a key is held.
- Keep a picture you like with f.keep(), which also saves the settings.
"""
import funground as f

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
    cell = round(f.map_range(f.mouse_x, 0, WIDTH, 6, 30, clamp=True))
    power = f.map_range(f.mouse_y, 0, HEIGHT, 3, 0.5, clamp=True)
    f.background("white")
    f.fill("black")
    for y in range(0, HEIGHT, cell):
        for x in range(0, WIDTH, cell):
            light = picture.get(min(x + cell // 2, WIDTH - 1), min(y + cell // 2, HEIGHT - 1)).brightness / 100
            darkness = 1 - light ** power                           # contrast: a power bends the greys
            f.circle(x + cell / 2, y + cell / 2, cell * darkness)
    f.fill(0, 0, 0, 170)
    f.rect(0, 0, WIDTH, 22)
    f.fill("white")
    f.text_size(13)
    f.text(f"cell {cell}   contrast {power:.1f}   (move the mouse)", 8, 4)


f.run(fps=15)
