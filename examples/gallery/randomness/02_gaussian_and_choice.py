"""Bell-curve randomness and random choices

random_gaussian gives numbers that cluster around a middle value, like heights in a class;
random_choice picks one item from a list. random_seed makes both repeat exactly.
"""
import playground as p

PALETTE = ["tomato", "gold", "seagreen", "skyblue", "orchid"]


def setup():
    p.size(640, 400)


def draw():
    p.random_seed(11)
    p.background("white")
    p.no_stroke()
    for _ in range(400):
        x = p.random_gaussian(320, 90)                     # most dots near the middle
        y = p.random_gaussian(200, 50)
        p.fill(p.random_choice(PALETTE))
        p.circle(x, y, 8)


p.run()
