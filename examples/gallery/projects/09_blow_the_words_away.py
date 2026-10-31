"""Blow the words away

A cloud of words hangs in front of a mouth like fog, and breath blows it away. Make a take with the photo booth
first: it saves take.gif and take.wav. This sketch plays the take over and over, and the words fly exactly where
the sound in it was loud: when you blew. Click to put the cloud on the mouth. Press G to save one loop with the
words as blow.gif. With no take it uses the live camera and microphone (hold Space to blow without one).

How it works:
- camera.load_clip("take.gif") and sound.load("take.wav") read the take. Each frame of the clip is drawn in turn with
  clip.frame(i), and the sound plays alongside, starting again with the clip so the two stay together.
- Before it starts, the sketch works out how loud the sound is during each frame of the clip, from
  take_audio.samples(), and turns it into a breath from 0 to 1. Frame i always gets breath i, so the words move at
  exactly the right moments, every loop.
- Each word is an object of class Word with its home in the cloud, its speed and how much of it is left. A breath
  pushes the words near the mouth away; then they fade and drift back. f.noise() makes the fog come and go.
- f.save_gif() keeps one whole loop, from its first frame, as blow.gif.

Make it yours:
- Change TEXT to your own sentence, or a poem.
- Change SPREAD for a wider or tighter cloud, and BLOW: a bigger number blows the words further.
- Give each word its own colour with f.random_choice() in Word.__init__.
- Use another take: any GIF and WAV of the same length work, such as a clap or a song.
- Make the words fall like leaves: add a small downward pull in Word.move().
"""
import math

import funground as f
from funground import sound
from funground import camera

WIDTH, HEIGHT = 480, 360
TEXT = ("every breath carries a word away into the morning mist "
        "and the quiet air lets it drift where it likes before it comes home")
SPREAD = 85             # how far the cloud reaches from its centre, in pixels
BLOW = 3.5              # how hard a full breath pushes a word next to the mouth


def load_take():
    """The photo booth's take next to this sketch, as (clip, sound), or (None, None) when there is none."""
    try:
        clip = camera.load_clip("take.gif")
    except FileNotFoundError:
        return None, None
    try:
        return clip, sound.load("take.wav")
    except FileNotFoundError:
        return clip, None                              # a silent take: hold Space to blow


def breath_of(level):
    """A loudness from 0 to 1 as a breath from 0 to 1, in decibels so a soft breath on a laptop counts too:
    -45 dB (a quiet room) is 0, -20 dB (a breath) is 1."""
    return f.constrain((20 * math.log10(level + 1e-9) + 45) / 25, 0, 1)


def breaths_of(take_audio, frames, fps):
    """How hard the breath is during each frame of the take: the loudness of the sound for that frame."""
    if take_audio is None:
        return [0.0] * frames
    samples = take_audio.samples()                          # 44 100 numbers for every second
    per_frame = 44100 / fps
    result = []
    for i in range(frames):
        part = samples[int(i * per_frame):int((i + 1) * per_frame)]
        level = math.sqrt(sum(v * v for v in part) / len(part)) if part else 0.0
        result.append(breath_of(level))
    return result


take, take_sound = load_take()
FPS = take.fps if take is not None else 24
breaths = breaths_of(take_sound, len(take), FPS) if take is not None else []
cam = None
mic = None
spot = f.Vector(WIDTH / 2, HEIGHT * 0.58)              # where the mouth is: click to move it
words = []
haze = 1.0                                             # how thick the fog is: 1 is thick, a breath thins it
gif = "none"                                           # "none", "waiting" for the loop to start, "saving", "saved"


class Word:
    def __init__(self, text, number, size, home):
        self.text = text
        self.seed = number * 3.7                         # each word wanders in its own part of the noise
        self.size = size
        self.home = home                                 # its place in the cloud, from the cloud's centre
        self.go_home(0)

    def go_home(self, time):
        """Back to its place in the cloud, at rest and fully there."""
        self.position = self.home_now(time)
        self.velocity = f.Vector(0, 0)
        self.fade = 1.0                                   # 1 is all there, 0 is gone

    def home_now(self, time):
        """Its place in the cloud: home, wandering a little as fog does."""
        drift = f.Vector(f.noise(self.seed, time * 0.2) - 0.5, f.noise(self.seed + 50, time * 0.2) - 0.5) * 14
        return spot + self.home + drift

    def move(self, breath, time):
        home = self.home_now(time)
        away = self.position - spot
        if breath > 0 and away.mag() < SPREAD * 3:
            push = breath * BLOW * 24 / FPS / (1 + (away.mag() / 40) ** 2)    # weaker further away; tuned at 24 fps
            self.velocity.add(away.copy().set_mag(push) + f.Vector(0, -push * 0.3))
        self.position.add(self.velocity)
        self.velocity.mult(0.93)                         # the air slows it down
        self.position.add((home - self.position) * 0.01)  # and the cloud slowly pulls it back
        from_home = self.position.dist(home)
        target = f.constrain(1 - from_home / 160, 0, 1)
        self.fade += (target - self.fade) * (0.15 if target < self.fade else 0.02)   # fade out fast, in slowly
        if self.fade < 0.02 and from_home > 120:         # gone: start again at home, invisible
            self.position = home
            self.velocity = f.Vector(0, 0)
            self.fade = 0

    def draw(self, time):
        fog = f.map_range(f.noise(self.seed, time * 0.3), 0.3, 0.7, 0.45, 1.0, clamp=True)
        with f.saved_state():
            f.opacity(255 * fog * self.fade)
            f.text_size(self.size)
            f.text(self.text, self.position.x, self.position.y)


def make_cloud():
    """Give every word a home near the centre where it does not cover a word already placed, so the cloud is
    tight but every word can be read. A word tries close places first, and further ones when there is no room."""
    boxes = []                                           # (x, y, width, height) of each placed word
    for number, text in enumerate(TEXT.split()):
        size = f.random(15, 26)
        f.text_size(size)
        width, height = f.text_width(text) + 6, size + 2
        for tries in range(800):
            reach = SPREAD * (0.1 + tries / 600)
            x, y = f.random_gaussian(0, reach), f.random_gaussian(0, reach * 0.5)
            if not any(abs(x - bx) < (width + bw) / 2 and abs(y - by) < (height + bh) / 2 for bx, by, bw, bh in boxes):
                break
        boxes.append((x, y, width, height))
        words.append(Word(text, number, size, f.Vector(x, y)))


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
        cam = camera.open()
        cam.start(WIDTH, HEIGHT)
        return cam
    except RuntimeError:
        return None


def open_microphone():
    try:
        microphone = sound.microphone()
        microphone.start()
        return microphone
    except RuntimeError:
        return None


def live_breath():
    """Blowing now: Space, or the microphone."""
    if f.key_down("space"):
        return 1.0
    return breath_of(mic.level()) if mic is not None else 0.0


def setup():
    global cam, mic
    f.size(WIDTH, HEIGHT)
    f.random_seed(9)
    f.noise_seed(9)                                    # the same fog each run
    f.text_align("center", "center")
    f.text_style("bold")
    f.no_stroke()
    make_cloud()
    if take is None:                                   # no take: the camera and the microphone, live
        cam = open_camera()
        mic = open_microphone()


def mouse_pressed():
    spot.x, spot.y = f.mouse_x, f.mouse_y


def key_pressed():
    global gif
    if f.key in ("g", "G") and take is not None and gif in ("none", "saved"):
        gif = "waiting"                                # the GIF starts with the loop's first frame


def draw():
    global haze, gif
    time = f.frame_count / FPS
    if take is not None:
        i = f.frame_count % len(take)
        if i == 0:
            if take_sound is not None:                 # the sound starts again with the clip
                take_sound.stop()
                take_sound.play()
            if gif == "waiting":
                f.save_gif("blow.gif", len(take) / FPS)
                gif = "saving"
            elif gif == "saving":
                gif = "saved"
        f.image(take.frame(i), 0, 0, WIDTH, HEIGHT)
        strength = max(breaths[i], 1.0 if f.key_down("space") else 0.0)
    else:
        if cam is not None and cam.is_ready():
            f.image(cam, 0, 0)
        else:
            f.background(f.linear_gradient(0, 0, 0, HEIGHT, ["#0b1026", "#2b2f5e"]))
        strength = live_breath()

    haze = max(0.1, haze - strength * 0.08)            # a breath thins the fog
    haze += (1 - haze) * 0.01                          # and it thickens again, slowly
    draw_haze(time)
    f.fill("white")
    for word in words:
        word.move(strength, time)
        word.draw(time)

    if gif == "saving":
        return                                         # nothing but the take and the words: this is the GIF
    f.no_fill()
    f.stroke(255, 255, 255, 60)
    f.circle(spot.x, spot.y, 16)                       # where the mouth should be
    f.no_stroke()
    f.fill(0, 0, 0, 150)
    f.rect(0, HEIGHT - 26, WIDTH, 26)
    f.fill("white")
    f.text_size(13)
    f.text(status(), WIDTH / 2, HEIGHT - 13)


def status():
    """What the bar at the bottom says."""
    if take is None:
        return "No take.gif: live camera. Make a take with the photo booth."
    if gif == "waiting":
        return "Saving starts with the next loop..."
    if gif == "saved":
        return "Saved blow.gif. Click the mouth, or press G again."
    return "Click the mouth. G saves one loop as blow.gif."


f.run(fps=FPS)
