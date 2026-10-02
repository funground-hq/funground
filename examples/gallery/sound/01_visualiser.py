"""Sound: play a tune and watch it

f.load_sound() reads a sound file. sound.loop() plays it over and over. While it plays,
sound.level() tells you how loud it is now, and sound.spectrum() tells you how strong
each range of pitch is: low notes on the left, high notes on the right. Both are
numbers from 0 to 1. With no sound device, the sketch still runs, in silence.
"""
# gallery: time-dependent
import funground as f

tune = f.load_sound("data/tune.wav")      # found next to this file
BANDS = 24


def setup():
    f.size(640, 400)
    tune.set_volume(0.5)
    tune.loop()


def draw():
    f.background("midnightblue")
    f.no_stroke()

    # the spectrum: one bar for each range of pitch
    bar_width = 600 / BANDS
    for i, strength in enumerate(tune.spectrum(BANDS)):
        height = 260 * strength
        f.fill(f.lerp_color("deepskyblue", "hotpink", i / BANDS))
        f.rect(20 + i * bar_width + 2, 300 - height, bar_width - 4, height)

    # the level: one wide bar below
    f.fill("white")
    f.rect(20, 330, 600 * min(1, tune.level() * 1.5), 30)
    f.text_size(14)
    f.text("level", 20, 385)
    f.text("pitch: low to high", 400, 385)


f.run()
