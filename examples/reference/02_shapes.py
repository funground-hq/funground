import funground as f


def setup():
    f.size(640, 400)


def draw():
    f.background("white")

    # The origin (0, 0) is the top-left corner: x grows to the right, y downwards.
    f.fill("black")
    corner = f"({f.width}, {f.height})"
    f.text("(0, 0)", 6, 4)
    f.text(corner, f.width - f.text_width(corner) - 6, f.height - 28)

    f.fill("white")
    f.stroke("black")
    f.circle(100, 80, 40)            # x, y, diameter
    f.ellipse(220, 80, 100, 50)      # centre x, centre y, width, height
    f.rect(40, 160, 120, 60)         # top-left x, y, width, height
    f.line(220, 160, 340, 220)       # x1, y1, x2, y2
    f.point(400, 100)                # a dot in the stroke colour

    # Fractional positions are honoured and every edge is anti-aliased (v0.6).
    f.circle(500.5, 80.25, 40)

    # Drawing many things with for
    for x in range(60, 601, 60):
        f.circle(x, 300, 30)


f.run()
