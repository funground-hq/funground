import funground as f

x = 50
speed = 3


def setup():
    f.size(640, 400)


def draw():
    global x, speed                  # draw() assigns to them, so Python needs this line

    f.background("white")            # clears the previous frame; leave it out for trails
    f.fill("tomato")
    f.circle(x, f.height / 2, 40)

    x += speed                       # a little each frame is motion
    if x > f.width - 20 or x < 20:   # bounce off the sides
        speed = -speed

    f.fill("black")
    f.text_size(16)
    f.text(f"frame {f.frame_count}", 10, 10)
    if f.frame_count > 1000:
        f.stop()                     # ask the loop to end after this draw()


f.run()
