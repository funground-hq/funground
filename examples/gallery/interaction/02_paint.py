"""A paint program

Drag the mouse to paint. The wheel changes the brush, the keys r, g and b pick a colour, and c
clears the page. A right click drops a dot.

How it works:
- Callbacks are functions with special names, such as mouse_dragged(). You define them, and
  funground calls them when something happens.
- f.background("white") is in setup(), so it runs once. draw() never wipes the canvas, and the
  paint stays.
- mouse_dragged() draws a line from f.pmouse_x, f.pmouse_y (where the mouse was last frame) to
  f.mouse_x, f.mouse_y (where it is now). That joins the strokes up smoothly.
- mouse_pressed() checks f.mouse_button and draws a dot on a right click. mouse_wheel(delta)
  changes the brush size, and f.constrain() keeps it between 1 and 40.
- key_pressed() uses f.key to clear or to pick a colour. key_typed() prints the key to the console.
- draw() redraws the strip at the bottom each frame, so the words stay up to date.

Make it yours:
- Add colours: put "y": "gold" in the dictionary in key_pressed().
- Change the brush limits: 1 and 40 in f.constrain().
- Change the starting colour (colour = "navy") or the starting brush (brush = 8).
- Make the right click drop a bigger dot: change brush * 3 to brush * 6 in mouse_pressed().
- Delete the print line in key_typed() if you do not want the messages in the console.
"""
import funground as f

brush = 8
colour = "navy"


def setup():
    f.size(640, 400)
    f.background("white")             # once: the drawing stays on the canvas


def draw():
    f.no_stroke()
    f.fill("white")
    f.rect(0, 360, 640, 40)
    f.fill("black")
    f.text_size(14)
    f.text(f"drag to paint  |  wheel: brush {brush}  |  r g b: colour  |  c: clear  |  last key: {f.key}", 10, 372)


def mouse_dragged():
    f.stroke(colour)
    f.stroke_width(brush)
    f.line(f.pmouse_x, f.pmouse_y, f.mouse_x, f.mouse_y)


def mouse_pressed():
    if f.mouse_button == "right":     # right-click drops a dot
        f.no_stroke()
        f.fill(colour)
        f.circle(f.mouse_x, f.mouse_y, brush * 3)


def mouse_wheel(delta):
    global brush
    brush = int(f.constrain(brush - delta, 1, 40))


def key_pressed():
    global colour
    if f.key == "c":
        f.background("white")
    colour = {"r": "tomato", "g": "seagreen", "b": "navy"}.get(f.key, colour)


def key_typed():
    print("typed", f.key, f.key_code, f.is_key_pressed)


f.run()
