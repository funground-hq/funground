import playground as p


def draw():
    p.background("white")
    p.fill("tomato")
    p.circle(p.width / 2, p.height / 2, 80)
    if p.frame_count > 200:
        p.stop()


p.run()
