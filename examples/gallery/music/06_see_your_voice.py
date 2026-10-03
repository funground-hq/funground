"""Music: see your voice

Sing, hum or talk to your microphone and watch three views of the same sound. The top
one is the wave: how the air moves, over the last half second. The middle one is the
spectrum: how strong each pitch is right now, low on the left and high on the right.
The bottom one is the pitch line: the note you sing, scrolling across, with faint guide
lines for the notes. It leaves a gap when you are quiet. Nothing is recorded or played
back. With no microphone to hear, the sketch still runs, and just shows quiet.
"""
# gallery: time-dependent
import funground as f

mic = f.microphone()


def setup():
    f.size(520, 440)
    mic.start()
    f.text_align("left", "top")


def label(message, y):
    f.no_stroke()
    f.fill(150)
    f.text_size(13)
    f.text(message, 20, y)


def draw():
    f.background(18, 20, 30)

    label("the wave", 10)
    f.fill(60, 150, 220, 160)
    f.stroke(120, 200, 255)
    f.stroke_width(1)
    f.draw_wave(mic, 20, 30, 480, 90)

    label("the spectrum", 135)
    f.fill(250, 170, 60)
    f.no_stroke()
    f.draw_spectrum(mic, 20, 155, 480, 90, bands=40)

    label("the pitch line", 255)
    f.no_fill()
    f.stroke(120, 235, 150)
    f.stroke_width(3)
    f.draw_pitch_line(mic, 20, 292, 480, 136, seconds=6, low="C3", high="C6")


f.run()
