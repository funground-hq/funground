import playground as p


def setup():
    p.size(640, 400)


def draw():
    p.background("white")

    # The origin (0, 0) is the top-left corner: x grows to the right, y downwards.
    p.fill("black")
    corner = f"({p.width}, {p.height})"
    p.text("(0, 0)", 6, 4)
    p.text(corner, p.width - p.text_width(corner) - 6, p.height - 28)

    p.fill("white")
    p.stroke("black")
    p.circle(100, 80, 40)            # x, y, diameter
    p.ellipse(220, 80, 100, 50)      # centre x, centre y, width, height
    p.rect(40, 160, 120, 60)         # top-left x, y, width, height
    p.line(220, 160, 340, 220)       # x1, y1, x2, y2
    p.point(400, 100)                # a dot in the stroke colour

    # Fractional positions are honoured and every edge is anti-aliased (v0.6).
    p.circle(500.5, 80.25, 40)

    # Drawing many things with for
    for x in range(60, 601, 60):
        p.circle(x, 300, 30)


p.run()
