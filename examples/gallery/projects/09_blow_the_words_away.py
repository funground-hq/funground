"""Blow the words away

You on the camera, and a cloud of words hanging in front of your mouth like fog. The words drift and
thin out and gather again. Blow into the microphone and the words nearest your mouth fly away and
fade. A moment later they drift back into the cloud. Click to move the cloud to where your mouth is.
With no camera the words hang in a night sky, and with no microphone you blow by holding Space.

How it works:
- Each word is an object of class Word. It knows its text, its home in the cloud, where it is now
  and how fast it moves, and how much of it is left (fade). A list holds all the words.
- The cloud is fog because each word's opacity changes slowly with f.noise(), so words come and go.
  Inside with f.saved_state(), f.opacity() sets one word's opacity and leaves the others alone.
- mic.level() gives the breath. It is turned into decibels, so a soft breath on a laptop's
  microphone counts too. A breath pushes each word away from the mouth, harder when it is close.
- A blown word slows down in the air, and its fade drops as it goes further from home. When it has
  faded away, it starts again at its home, invisible, and fades in.
- Behind the words, a few soft puffs of fog drift: circles filled with f.radial_gradient(), white in the
  middle and see-through at the edge. A breath thins them, and they thicken again slowly.
- f.image(cam, 0, 0) draws the camera behind everything. f.save_gif() keeps three seconds when you
  press G.

Make it yours:
- Change TEXT to your own sentence, or a poem.
- Change SPREAD for a wider or tighter cloud.
- Change BLOW: a bigger number blows the words further.
- Give each word its own colour with f.random_choice() in Word.__init__.
- Make the words fall like leaves: add a small downward pull in Word.move().
"""
import math

import funground as f

WIDTH, HEIGHT = 640, 480
TEXT = ("every breath carries a word away into the morning mist "
        "and the quiet air lets it drift where it likes before it comes home")
SPREAD = 110            # how far the cloud reaches from its centre, in pixels
BLOW = 3.5              # how hard a full breath pushes a word next to the mouth

cam = None
mic = None
spot = f.Vector(WIDTH / 2, HEIGHT * 0.7)               # where the mouth is: click to move it
words = []
haze = 1.0                                             # how thick the fog is: 1 is thick, a breath thins it


class Word:
    def __init__(self, text, number):
        self.text = text
        self.seed = number * 3.7                         # each word wanders in its own part of the noise
        self.size = f.random(12, 22)
        self.home = f.Vector(f.random_gaussian(0, SPREAD * 0.85), f.random_gaussian(0, SPREAD * 0.4))
        self.position = spot + self.home
        self.velocity = f.Vector(0, 0)
        self.fade = 1.0                                   # 1 is all there, 0 is gone

    def home_now(self, time):
        """Its place in the cloud: home, wandering a little as fog does."""
        drift = f.Vector(f.noise(self.seed, time * 0.2) - 0.5, f.noise(self.seed + 50, time * 0.2) - 0.5) * 60
        return spot + self.home + drift

    def move(self, breath, time):
        home = self.home_now(time)
        away = self.position - spot
        if breath > 0 and away.mag() < SPREAD * 3:
            push = breath * BLOW / (1 + (away.mag() / 50) ** 2)        # much weaker further from the mouth
            self.velocity.add(away.copy().set_mag(push) + f.Vector(0, -push * 0.3))
        self.position.add(self.velocity)
        self.velocity.mult(0.93)                         # the air slows it down
        self.position.add((home - self.position) * 0.01)  # and the cloud slowly pulls it back
        from_home = self.position.dist(home)
        target = f.constrain(1 - from_home / 200, 0, 1)
        self.fade += (target - self.fade) * (0.15 if target < self.fade else 0.02)   # fade out fast, in slowly
        if self.fade < 0.02 and from_home > 150:         # gone: start again at home, invisible
            self.position = home
            self.velocity = f.Vector(0, 0)
            self.fade = 0

    def draw(self, time):
        fog = f.map_range(f.noise(self.seed, time * 0.3), 0.3, 0.7, 0.15, 0.9, clamp=True)
        with f.saved_state():
            f.opacity(255 * fog * self.fade)
            f.text_size(self.size)
            f.text(self.text, self.position.x, self.position.y)


def draw_haze(time):
    """Soft puffs of fog behind the words: each a circle filled with white that fades out to its edge."""
    for i in range(7):
        x = spot.x + (f.noise(i * 9.1, time * 0.1) - 0.5) * SPREAD * 3.5
        y = spot.y + (f.noise(i * 9.1 + 30, time * 0.1) - 0.5) * SPREAD * 1.3
        radius = SPREAD * (0.6 + 0.6 * f.noise(i, time * 0.2))
        f.fill(f.radial_gradient(x, y, radius, [(235, 240, 255, round(34 * haze)), (235, 240, 255, 0)]))
        f.circle(x, y, 2 * radius)


def open_camera():
    try:
        camera = f.camera()
        camera.start(WIDTH, HEIGHT)
        return camera
    except RuntimeError:
        return None


def open_microphone():
    try:
        microphone = f.microphone()
        microphone.start()
        return microphone
    except RuntimeError:
        return None


def breath():
    """How hard you are blowing, from 0 to 1: the microphone in decibels, or Space."""
    if f.key_down("space"):
        return 1.0
    if mic is None:
        return 0.0
    decibels = 20 * math.log10(mic.level() + 1e-9)
    return f.constrain((decibels + 45) / 25, 0, 1)        # -45 dB (a quiet room) is 0, -20 dB (a breath) is 1


def setup():
    global cam, mic
    f.size(WIDTH, HEIGHT)
    f.random_seed(9)
    f.noise_seed(9)                                  # the same fog each run
    f.text_align("center", "center")
    f.no_stroke()
    cam = open_camera()
    mic = open_microphone()
    for number, text in enumerate(TEXT.split()):
        words.append(Word(text, number))


def mouse_pressed():
    spot.x, spot.y = f.mouse_x, f.mouse_y


def key_pressed():
    if f.key == "g":
        f.save_gif("blow.gif", 3)


def draw():
    global haze
    time = f.frame_count / 30
    live = cam is not None and cam.is_ready()
    if live:
        f.image(cam, 0, 0)
    else:
        f.background(f.linear_gradient(0, 0, 0, HEIGHT, ["#0b1026", "#2b2f5e"]))

    strength = breath()
    haze = max(0.1, haze - strength * 0.08)              # a breath thins the fog
    haze += (1 - haze) * 0.01                            # and it thickens again, slowly
    draw_haze(time)
    f.fill("white")
    for word in words:
        word.move(strength, time)
        word.draw(time)

    f.no_fill()
    f.stroke(255, 255, 255, 60)
    f.circle(spot.x, spot.y, 16)                         # where the mouth should be
    f.no_stroke()
    f.fill(0, 0, 0, 150)
    f.rect(0, HEIGHT - 26, WIDTH, 26)
    f.fill("white")
    f.text_size(13)
    f.text("Click your mouth, then blow. " + ("" if mic else "No microphone: hold Space. ")
           + ("" if live else "No camera. ") + "G saves a GIF.", WIDTH / 2, HEIGHT - 13)


f.run(fps=30)
