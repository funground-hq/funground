"""Bell-curve randomness and random choices

random_gaussian gives numbers that cluster around a middle value, like heights in a class;
random_choice picks one item from a list. random_seed makes both repeat exactly.
"""
import funground as f

PALETTE = ["tomato", "gold", "seagreen", "skyblue", "orchid"]


def setup():
    f.size(640, 400)


def draw():
    f.random_seed(11)
    f.background("white")
    f.no_stroke()
    for _ in range(400):
        x = f.random_gaussian(320, 90)                     # most dots near the middle
        y = f.random_gaussian(200, 50)
        f.fill(f.random_choice(PALETTE))
        f.circle(x, y, 8)


f.run()
