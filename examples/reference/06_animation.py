import playground as p

x = 50
speed = 3


def setup():
    p.size(640, 400)


def draw():
    global x, speed                  # draw() assigns to them, so Python needs this line

    p.background("white")            # clears the previous frame; leave it out for trails
    p.fill("tomato")
    p.circle(x, p.height / 2, 40)

    x += speed                       # a little each frame is motion
    if x > p.width - 20 or x < 20:   # bounce off the sides
        speed = -speed

    p.fill("black")
    p.text_size(16)
    p.text(f"frame {p.frame_count}", 10, 10)
    if p.frame_count > 1000:
        p.stop()                     # ask the loop to end after this draw()


p.run()
