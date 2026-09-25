"""Confetti

p.random(high) or p.random(low, high) gives a random number; p.random_seed(n) makes the same
"random" picture every time. constrain keeps a value in range; distance measures between points.
"""
import playground as p


def setup():
    p.size(640, 400)


def draw():
    p.random_seed(7)                 # the same confetti every frame
    p.background("white")
    p.no_stroke()
    for _ in range(160):
        x = p.random(p.width)
        y = p.constrain(p.random(-40, p.height + 40), 10, p.height - 10)
        near = p.distance(x, y, p.width / 2, p.height / 2) < 120
        p.fill("tomato" if near else "skyblue")
        p.circle(x, y, p.random(6, 18))


p.run()
