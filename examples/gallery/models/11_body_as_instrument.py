"""Body as instrument

Your right hand plays the notes of a raga: low at the hip, high above the head. Lift your right foot and put it down, and a drum sounds. A quiet drone hums underneath. With no camera, it uses a photo, so it still works, but you will need the camera to hear it change. It needs the models library, which is a separate install: funground-ml.

How it works:
- sangeet.raga("Bhupali") gives a record of the raga. Its aroha, the rising line, is the text "S R G P D S'", and split() cuts it into six swaras. sound.note_to_frequency(swara, sa=SA) turns each swara into a pitch, counted from D4 as Sa. sound.pluck makes a plucked-string sound. All six are made once, before the sketch starts, so playing them later costs no time.
- low is the height of your hip and high is a little above your head. Both are measured from your body on every frame, so the instrument still works if you step nearer or further away.
- f.map_range turns the height of your right wrist into a number from 0 to just under 6. int cuts that to a whole step from 0 to 5, and clamp=True keeps it inside that range when your hand goes below the hip or above the top.
- A note is played only when step differs from last_step. Without that check, the same note would restart 24 times a second.
- A stamp is a foot that was up and is now down. foot_is_up is true when the right ankle is higher than the left by more than a fifth of your torso length. The drum plays in the one frame where foot_was_up is true and foot_is_up is false. Using the torso as the unit, not a fixed number of pixels, keeps this working at any distance.
- sound.drone("D3", 8, volume=0.2).loop() starts a quiet drone that repeats for as long as the sketch runs.

Make it yours:
- Change the raga. sangeet.ragas() lists them all, among them Yaman, Durga and Bhairav. Listen to how the mood changes with the same movement.
- Come down by a different path: use raga.avaroha when the hand is falling.
- Give the left hand its own job, such as the volume: notes[step].set_volume(...).
- Replace the drum with a whole theka: sangeet.tala("Keherwa", tempo=100).loop().
- Two players: each one's hand plays a different octave. Change SA to "D3" for the second set of notes.
"""
import funground as f
from funground import camera, ml, sangeet, sound

SA = "D4"                                      # the note that Sa is tuned to
raga = sangeet.raga("Bhupali")
swaras = raga.aroha.split()                    # S R G P D S'
notes = [sound.pluck(sound.note_to_frequency(swara, sa=SA), 1.5) for swara in swaras]
drum = sound.tone(70, 0.3, volume=0.9, attack=0.005, decay=0.1, sustain=0.2)

still = f.load_image("data/standing_woman_640.jpg")      # used when there is no camera
still.resize(320, 480)
cam = None
last_step = -1
foot_was_up = False
stamps = 0


def setup():
    global cam
    f.size(640, 480)
    sound.drone("D3", 8, volume=0.2).loop()
    try:
        cam = camera.open()
        cam.start(640, 480)
    except RuntimeError:
        cam = None


def draw():
    global last_step, foot_was_up, stamps
    source = cam if cam is not None and cam.is_ready() else still
    f.background("black")
    f.image(source, 0, 0)
    body = ml.pose(source)
    if body is None:
        return
    torso = body.left_shoulder.dist(body.left_hip)
    low = body.right_hip.y                     # hand at the hip: the lowest note
    high = body.nose.y - torso * 0.5           # hand above the head: the highest note
    step = int(f.map_range(body.right_wrist.y, low, high, 0, len(notes) - 0.01, clamp=True))
    if step != last_step:
        notes[step].play()
        last_step = step
    foot_is_up = body.left_ankle.y - body.right_ankle.y > torso * 0.2
    if foot_was_up and not foot_is_up:
        drum.play()
        stamps += 1
    foot_was_up = foot_is_up
    band = (low - high) / len(notes)
    f.no_stroke()
    f.text_size(18)
    for i, swara in enumerate(swaras):
        y = low - (i + 1) * band
        if i == step:
            f.fill("gold")
        else:
            f.fill(255, 255, 255, 60)
        f.rect(550, y + 2, 70, band - 4, 6)
        f.fill("black")
        f.text(swara, 578, y + band / 2 - 10)
    f.fill("gold")
    f.circle(body.right_wrist.x, body.right_wrist.y, 18)
    f.fill("white")
    f.text(raga.name + "   stamps: " + str(stamps), 20, 16)


f.run(fps=24)
