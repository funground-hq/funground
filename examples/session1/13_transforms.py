import playground as p


def setup():
    p.size(640, 400)


def draw():
    p.background("white")

    # Move the origin, then draw: everything after translate() is shifted.
    p.fill("gold")
    p.stroke("black")
    p.translate(120, 100)
    p.rect(-40, -25, 80, 50)

    # push() remembers the transform and the style; pop() brings them back.
    p.push()
    p.rotate(30)            # degrees, clockwise on screen
    p.fill("tomato")
    p.no_stroke()
    p.rect(-40, -25, 80, 50)

    p.push()                # nested: this one is inside the rotated space
    p.translate(150, 0)
    p.scale(0.5)
    p.fill("navy")
    p.rect(-40, -25, 80, 50)
    p.pop()

    p.pop()                 # back to gold fill, black stroke, no rotation

    # A fan of rectangles: each turn adds to the one before (transforms are cumulative).
    with p.state():
        p.translate(280, 150)
        for _ in range(6):
            p.rect(0, -6, 100, 12)
            p.rotate(15)

    # A spinning square: frame_count makes it turn a little more each frame.
    with p.state():
        p.translate(180, 150)
        p.rotate(p.frame_count * 3)
        p.fill("skyblue")
        p.rect(-30, -30, 60, 60)

    # Nothing above leaks out: this text is drawn at the shifted origin from line 12 only.
    p.text("transforms", 200, 220, "black")


p.run()
