import playground as p


def setup():
    p.size(640, 400)


def draw():
    p.background("white")

    p.fill("gold")                   # inside colour of later shapes
    p.stroke("black")                # outline / line colour
    p.stroke_width(3)                # outline thickness, minimum 1
    p.circle(120, 120, 100)

    p.no_fill()                      # outline only
    p.stroke("tomato")
    p.rect(220, 70, 120, 100)

    p.fill("skyblue")
    p.no_stroke()                    # fill only
    p.ellipse(120, 300, 160, 80)

    p.stroke("navy")
    p.stroke_width(8)
    p.line(300, 250, 600, 350)       # lines and points use the stroke only
    p.point(560, 260)                # a dot about stroke_width across

    # Strokes are centred on the edge (v0.6): half of this 20-pixel band lies
    # outside the 100x100 square and half inside. The thin red rect is the geometry.
    p.fill("lightyellow")
    p.stroke("black")
    p.stroke_width(20)
    p.rect(440, 60, 100, 100)
    p.no_fill()
    p.stroke("red")
    p.stroke_width(1)
    p.rect(440, 60, 100, 100)


p.run()
