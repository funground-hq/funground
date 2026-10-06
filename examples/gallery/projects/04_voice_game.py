"""Voice-controlled game

A little bird flies through gates, and your voice is the control. First comes a "set up your voice"
screen. It measures the quiet of your room, shows a live bar of how loud you are, and lets you move
two marks on it: where the bird starts to lift, and where it reaches full height. A practice bird on
the right shows the result, so you can test before you play. Then say "aaah" and the bird goes up.
The louder you are, the higher it goes. Fly through the gap in each gate to score. Touch a gate and
the game is over. With no microphone, press the space bar to hop the bird up.

How it works:
- The game has four states: "setup", "ready", "play" and "over". update() moves the game on, and
  draw() paints it. draw_setup(), draw_scene(), draw_gate(), draw_bird() and draw_meter() do the
  painting.
- listen() turns the microphone into one number from 0 to 1. Microphones differ a lot, so the game
  measures loudness in decibels (db()) and compares it with the room. For the first CALIBRATE frames
  (a second), it listens to the quiet room and keeps the middle reading, the median, as the floor.
  After that, it smooths mic.level() and measures how many decibels you are above the floor.
- settings() gives the two marks, "starts at" and "full at", from the sliders that f.create_slider()
  made. Below "starts at" the result is 0, and at "full at" it is 1. f.constrain() keeps it between.
  The arrow keys move the sliders too, and key_pressed() reads them. update() shows the sliders on the
  setup screen only: .visible() hides them while you play, and they keep their values.
- The setup screen draws a tall bar of your loudness, the two marks, and a practice bird that eases
  toward the height your voice gives. The small "mic" bar shows the raw decibels in every state.
  Loudness controls the bird, not pitch, because mic.pitch() gives nothing for breath or noise.
- The bird eases toward a target height, set by voice. Gates are dictionaries in a list. They slide
  left, and score goes up when one passes. hits() finds the nearest point of each gate box to the
  bird. The sounds come from f.pluck(), f.note() and f.tone(), and sound.play() plays them.

Make it yours:
- Change GAP from 150 to 200 for an easier game, or to 120 for a harder one.
- Change QUIET_DB = 15 and RANGE_DB = 30. They are where the two sliders start, in decibels above
  the room. A quieter voice needs a smaller QUIET_DB.
- Change SPACING for gates closer together or further apart. Change the 3 in speed = 3 + ... to
  change the speed.
- Add a third slider in setup(), for how quickly the bird falls: change the 0.14 in update().
- Change the colours of the bird, such as f.fill(255, 200, 40) for the body, or the sounds: try
  "C6" in sound_point.
"""
import math

import funground as f

W, H = 640, 420
GROUND = 370                               # where the grass starts
BIRD_X = 130
BIRD_R = 15
GATE_W = 64
GAP = 150                                  # the height of the opening in each gate
SPACING = 210                              # how far apart the gates are
CALIBRATE = 60                             # frames spent listening to the quiet room (a second)
QUIET_DB = 15                              # where "starts at" begins: decibels above the room that count as nothing
RANGE_DB = 30                              # then this many more decibels take the voice from 0 to 1 ("full at")
SCALE_DB = 60                              # the setup meter shows 0 to this many decibels above the room
METER_TOP, METER_BOTTOM = 84, 340          # where the setup meter is drawn
BUTTON = (265, 318, 210, 44)               # the "start game" button on the setup screen: x, y, width, height
LOW, HIGH = 50, GROUND - 28                # the bird stays between these heights

try:
    mic = f.microphone()
    mic_name = (f.microphones() or ["microphone"])[0]
except RuntimeError:                       # no microphone on this computer: space still works
    mic = None
    mic_name = ""

# Sound effects: all made from numbers, and made quiet enough to be pleasant.
sound_start = f.pluck("C5", 0.5, volume=0.4)
sound_point = f.note("G5", 0.18, volume=0.35)
sound_crash = f.tone(120, 0.45, wave="triangle", volume=0.45, release=0.3)

state = "setup"                            # setup, ready, play or over
start_at = None                            # the slider for where the bird starts to lift (made in setup())
full_at = None                             # the slider for where it reaches full height
calibrate_from = 0                         # the frame when the room measuring began
practice_y = float(HIGH)                   # the practice bird on the setup screen
bird_y = 200.0
gates = []
score = 0
best = 0
floor = -80.0                              # how loud the quiet room is, in decibels
quiet = []                                 # readings (in decibels) while listening to the room
heard = -80.0                              # the microphone level in decibels, smoothed
above = 0.0                                # decibels above the room, smoothed: the raw "mic" bar
voice = 0.0                                # 0 to 1: how hard you are calling the bird up
hop = 0.0                                  # a space bar press, which fades away
crashed_at = 0
clouds = [(90, 70, 1.0), (215, 50, 0.8), (500, 95, 1.2)]


def new_gate(x):
    return {"x": x, "gap": f.random(LOW + GAP / 2 + 10, GROUND - GAP / 2 - 30), "passed": False}


def reset():
    """A fresh game: the first gates wait off to the right."""
    global gates, score, bird_y
    gates = [new_gate(520 + i * SPACING) for i in range(4)]
    score = 0
    bird_y = 200.0


def setup():
    global start_at, full_at
    f.size(W, H)
    f.random_seed(11)
    start_at = f.create_slider(0, 40, QUIET_DB, step=1, label="starts at (dB)")
    full_at = f.create_slider(10, 70, QUIET_DB + RANGE_DB, step=1, label="full at (dB)")
    reset()
    if mic:
        mic.start()


def settings():
    """The two marks, in decibels above the room: where the bird starts to lift, and where it is at full height."""
    low = start_at.value()
    return low, max(full_at.value(), low + 5)      # full is always a little above start


def calibrating():
    return f.frame_count - calibrate_from < CALIBRATE


def measure_room_again():
    global calibrate_from, quiet
    calibrate_from = f.frame_count
    quiet = []


def begin():
    """Leave the setup screen. With no microphone, the space bar that got us here is also the first hop."""
    global state, hop
    reset()
    state = "ready"
    hop = 1.0 if mic is None else 0.0


def key_pressed():
    global hop, state
    key = f.key.lower() if isinstance(f.key, str) and len(f.key) == 1 else f.key
    if state == "setup":
        if key in ("enter", " "):
            begin()
        elif key == "r" and mic:
            measure_room_again()
        elif key == "up":
            start_at.value(start_at.value() + 1)
        elif key == "down":
            start_at.value(start_at.value() - 1)
        elif key == "right":
            full_at.value(full_at.value() + 1)
        elif key == "left":
            full_at.value(full_at.value() - 1)
        return
    if key == "s" and state in ("ready", "over"):
        state = "setup"
        return
    if key == " ":
        hop = 1.0


def mouse_pressed():
    x, y, w, h = BUTTON
    if state == "setup" and x <= f.mouse_x <= x + w and y <= f.mouse_y <= y + h:
        begin()


def db(level):
    """Loudness in decibels: 0 is as loud as it gets, and every 20 less is ten times quieter."""
    return 20 * math.log10(level + 1e-9)


def listen():
    """Turn the microphone into a number from 0 (quiet) to 1 (loud), measured against the room."""
    global floor, heard, above
    if mic is None:
        return 0.0
    now = db(mic.level())
    if calibrating():                      # at the start, just learn the quiet of the room
        if f.frame_count - calibrate_from > 5:     # the first few frames are the microphone waking up
            quiet.append(now)
        if quiet:
            floor = max(-80.0, sorted(quiet)[len(quiet) // 2])    # the median: a click does not move it
        heard = floor
        return 0.0
    heard += (now - heard) * 0.35          # smooth the jumps
    above = max(0.0, heard - floor)        # decibels louder than the room
    low, high = settings()
    return f.constrain((above - low) / (high - low), 0, 1)


def hits(gate):
    """Does the bird touch the top or the bottom of this gate? Nearest point of each box, then a distance."""
    for top, bottom in ((0, gate["gap"] - GAP / 2), (gate["gap"] + GAP / 2, GROUND)):
        nearest_x = f.constrain(BIRD_X, gate["x"], gate["x"] + GATE_W)
        nearest_y = f.constrain(bird_y, top, bottom)
        if math.hypot(BIRD_X - nearest_x, bird_y - nearest_y) < BIRD_R - 1:
            return True
    return False


def update():
    global state, bird_y, voice, hop, score, best, crashed_at, practice_y
    voice = max(listen(), hop)
    hop *= 0.93                            # a space bar press lifts the bird for a moment
    if hop < 0.05:
        hop = 0.0
    start_at.visible(state == "setup")     # the sliders show on the setup screen only
    full_at.visible(state == "setup")

    if state == "setup":
        practice_y += ((HIGH - voice * (HIGH - LOW)) - practice_y) * 0.14
    elif state == "ready":
        bird_y = 200 + 8 * math.sin(f.frame_count * 0.1)
        if voice > 0.3 or hop > 0.9:
            state = "play"
            sound_start.play()
    elif state == "play":
        target = HIGH - voice * (HIGH - LOW)           # loud is up
        bird_y += (target - bird_y) * 0.14
        speed = 3 + min(score, 20) * 0.1               # a little faster with each point
        for gate in gates:
            gate["x"] -= speed
            if not gate["passed"] and gate["x"] + GATE_W < BIRD_X - BIRD_R:
                gate["passed"] = True
                score += 1
                best = max(best, score)
                sound_point.play()
        if gates[0]["x"] < -GATE_W:
            gates.pop(0)
            gates.append(new_gate(gates[-1]["x"] + SPACING))
        if any(hits(g) for g in gates):
            state = "over"
            crashed_at = f.frame_count
            sound_crash.play()
    elif state == "over":
        waited = f.frame_count - crashed_at > 50       # so the shout that crashed you does not restart it
        if waited and (voice > 0.3 or hop > 0.9):
            reset()
            state = "play"
            sound_start.play()


def draw_scene():
    f.no_stroke()
    f.fill(f.linear_gradient(0, 0, 0, GROUND, [(110, 190, 240), (215, 240, 255)]))
    f.rect(0, 0, W, GROUND)
    f.fill(255, 255, 255, 200)
    for x, y, size in clouds:
        for dx, dy, r in ((0, 0, 44), (30, 8, 36), (-30, 10, 34), (8, -14, 34)):
            f.circle(x + dx * size, y + dy * size, r * size)
    f.fill(120, 190, 130)                          # far hills
    f.ellipse(120, GROUND, 360, 150)
    f.ellipse(470, GROUND, 420, 110)
    f.fill(90, 170, 90)                            # the grass
    f.rect(0, GROUND, W, H - GROUND)
    f.fill(70, 140, 75)
    f.rect(0, GROUND, W, 8)


def draw_gate(gate):
    x, top_end, bottom_start = gate["x"], gate["gap"] - GAP / 2, gate["gap"] + GAP / 2
    f.fill(60, 160, 110)
    f.stroke(30, 100, 70)
    f.stroke_width(3)
    f.rect(x, -4, GATE_W, top_end + 4)
    f.rect(x, bottom_start, GATE_W, GROUND - bottom_start)
    f.fill(80, 190, 130)
    f.rect(x - 6, top_end - 22, GATE_W + 12, 22, 5)           # the caps at the gap
    f.rect(x - 6, bottom_start, GATE_W + 12, 22, 5)
    f.no_stroke()


def draw_bird():
    flap = math.sin(f.frame_count * 0.5) * (14 if state == "play" else 5)
    f.push()
    f.translate(BIRD_X, bird_y)
    f.rotate(f.constrain((voice - 0.45) * -30, -25, 25) if state == "play" else 0)
    f.no_stroke()
    f.fill(255, 200, 40)
    f.circle(0, 0, BIRD_R * 2)
    f.fill(255, 150, 30)                           # the wing
    f.ellipse(-5, 4 + flap * 0.3, 16, 10 + flap * 0.4)
    f.fill(255, 110, 40)                           # the beak
    f.triangle(BIRD_R - 3, -3, BIRD_R + 9, 2, BIRD_R - 3, 6)
    f.fill("white")
    f.circle(5, -5, 9)
    f.fill("black")
    f.circle(7, -5, 4)
    f.pop()


def draw_meter():
    """How hard you are calling the bird up: a bar on the left."""
    f.no_stroke()
    f.fill(0, 0, 0, 50)
    f.rect(16, LOW, 14, HIGH - LOW, 7)
    f.fill("tomato" if state == "over" else "gold")
    f.rect(16, HIGH - voice * (HIGH - LOW), 14, voice * (HIGH - LOW) + 0.001, 7)
    f.fill(40, 60, 90)
    f.text_size(12)
    f.text_align("left", "top")
    f.text("voice", 12, HIGH + 8)


def draw_hearing():
    """The raw loudness, always on: a small light and bar at the top left, and the device name."""
    f.text_size(12)
    f.text_align("left", "center")
    f.no_stroke()
    f.fill(40, 60, 90)
    if mic is None:
        f.text("no microphone found: press space", 12, 14)
        return
    waiting = calibrating()
    f.text("mic", 12, 14)
    f.fill(0, 0, 0, 50)
    f.rect(38, 8, 80, 12, 6)
    share = 0.0 if waiting else f.constrain(above / 40, 0, 1)
    f.fill("limegreen" if above > settings()[0] and not waiting else "gray")
    f.rect(38, 8, 80 * share + 0.001, 12, 6)
    f.fill(40, 60, 90, 200)
    f.text(mic_name[:40], 12, H - 12)


def meter_y(decibels):
    """The height on the setup meter of a number of decibels above the room."""
    return METER_BOTTOM - f.constrain(decibels / SCALE_DB, 0, 1) * (METER_BOTTOM - METER_TOP)


def draw_setup():
    """The set up your voice screen: room check, live meter with two marks, a practice bird, and the start button."""
    draw_scene()
    f.no_stroke()
    f.fill(255, 255, 255, 235)
    f.rect(20, 30, W - 40, 370, 16)
    f.fill(40, 60, 90)
    f.text_align("center", "center")
    f.text_size(26)
    f.text("Set up your voice", W / 2, 56)

    x, y, w, h = BUTTON
    f.fill(60, 160, 110)
    f.rect(x, y, w, h, 12)
    f.fill("white")
    f.text_size(18)
    f.text("start game  (Enter)", x + w / 2, y + h / 2)
    f.fill(40, 60, 90)
    if mic is None:
        f.text_size(17)
        f.text("no microphone found:", W / 2, 150)
        f.text("press space to play with the space bar", W / 2, 180)
        return

    low, high = settings()
    f.text_size(14)
    f.text("your voice", 67, 72)
    f.fill(0, 0, 0, 40)                            # the meter, and how loud you are right now
    f.rect(50, METER_TOP, 34, METER_BOTTOM - METER_TOP, 6)
    f.fill("limegreen" if above > low and not calibrating() else "gold")
    f.rect(50, meter_y(above), 34, METER_BOTTOM - meter_y(above) + 0.001, 6)
    f.text_align("left", "center")
    for decibels, name, colour in ((low, "starts to lift", "seagreen"), (high, "full height", "tomato")):
        f.stroke(colour)
        f.stroke_width(3)
        f.line(40, meter_y(decibels), 94, meter_y(decibels))
        f.no_stroke()
        f.fill(colour)
        f.text(f"{name}: {decibels} dB", 100, meter_y(decibels))
    f.stroke(40, 60, 90)                           # the room: the bottom of the meter
    f.stroke_width(2)
    f.line(40, METER_BOTTOM, 94, METER_BOTTOM)
    f.no_stroke()
    f.fill(40, 60, 90)
    f.text(f"the quiet room: {round(floor)} dB", 40, METER_BOTTOM + 22)

    f.text_size(15)
    if calibrating():
        left = CALIBRATE - (f.frame_count - calibrate_from)
        f.fill(200, 90, 40)
        f.text("Stay quiet... measuring the room", 265, 100)
        f.fill(0, 0, 0, 40)
        f.rect(265, 118, 210, 10, 5)
        f.fill(200, 90, 40)
        f.rect(265, 118, 210 * (1 - left / CALIBRATE) + 0.001, 10, 5)
    else:
        f.text("Say aaah softly, then loudly.", 265, 100)
        f.text("Adjust until soft lifts a little", 265, 120)
        f.text("and loud reaches the top.", 265, 140)
    f.fill(40, 60, 90)
    f.text_size(14)
    f.text(f"Up / Down: starts at  ({low} dB)", 265, 190)
    f.text(f"Left / Right: full at  ({high} dB)", 265, 212)
    f.text("or use the two sliders below the game", 265, 234)
    f.text("R: measure the room again", 265, 268)

    f.fill(0, 0, 0, 40)                            # the practice bird
    f.rect(515, 34, 80, HIGH - LOW + 30, 14)
    f.fill(255, 200, 40)
    f.circle(555, practice_y, 28)
    f.fill("black")
    f.circle(561, practice_y - 4, 5)
    f.fill(40, 60, 90)
    f.text_align("center", "center")
    f.text("try it", 555, HIGH + 30)


def draw():
    update()
    if state == "setup":
        draw_setup()
        draw_hearing()
        return
    draw_scene()
    for gate in gates:
        draw_gate(gate)
    draw_bird()
    draw_meter()
    draw_hearing()

    f.no_stroke()
    f.fill(40, 60, 90)
    f.text_align("center", "center")
    f.text_size(46)
    f.text(str(score), W / 2, 40)
    f.text_align("right", "center")
    f.text_size(16)
    f.text(f"best {best}", W - 16, 24)

    f.fill(255, 255, 255, 235)
    f.text_align("center", "center")
    f.text_size(20)
    if state == "ready":
        f.rect(165, 120, 350, 86, 14)
        f.fill(40, 60, 90)
        if mic and calibrating():
            f.text("listening... stay quiet a moment", 340, 155)
        else:
            f.text("Say aaah to fly: louder is higher", 340, 145)
            f.text_size(15)
            f.text("or press the space bar" + ("" if mic else "  (no microphone found)"), 340, 172)
        f.text_size(13)
        f.text("S: voice settings", 340, 194)
    elif state == "over":
        f.rect(165, 120, 350, 86, 14)
        f.fill(40, 60, 90)
        f.text(f"Oh no! Score {score}", 340, 145)
        f.text_size(15)
        f.text("Make a sound or press space to fly again", 340, 172)
        f.text_size(13)
        f.text("S: voice settings", 340, 194)


f.run()
