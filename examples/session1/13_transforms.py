import funground as f


def setup():
    f.size(640, 400)


def draw():
    f.background("white")

    # Move the origin, then draw: everything after translate() is shifted.
    f.fill("gold")
    f.stroke("black")
    f.translate(120, 100)
    f.rect(-40, -25, 80, 50)

    # push() remembers the transform and the style; pop() brings them back.
    f.push()
    f.rotate(30)            # degrees, clockwise on screen
    f.fill("tomato")
    f.no_stroke()
    f.rect(-40, -25, 80, 50)

    f.push()                # nested: this one is inside the rotated space
    f.translate(150, 0)
    f.scale(0.5)
    f.fill("navy")
    f.rect(-40, -25, 80, 50)
    f.pop()

    f.pop()                 # back to gold fill, black stroke, no rotation

    # A fan of rectangles: each turn adds to the one before (transforms are cumulative).
    with f.saved_state():
        f.translate(280, 150)
        for _ in range(6):
            f.rect(0, -6, 100, 12)
            f.rotate(15)

    # A spinning square: frame_count makes it turn a little more each frame.
    with f.saved_state():
        f.translate(180, 150)
        f.rotate(f.frame_count * 3)
        f.fill("skyblue")
        f.rect(-30, -30, 60, 60)

    # Nothing above leaks out: this text is drawn at the shifted origin from line 12 only.
    f.text("transforms", 200, 220, "black")


f.run()
