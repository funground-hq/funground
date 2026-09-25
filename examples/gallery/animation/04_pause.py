"""Pause, step and quit

no_loop() stops draw() being called every frame (it still runs once); a key callback can call
redraw() to draw one more frame or loop() to carry on. is_looping() says which it is doing, and
exit() ends the sketch.
"""
import playground as p

angle = 0


def setup():
    p.size(640, 400)
    p.no_loop()                           # start paused: draw() runs once


def draw():
    global angle
    p.background("white")
    with p.saved_state():
        p.translate(320, 200)
        p.rotate(angle)
        p.fill("gold")
        p.stroke("black")
        p.rect(-80, -80, 160, 160)
    angle += 6
    p.fill("black")
    p.text_size(18)
    state = "running" if p.is_looping() else "paused"
    p.text(f"{state}, frame {p.frame_count}  -  space: run/pause   s: one step   q: quit", 20, 30)


def key_pressed():
    if p.key == " ":
        if p.is_looping():
            p.no_loop()
        else:
            p.loop()
    elif p.key == "s":
        p.redraw()                        # exactly one more frame
    elif p.key == "q":
        p.exit()


p.run()
