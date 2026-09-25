import playground as p


def setup():
    p.size(640, 400)                 # runs once: make the window


def draw():
    p.background("white")            # runs again and again, up to 60 times a second
    p.fill("tomato")
    p.circle(320, 200, 80)


p.run()                              # finds setup() and draw() in this file and starts
