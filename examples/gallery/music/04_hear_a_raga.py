"""Music: hear a raga

Pick a raga with the slider or the left and right keys. Its aroha (the way up) and avaroha (the
way down) play over a drone, and each swara lights up as it sounds. The text gives its thaat,
vadi, samvadi, pakad and time of day, and the three ragas with the most similar swaras.

How it works:
- f.ragas() lists the names funground knows. f.raga(name) gives one raga, with .thaat, .swaras,
  .aroha, .avaroha, .vadi, .samvadi, .time and .pakad.
- f.drone() makes a steady background note, and f.melody() turns a string of swara names into a
  tune. Sa is the home note and "-" is a rest.
- The tune and the drone each use .reverb() and .loop(). The room() helper adds the echo's tail
  back onto the start, so the loop has no gap.
- Every frame, tune.current_time() divided by the length of a beat says which swara is sounding.
  That one is drawn in gold.
- f.create_slider() picks the raga, and choose() builds a new tune when the slider moves.
- f.match_ragas() takes how often each of the 12 swaras is used. It gives back the ragas whose
  swaras are most alike, best first.

Make it yours:
- Change SA from "C#4" to another note, such as "D4". The whole tune and its lights move to that
  key.
- Change TEMPO to make the tune slower or faster.
- Change tuning="just" to tuning="equal" in f.melody() and listen for the small differences.
- Play the pakad instead: build the tune from raga.pakad.split() instead of the aroha and avaroha.
- Change the background colour to fit raga.time, for example a dark blue for night ragas and a warm
  one for morning.
"""
# gallery: time-dependent
import funground as f

SA = "C#4"
TEMPO = 100
BEAT = 60 / TEMPO
SWARAS = "S r R g G m M P d D n N".split()
NAMES = f.ragas()


def room(sound, amount):
    """sound.reverb(amount), with the echo that runs past the end added back onto the start,
    so the sound still loops with no gap."""
    length = len(sound.samples())
    wet = sound.reverb(amount).samples()
    looped = wet[:length]
    for i, value in enumerate(wet[length:]):
        looped[i % length] += value
    return f.create_sound(looped)


drone = room(f.drone("C#3", 7), 0.4)      # reverb on the drone, and it still loops with no gap
drone.set_volume(0.6)                     # under the tune, as a tanpura sits under a singer
raga = None
tune = None
tokens = []
alike = []


def choose(index):
    """Make the tune for one raga: up, a rest, down, a longer rest."""
    global raga, tune, tokens, alike
    if tune:
        tune.stop()
    raga = f.raga(NAMES[index])
    tokens = raga.aroha.split() + ["-"] + raga.avaroha.split() + ["-", "-"]
    tune = f.melody(" ".join(tokens), tempo=TEMPO, sa=SA, tuning="just").reverb(0.3)
    tune.set_volume(0.8)
    tune.loop()
    # how often each of the 12 swaras is in the tune, to compare with every raga
    counts = [0] * 12
    for token in tokens:
        if token != "-":
            counts[SWARAS.index(token.rstrip("',"))] += 1
    alike = f.match_ragas(counts)[:3]


def setup():
    global picker
    f.size(640, 400)
    picker = f.create_slider(0, len(NAMES) - 1, 0, step=1, label="raga")
    drone.loop()
    choose(0)


def key_pressed():
    if f.key == "left":
        picker.value(max(0, picker.value() - 1))
    elif f.key == "right":
        picker.value(min(len(NAMES) - 1, picker.value() + 1))


def draw():
    if NAMES[picker.value()] != raga.name:
        choose(picker.value())
    f.background("#1b1424")

    # which token is sounding now
    step = int(tune.current_time() / BEAT) if tune.is_playing() else 0
    now = tokens[min(step, len(tokens) - 1)].rstrip("',")

    # the twelve swaras: the raga's in colour, the one sounding now bright
    f.text_align("center", "center")
    f.text_size(18)
    for i, swara in enumerate(SWARAS):
        x = 50 + i * 49
        used = swara in raga.swaras
        f.no_stroke()
        if swara == now:
            f.fill("gold")
        elif used:
            f.fill("#7a4fa0")
        else:
            f.fill("#2c2236")
        f.circle(x, 170, 40)
        f.fill("black" if swara == now else "white" if used else "#5b4d68")
        f.text(swara, x, 170)
        if swara in (raga.vadi, raga.samvadi):
            f.fill("orange")
            f.text("vadi" if swara == raga.vadi else "samvadi", x, 210)

    f.text_align("left", "center")
    f.fill("white")
    f.text_size(32)
    f.text(raga.name, 30, 70)
    f.text_size(15)
    f.fill("#d8c8e8")
    f.text(f"{raga.thaat} thaat.  {raga.time}", 30, 108)
    f.text("aroha:    " + raga.aroha, 30, 265)
    f.text("avaroha: " + raga.avaroha, 30, 290)
    f.text("pakad:    " + raga.pakad, 30, 315)
    f.text("most alike:  " + ",  ".join(f"{name} {score:.2f}" for name, score in alike), 30, 345)
    f.fill("#8a7a9a")
    f.text("left and right keys, or the slider: another raga", 30, 375)


f.run()
