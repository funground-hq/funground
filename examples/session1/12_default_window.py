import funground as f


def draw():
    f.background("white")
    f.fill("tomato")
    f.circle(f.width / 2, f.height / 2, 80)
    if f.frame_count > 200:
        f.stop()


f.run()
