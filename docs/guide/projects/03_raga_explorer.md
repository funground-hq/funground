# Project 3: Raga explorer

This project is for music learners, and it is only possible in funground. You pick a raga. You hear
its way up and its way down over a drone, and you watch each swara light up. Then you sing it, and
the page shows which swaras you sang.

Read [chapter 17](../17_ragas_and_talas.md) first if you have not. A raga is more than its notes. This
project works with the notes, and it says so on the screen.

## How it works

**The data.** `f.ragas()` gives the names, and `f.raga(name)` gives the facts for one. The page is
drawn from them: `raga.swaras` says which rows of the ladder are dark, `raga.vadi` and `raga.samvadi`
get a coloured border, and `raga.aroha` and `raga.avaroha` are the notes for the tune.

**The tune.** The aroha and avaroha are sargam strings. They are joined with a rest between, and a
glide (`~`) goes into the last note. `sa=` says which note is Sa, and `tuning="just"` gives the
pure intervals.

```py
up = raga.aroha.split()
down = raga.avaroha.split()
tokens = up + ["-"] + down[:-2] + [down[-2] + "~" + down[-1] + ":2"] + ["-", "-"]
tune = f.melody(" ".join(tokens), tempo=TEMPO, sa=SA, tuning="just").reverb(0.3)
```

**The drone.** `f.drone()` makes the steady tanpura note. A raga with no Pa (Marwa) gets Ni on its
first string, from the `pattern`. A reverb makes it warm, and the small `room()` function folds the
echo back onto the start, so the loop has no gap. Sounds are made the first time they are needed
and kept in a dictionary.

```py
pattern = "P S' S' S" if "P" in raga.swaras else "N S' S' S"
drones[pattern] = room(f.drone("D3", 7, pattern=pattern), 0.4)
```

**The playback.** The beat that is sounding comes from the clock of the tune itself, so the ladder
and the sound cannot drift apart. The mark on a note (the apostrophe or comma) is taken off to find
its row.

```py
heard = lit[min(int(tune.current_time() / BEAT), len(lit) - 1)]
```

**Singing.** The microphone's pitch is folded into one octave and smoothed, as in stage 2. A row
turns red if you sing a swara the raga does not use. A variable called `mode` says what the page is
doing: `idle`, `listen`, `sing`, `thinking` or `result`.

## Stage 1: make it work

Hear one raga. `f.raga("Bhupali")` gives its facts. Its aroha and avaroha are sargam strings, so
they go straight into `f.melody`. A ladder of the twelve swaras lights the one that is sounding.
Rows the raga does not use stay dark.

```python
import funground as f

SA = "D4"
TEMPO = 80
SWARAS = "SrRgGmMPdDnN"
raga = f.raga("Bhupali")
steps = (raga.aroha + " - " + raga.avaroha).split()      # "-" is a rest
tune = f.melody(" ".join(steps), tempo=TEMPO, sa=SA, tuning="just")
drone = f.drone("D3", 8, volume=0.4)


def setup():
    f.size(420, 370)
    f.text_size(16)
    f.text_align("left", "center")
    tune.loop()
    drone.loop()


def draw():
    f.background("#1b1424")
    step = min(int(tune.current_time() / (60 / TEMPO)), len(steps) - 1)
    sounding = steps[step].rstrip("',")            # S' and N, are S and N on the ladder
    f.no_stroke()
    for i, swara in enumerate(SWARAS):
        y = 330 - i * 28
        if swara == sounding:
            f.fill("gold")
        elif swara in raga.swaras:
            f.fill("#7a4fa0")
        else:
            f.fill("#2c2236")
        f.rect(20, y - 12, 380, 24, 6)
        f.fill("black" if swara == sounding else "white")
        f.text(swara, 30, y)


f.run()
```

The drone is quieter than the tune, as a tanpura is under a singer. Change `"Bhupali"` to
another name from `f.ragas()` and listen to how it changes.

## Stage 2: make it yours

**Choose the raga.** Make a slider over the list of names. Make it in `setup()`. When its value
changes, make the tune again.

```py
NAMES = f.ragas()
picker = f.create_slider(0, len(NAMES) - 1, 0, step=1, label="raga")

if NAMES[picker.value()] != raga.name:
    raga = f.raga(NAMES[picker.value()])         # then make the tune and the drone again
```

**Show the facts.** The raga has `thaat`, `vadi`, `samvadi` and `time`. Draw them as text, and
draw a ring round the vadi row and the samvadi row on the ladder.

**Add a glide.** In Indian music the voice slides between notes. `S~G` in a melody is a meend, a
glide from S to G. Glide into the last note of the avaroha:

```py
down = raga.avaroha.split()
ending = down[-2] + "~" + down[-1] + ":2"      # for example R~S:2, a glide over two beats
tune = f.melody(" ".join(down[:-2] + [ending]), tempo=80, sa=SA, tuning="just")
```

**Give it a room.** `.reverb(0.3)` on the tune and `.reverb(0.4)` on the drone make them sound
warmer. A drone with reverb rings on after its end, and it would stop with a gap when it loops.
Fold the ringing back onto the start. The gallery example has a small function, `room()`, that does it.

**Sing it back.** Now add the microphone. It gives `mic.pitch()`, the pitch of the note you sing.
Turn it into a row on the ladder: how many semitones above Sa, folded into one octave. Then you
can sing in any octave that suits you.

A raw pitch line jumps about. Three small steps make it calm. They are the same ones as in the
gallery example "A sargam phrase over a drone".

1. **Gate.** Ignore the microphone when `mic.level()` is low. That is breath and room noise.
2. **Fold.** Keep the pitch in one octave, so a slip to the next octave lands on the right row.
3. **Smooth.** Take the middle one of the last five readings. Break the line when the voice jumps.

```python
import math

import funground as f

SA = "D4"
SA_HZ = f.note_to_frequency(SA)
SWARAS = "SrRgGmMPdDnN"
raga = f.raga("Bhupali")
mic = f.microphone()
drone = f.drone("D3", 8, volume=0.4)
trail = []                                       # the pitch line, in rows above Sa
recent = []


def next_point():
    """A row above Sa (0 is S, 11 is N), or None when there is nothing to draw."""
    hz = mic.pitch() if mic.level() > 0.001 else None       # gate
    if hz is None:
        del recent[:]
        return None
    here = (12 * math.log2(hz / SA_HZ) + 0.5) % 12 - 0.5    # fold into one octave
    if recent and abs(here - sorted(recent)[len(recent) // 2]) > 2:
        recent[:] = [here]                       # a jump: break the line
        return None
    recent.append(here)
    del recent[:-5]
    return sorted(recent)[len(recent) // 2]      # smooth: the middle of the last five


def setup():
    f.size(420, 370)
    f.text_size(16)
    f.text_align("left", "center")
    drone.loop()
    mic.start()


def draw():
    trail.append(next_point())
    del trail[:-90]
    f.background("#1b1424")
    f.no_stroke()
    for i, swara in enumerate(SWARAS):
        y = 330 - i * 28
        f.fill("#7a4fa0" if swara in raga.swaras else "#2c2236")
        f.rect(20, y - 12, 380, 24, 6)
        f.fill("white")
        f.text(swara, 30, y)
    f.stroke("hotpink")
    f.stroke_width(3)
    last = None
    for k, row in enumerate(trail):
        point = None if row is None else (60 + k * 4, 330 - row * 28)
        if point and last:
            f.line(*last, *point)
        last = point


f.run()
```

Wear headphones, so the drone does not get into the microphone. Sing with Sa on D. If the line
does not move, lower `0.001` in the gate. If it jumps about in a noisy room, raise it, to `0.005`
for example. (`0.001` is very quiet. Laptop microphones are.)

**Count what you sang.** `mic.capture(seconds)` gives a sound of the last few seconds you sang.
Count the swaras in it, and let `f.match_ragas` say which ragas use those notes.

```py
heard = mic.capture(10)                          # the last 10 seconds, as a sound
shares = heard.swara_histogram(SA)               # 12 numbers: how long each swara sounded
if sum(shares) > 0:                              # all zeros means nothing was heard
    for name, score in f.match_ragas(shares)[:3]:
        print(name, round(score, 2))
```

The first call takes a second or two, so call it once, when the singer presses "stop". Do not call
it in every frame. Draw the 12 shares as bars and the three scores as longer bars.

Be honest in what you write on screen. `match_ragas` compares notes. Bhupali and Deshkar use the
same five swaras, so it cannot tell them apart. What makes a raga is how it moves, and the
program does not hear that. Say so on the page.

## Stage 3: make it shine

The full version is in the gallery: `examples/gallery/projects/03_raga_explorer.py`. It has the
slider, the facts, the drone with reverb that loops without a gap, the tune with a meend into Sa,
the ladder that lights, and a "sing" mode with the calm pitch line. A row turns red when you sing a
swara the raga does not use. After "stop" it draws your swaras as bars and the three closest ragas
as longer bars, with a note that it compares notes only. Marwa has no Pa, so its drone has Ni on
the first string. The sounds are made the first time you press "listen", so that press takes a
moment.

## Challenge cards

- **Can you** change `SA` so the whole page suits your own voice? Use `"C#4"` or `"A3"`.
- **Can you** add a tala? Play `f.tala("Teentaal", tempo=80)` under the tune, and light the beat.
- **Can you** play the raga's `pakad` as well as the aroha and avaroha?
- **Can you** show the time of day as a sun or a moon, drawn with shapes?
- **Can you** keep the best match from each singing in a list, and show the last five?

**Back to:** [18. Projects](../18_projects.md)
