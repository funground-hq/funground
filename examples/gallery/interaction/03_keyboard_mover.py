"""Move with the keyboard

Two ways to read the keyboard. For smooth movement, ask every frame whether a key is held:
p.key_down("left"). For one-off actions, define key_pressed(), which runs once per press;
p.key says which key it was. key_released() runs when the key comes back up.
"""
import playground as p

x, y = 320, 200
speed = 4
colour = "tomato"
message = "arrow keys move  |  space: change colour"


def setup():
    p.size(640, 400)


def draw():
    global x, y
    if p.key_down("left"):
        x -= speed
    if p.key_down("right"):
        x += speed
    if p.key_down("up"):
        y -= speed
    if p.key_down("down"):
        y += speed
    x = p.constrain(x, 20, p.width - 20)
    y = p.constrain(y, 20, p.height - 60)

    p.background("white")
    p.no_stroke()
    p.fill(colour)
    p.circle(x, y, 40)
    p.fill("black")
    p.text_size(14)
    p.text(message, 10, 372)


def key_pressed():
    global colour
    if p.key == " ":
        colour = "seagreen" if colour == "tomato" else "tomato"


def key_released():
    global message
    message = f"released: {p.key}"


p.run()
