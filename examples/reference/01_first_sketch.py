import funground as f


def setup():
    f.size(640, 400)                 # runs once: make the window


def draw():
    f.background("white")            # runs again and again, up to 60 times a second
    f.fill("tomato")
    f.circle(320, 200, 80)


f.run()                              # finds setup() and draw() in this file and starts
