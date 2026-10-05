# Project 4: Voice-controlled game

A bird flies through gates. Your voice is the control. This project uses the microphone,
collisions, a score and some sound effects. It works with the space bar too, so it also runs on a
computer with no microphone, and in a room too quiet for shouting.

## How it works

**Room calibration.** Microphones and rooms are different. So for the first second the game just
listens, and keeps the middle reading, in decibels, as the **floor**. The middle reading is not
moved by a single click or a cough.

```py
now = db(mic.level())                              # db(): 20 * log10(level)
if calibrating():
    quiet.append(now)
    floor = max(-80.0, sorted(quiet)[len(quiet) // 2])    # the median
```

**Decibels above the room.** After that, the reading is smoothed a little. The game then works out
how many decibels louder than the floor it is. This is `above`. It does not matter how quiet the
microphone is, only how much you rise above the room.

```py
heard += (now - heard) * 0.35                      # smooth the jumps
above = max(0.0, heard - floor)                    # decibels louder than the room
```

**The setup screen marks.** Two sliders hold two marks, in decibels above the room. Below
"starts to lift" the voice counts as 0. At "full height" it counts as 1. `settings()` keeps the top
mark a little above the bottom one. The setup screen draws both marks on a tall bar of `above`, and
a practice bird that uses the same numbers as the real bird.

```py
low, high = settings()                             # from the two sliders
return f.constrain((above - low) / (high - low), 0, 1)
```

**From voice to height.** The number from 0 to 1 sets a target height. Loud is up. The bird moves
a part of the way to the target in each frame, so it glides. The space bar adds a hop that fades
away, and the bigger of the two wins. This is also how the game works without a microphone.

```py
voice = max(listen(), hop)
target = HIGH - voice * (HIGH - LOW)               # loud is up
bird_y += (target - bird_y) * 0.14
```

## Stage 1: make it work

The bird. `mic.level()` is how loud the sound is, from 0 to 1. Laptop microphones can be very
quiet: a voice may only read 0.01. So the code turns the level into decibels, which show small
sounds as clearly as big ones, and the bird's height comes from that. Loud should mean up. The bird moves a part of the way each frame, so it glides and does not
jump. The space bar adds a hop. A computer with no microphone gives an error from `f.microphone()`,
so the sketch catches it and carries on with the keyboard.

```python
import math

import funground as f

try:
    mic = f.microphone()
except RuntimeError:                  # no microphone on this computer
    mic = None
bird_y = 300.0
hop = 0.0


def setup():
    f.size(480, 360)
    if mic:
        mic.start()


def key_pressed():
    global hop
    if f.key == " ":
        hop = 1.0


def draw():
    global bird_y, hop
    db = 20 * math.log10(mic.level() + 1e-9) if mic else -99     # decibels: -65 is a quiet room
    voice = f.constrain((db + 65) / 35, 0, 1)                    # 0 is quiet and 1 is loud
    voice = max(voice, hop)
    hop *= 0.93                                          # a hop fades away
    target = 330 - voice * 280                           # loud is up
    bird_y += (target - bird_y) * 0.14                   # move a part of the way
    f.background(150, 205, 245)
    f.no_stroke()
    f.fill("gold")
    f.circle(120, bird_y, 30)
    f.fill("black")
    f.circle(128, bird_y - 4, 5)
    f.fill(0, 0, 0, 60)
    f.rect(16, 330 - voice * 280, 14, voice * 280 + 1)    # the voice meter


f.run()
```

Say "aaah" and the bird goes up. If it does not rise much, make the `65` smaller. If it rises for
the slightest noise, make it bigger.

## Stage 2: make it yours

**Choose what controls the bird.** There are two good choices.

- **Loudness**, `mic.level()`. Any sound moves the bird, so it always answers. Use this.
- **Pitch**, `mic.pitch()`. High notes could be up. But the microphone only gives a pitch when it
  hears one clear note. Breath and noise give `None`, and the bird would fall at the wrong moment.

If you want a pitch game, treat `None` as "do nothing" and smooth the pitch first, as in [project 3](03_raga_explorer.md).

**Learn the room.** Rooms and microphones are not equally quiet. In the first half second, listen
and keep the middle reading, in decibels. Then measure how many decibels you are above it. A voice
15 decibels above the room counts as 0, and 45 decibels above counts as 1.

```py
db = 20 * math.log10(mic.level() + 1e-9)
if f.frame_count < 30:
    quiet.append(db)                                  # stay quiet for half a second
    floor = sorted(quiet)[len(quiet) // 2]            # the middle one: a click does not move it
else:
    voice = f.constrain((db - floor - 15) / 30, 0, 1)
```

**Let the player set up their voice.** Every voice and microphone is different, so do not make
the player edit the code. Show a set up screen before the game. It needs four things.

- **A room check.** Listen for a second, as above, and show the quiet level it found.
- **A live bar.** Show how many decibels above the room the voice is right now. Draw two marks on
  it: "starts to lift" and "full height".
- **Two sliders.** `f.create_slider()` makes a slider. Make them in `setup()`, and read them with
  `.value()`. One slider moves each mark. Arrow keys can move them too, in `key_pressed()`.
- **A practice bird.** It uses the same marks as the real bird, so the player can say "aaah" softly
  and then loudly, and see what will happen before the game begins.

```py
def settings():
    low = start_at.value()
    return low, max(full_at.value(), low + 5)      # the top mark stays a little above the bottom one


voice = f.constrain((above - settings()[0]) / (settings()[1] - settings()[0]), 0, 1)
```

Use a variable such as `state = "setup"` to say which screen is showing. The Enter key, or a
click on a "start game" button, changes it to `"ready"`. The `S` key can bring the setup screen back,
and the sliders keep their values.

**Add gates.** A gate is a dictionary: where it is, and the height of its gap. Each frame, move
every gate left. When one is off the screen, take it away and add a new one on the right.

**Check for a crash.** The bird is a circle and the parts of a gate are rectangles. Find the point
in the rectangle that is nearest to the bird, with `f.constrain`. If that point is closer than the
bird's radius, the bird has touched the gate.

```py
near_x = f.constrain(BIRD_X, gate_x, gate_x + GATE_W)
near_y = f.constrain(bird_y, top, bottom)
touching = math.hypot(BIRD_X - near_x, bird_y - near_y) < BIRD_R
```

**Score and best score.** Add one when a gate goes past the bird. Keep `best = max(best, score)`.

**Sound effects.** Make them once, at the top of the file, and play them when something happens.
Quiet is nicer, so give each a `volume`.

```py
sound_point = f.note("G5", 0.18, volume=0.35)          # a short bright note for a point
sound_crash = f.tone(120, 0.45, wave="triangle", volume=0.45, release=0.3)   # a low thud
sound_start = f.pluck("C5", 0.5, volume=0.4)           # a plucked string to begin

sound_point.play()
```

Here is the game in short: gates, a crash, a score, a best score and a space bar to start.

```python
import math

import funground as f

W, H = 480, 360
BIRD_X, BIRD_R, GATE_W, GAP = 100, 14, 56, 130

try:
    mic = f.microphone()
except RuntimeError:
    mic = None
sound_point = f.note("G5", 0.18, volume=0.35)
sound_crash = f.tone(120, 0.45, wave="triangle", volume=0.45, release=0.3)

bird_y, hop, score, best = 200.0, 0.0, 0, 0
playing = False
gates = []
quiet = []
floor = -80.0


def new_gate(x):
    return {"x": x, "gap": f.random(110, 260), "passed": False}


def restart():
    global gates, score, playing
    gates = [new_gate(400 + i * 190) for i in range(3)]
    score, playing = 0, True


def setup():
    global playing
    f.size(W, H)
    f.random_seed(5)
    if mic:
        mic.start()
    restart()
    playing = False                    # wait for the space bar


def key_pressed():
    global hop
    if f.key == " ":
        hop = 1.0
        if not playing:
            restart()


def touches(gate):
    for top, bottom in ((0, gate["gap"] - GAP / 2), (gate["gap"] + GAP / 2, H)):
        near_x = f.constrain(BIRD_X, gate["x"], gate["x"] + GATE_W)
        near_y = f.constrain(bird_y, top, bottom)
        if math.hypot(BIRD_X - near_x, bird_y - near_y) < BIRD_R:
            return True
    return False


def draw():
    global bird_y, hop, score, best, floor, playing
    voice = 0
    if mic:
        db = 20 * math.log10(mic.level() + 1e-9)       # loudness in decibels
        if f.frame_count < 30:                     # learn how quiet the room is
            quiet.append(db)
            floor = sorted(quiet)[len(quiet) // 2]    # the middle reading
        else:
            voice = f.constrain((db - floor - 15) / 30, 0, 1)
    voice = max(voice, hop)
    hop *= 0.93
    if playing:
        bird_y += ((H - 30 - voice * (H - 80)) - bird_y) * 0.14
        for gate in gates:
            gate["x"] -= 3
            if not gate["passed"] and gate["x"] + GATE_W < BIRD_X:
                gate["passed"] = True
                score += 1
                best = max(best, score)
                sound_point.play()
        if gates[0]["x"] < -GATE_W:
            gates.pop(0)
            gates.append(new_gate(gates[-1]["x"] + 190))
        if any(touches(g) for g in gates):
            playing = False
            sound_crash.play()

    f.background(150, 205, 245)
    f.no_stroke()
    f.fill(70, 150, 100)
    for gate in gates:
        f.rect(gate["x"], 0, GATE_W, gate["gap"] - GAP / 2)
        f.rect(gate["x"], gate["gap"] + GAP / 2, GATE_W, H)
    f.fill("gold")
    f.circle(BIRD_X, bird_y, BIRD_R * 2)
    f.fill(40, 60, 90)
    f.text_size(30)
    f.text(f"{score}   best {best}", 20, 40)
    if not playing:
        f.text_size(16)
        f.text("press the space bar to fly", 130, 200)


f.run()
```

## Stage 3: make it shine

The full version is in the gallery: `examples/gallery/projects/04_voice_game.py`. It has a sky with
a gradient, clouds and hills, a bird with a wing that flaps, and gates with caps. It opens on a
"Set up your voice" screen. It learns the room's quiet in the first second, then shows a tall bar of
your voice in decibels above the room, with two marks you can move: where the bird starts to lift,
and where it reaches full height. Use the up and down arrow keys, the left and right arrow keys, or
the two sliders under the game. A practice bird on the right shows the result. Press Enter to start,
`R` to measure the room again, and `S` on the ready or game over screen to come back and change
things. With no microphone, the screen says so and the space bar starts the game. A small "mic" bar
at the top shows what the microphone hears, so you
can see it hears you, and a bar on the left shows what the game uses. The game also shows the
name of the microphone. The game gets a little faster with
each point. After a crash it waits a moment before it starts again, so the shout that crashed you
does not start it at once. It plays a pluck to begin, a note for each point and a thud at the end.
The best score and your settings are kept while the game is open. The first screen is always the
same.

## Challenge cards

- **Can you** add a third slider to the setup screen for how quickly the bird falls? Use its value
  in place of the `0.14` that eases the bird toward its target.
- **Can you** make the gap smaller for each point, until it is only 100 pixels high?
- **Can you** use pitch and not loudness? Higher is up. Smooth it, and do nothing on `None`.
- **Can you** add a coin between the gates? Score two points if the bird touches it.
- **Can you** save the best score in a file, so it is still there next time?
- **Can you** swap the bird for a kite, a balloon or a rocket, and the gates for something else?

**Back to:** [18. Projects](../18_projects.md)
