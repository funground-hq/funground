"""Move with the keyboard

Two ways to read the keyboard. For smooth movement, ask every frame whether a key is held:
f.key_down("left"). For one-off actions, define key_pressed(), which runs once per press;
f.key says which key it was. key_released() runs when the key comes back up.
"""
import funground as f

x, y = 320, 200
speed = 4
colour = "tomato"
message = "arrow keys move  |  space: change colour"


def setup():
    f.size(640, 400)


def draw():
    global x, y
    if f.key_down("left"):
        x -= speed
    if f.key_down("right"):
        x += speed
    if f.key_down("up"):
        y -= speed
    if f.key_down("down"):
        y += speed
    x = f.constrain(x, 20, f.width - 20)
    y = f.constrain(y, 20, f.height - 60)

    f.background("white")
    f.no_stroke()
    f.fill(colour)
    f.circle(x, y, 40)
    f.fill("black")
    f.text_size(14)
    f.text(message, 10, 372)


def key_pressed():
    global colour
    if f.key == " ":
        colour = "seagreen" if colour == "tomato" else "tomato"


def key_released():
    global message
    message = f"released: {f.key}"


f.run()
