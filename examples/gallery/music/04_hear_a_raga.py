"""Music: hear a raga

f.ragas() lists the ragas funground knows, and f.raga(name) tells you about one: its thaat
(parent scale), the swaras it uses, its aroha (the way up) and avaroha (the way down), its
vadi and samvadi (the two most important notes) and the time of day it belongs to. Pick a
raga with the slider or the left and right keys. Its aroha and avaroha play over a drone,
and each swara lights up as it sounds. Swaras the raga leaves out are dark.
f.match_ragas() then says which ragas use the most similar swaras: ragas that share
the same swaras come out almost level, as only the notes are compared.
"""
# gallery: time-dependent
import funground as f

SA = "C#4"
TEMPO = 100
BEAT = 60 / TEMPO
SWARAS = "S r R g G m M P d D n N".split()
NAMES = f.ragas()

drone = f.drone("C#3", 7)
drone.set_volume(0.5)
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
    tune = f.melody(" ".join(tokens), tempo=TEMPO, wave="triangle", sa=SA, tuning="just")
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
