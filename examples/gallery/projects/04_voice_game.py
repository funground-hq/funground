"""Voice-controlled game

A little bird flies through gates, and your voice is the control. Say "aaah" and the bird goes
up. The louder you are, the higher it goes. Go quiet and it sinks. Fly through the gap in each
gate to score. Touch a gate and the game is over. If you have no microphone, or the room is too
quiet for shouting, press the space bar: each press hops the bird up, and a quick tap makes a
small hop.

Why loudness and not pitch? Loudness is easy to control and easy to measure: any sound at all
moves the bird, and it never goes missing. Pitch is harder. The microphone only reports a pitch
when it hears one clear note, so breathy sounds and noise give nothing, and the bird would
fall at the wrong moment. The game also listens to the room for half a second at the start, to
learn how quiet it is. Stay quiet then. It keeps learning how loud you are, so a whisper or a
shout can both fly the bird.
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
CALIBRATE = 30                             # frames spent listening to the quiet room at the start
LOW, HIGH = 50, GROUND - 28                # the bird stays between these heights

try:
    mic = f.microphone()
except RuntimeError:                       # no microphone on this computer: space still works
    mic = None

# Sound effects: all made from numbers, and made quiet enough to be pleasant.
sound_start = f.pluck("C5", 0.5, volume=0.4)
sound_point = f.note("G5", 0.18, volume=0.35)
sound_crash = f.tone(120, 0.45, wave="triangle", volume=0.45, release=0.3)

state = "ready"                            # ready, play or over
bird_y = 200.0
gates = []
score = 0
best = 0
floor = 0.0                                # how loud the quiet room is
quiet = []                                 # readings while listening to the room
loud = 0.1                                 # about how loud you can be: it follows your voice
heard = 0.0                                # the microphone level, smoothed
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
    f.size(W, H)
    f.random_seed(11)
    reset()
    if mic:
        mic.start()


def key_pressed():
    global hop
    if f.key == " ":
        hop = 1.0


def listen():
    """Turn the microphone into a number from 0 (quiet) to 1 (loud)."""
    global floor, loud, heard
    if mic is None:
        return 0.0
    level = mic.level()
    if f.frame_count < CALIBRATE:          # at the start, just learn the quiet of the room
        if f.frame_count > 5:
            quiet.append(level)
        floor = sum(quiet) / len(quiet) if quiet else 0.0
        return 0.0
    heard += (level - heard) * 0.35        # smooth the jumps
    loud = max(loud * 0.995, floor + 0.04, heard)    # follow your voice, slowly forgetting a big shout
    strength = (heard - floor - 0.01) / (loud - floor)
    return f.constrain(strength, 0, 1) if strength > 0.12 else 0.0     # a little noise does nothing


def hits(gate):
    """Does the bird touch the top or the bottom of this gate? Nearest point of each box, then a distance."""
    for top, bottom in ((0, gate["gap"] - GAP / 2), (gate["gap"] + GAP / 2, GROUND)):
        nearest_x = f.constrain(BIRD_X, gate["x"], gate["x"] + GATE_W)
        nearest_y = f.constrain(bird_y, top, bottom)
        if math.hypot(BIRD_X - nearest_x, bird_y - nearest_y) < BIRD_R - 1:
            return True
    return False


def update():
    global state, bird_y, voice, hop, score, best, crashed_at
    voice = max(listen(), hop)
    hop *= 0.93                            # a space bar press lifts the bird for a moment
    if hop < 0.05:
        hop = 0.0

    if state == "ready":
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


def draw():
    update()
    draw_scene()
    for gate in gates:
        draw_gate(gate)
    draw_bird()
    draw_meter()

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
        f.rect(165, 120, 350, 70, 14)
        f.fill(40, 60, 90)
        f.text("Say aaah to fly: louder is higher", 340, 145)
        f.text_size(15)
        f.text("or press the space bar" + ("" if mic else "  (no microphone found)"), 340, 172)
    elif state == "over":
        f.rect(165, 120, 350, 70, 14)
        f.fill(40, 60, 90)
        f.text(f"Oh no! Score {score}", 340, 145)
        f.text_size(15)
        f.text("Make a sound or press space to fly again", 340, 172)


f.run()
