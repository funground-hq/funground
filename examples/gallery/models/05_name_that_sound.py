"""Name that sound

Make a noise near your microphone: clap, whistle, hum, tap a glass, play some music, bark like a dog. The computer says what it
thinks it heard. The big word is its best guess. The bars below are its next guesses, and the longer the bar, the surer it is.
When the room goes quiet, the words go away. It needs the models library, which is a separate install: funground-ml.

How it works:
- ml.sound(mic) listens to the last second of the microphone, and works out a new answer about twice a second. It does this
  beside the sketch, so draw() never waits. It gives None when there is nothing to name.
- heard.name is the best guess and heard.score says how sure the model is, from 0 to 1. heard.next is a list of up to four
  more guesses, and each has its own name and score.
- heard.is_new is True in the one frame when a new answer arrives. Here it makes the small dot flash.
- The model often gives a broad name, such as "Music" or "Speech", and it can be wrong. That is why the other guesses are shown.
- While nothing is named, a circle that follows mic.level() shows that the microphone is working.
- The first run downloads the sound model (16 MB, once) into a models folder beside the sketch.

Make it yours:
- Change BAR_WIDTH to make the bars longer or shorter.
- Draw a picture for some names, such as a circle for "Clapping", and let it grow with heard.score.
- Keep a list of the names you have heard, and add to it when heard.is_new is True.
- Try ml.sound(mic.capture(3)) to name the last three seconds as one sound.
"""
import funground as f
from funground import ml, sound

BAR_WIDTH = 270
mic = sound.microphone()
flash = 0.0


def setup():
    f.size(640, 480)
    mic.start()


def draw():
    global flash
    heard = ml.sound(mic)
    f.background("navy")
    f.no_stroke()
    f.text_align("left", "center")
    f.fill("lightsteelblue")
    f.text_size(20)
    f.text("Name that sound", 40, 40)
    if heard is None:
        f.fill("steelblue")
        f.circle(320, 190, 50 + 300 * mic.level())
        f.fill("white")
        f.text_align("center", "center")
        f.text_size(24)
        f.text("Listening... make a sound", 320, 330)
        return
    if heard.is_new:
        flash = 1.0
    flash = max(0.0, flash - 0.08)
    f.fill("gold")
    f.circle(600, 40, 8 + 14 * flash)
    f.fill("white")
    f.text_size(52)
    f.text(heard.name, 40, 110)
    f.text_size(20)
    for i, guess in enumerate([heard] + list(heard.next)):
        y = 200 + i * 54
        f.fill("gold" if i == 0 else "lightsteelblue")
        f.text(guess.name, 40, y)
        f.fill("steelblue")
        f.rect(330, y - 12, BAR_WIDTH, 24)
        f.fill("gold" if i == 0 else "white")
        f.rect(330, y - 12, BAR_WIDTH * guess.score, 24)


f.run()
