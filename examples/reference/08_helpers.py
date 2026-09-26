import math

import funground as f


def setup():
    f.size(640, 400)


def draw():
    f.background("white")
    f.random_seed(7)                 # same seed, same numbers: the dots stay put

    for _ in range(40):
        x = f.constrain(f.random(f.width), 20, f.width - 20)      # keep inside the window
        y = f.constrain(f.random(f.height), 20, f.height - 20)
        if f.distance(x, y, f.width / 2, f.height / 2) < 120:
            f.fill("tomato")
        else:
            f.fill("skyblue")
        f.circle(x, y, 20)

    # radians() and degrees() convert for math.sin / math.cos
    # (rotate() itself takes degrees, so they are only needed for trigonometry).
    f.stroke("navy")
    f.stroke_width(3)
    for deg in range(0, 360, 5):
        f.point(140 + deg, 200 + 60 * math.sin(f.radians(deg)))
    f.fill("black")
    f.text(f"atan2 -> {f.degrees(math.atan2(1, 1)):.0f} degrees", 20, 360)


f.run()
