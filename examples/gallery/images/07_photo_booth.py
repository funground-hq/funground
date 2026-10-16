"""Photo booth

The camera, live on the canvas. Press the space bar and it records three seconds, counting down as it goes.
Then it saves them as an animated picture called booth.gif, in the folder you ran it from.
With no camera, it shows a photo.

How it works:
- f.camera() makes a camera object, and cam.start() opens it. f.image(cam, 0, 0) draws its latest frame, like
  any picture.
- cam.record(3) starts a clip. The clip fills with one frame for each frame the sketch draws, so f.run(fps=15)
  makes it 15 frames a second.
- clip.done is True when the clip is full, and len(clip) counts the frames so far. The countdown is worked out
  from them.
- clip.save("booth.gif") writes the animated GIF. Everything before that was only in memory.
- cam.is_ready() is False until the first frame arrives, and for ever if there is no camera. Then a photo
  from f.load_image() is shown, and the space bar does nothing.
- f.cameras() lists the names of the cameras, and the sketch prints them. Give part of a name to f.camera()
  to choose one.

Make it yours:
- Change SECONDS to record for longer. A clip can be at most 10 seconds.
- Change f.run(fps=15) to 10 for a smaller file, or to 24 for smoother movement.
- Show the countdown as a big number in the middle with f.text_size(80) and f.text_align("center").
- Name each file differently, such as "booth-1.gif", "booth-2.gif", and so on.
- Add f.tint("gold") or another colour before f.image() for a coloured filter.
"""
import math

import funground as f

WIDTH, HEIGHT = 400, 300
SECONDS = 3
photo = f.load_image("data/photo.jpg")       # shown when there is no camera
cam = None
clip = None                                  # the clip being recorded, or None
message = ""                                 # what the strip at the bottom says after a save


def open_camera():
    """The camera, started, or None when this computer has none or will not share it."""
    try:
        print("Cameras:", f.cameras())
        camera = f.camera()
        camera.start(WIDTH, HEIGHT)
        return camera
    except RuntimeError:
        return None


def setup():
    global cam
    f.size(WIDTH, HEIGHT)
    cam = open_camera()


def key_pressed():
    global clip, message
    if f.key == " " and clip is None and cam is not None and cam.is_ready():
        clip = cam.record(SECONDS)
        message = ""


def say(words):
    """A dark strip along the bottom with some words on it."""
    f.fill(0, 0, 0, 170)
    f.rect(0, HEIGHT - 28, WIDTH, 28)
    f.fill("white")
    f.text_size(14)
    f.text(words, 8, HEIGHT - 21)


def draw():
    global clip, message
    live = cam is not None and cam.is_ready()
    f.image(cam if live else photo, 0, 0)
    if clip is not None and clip.done:
        clip.save("booth.gif")
        clip = None
        message = "Saved booth.gif. Press space to record again."
    if not live:
        say("No camera: showing a photo")
    elif clip is not None:
        seconds_left = SECONDS - len(clip) / clip.fps
        say(f"Recording... {math.ceil(seconds_left)}")
    else:
        say(message or "Press space to record 3 seconds.")


f.run(fps=15)
