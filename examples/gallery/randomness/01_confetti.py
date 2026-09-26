"""Confetti

f.random(high) or f.random(low, high) gives a random number; f.random_seed(n) makes the same
"random" picture every time. constrain keeps a value in range; distance measures between points.
"""
import funground as f


def setup():
    f.size(640, 400)


def draw():
    f.random_seed(7)                 # the same confetti every frame
    f.background("white")
    f.no_stroke()
    for _ in range(160):
        x = f.random(f.width)
        y = f.constrain(f.random(-40, f.height + 40), 10, f.height - 10)
        near = f.distance(x, y, f.width / 2, f.height / 2) < 120
        f.fill("tomato" if near else "skyblue")
        f.circle(x, y, f.random(6, 18))


f.run()
