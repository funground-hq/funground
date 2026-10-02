# 16. Sound

funground can play a sound file and listen to it as it plays. You can use that to make a picture
move with the music.

## Playing a sound

`f.load_sound("beep.wav")` reads a sound file. It can be a WAV, OGG or MP3 file. Like a picture, it
is looked for next to your sketch first, then in the current folder. You get a **sound** back.

```py
beep = f.load_sound("beep.wav")

beep.play()             # play from the start
beep.loop()             # play over and over
beep.pause()            # stop, but keep the place
beep.stop()             # stop and go back to the start
beep.set_volume(0.5)    # from 0 (silent) to 1 (full)
beep.is_playing()       # True or False
beep.duration()         # the length, in seconds
beep.current_time()     # how far into the sound it is now, in seconds
```

`play()` after `pause()` carries on from where it stopped. `play()` on a sound that is already
playing starts it again from the start. You can load as many sounds as you like, and they play
together.

A sound that is not looping stops by itself at the end, and `is_playing()` becomes `False`.

## Watching the sound

Two methods tell you what the sound is doing right now. Both are plain numbers from 0 to 1.

- `sound.level()` is how loud it is. It is 0 when the sound is not playing.
- `sound.spectrum(bands)` is a list of `bands` numbers, one for each range of pitch, from low notes
  to high notes. The default is 32 bands. A band is strong when the sound has a lot of that pitch.

This sketch makes a short tune file for itself, so it runs as it is. Then it plays the tune and
draws it as bars.

```python
import math
import struct
import wave

import funground as f

# Make a two-second file of two notes, so there is something to play.
with wave.open("tune.wav", "wb") as out:
    out.setnchannels(1)
    out.setsampwidth(2)
    out.setframerate(22050)
    for i in range(44100):
        note = 330 if i < 22050 else 880
        out.writeframes(struct.pack("<h", int(12000 * math.sin(2 * math.pi * note * i / 22050))))

tune = f.load_sound("tune.wav")


def setup():
    f.size(640, 400)
    tune.loop()


def draw():
    f.background("black")
    f.fill("white")
    for i, strength in enumerate(tune.spectrum(16)):
        f.rect(20 + i * 38, 380, 30, -300 * strength)
    f.circle(320, 40, 20 + 60 * tune.level())


f.run()
```

The gallery has a bigger one: [a tune and its bars](../gallery/README.md).

## Good to know

- **No sound device?** The sketch still works. With no speakers, or with `FUNGROUND_HEADLESS=1`,
  a sound loads and "plays" in silence. It keeps time, so `is_playing()`, `level()` and
  `spectrum()` give the same answers as if you could hear it.
- **Time, not speakers.** The place in the sound comes from the sketch's clock, not from the
  speakers. If the computer is slow to start the sound, the numbers can be a little ahead of what you
  hear.
- **Stereo** is mixed down to one channel before it is measured.
- **Speed.** `spectrum()` is worked out only when you ask, and at most once for each frame. It takes
  about a millisecond or two, so it is fine to call every frame.
- **Not drawing.** Sounds add nothing to the picture, to a saved file or to the list of drawing
  commands.
- **Mistakes.** A file that is not there gives `FileNotFoundError`, saying where it looked. A file
  that is not a sound gives `ValueError`. So do a volume outside 0 to 1 and `bands` outside 1 to
  256.

**Previous:** [15. Coming from DrawBot](15_coming_from_drawbot.md)
