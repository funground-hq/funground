"""Pause, step and quit

no_loop() stops draw() being called every frame (it still runs once); a key callback can call
redraw() to draw one more frame or loop() to carry on. is_looping() says which it is doing, and
exit() ends the sketch.
"""
import funground as f

angle = 0


def setup():
    f.size(640, 400)
    f.no_loop()                           # start paused: draw() runs once


def draw():
    global angle
    f.background("white")
    with f.saved_state():
        f.translate(320, 200)
        f.rotate(angle)
        f.fill("gold")
        f.stroke("black")
        f.rect(-80, -80, 160, 160)
    angle += 6
    f.fill("black")
    f.text_size(18)
    state = "running" if f.is_looping() else "paused"
    f.text(f"{state}, frame {f.frame_count}  -  space: run/pause   s: one step   q: quit", 20, 30)


def key_pressed():
    if f.key == " ":
        if f.is_looping():
            f.no_loop()
        else:
            f.loop()
    elif f.key == "s":
        f.redraw()                        # exactly one more frame
    elif f.key == "q":
        f.exit()


f.run()
