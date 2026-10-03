"""Music: a song's fingerprint

A short song is built from two parts with f.melody() and put together with f.mix(). Then
f.spectrogram() turns the whole sound into a picture: time goes across, pitch goes up,
and the louder a pitch is, the brighter it is. You can see each note as a bright dash,
and the low bass notes along the bottom. Click to play the song, and a line shows where
it is. The picture is also saved as fingerprint.png. With no sound device the song plays
silently and keeps time.
"""
import funground as f

TEMPO = 140
LEAD = "C5 E5 G5 E5 C5:2  D5 F5 A5 F5 D5:2  E5 G5 B5 G5 E5:2  C5:4"
BASS = "C3:6 D3:6 E3:6 C3:4"

song = f.mix(f.melody(LEAD, tempo=TEMPO, wave="triangle"),
             f.melody(BASS, tempo=TEMPO, wave="sine"))
LEFT, TOP, WIDTH, HEIGHT = 50, 50, 440, 220
fingerprint = None


def setup():
    global fingerprint
    f.size(520, 320)
    f.fill(255, 150, 60)                      # the brightest colour in the picture
    fingerprint = f.spectrogram(song, WIDTH, HEIGHT)
    fingerprint.save("fingerprint.png")
    f.text_size(12)


def pitch_height(name):
    """How far down the picture a note is (the picture runs from 40 Hz to 16 kHz)."""
    from math import log
    return TOP + HEIGHT * (1 - log(f.note_to_frequency(name) / 40) / log(16000 / 40))


def draw():
    f.background(20)
    f.image(fingerprint, LEFT, TOP)

    # a few notes down the side
    f.no_stroke()
    f.fill(170)
    f.text_align("right", "center")
    for name in ("C3", "C4", "C5", "C6"):
        f.text(name, LEFT - 8, pitch_height(name))
    f.text_align("left", "top")
    f.text("click to play", LEFT, TOP + HEIGHT + 14)

    # where the song is now
    if song.is_playing():
        x = LEFT + WIDTH * song.current_time() / song.duration()
        f.stroke(255)
        f.stroke_width(2)
        f.line(x, TOP, x, TOP + HEIGHT)


def mouse_pressed():
    song.play()


f.run()
