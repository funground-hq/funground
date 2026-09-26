import funground as f


def setup():
    f.size(640, 400)


def draw():
    f.background("white")

    f.fill("gold")                   # inside colour of later shapes
    f.stroke("black")                # outline / line colour
    f.stroke_width(3)                # outline thickness, minimum 1
    f.circle(120, 120, 100)

    f.no_fill()                      # outline only
    f.stroke("tomato")
    f.rect(220, 70, 120, 100)

    f.fill("skyblue")
    f.no_stroke()                    # fill only
    f.ellipse(120, 300, 160, 80)

    f.stroke("navy")
    f.stroke_width(8)
    f.line(300, 250, 600, 350)       # lines and points use the stroke only
    f.point(560, 260)                # a dot about stroke_width across

    # Strokes are centred on the edge (v0.6): half of this 20-pixel band lies
    # outside the 100x100 square and half inside. The thin red rect is the geometry.
    f.fill("lightyellow")
    f.stroke("black")
    f.stroke_width(20)
    f.rect(440, 60, 100, 100)
    f.no_fill()
    f.stroke("red")
    f.stroke_width(1)
    f.rect(440, 60, 100, 100)


f.run()
