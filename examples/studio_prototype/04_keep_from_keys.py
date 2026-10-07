"""Press K to keep a frame (Play prototype)

A ring of squares turns slowly. The slider sets how far each square turns from the one inside it.
When a frame looks good, press K. f.keep() saves that frame into the studio folder, with the
slider's value and the frame number in its record.

How it works:
- key_pressed() runs once each time a key goes down. f.key says which key it was.
- f.keep() inside it keeps the next frame that is drawn. The picture, the copy of this file and
  the record are all written when that frame is complete, so they all describe the same frame.
- The record lists every control and its value, so you do not have to write the slider's value
  down yourself.
- The extra setting twist= is there to show that you can add your own notes as well.
"""
import funground as f


def setup():
    global twist
    f.size(480, 480)
    twist = f.create_slider(0, 30, 9, 1, label="twist")


def draw():
    f.background("#10131a")
    f.translate(f.width / 2, f.height / 2)
    f.no_fill()
    f.stroke_width(2)
    for i in range(28):
        with f.saved_state():
            f.rotate(f.frame_count * 0.4 + i * twist.value())
            f.stroke(f.lerp_color("#5bc0eb", "#fde74c", i / 28))
            side = 24 + i * 13
            f.rect(-side / 2, -side / 2, side, side)


def key_pressed():
    if f.key == "k":
        f.keep("this twist feels like a shell", twist=twist.value())


f.run()
