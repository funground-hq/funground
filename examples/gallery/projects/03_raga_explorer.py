"""Raga explorer

Pick a raga with the slider or the left and right keys. The page shows its thaat (parent scale),
its vadi and samvadi (its two most important swaras) and the time of day it belongs to. "listen"
plays its aroha (the way up) and avaroha (the way down) over a drone, lighting each swara. "sing"
lets you sing it, and then shows which ragas fit your notes best.

How it works:
- The program is five small parts. Data comes from f.ragas() and f.raga(). Sounds come from
  make_drone() and make_tune(). Singing is read by listen_to_voice(). Results come from
  work_out_the_singing(). The drawing is in draw(), show_notes() and show_results().
- A variable called mode (idle, listen, sing, thinking or result) says what the page is doing.
  update() reads the buttons and the slider and changes the mode. draw() paints what the mode says.
- make_tune() joins raga.aroha and raga.avaroha, with a rest between. A meend, a glide, runs into
  the last note, written with ~. f.melody(..., sa=SA, tuning="just") plays it. Sa is the home note.
- make_drone() uses f.drone(). A drone is the steady tanpura note under the singer. A raga with no
  Pa gets Ni on the first string. Each sound is made once and kept in a dictionary.
- The ladder has a row for each swara. A row is dark if the raga leaves that swara out. The vadi
  and samvadi have a coloured border. The lit row follows tune.current_time().
- When you sing, mic.pitch() is folded into one octave and smoothed. A row turns red for a swara the
  raga does not use. On "stop", mic.capture(seconds).swara_histogram(SA) counts the swaras, and
  f.match_ragas(shares)[:3] gives the closest three ragas. It compares notes only. A raga is also
  its way of moving between them.

Make it yours:
- Change TEMPO to make the aroha and avaroha slower or faster.
- Remove the glide. In make_tune(), use tokens = up + ["-"] + down + ["-", "-"].
- Change GATE if your room is noisy or quiet. A bigger number needs a louder voice.
- Change the ladder colours, such as "#7a4fa0" for the swaras that the raga uses.
- Change the matches that show. Change [:3] in work_out_the_singing() to [:2] to show two ragas.
"""
import math
import time

import funground as f

SA = "D4"                                  # Sa for the tune. Singing is folded, so any octave counts
SA_HZ = f.note_to_frequency(SA)
TEMPO = 90
BEAT = 60 / TEMPO
SWARAS = "SrRgGmMPdDnN"
NAMES = f.ragas()

# the ladder: one row for each swara, S at the bottom
LEFT, WIDTH = 24, 420
TOP, ROW = 112, 27
GATE = 0.01                                # the microphone must be at least this loud to count
CHARTS = 470                               # where the right-hand panel starts

try:
    mic = f.microphone()
except RuntimeError:                       # no microphone on this computer: the page still works
    mic = None

drones = {}                                # sounds are made when first needed, then kept
tunes = {}


def room(sound, amount):
    """sound.reverb(amount), with the echo that runs past the end added back onto the start,
    so the sound still loops with no gap."""
    length = len(sound.samples())
    wet = sound.reverb(amount).samples()
    looped = wet[:length]
    for i, value in enumerate(wet[length:]):
        looped[i % length] += value
    return f.create_sound(looped)


def make_drone(raga):
    """A tanpura on Sa. A raga with no Pa (Marwa) gets Ni on its first string instead."""
    pattern = "P S' S' S" if "P" in raga.swaras else "N S' S' S"
    if pattern not in drones:
        drones[pattern] = room(f.drone("D3", 7, pattern=pattern), 0.4)
        drones[pattern].set_volume(0.5)        # under the singer, as a tanpura sits
    return drones[pattern]


def make_tune(raga):
    """The tune and the swara for each beat: up, a rest, down with a glide into Sa, then rests."""
    if raga.name not in tunes:
        up = raga.aroha.split()
        down = raga.avaroha.split()
        tokens = up + ["-"] + down[:-2] + [down[-2] + "~" + down[-1] + ":2"] + ["-", "-"]
        beats = up + [None] + down + [None, None]
        tune = f.melody(" ".join(tokens), tempo=TEMPO, sa=SA, tuning="just").reverb(0.3)
        tune.set_volume(0.8)
        lit = [b.rstrip("',") if b else None for b in beats]
        tunes[raga.name] = (tune, lit)
    return tunes[raga.name]


# what is happening now
mode = "idle"                              # idle, listen, sing, thinking or result
raga = f.raga(NAMES[0])
tune, lit = None, []
drone = None
trail = []                                 # the pitch line, in rows above S, or None for a gap
recent = []
sing_start = 0.0
shares = []                                # the 12 swara shares, after singing
matches = []
message = ""


def stop_all():
    global mode, tune, drone
    if tune:
        tune.stop()
    if drone:
        drone.stop()
    if mic:
        mic.stop()
    tune = drone = None
    mode = "idle"


def choose(index):
    """Change the raga. Everything stops, and the last singing is forgotten."""
    global raga, shares, matches, message
    stop_all()
    raga = f.raga(NAMES[index])
    shares, matches, message = [], [], ""
    del trail[:]


def swara_height(hz):
    """Where the voice is, in rows above S, folded into one octave: 0 is S and 11 is N."""
    steps = 12 * math.log2(hz / SA_HZ)
    return (steps + 0.5) % 12 - 0.5        # an octave slip lands on the right row, not off the ladder


def listen_to_voice():
    """The next point of the pink line: a height in rows, or None for a gap. The microphone's pitch is
    gated (it must be loud enough), folded into one octave and smoothed (the middle of the last five)."""
    hz = mic.pitch() if mic.level() > GATE else None
    if hz is None:
        del recent[:]
        return None
    here = swara_height(hz)
    if recent and abs(here - sorted(recent)[len(recent) // 2]) > 2:
        recent[:] = [here]                 # a jump: break the line and start again
        return None
    recent.append(here)
    del recent[:-5]
    return sorted(recent)[len(recent) // 2]


def setup():
    global picker, listen_button, sing_button, stop_button
    f.size(720, 470)
    picker = f.create_slider(0, len(NAMES) - 1, 0, step=1, label="raga")
    listen_button = f.create_button("listen")
    sing_button = f.create_button("sing")
    stop_button = f.create_button("stop")


def key_pressed():
    if f.key == "left":
        picker.value(max(0, picker.value() - 1))
    elif f.key == "right":
        picker.value(min(len(NAMES) - 1, picker.value() + 1))


def work_out_the_singing():
    """Count the swaras in what the microphone heard, and rank the ragas. The first call takes a second or two."""
    global shares, matches, message, mode
    seconds = min(10, max(1.0, time.monotonic() - sing_start))
    shares = mic.capture(seconds).swara_histogram(SA)
    if sum(shares) == 0:
        message = "No clear notes were heard. Sing nearer the microphone, and try again."
        matches = []
    else:
        matches = f.match_ragas(shares)[:3]
        message = ""
    mode = "result"


def update():
    """Buttons, keys and the slider. The page does nothing until you ask."""
    global mode, tune, lit, drone, sing_start, message
    if NAMES[picker.value()] != raga.name:
        choose(picker.value())
    if mode == "thinking":                 # "working it out" was drawn last frame; now do the work
        work_out_the_singing()
    if listen_button.clicked():
        stop_all()
        tune, lit = make_tune(raga)
        drone = make_drone(raga)
        drone.loop()
        tune.loop()
        mode = "listen"
    if sing_button.clicked():
        stop_all()
        if mic is None:
            message = "No microphone was found. You can still listen."
        else:
            drone = make_drone(raga)
            drone.loop()
            mic.start()
            del trail[:]
            del recent[:]
            sing_start = time.monotonic()
            mode = "sing"
            message = ""
    if stop_button.clicked():
        was_singing = mode == "sing"
        stop_all()
        if was_singing:
            mode = "thinking"


def draw():
    update()
    f.background("#1b1424")

    # the swara to light: the one sounding in "listen", the one you sing in "sing"
    heard = None
    if mode == "listen" and tune.is_playing():
        heard = lit[min(int(tune.current_time() / BEAT), len(lit) - 1)]
    if mode == "sing":
        height = listen_to_voice()
        trail.append(height)
        del trail[:-95]
        if height is not None:
            heard = SWARAS[round(height) % 12]

    # the name and the facts
    f.text_align("left", "center")
    f.no_stroke()
    f.fill("white")
    f.text_size(32)
    f.text(raga.name, LEFT, 38)
    f.text_size(14)
    f.fill("#d8c8e8")
    f.text(f"{raga.thaat} thaat.  {raga.time}", LEFT, 68)
    f.fill("orange")
    f.text(f"vadi: {raga.vadi}", LEFT, 90)
    f.fill("#58c4b8")
    f.text(f"samvadi: {raga.samvadi}", LEFT + 110, 90)

    # the ladder
    f.text_size(16)
    for i, swara in enumerate(SWARAS):
        y = TOP + (11 - i) * ROW
        used = swara in raga.swaras
        f.no_stroke()
        if swara == heard:
            f.fill("gold" if used else "tomato")
        else:
            f.fill("#7a4fa0" if used else "#2c2236")
        f.rect(LEFT, y, WIDTH, ROW - 4, 6)
        if swara in (raga.vadi, raga.samvadi):
            f.no_fill()
            f.stroke_width(2)
            f.stroke("orange" if swara == raga.vadi else "#58c4b8")
            f.rect(LEFT, y, WIDTH, ROW - 4, 6)
            f.no_stroke()
        f.fill("black" if swara == heard else "white" if used else "#5b4d68")
        f.text(swara, LEFT + 12, y + (ROW - 4) / 2)

    # the pink line: your voice, newest on the right, a gap wherever it breaks
    f.stroke("hotpink")
    f.stroke_width(3)
    f.no_fill()
    last = None
    for k, height in enumerate(trail):
        if height is None:
            last = None
            continue
        point = (LEFT + 50 + k * 4, TOP + (11 - height) * ROW + (ROW - 4) / 2)
        if last:
            f.line(*last, *point)
        last = point

    # the right-hand panel
    f.no_stroke()
    f.text_align("left", "top")
    if shares and matches:
        show_results()
    else:
        show_notes()

    # a line of help at the bottom
    f.text_align("left", "center")
    f.text_size(14)
    f.fill("#8a7a9a")
    if mode == "thinking":
        f.fill("gold")
        f.text("Working out which swaras you sang...", LEFT, 452)
    elif mode == "sing":
        f.fill("hotpink")
        f.text("Listening. Sing the raga, with Sa on D, then press stop.", LEFT, 452)
    elif message:
        f.fill("tomato")
        f.text(message, LEFT, 452)
    else:
        f.text("left and right keys, or the slider: another raga.   Then press listen or sing.", LEFT, 452)


def show_notes():
    """The raga's own words: how it goes up, how it comes down, and a phrase that marks it."""
    f.text_size(13)
    y = TOP
    for title, text in (("aroha, up", raga.aroha), ("avaroha, down", raga.avaroha), ("pakad, a phrase", raga.pakad)):
        f.fill("#8a7a9a")
        f.text(title, CHARTS, y)
        f.fill("white")
        f.text_size(15)
        f.text(text, CHARTS, y + 18)
        f.text_size(13)
        y += 64
    f.fill("#d8c8e8")
    f.text_box("Dark rows are swaras this raga leaves out. Gold rows light up as it sounds."
               " Singing a swara it leaves out turns a row red.", CHARTS, y + 4, 230, 80)


def show_results():
    """What you sang, as bars, and the three ragas with the closest notes."""
    f.text_size(13)
    f.fill("#8a7a9a")
    f.text("the swaras you sang", CHARTS, TOP)
    biggest = max(shares)
    for i, swara in enumerate(SWARAS):
        x = CHARTS + i * 19
        used = swara in raga.swaras
        f.fill("#c58ae8" if used else "tomato")
        tall = 60 * shares[i] / biggest
        f.rect(x, TOP + 24 + 60 - tall, 14, tall)
        f.fill("white" if used else "tomato")
        f.text_size(11)
        f.text(swara, x + 3, TOP + 90)
    f.text_size(13)
    f.fill("#8a7a9a")
    f.text("the closest ragas, by notes", CHARTS, TOP + 130)
    for k, (name, score) in enumerate(matches):
        y = TOP + 150 + k * 34
        f.fill("white")
        f.text(f"{name}  {score:.2f}", CHARTS, y)
        f.fill("#2c2236")
        f.rect(CHARTS, y + 18, 220, 10, 5)
        f.fill("gold" if name == raga.name else "#7a4fa0")
        f.rect(CHARTS, y + 18, 220 * score, 10, 5)
    f.fill("#d8c8e8")
    f.text_size(12)
    f.text_box("This compares notes only. It cannot hear the way you move between them, and that is what makes"
               " a raga. Ragas with the same swaras score almost the same.", CHARTS, TOP + 250, 230, 80)


f.run()
