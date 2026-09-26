"""Movers with vectors

A Vector holds an x and a y together: a position, a velocity, a force. Each frame the forces
add to the velocity and the velocity adds to the position, just as in p5.js - methods like
add() and limit() change the vector itself. heading() gives the direction, for the arrows.
"""
import playground as p

movers = []


def setup():
    p.size(640, 400)
    p.random_seed(3)
    for i in range(6):
        position = p.Vector(80 + i * 95, 60)
        velocity = p.Vector.from_angle(p.random(0, 180), 4)
        movers.append([position, velocity])


def draw():
    p.background("midnightblue")
    gravity = p.Vector(0, 0.3)
    wind = p.Vector(0.05, 0)
    for position, velocity in movers:
        velocity.add(gravity).add(wind).limit(12)
        position.add(velocity)
        if position.y > p.height - 20:          # bounce off the floor, losing a little energy
            position.y = p.height - 20
            velocity.y *= -0.9
        if position.x < 20 or position.x > p.width - 20:
            velocity.x *= -1
            position.x = p.constrain(position.x, 20, p.width - 20)

        p.no_stroke()
        p.fill("gold")
        p.circle(position.x, position.y, 30)
        tip = position + velocity * 6            # operators make new vectors
        p.stroke("white")
        p.stroke_width(2)
        p.line(position.x, position.y, tip.x, tip.y)
        with p.saved_state():
            p.translate(tip.x, tip.y)
            p.rotate(velocity.heading())
            p.line(0, 0, -8, -5)
            p.line(0, 0, -8, 5)


p.run()
