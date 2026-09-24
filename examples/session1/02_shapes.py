import playground as p


def setup():
    p.size(640, 400)


def draw():
    p.background("white")
    p.circle(100, 80, 40)            # x, y, diameter
    p.ellipse(220, 80, 100, 50)      # center x, center y, width, height
    p.rect(40, 160, 120, 60)         # top-left x, y, width, height
    p.line(220, 160, 340, 220)       # x1, y1, x2, y2
    p.point(400, 100)

    for x in range(60, 601, 60):
        p.circle(x, 300, 30)


p.run()
