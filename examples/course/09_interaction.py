# Original Funground course sketch. CC0; see ../LICENSE.

import funground as f

opened = False

def inside_ring(x, y):
    return (x - 210)**2 + (y - 135)**2 < 65**2

def setup():
    f.size(420, 300)

def draw():
    hover = inside_ring(f.mouse_x, f.mouse_y)
    f.background("#f3efe6")
    f.no_fill()
    f.stroke("#2a9d8f" if opened else "#264653")
    f.stroke_width(8 if hover else 3)
    f.circle(210, 135, 130)
    f.no_stroke()
    f.fill("#e76f51")
    f.circle(210, 135, 55 if opened else 18)
    f.fill("#264653")
    f.text_align("center", "top")
    f.text_size(17)
    message = "Open. Click again to close." if opened else "Move into the ring, then click."
    f.text(message, 210, 240)
    if f.frame_count == 0:
        f.save("09_interaction.png")

def mouse_pressed():
    global opened
    if inside_ring(f.mouse_x, f.mouse_y):
        opened = not opened

f.run()
