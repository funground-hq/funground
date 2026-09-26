"""Movers with vectors

A Vector holds an x and a y together: a position, a velocity, a force. Each frame the forces
add to the velocity and the velocity adds to the position, just as in p5.js - methods like
add() and limit() change the vector itself. heading() gives the direction, for the arrows.
"""
import funground as f

movers = []


def setup():
    f.size(640, 400)
    f.random_seed(3)
    for i in range(6):
        position = f.Vector(80 + i * 95, 60)
        velocity = f.Vector.from_angle(f.random(0, 180), 4)
        movers.append([position, velocity])


def draw():
    f.background("midnightblue")
    gravity = f.Vector(0, 0.3)
    wind = f.Vector(0.05, 0)
    for position, velocity in movers:
        velocity.add(gravity).add(wind).limit(12)
        position.add(velocity)
        if position.y > f.height - 20:          # bounce off the floor, losing a little energy
            position.y = f.height - 20
            velocity.y *= -0.9
        if position.x < 20 or position.x > f.width - 20:
            velocity.x *= -1
            position.x = f.constrain(position.x, 20, f.width - 20)

        f.no_stroke()
        f.fill("gold")
        f.circle(position.x, position.y, 30)
        tip = position + velocity * 6            # operators make new vectors
        f.stroke("white")
        f.stroke_width(2)
        f.line(position.x, position.y, tip.x, tip.y)
        with f.saved_state():
            f.translate(tip.x, tip.y)
            f.rotate(velocity.heading())
            f.line(0, 0, -8, -5)
            f.line(0, 0, -8, 5)


f.run()
