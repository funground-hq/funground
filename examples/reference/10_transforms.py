import playground as p


def setup():
    p.size(640, 400)


def draw():
    p.background("white")

    # translate() moves the origin: (0, 0) is now at (160, 200) on screen.
    p.translate(160, 200)
    p.fill("gold")
    p.stroke("black")
    p.rect(-40, -25, 80, 50)

    # push() remembers the transform AND the style; pop() brings both back.
    p.push()
    p.rotate(30)                     # degrees, clockwise on screen
    p.fill("tomato")
    p.no_stroke()
    p.rect(-40, -25, 80, 50)
    p.pop()                          # gold fill, black stroke, no rotation again

    # Transforms are cumulative: each rotate() adds to the one before.
    with p.saved_state():                  # push on entry, pop on exit, even after an error
        p.fill("skyblue")
        for _ in range(12):
            p.rect(60, -6, 60, 12)
            p.rotate(30)

    # scale() grows or shrinks later drawing; scale(2, 1) would stretch sideways.
    with p.saved_state():
        p.translate(220, -140)       # relative to the moved origin: (380, 60) on screen
        p.fill("yellowgreen")
        for _ in range(3):
            p.circle(0, 0, 40)
            p.translate(60, 0)
            p.scale(1.4)

    with p.saved_state():
        p.translate(260, 60)
        p.rotate(p.frame_count * 3)  # a little further every frame: it spins
        p.fill("navy")
        p.rect(-35, -35, 70, 70)

    # Every block above was undone, so this is placed from the origin set on line 11.
    p.text("transforms", -140, 160, "black")


p.run()
