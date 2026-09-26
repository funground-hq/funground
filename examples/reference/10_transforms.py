import funground as f


def setup():
    f.size(640, 400)


def draw():
    f.background("white")

    # translate() moves the origin: (0, 0) is now at (160, 200) on screen.
    f.translate(160, 200)
    f.fill("gold")
    f.stroke("black")
    f.rect(-40, -25, 80, 50)

    # push() remembers the transform AND the style; pop() brings both back.
    f.push()
    f.rotate(30)                     # degrees, clockwise on screen
    f.fill("tomato")
    f.no_stroke()
    f.rect(-40, -25, 80, 50)
    f.pop()                          # gold fill, black stroke, no rotation again

    # Transforms are cumulative: each rotate() adds to the one before.
    with f.saved_state():                  # push on entry, pop on exit, even after an error
        f.fill("skyblue")
        for _ in range(12):
            f.rect(60, -6, 60, 12)
            f.rotate(30)

    # scale() grows or shrinks later drawing; scale(2, 1) would stretch sideways.
    with f.saved_state():
        f.translate(220, -140)       # relative to the moved origin: (380, 60) on screen
        f.fill("yellowgreen")
        for _ in range(3):
            f.circle(0, 0, 40)
            f.translate(60, 0)
            f.scale(1.4)

    with f.saved_state():
        f.translate(260, 60)
        f.rotate(f.frame_count * 3)  # a little further every frame: it spins
        f.fill("navy")
        f.rect(-35, -35, 70, 70)

    # Every block above was undone, so this is placed from the origin set on line 11.
    f.text("transforms", -140, 160, "black")


f.run()
