import funground as f


def setup():
    f.size(640, 400)


def draw():
    f.background("white")
    f.circle(100, 80, 40)            # x, y, diameter
    f.ellipse(220, 80, 100, 50)      # center x, center y, width, height
    f.rect(40, 160, 120, 60)         # top-left x, y, width, height
    f.line(220, 160, 340, 220)       # x1, y1, x2, y2
    f.point(400, 100)

    for x in range(60, 601, 60):
        f.circle(x, 300, 30)


f.run()
