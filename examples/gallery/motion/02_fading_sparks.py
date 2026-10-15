"""Sparks that fade: a class and a list of objects

A spark fountain travels across the night. Every frame it throws a few new sparks into the air. Each
spark falls, turns from yellow to red and fades until it is gone, so the old ones do not vanish at once.

How it works:
- class Spark describes one spark: what it knows (its position, velocity and age, set in __init__) and
  what it can do (move, draw itself, say when it has faded). Spark(x, y) makes a new one.
- The list sparks holds every spark that is still alive. Each frame, draw() appends a few new ones.
- Each spark's age grows by 1 every frame. f.map_range() turns the age into its opacity, from 255
  (solid) down to 0, and f.lerp_color() turns it from yellow to red.
- with f.saved_state(): keeps each spark's f.opacity() to that spark alone.
- Faded sparks are dropped: the list is made again from only the sparks that are still alive.
  Without that, the list would grow for ever and the sketch would slow down.

Make it yours:
- Change NEW_EACH_FRAME to throw more or fewer sparks.
- Change LIFETIME: a longer life gives long, slow trails.
- Throw the sparks from the mouse: use Spark(f.mouse_x, f.mouse_y).
- Give Spark a colour of its own, chosen in __init__ with f.random_choice().
- Add a second class, such as Smoke, with its own list.
"""
import math

import funground as f

NEW_EACH_FRAME = 6
LIFETIME = 30          # frames from birth until the spark has faded away

sparks = []


class Spark:
    def __init__(self, x, y):
        self.position = f.Vector(x, y)
        self.velocity = f.Vector.from_angle(f.random(220, 320), f.random(4, 8))   # upwards, spread out
        self.age = 0

    def move(self):
        self.velocity.add(f.Vector(0, 0.15))      # gravity pulls it down
        self.position.add(self.velocity)
        self.age += 1

    def draw(self):
        life_used = self.age / LIFETIME
        with f.saved_state():
            f.opacity(f.map_range(self.age, 0, LIFETIME, 255, 0, clamp=True))
            f.fill(f.lerp_color("yellow", "red", life_used))
            f.circle(self.position.x, self.position.y, 14 - 10 * life_used)

    def faded(self):
        return self.age >= LIFETIME


def setup():
    f.size(640, 400)
    f.random_seed(5)
    f.no_stroke()


def draw():
    global sparks
    f.background("midnightblue")

    fountain_x = f.width / 2 + 220 * math.sin(f.frame_count * 0.06)
    for i in range(NEW_EACH_FRAME):
        sparks.append(Spark(fountain_x, f.height - 40))

    for spark in sparks:
        spark.move()
        spark.draw()
    sparks = [spark for spark in sparks if not spark.faded()]

    f.fill("white")
    f.text(f"{len(sparks)} sparks", 16, 28)


f.run()
