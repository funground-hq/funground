"""Blow the words away

You on the camera, and a cloud of words hanging in front of your mouth like fog. The words drift and
thin out and gather again, and your breath blows them away. Press Record, blow, and press Stop: the
sketch plays your take back with the words flying exactly when you blew, and saves it as blow.gif
(and the plain video as take.gif). Click the picture to put the cloud on your mouth, and zoom in for
a close-up. With no camera the words hang in a night sky; with no microphone, hold Space to blow.

How it works:
- Each word is an object of class Word. It knows its text, its home in the cloud, where it is now
  and how fast it moves, and how much of it is left (fade). A list holds all the words.
- The cloud is fog because each word's opacity changes slowly with f.noise(), and soft puffs of
  f.radial_gradient() drift behind them. f.opacity() inside with f.saved_state() fades one word only.
- mic.level() gives the breath, turned into decibels so a soft breath on a laptop counts too. A
  breath pushes each word away from the mouth, harder when it is close; then it fades and drifts back.
- Record starts cam.record(), and the sketch keeps the breath of every frame in a list. Stop calls
  clip.stop(). The take is played back with clip.frame(i), and the words move with the breath kept
  for that frame, while f.save_gif() records the playback. clip.save() writes the plain video.
- Zoom draws only the middle part of the camera picture, larger: f.image() with a source box.

Make it yours:
- Change TEXT to your own sentence, or a poem.
- Change SPREAD for a wider or tighter cloud, and BLOW: a bigger number blows the words further.
- Give each word its own colour with f.random_choice() in Word.__init__.
- Make the words fall like leaves: add a small downward pull in Word.move().
- Change MAX_TAKE for longer takes. Every frame stays in memory, and a long GIF is slow to save.
"""
import math

import funground as f

WIDTH, HEIGHT = 480, 360
FPS = 24
MAX_TAKE = 6            # seconds: a take stops by itself after this
TEXT = ("every breath carries a word away into the morning mist "
        "and the quiet air lets it drift where it likes before it comes home")
SPREAD = 85             # how far the cloud reaches from its centre, in pixels
BLOW = 3.5              # how hard a full breath pushes a word next to the mouth
BUTTONS = {"zoom out": (WIDTH - 196, 10, 34, 30), "zoom in": (WIDTH - 156, 10, 34, 30),
           "record": (WIDTH - 112, 10, 102, 30)}         # x, y, width, height

cam = None
mic = None
spot = f.Vector(WIDTH / 2, HEIGHT * 0.58)              # where the mouth is: click to move it
words = []
haze = 1.0                                             # how thick the fog is: 1 is thick, a breath thins it
zoom = 1.0
mode = "live"                                          # "live", "recording" or "playing back"
take = None                                            # the clip being recorded or played back
breaths = []                                           # the breath of each frame of the take
played = 0                                             # how many frames of the take have been played back
card_left = 0                                          # frames left of the card shown before the playback
message = ""


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
            push = breath * BLOW / (1 + (away.mag() / 40) ** 2)        # much weaker further from the mouth
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


def draw_background(picture):
    """The camera (or a frame of the take), zoomed in on its middle; a night sky without one."""
    if picture is None:
        f.background(f.linear_gradient(0, 0, 0, HEIGHT, ["#0b1026", "#2b2f5e"]))
        return
    part_w, part_h = WIDTH / zoom, HEIGHT / zoom
    f.image(picture, 0, 0, WIDTH, HEIGHT, (WIDTH - part_w) / 2, (HEIGHT - part_h) / 2, part_w, part_h)


def draw_buttons():
    labels = {"zoom out": "-", "zoom in": "+",
              "record": {"live": "Record", "recording": "Stop", "playing back": "Playing"}[mode]}
    for name, (x, y, w, h) in BUTTONS.items():
        if name == "record" and mode == "recording":
            f.fill(200, 30, 40, 230)
        else:
            f.fill(0, 0, 0, 160)
        f.rect(x, y, w, h, 8)
        f.fill("white")
        f.text_size(15)
        f.text(labels[name], x + w / 2 + (8 if name == "record" else 0), y + h / 2)
    x, y, w, h = BUTTONS["record"]
    f.fill("white" if mode == "recording" and f.frame_count % FPS < FPS // 2 else (230, 40, 50))
    f.circle(x + 16, y + h / 2, 12)                      # the record light: it blinks while recording


def inside(button):
    x, y, w, h = BUTTONS[button]
    return x <= f.mouse_x <= x + w and y <= f.mouse_y <= y + h


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
    f.text_style("bold")
    f.no_stroke()
    cam = open_camera()
    mic = open_microphone()
    make_cloud()


def start_recording():
    global mode, take, breaths, message
    take = cam.record(MAX_TAKE) if cam is not None and cam.is_ready() else None
    breaths = []
    message = ""
    mode = "recording"


def stop_recording():
    """Stop the take, save the plain video, and show for a moment that the playback is about to start."""
    global mode, card_left
    if take is not None:
        take.stop()
    if not breaths:
        return start_live("Nothing was recorded.")
    mode, card_left = "about to play", FPS            # a card for one second (it saves take.gif), then the playback


def start_playback():
    """Play the take from the start, with the words in their cloud, while f.save_gif() records it."""
    global mode, played
    for word in words:
        word.go_home(0)
    f.save_gif("blow.gif", len(breaths) / FPS)
    played = 0
    mode = "playing back"


def start_live(words_to_show):
    global mode, message
    mode = "live"
    message = words_to_show


def mouse_pressed():
    global zoom
    if inside("record"):
        if mode == "live":
            start_recording()
        elif mode == "recording":
            stop_recording()
    elif inside("zoom in"):
        zoom = min(3.0, zoom + 0.25)
    elif inside("zoom out"):
        zoom = max(1.0, zoom - 0.25)
    elif mode == "live":
        spot.x, spot.y = f.mouse_x, f.mouse_y


def status(live):
    """What the bar at the bottom says."""
    if mode == "recording":
        return f"Recording: {len(breaths) / FPS:.1f} s. Blow! Press Stop when you are done."
    return message or ("Click your mouth, then Record." + ("" if mic else " No microphone: hold Space.")
                       + ("" if live else " No camera."))


def draw():
    global haze, played, card_left
    time = f.frame_count / FPS
    live = cam is not None and cam.is_ready()

    if mode == "about to play":                         # a card between Stop and the playback (not in the GIF)
        f.background(0, 0, 0)
        f.fill("white")
        f.text_size(22)
        f.text("Your take", WIDTH / 2, HEIGHT / 2 - 20)
        f.text_size(15)
        f.text("Playing it back and saving blow.gif...", WIDTH / 2, HEIGHT / 2 + 14)
        if card_left == FPS - 1 and take is not None:
            take.save("take.gif")                        # the plain video, once the card is on screen
        card_left -= 1
        if card_left <= 0:
            start_playback()
        return
    if mode == "playing back":
        strength = breaths[played]
        draw_background(take.frame(played) if take is not None and played < len(take) else None)
        played += 1
    else:
        strength = breath()
        draw_background(cam if live else None)
        if mode == "recording":
            breaths.append(strength)
            if len(breaths) >= MAX_TAKE * FPS:
                stop_recording()

    haze = max(0.1, haze - strength * 0.08)              # a breath thins the fog
    haze += (1 - haze) * 0.01                            # and it thickens again, slowly
    draw_haze(time)
    f.fill("white")
    for word in words:
        word.move(strength, time)
        word.draw(time)

    if mode == "playing back":                           # nothing but the take and the words: this is the GIF
        if played >= len(breaths):
            start_live("Saved blow.gif" + (" and take.gif." if take is not None else "."))
        return
    if mode == "recording":
        f.no_fill()
        f.stroke(220, 30, 40)
        f.stroke_width(6)
        f.rect(3, 3, WIDTH - 6, HEIGHT - 6)              # a red frame: the take is being recorded
        f.no_stroke()
    else:
        f.no_fill()
        f.stroke(255, 255, 255, 60)
        f.circle(spot.x, spot.y, 16)                     # where the mouth should be
        f.no_stroke()
    draw_buttons()
    f.fill(0, 0, 0, 150)
    f.rect(0, HEIGHT - 26, WIDTH, 26)
    f.fill("white")
    f.text_size(13)
    f.text(status(live), WIDTH / 2, HEIGHT - 13)


f.run(fps=FPS)
