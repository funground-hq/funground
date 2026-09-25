import math

import playground as p


def setup():
    p.size(640, 400)


def draw():
    p.background("white")
    p.random_seed(7)                 # same seed, same numbers: the dots stay put

    for _ in range(40):
        x = p.constrain(p.random(p.width), 20, p.width - 20)      # keep inside the window
        y = p.constrain(p.random(p.height), 20, p.height - 20)
        if p.distance(x, y, p.width / 2, p.height / 2) < 120:
            p.fill("tomato")
        else:
            p.fill("skyblue")
        p.circle(x, y, 20)

    # radians() and degrees() convert for math.sin / math.cos
    # (rotate() itself takes degrees, so they are only needed for trigonometry).
    p.stroke("navy")
    p.stroke_width(3)
    for deg in range(0, 360, 5):
        p.point(140 + deg, 200 + 60 * math.sin(p.radians(deg)))
    p.fill("black")
    p.text(f"atan2 -> {p.degrees(math.atan2(1, 1)):.0f} degrees", 20, 360)


p.run()
