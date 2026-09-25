"""Text

text_size sets the size in pixels; text is placed by its top-left corner. text_width measures a
message, which is how you centre it.
"""
import playground as p


def setup():
    p.size(640, 400)


def draw():
    p.background("white")
    p.fill("black")
    p.text_size(40)
    message = "Hello, Playground!"
    x = (p.width - p.text_width(message)) / 2      # centred
    p.text(message, x, 60)

    p.text_size(18)
    p.fill("gray40")
    p.text("placed by the top-left corner", 40, 160)
    p.text(3.14159, 40, 200)                        # numbers become text
    p.text(f"frame {p.frame_count}", 40, 240, color="tomato")


p.run()
